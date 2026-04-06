"""基于 TMM 与 Levenberg-Marquardt 的钙钛矿厚度反演脚本。

本脚本与 step01 数据解耦，只读取 data/processed/target_reflectance.csv
作为目标干涉光谱输入，不再重写绝对反射率标定逻辑。

模块划分：
1. 目标曲线读取
2. ITO 色散解析与插值
3. ITO 色散吸收补偿
4. PVK 外推 n-k 中间件加载与插值
5. BEMA 表面粗糙度修正
6. 厚玻璃非相干修正 + 相干薄膜 TMM
7. lmfit 六参数厚度反演
8. 结果绘图
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib
import numpy as np
import pandas as pd
from lmfit import Parameters, minimize
from scipy.io import loadmat
from tmm import coh_tmm

# 使用非交互式后端，保证在终端环境里也能稳定输出图片。
matplotlib.use("Agg")
import matplotlib.pyplot as plt


WAVELENGTH_MIN_NM = 850.0
WAVELENGTH_MAX_NM = 1100.0

GLASS_INDEX = 1.5
AIR_INDEX = 1.0
ITO_THICKNESS_NM = 105.0
NIOX_THICKNESS_NM = 20.0
SAM_THICKNESS_NM = 2.0
SAM_NK = 1.8 + 0.0j

INITIAL_PVK_BULK_THICKNESS_NM = 448.0
MIN_PVK_BULK_THICKNESS_NM = 400.0
MAX_PVK_BULK_THICKNESS_NM = 500.0
INITIAL_PVK_ROUGHNESS_THICKNESS_NM = 51.0
MIN_PVK_ROUGHNESS_THICKNESS_NM = 0.0
MAX_PVK_ROUGHNESS_THICKNESS_NM = 100.0
INITIAL_ITO_ALPHA = 12.0
MIN_ITO_ALPHA = 0.0
MAX_ITO_ALPHA = 30.0
INITIAL_THICKNESS_SIGMA_NM = 15.6
MIN_THICKNESS_SIGMA_NM = 0.0
MAX_THICKNESS_SIGMA_NM = 60.0
INITIAL_PVK_B_SCALE = 1.0
MIN_PVK_B_SCALE = 0.1
MAX_PVK_B_SCALE = 3.0
INITIAL_NIOX_K = 0.0
MIN_NIOX_K = 0.0
MAX_NIOX_K = 0.5


def get_project_root() -> Path:
    """根据脚本位置推导项目根目录。"""
    return Path(__file__).resolve().parents[2]


def normalize_column_name(name: str) -> str:
    """统一列名格式，减少大小写与空格差异带来的脆弱性。"""
    return "".join(str(name).strip().lower().split())


def find_required_column(columns: list[str], target: str) -> str:
    """在 DataFrame 列名中查找指定字段。"""
    normalized = {normalize_column_name(column): column for column in columns}
    key = normalize_column_name(target)
    if key not in normalized:
        raise ValueError(f"缺少必需列 {target}，现有列为: {columns}")
    return normalized[key]


def validate_interp_domain(
    target_wavelength: np.ndarray,
    source_wavelength: np.ndarray,
    source_name: str,
) -> None:
    """确认插值源完整覆盖目标波段，避免无提示外推。"""
    if target_wavelength.size == 0:
        raise ValueError("目标波长数组为空，无法继续计算。")
    if source_wavelength.size == 0:
        raise ValueError(f"{source_name} 数据为空，无法插值。")
    if target_wavelength.min() < source_wavelength.min() or target_wavelength.max() > source_wavelength.max():
        raise ValueError(
            f"{source_name} 的波长覆盖范围不足: "
            f"target=({target_wavelength.min():.2f}, {target_wavelength.max():.2f}) nm, "
            f"source=({source_wavelength.min():.2f}, {source_wavelength.max():.2f}) nm"
        )


def load_target_reflectance_csv(csv_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """读取 step01 导出的目标反射率曲线。

    约定输入文件必须包含两列：
    - Wavelength: 波长，单位 nm
    - R_smooth: 平滑绝对反射率，单位为 0-1 小数
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"未找到目标反射率文件: {csv_path}\n"
            "请先运行 src/scripts/step01_absolute_calibration.py 生成 data/processed/target_reflectance.csv。"
        )

    data = pd.read_csv(csv_path)
    wavelength_col = find_required_column(data.columns.tolist(), "Wavelength")
    reflectance_col = find_required_column(data.columns.tolist(), "R_smooth")

    wavelength = pd.to_numeric(data[wavelength_col], errors="coerce").to_numpy(dtype=float)
    reflectance = pd.to_numeric(data[reflectance_col], errors="coerce").to_numpy(dtype=float)

    valid_mask = np.isfinite(wavelength) & np.isfinite(reflectance)
    wavelength = wavelength[valid_mask]
    reflectance = reflectance[valid_mask]

    sort_index = np.argsort(wavelength)
    wavelength = wavelength[sort_index]
    reflectance = reflectance[sort_index]

    band_mask = (wavelength >= WAVELENGTH_MIN_NM) & (wavelength <= WAVELENGTH_MAX_NM)
    wavelength = wavelength[band_mask]
    reflectance = reflectance[band_mask]

    if wavelength.size == 0:
        raise ValueError("目标反射率文件在 850-1100 nm 内无有效数据。")
    if np.any((reflectance < 0.0) | (reflectance > 1.0)):
        raise ValueError("R_smooth 应为 0-1 范围内的绝对反射率小数。")
    # 这里不强求光谱仪采样点恰好落在 850.000 和 1100.000 nm，
    # 因为离散实测网格通常只会“覆盖附近”而不会精确命中边界。
    # 只要最小/最大波长在目标窗口的 1 nm 邻域内，就认为目标波段覆盖有效。
    boundary_tolerance_nm = 1.0
    if (
        wavelength.min() > WAVELENGTH_MIN_NM + boundary_tolerance_nm
        or wavelength.max() < WAVELENGTH_MAX_NM - boundary_tolerance_nm
    ):
        raise ValueError(
            "目标曲线未覆盖完整 850-1100 nm 波段，"
            f"实际范围为 ({wavelength.min():.2f}, {wavelength.max():.2f}) nm。"
        )

    return wavelength, reflectance


def maybe_convert_wavelength_to_nm(wavelength_raw: np.ndarray) -> np.ndarray:
    """智能判断 ITO 数据首列单位是 Angstrom 还是 nm。

    当前仓库里的 ITO 文件虽然扩展名是 .mat，但内容实际是文本表，
    首列范围约为 2100-16900。如果直接把它当作 nm，会导致数据库波段变成
    2100-16900 nm，完全无法覆盖本项目的 850-1100 nm。这里做一个稳健约定：

    - 若量级明显大于 2000，则视为 Angstrom，除以 10 转成 nm
    - 若量级在常见近紫外到近红外范围 200-2000，则直接视为 nm
    """
    if wavelength_raw.size == 0:
        raise ValueError("ITO 波长数组为空。")

    max_value = float(np.nanmax(wavelength_raw))
    min_value = float(np.nanmin(wavelength_raw))

    if max_value > 2000.0:
        wavelength_nm = wavelength_raw / 10.0
    elif min_value >= 100.0 and max_value <= 2000.0:
        wavelength_nm = wavelength_raw.copy()
    else:
        raise ValueError(
            "无法自动识别 ITO 波长单位。"
            f"原始范围为 ({min_value:.2f}, {max_value:.2f})，既不像常规 nm，也不像 Angstrom。"
        )
    return wavelength_nm


def extract_mat_candidate_arrays(mat_data: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """尽可能从 MAT 字典中抽取 wavelength/e1/e2 三列。

    这里做轻量泛化匹配，兼容常见键名形式。若无法可靠识别，则返回 None，
    交给文本解析分支处理。
    """
    arrays: dict[str, np.ndarray] = {}
    for key, value in mat_data.items():
        if key.startswith("__"):
            continue
        array = np.asarray(value).squeeze()
        if array.ndim != 1 or array.size == 0:
            continue
        arrays[normalize_column_name(key)] = array.astype(float, copy=False)

    wavelength = None
    e1 = None
    e2 = None

    for key, array in arrays.items():
        if wavelength is None and ("wavelength" in key or key in {"wl", "lambda", "energy"}):
            wavelength = array
        elif e1 is None and key in {"e1", "eps1", "epsilon1", "real", "realpart"}:
            e1 = array
        elif e2 is None and key in {"e2", "eps2", "epsilon2", "imag", "imagpart"}:
            e2 = array

    if wavelength is None or e1 is None or e2 is None:
        return None
    if not (wavelength.size == e1.size == e2.size):
        raise ValueError("MAT 文件中的 wavelength/e1/e2 长度不一致。")
    return wavelength, e1, e2


def parse_text_ito_table(ito_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """按三列表格解析 ITO 数据文件。

    当前本地文件的真实格式为：
    - 第 1 行：文献信息
    - 第 2 行：ANGSTROMS
    - 第 3 行：E1E2
    - 之后每行三列：波长、e1、e2
    """
    rows: list[list[float]] = []
    with ito_path.open("r", encoding="utf-8-sig") as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) != 3:
                continue
            try:
                rows.append([float(value) for value in parts])
            except ValueError:
                continue

    if not rows:
        raise ValueError(f"无法从 ITO 文本文件中解析出三列数值数据: {ito_path}")

    data = np.asarray(rows, dtype=float)
    wavelength_raw = data[:, 0]
    e1 = data[:, 1]
    e2 = data[:, 2]
    return wavelength_raw, e1, e2


def load_ito_dispersion(ito_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """读取 ITO 介电函数数据库。

    先尝试满足原始要求，使用 scipy.io.loadmat。
    若文件实际上不是可读的 MATLAB 二进制，或者没有可识别的字段，
    则自动回退到文本表解析。
    """
    wavelength_raw: np.ndarray
    e1: np.ndarray
    e2: np.ndarray

    try:
        mat_data = loadmat(ito_path)
        extracted = extract_mat_candidate_arrays(mat_data)
        if extracted is None:
            raise ValueError("MAT 文件中未识别出 wavelength/e1/e2 三列。")
        wavelength_raw, e1, e2 = extracted
    except Exception:
        wavelength_raw, e1, e2 = parse_text_ito_table(ito_path)

    wavelength_nm = maybe_convert_wavelength_to_nm(np.asarray(wavelength_raw, dtype=float))
    e1 = np.asarray(e1, dtype=float)
    e2 = np.asarray(e2, dtype=float)

    valid_mask = np.isfinite(wavelength_nm) & np.isfinite(e1) & np.isfinite(e2)
    wavelength_nm = wavelength_nm[valid_mask]
    e1 = e1[valid_mask]
    e2 = e2[valid_mask]

    sort_index = np.argsort(wavelength_nm)
    wavelength_nm = wavelength_nm[sort_index]
    e1 = e1[sort_index]
    e2 = e2[sort_index]

    if wavelength_nm.size == 0:
        raise ValueError("ITO 数据清洗后为空。")

    return wavelength_nm, e1, e2


def convert_dielectric_to_nk(e1: np.ndarray, e2: np.ndarray) -> np.ndarray:
    """将介电常数实部/虚部转换为复折射率 n + ik。"""
    magnitude = np.sqrt(e1**2 + e2**2)
    n = np.sqrt(np.maximum((magnitude + e1) / 2.0, 0.0))
    k = np.sqrt(np.maximum((magnitude - e1) / 2.0, 0.0))
    return n + 1j * k


def build_ito_interpolator(wavelength_nm: np.ndarray, nk: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
    """构造 ITO 复折射率插值函数。"""

    def get_ito_nk(query_wavelength_nm: np.ndarray) -> np.ndarray:
        query = np.asarray(query_wavelength_nm, dtype=float)
        validate_interp_domain(query, wavelength_nm, "ITO 数据库")
        real_part = np.interp(query, wavelength_nm, np.real(nk))
        imag_part = np.interp(query, wavelength_nm, np.imag(nk))
        return real_part + 1j * imag_part

    return get_ito_nk


def apply_dispersive_absorption_correction(
    base_nk: np.ndarray,
    wavelength_nm: np.ndarray,
    alpha_ito: float,
) -> np.ndarray:
    """锁定 ITO 实部 n，仅对虚部 k 施加长波增强的色散放大。"""
    base_nk_array = np.asarray(base_nk, dtype=np.complex128)
    wavelength = np.asarray(wavelength_nm, dtype=np.float64)
    x_norm = (wavelength - 850.0) / (1100.0 - 850.0)
    x_norm = np.clip(x_norm, 0.0, 1.0)
    dynamic_multiplier = 1.0 + alpha_ito * (x_norm**2)
    n_base = np.real(base_nk_array)
    k_base = np.imag(base_nk_array)
    k_new = k_base * dynamic_multiplier
    return n_base + 1j * k_new


def load_pvk_dispersion(csv_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """读取 [LIT-0001] 数字化后经 Cauchy 外推得到的 CsFAPI n-k 中间件。"""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"未找到 PVK 扩展光谱文件: {csv_path}\n"
            "请先运行 src/scripts/step01b_cauchy_extrapolation.py 生成 data/processed/CsFAPI_nk_extended.csv。"
        )

    data = pd.read_csv(csv_path)
    wavelength_col = find_required_column(data.columns.tolist(), "Wavelength")
    n_col = find_required_column(data.columns.tolist(), "n")
    k_col = find_required_column(data.columns.tolist(), "k")

    wavelength_nm = pd.to_numeric(data[wavelength_col], errors="coerce").to_numpy(dtype=float)
    refractive_index = pd.to_numeric(data[n_col], errors="coerce").to_numpy(dtype=float)
    extinction_coefficient = pd.to_numeric(data[k_col], errors="coerce").to_numpy(dtype=float)

    valid_mask = np.isfinite(wavelength_nm) & np.isfinite(refractive_index) & np.isfinite(extinction_coefficient)
    wavelength_nm = wavelength_nm[valid_mask]
    refractive_index = refractive_index[valid_mask]
    extinction_coefficient = extinction_coefficient[valid_mask]

    sort_index = np.argsort(wavelength_nm)
    wavelength_nm = wavelength_nm[sort_index]
    refractive_index = refractive_index[sort_index]
    extinction_coefficient = extinction_coefficient[sort_index]

    if wavelength_nm.size == 0:
        raise ValueError("PVK 扩展光谱清洗后为空。")
    return wavelength_nm, refractive_index, extinction_coefficient


def build_pvk_interpolator(
    wavelength_nm: np.ndarray,
    refractive_index: np.ndarray,
    extinction_coefficient: np.ndarray,
) -> Callable[[np.ndarray], np.ndarray]:
    """构造 PVK 复折射率插值函数。"""

    def get_pvk_nk(query_wavelength_nm: np.ndarray) -> np.ndarray:
        query = np.asarray(query_wavelength_nm, dtype=float)
        validate_interp_domain(query, wavelength_nm, "PVK 扩展光谱")
        real_part = np.interp(query, wavelength_nm, refractive_index)
        imag_part = np.interp(query, wavelength_nm, extinction_coefficient)
        return real_part + 1j * imag_part

    return get_pvk_nk


def calc_bema_rough_nk(bulk_nk: np.ndarray) -> np.ndarray:
    """计算 50/50 PVK-Air Bruggeman EMA 粗糙层复折射率。"""
    eps1 = np.asarray(bulk_nk, dtype=np.complex128) ** 2
    eps2 = 1.0 + 0.0j
    b_term = 0.5 * (eps1 + eps2)
    eps_eff = 0.5 * (b_term + np.sqrt(b_term**2 + 2.0 * eps1 * eps2))
    return np.sqrt(eps_eff)


def calc_macro_reflectance(
    d_bulk_nm: float,
    d_rough_nm: float,
    ito_alpha: float,
    sigma_thickness_nm: float,
    pvk_b_scale: float,
    niox_k: float,
    wavelength_nm: np.ndarray,
    get_ito_nk: Callable[[np.ndarray], np.ndarray],
    get_pvk_nk: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    """计算包含厚玻璃非相干修正的宏观反射率。

    真实样品结构是：
    Air -> 1.1 mm Glass -> ITO -> NiOx -> SAM -> PVK_Bulk -> PVK_Roughness -> Air。

    关键点在于：1.1 mm 玻璃厚板绝不能直接放进相干 TMM 相位矩阵。

    原因是：
    - 玻璃厚度远大于光源与光谱系统的有效相干长度；
    - 玻璃内部的往返相位在真实实验里已经被平均掉；
    - 若把 1.1 mm 玻璃当作相干层，模型会产生大量实验上不可稳定观察的快速振荡。

    因此这里采用“前表面菲涅尔反射 + 后侧薄膜叠层相干反射 + 非相干强度级联”的结构：
    1. 先在 semi-infinite Glass 基底上计算后侧薄膜堆栈的相干反射率 R_coh；
    2. 再把玻璃前表面的 R_front 与 R_coh 按非相干多次反射公式组合成宏观 R_total。
    """
    wavelength = np.asarray(wavelength_nm, dtype=float)
    ito_base_nk = get_ito_nk(wavelength)
    ito_nk = apply_dispersive_absorption_correction(ito_base_nk, wavelength, ito_alpha)
    pvk_base_nk = get_pvk_nk(wavelength)
    n_base = np.real(pvk_base_nk)
    k_base = np.imag(pvk_base_nk)
    n_anchor = float(np.real(get_pvk_nk(np.array([1000.0], dtype=float)))[0])
    n_new = n_anchor + pvk_b_scale * (n_base - n_anchor)
    pvk_pert_nk = n_new + 1j * k_base
    pvk_rough_nk = calc_bema_rough_nk(pvk_pert_nk)
    niox_nk = 2.1 + 1j * niox_k
    r_front = ((GLASS_INDEX - AIR_INDEX) / (GLASS_INDEX + AIR_INDEX)) ** 2

    def calc_single_reflectance(single_d_bulk_nm: float) -> np.ndarray:
        r_coh = np.empty_like(wavelength, dtype=float)

        for index, wl_nm in enumerate(wavelength):
            n_list = [
                GLASS_INDEX + 0.0j,
                ito_nk[index],
                niox_nk,
                SAM_NK,
                pvk_pert_nk[index],
                pvk_rough_nk[index],
                AIR_INDEX + 0.0j,
            ]
            d_list = [
                np.inf,
                ITO_THICKNESS_NM,
                NIOX_THICKNESS_NM,
                SAM_THICKNESS_NM,
                single_d_bulk_nm,
                d_rough_nm,
                np.inf,
            ]
            tmm_result = coh_tmm("s", n_list, d_list, 0.0, wl_nm)
            r_coh[index] = float(tmm_result["R"])

        return r_front + (((1.0 - r_front) ** 2) * r_coh) / (1.0 - r_front * r_coh)

    if sigma_thickness_nm < 0.1:
        return calc_single_reflectance(d_bulk_nm)

    offsets_nm = np.linspace(-3.0 * sigma_thickness_nm, 3.0 * sigma_thickness_nm, 9, dtype=float)
    weights = np.exp(-(offsets_nm**2) / (2.0 * sigma_thickness_nm**2))
    weights /= np.sum(weights)

    r_total_averaged = np.zeros_like(wavelength, dtype=float)
    for offset_nm, weight in zip(offsets_nm, weights):
        r_total_averaged += weight * calc_single_reflectance(d_bulk_nm + offset_nm)
    return r_total_averaged


def residual(
    params: Parameters,
    wavelength_nm: np.ndarray,
    r_target: np.ndarray,
    get_ito_nk: Callable[[np.ndarray], np.ndarray],
    get_pvk_nk: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    """lmfit 残差函数。"""
    d_bulk_nm = params["d_bulk"].value
    d_rough_nm = params["d_rough"].value
    ito_alpha = params["ito_alpha"].value
    sigma_thickness_nm = params["sigma_thickness"].value
    pvk_b_scale = params["pvk_b_scale"].value
    niox_k = params["niox_k"].value
    r_model = calc_macro_reflectance(
        d_bulk_nm,
        d_rough_nm,
        ito_alpha,
        sigma_thickness_nm,
        pvk_b_scale,
        niox_k,
        wavelength_nm,
        get_ito_nk,
        get_pvk_nk,
    )
    return r_model - r_target


def plot_fit_result(
    wavelength_nm: np.ndarray,
    r_target: np.ndarray,
    r_fit: np.ndarray,
    d_bulk_nm: float,
    d_rough_nm: float,
    d_total_nm: float,
    ito_alpha: float,
    sigma_thickness_nm: float,
    pvk_b_scale: float,
    niox_k: float,
    chisqr: float,
    output_path: Path,
) -> None:
    """绘制并保存反演结果图。"""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    ax.plot(
        wavelength_nm,
        r_target * 100.0,
        color="gray",
        linewidth=3.0,
        alpha=0.55,
        label="Measured Target",
    )
    ax.plot(
        wavelength_nm,
        r_fit * 100.0,
        color="#1565c0",
        linewidth=2.0,
        linestyle="--",
        label="Best TMM Fit",
    )

    textbox = (
        f"Fitted d_bulk = {d_bulk_nm:.1f} nm\n"
        f"Fitted d_rough = {d_rough_nm:.1f} nm\n"
        f"Total d_total = {d_total_nm:.1f} nm\n"
        f"ITO IR Alpha = {ito_alpha:.3f}\n"
        f"Thickness Sigma = {sigma_thickness_nm:.1f} nm\n"
        f"PVK B-Scale = {pvk_b_scale:.3f}\n"
        f"NiOx k = {niox_k:.4f}\n"
        f"Chi-Square = {chisqr:.3f}"
    )
    ax.text(
        0.03,
        0.97,
        textbox,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85, "edgecolor": "#666666"},
    )

    ax.set_xlim(WAVELENGTH_MIN_NM, WAVELENGTH_MAX_NM)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Absolute Reflectance (%)")
    ax.set_title("TMM Inversion (6-Params): Dispersion Perturbation + NiOx Abs")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    project_root = get_project_root()

    target_csv = project_root / "data" / "processed" / "target_reflectance.csv"
    pvk_csv = project_root / "data" / "processed" / "CsFAPI_nk_extended.csv"
    ito_path = project_root / "resources" / "ITO_20 Ohm_105 nm_e1e2.mat"
    output_path = project_root / "results" / "figures" / "tmm_inversion_result.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wavelength_nm, r_target = load_target_reflectance_csv(target_csv)

    ito_wavelength_nm, ito_e1, ito_e2 = load_ito_dispersion(ito_path)
    validate_interp_domain(wavelength_nm, ito_wavelength_nm, "ITO 数据库")
    ito_nk = convert_dielectric_to_nk(ito_e1, ito_e2)
    get_ito_nk = build_ito_interpolator(ito_wavelength_nm, ito_nk)

    pvk_wavelength_nm, pvk_n, pvk_k = load_pvk_dispersion(pvk_csv)
    validate_interp_domain(wavelength_nm, pvk_wavelength_nm, "PVK 扩展光谱")
    get_pvk_nk = build_pvk_interpolator(pvk_wavelength_nm, pvk_n, pvk_k)

    params = Parameters()
    params.add(
        "d_bulk",
        value=INITIAL_PVK_BULK_THICKNESS_NM,
        min=MIN_PVK_BULK_THICKNESS_NM,
        max=MAX_PVK_BULK_THICKNESS_NM,
    )
    params.add(
        "d_rough",
        value=INITIAL_PVK_ROUGHNESS_THICKNESS_NM,
        min=MIN_PVK_ROUGHNESS_THICKNESS_NM,
        max=MAX_PVK_ROUGHNESS_THICKNESS_NM,
    )
    params.add(
        "ito_alpha",
        value=INITIAL_ITO_ALPHA,
        min=MIN_ITO_ALPHA,
        max=MAX_ITO_ALPHA,
    )
    params.add(
        "sigma_thickness",
        value=INITIAL_THICKNESS_SIGMA_NM,
        min=MIN_THICKNESS_SIGMA_NM,
        max=MAX_THICKNESS_SIGMA_NM,
    )
    params.add(
        "pvk_b_scale",
        value=INITIAL_PVK_B_SCALE,
        min=MIN_PVK_B_SCALE,
        max=MAX_PVK_B_SCALE,
    )
    params.add(
        "niox_k",
        value=INITIAL_NIOX_K,
        min=MIN_NIOX_K,
        max=MAX_NIOX_K,
    )

    result = minimize(
        residual,
        params,
        args=(wavelength_nm, r_target, get_ito_nk, get_pvk_nk),
        method="leastsq",
    )

    d_bulk_best_nm = float(result.params["d_bulk"].value)
    d_rough_best_nm = float(result.params["d_rough"].value)
    ito_alpha_best = float(result.params["ito_alpha"].value)
    sigma_thickness_best_nm = float(result.params["sigma_thickness"].value)
    pvk_b_scale_best = float(result.params["pvk_b_scale"].value)
    niox_k_best = float(result.params["niox_k"].value)
    d_total_best_nm = d_bulk_best_nm + d_rough_best_nm
    r_best_fit = calc_macro_reflectance(
        d_bulk_best_nm,
        d_rough_best_nm,
        ito_alpha_best,
        sigma_thickness_best_nm,
        pvk_b_scale_best,
        niox_k_best,
        wavelength_nm,
        get_ito_nk,
        get_pvk_nk,
    )

    if np.any(~np.isfinite(r_best_fit)):
        raise ValueError("最佳拟合反射率中出现 NaN 或 Inf，说明模型数值计算失败。")

    plot_fit_result(
        wavelength_nm=wavelength_nm,
        r_target=r_target,
        r_fit=r_best_fit,
        d_bulk_nm=d_bulk_best_nm,
        d_rough_nm=d_rough_best_nm,
        d_total_nm=d_total_best_nm,
        ito_alpha=ito_alpha_best,
        sigma_thickness_nm=sigma_thickness_best_nm,
        pvk_b_scale=pvk_b_scale_best,
        niox_k=niox_k_best,
        chisqr=float(result.chisqr),
        output_path=output_path,
    )

    print("TMM 六参数厚度反演完成。")
    print(f"目标曲线输入: {target_csv}")
    print(f"反演结果图片: {output_path}")
    print(f"Fitted d_bulk = {d_bulk_best_nm:.3f} nm")
    print(f"Fitted d_rough = {d_rough_best_nm:.3f} nm")
    print(f"Fitted d_total = {d_total_best_nm:.3f} nm")
    print(f"ITO IR Alpha = {ito_alpha_best:.6f}")
    print(f"Thickness Sigma = {sigma_thickness_best_nm:.6f} nm")
    print(f"PVK B-Scale = {pvk_b_scale_best:.6f}")
    print(f"NiOx k = {niox_k_best:.6f}")
    print(f"Chi-Square = {float(result.chisqr):.6f}")
    print(f"拟合状态: success={result.success}, nfev={result.nfev}")


if __name__ == "__main__":
    main()
