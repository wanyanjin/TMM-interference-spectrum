"""基于 TMM 与 Levenberg-Marquardt 的钙钛矿厚度反演脚本。

本脚本与 step01 数据解耦，只读取 data/processed/target_reflectance.csv
作为目标干涉光谱输入，不再重写绝对反射率标定逻辑。

模块划分：
1. 目标曲线读取
2. ITO 色散解析与插值
3. PVK 的 Tauc-Lorentz 色散模型
4. 厚玻璃非相干修正 + 相干薄膜 TMM
5. lmfit 单参数厚度反演
6. 结果绘图
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
NIOX_NK = 2.1 + 0.0j
SAM_NK = 1.8 + 0.0j

INITIAL_PVK_THICKNESS_NM = 500.0
MIN_PVK_THICKNESS_NM = 400.0
MAX_PVK_THICKNESS_NM = 650.0

PVK_EPS_INF = 1.10
PVK_EG_EV = 1.556
PVK_OSCILLATORS = (
    (24.53, 1.57, 0.13),
    (7.60, 2.46, 0.49),
    (6.50, 3.31, 3.89),
)


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


def tauc_lorentz_eps2_single_oscillator(
    energy_ev: np.ndarray,
    amplitude: float,
    resonance_ev: float,
    broadening_ev: float,
    bandgap_ev: float,
) -> np.ndarray:
    """计算单个 Tauc-Lorentz 振子的虚部介电常数 eps2。"""
    energy = np.asarray(energy_ev, dtype=float)
    eps2 = np.zeros_like(energy, dtype=float)
    valid_mask = energy > bandgap_ev
    if not np.any(valid_mask):
        return eps2

    e = energy[valid_mask]
    numerator = amplitude * resonance_ev * broadening_ev * (e - bandgap_ev) ** 2
    denominator = e * ((e**2 - resonance_ev**2) ** 2 + broadening_ev**2 * e**2)
    eps2[valid_mask] = numerator / denominator
    return eps2


def tauc_lorentz_eps1_from_kkr(energy_ev: np.ndarray) -> np.ndarray:
    """用 Kramers-Kronig 数值积分求 Tauc-Lorentz 的 eps1。

    资源文档给出了 eps1 的闭式表达，但在当前参数和子带隙反演区间里，
    闭式各项会发生强烈数值抵消，直接计算会把 eps1 推到非物理负值，
    继而导致 PVK 折射率塌缩到 0。这里改用同一 TL 模型下与之等价的
    Kramers-Kronig 数值积分形式，提高稳定性。

    对本任务关心的 850-1100 nm 而言，所有能量 E 都满足 E < Eg，
    积分区间从 Eg 起始，因此分母 xi^2 - E^2 不会穿过 0，不需要处理主值奇点。
    """
    energy = np.asarray(energy_ev, dtype=float)
    integration_energy = np.linspace(PVK_EG_EV, 6.5, 4000)

    eps2_total = np.zeros_like(integration_energy)
    for amplitude, resonance_ev, broadening_ev in PVK_OSCILLATORS:
        eps2_total += tauc_lorentz_eps2_single_oscillator(
            energy_ev=integration_energy,
            amplitude=amplitude,
            resonance_ev=resonance_ev,
            broadening_ev=broadening_ev,
            bandgap_ev=PVK_EG_EV,
        )

    numerator = integration_energy[None, :] * eps2_total[None, :]
    denominator = integration_energy[None, :] ** 2 - energy[:, None] ** 2
    integral = np.trapezoid(numerator / denominator, integration_energy, axis=1)
    return PVK_EPS_INF + (2.0 / np.pi) * integral


def get_pvk_nk(wavelength_nm: np.ndarray) -> np.ndarray:
    """根据 Glass/CsFAPI 参数计算 PVK 的复折射率。

    本任务限定 850-1100 nm 波段，对应能量低于 Eg=1.556 eV，
    因此按要求强制 eps2=0，也即 k=0。
    """
    wavelength = np.asarray(wavelength_nm, dtype=float)
    energy_ev = 1239.841984 / wavelength

    # 这里仍然遵循 Tauc-Lorentz 模型，只是用 KK 数值积分求实部，
    # 避免闭式表达在当前参数区间出现的严重数值抵消。
    eps1_total = tauc_lorentz_eps1_from_kkr(energy_ev)

    # 在本波段 E < Eg，按模型要求将虚部严格置零，因此 PVK 为无吸收层。
    eps2_total = np.zeros_like(eps1_total)

    # 数值上若 eps1_total 出现接近 0 的微小负值，通常是浮点误差而不是物理结果。
    eps1_total = np.maximum(eps1_total, 0.0)
    n = np.sqrt(eps1_total)
    k = np.zeros_like(eps2_total)
    return n + 1j * k


def calc_macro_reflectance(
    d_pvk_nm: float,
    wavelength_nm: np.ndarray,
    get_ito_nk: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    """计算包含厚玻璃非相干修正的宏观反射率。

    真实样品结构是 Air -> 1.1 mm Glass -> ITO -> NiOx -> SAM -> PVK -> Air。
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
    ito_nk = get_ito_nk(wavelength)
    pvk_nk = get_pvk_nk(wavelength)

    r_coh = np.empty_like(wavelength, dtype=float)

    for index, wl_nm in enumerate(wavelength):
        n_list = [
            GLASS_INDEX + 0.0j,
            ito_nk[index],
            NIOX_NK,
            SAM_NK,
            pvk_nk[index],
            AIR_INDEX + 0.0j,
        ]
        d_list = [np.inf, ITO_THICKNESS_NM, NIOX_THICKNESS_NM, SAM_THICKNESS_NM, d_pvk_nm, np.inf]
        tmm_result = coh_tmm("s", n_list, d_list, 0.0, wl_nm)
        r_coh[index] = float(tmm_result["R"])

    r_front = ((GLASS_INDEX - AIR_INDEX) / (GLASS_INDEX + AIR_INDEX)) ** 2
    r_total = r_front + (((1.0 - r_front) ** 2) * r_coh) / (1.0 - r_front * r_coh)
    return r_total


def residual(
    params: Parameters,
    wavelength_nm: np.ndarray,
    r_target: np.ndarray,
    get_ito_nk: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    """lmfit 残差函数。"""
    d_pvk_nm = params["d_pvk"].value
    r_model = calc_macro_reflectance(d_pvk_nm, wavelength_nm, get_ito_nk)
    return r_model - r_target


def plot_fit_result(
    wavelength_nm: np.ndarray,
    r_target: np.ndarray,
    r_fit: np.ndarray,
    d_best_nm: float,
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

    textbox = f"Fitted d_pvk = {d_best_nm:.1f} nm\nChi-Square = {chisqr:.3f}"
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
    ax.set_title("TMM Inversion for Perovskite Thickness (850-1100 nm)")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    project_root = get_project_root()

    target_csv = project_root / "data" / "processed" / "target_reflectance.csv"
    ito_path = project_root / "resources" / "ITO_20 Ohm_105 nm_e1e2.mat"
    output_path = project_root / "results" / "figures" / "tmm_inversion_result.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wavelength_nm, r_target = load_target_reflectance_csv(target_csv)

    ito_wavelength_nm, ito_e1, ito_e2 = load_ito_dispersion(ito_path)
    validate_interp_domain(wavelength_nm, ito_wavelength_nm, "ITO 数据库")
    ito_nk = convert_dielectric_to_nk(ito_e1, ito_e2)
    get_ito_nk = build_ito_interpolator(ito_wavelength_nm, ito_nk)

    params = Parameters()
    params.add(
        "d_pvk",
        value=INITIAL_PVK_THICKNESS_NM,
        min=MIN_PVK_THICKNESS_NM,
        max=MAX_PVK_THICKNESS_NM,
    )

    result = minimize(
        residual,
        params,
        args=(wavelength_nm, r_target, get_ito_nk),
        method="leastsq",
    )

    d_best_nm = float(result.params["d_pvk"].value)
    r_best_fit = calc_macro_reflectance(d_best_nm, wavelength_nm, get_ito_nk)

    if np.any(~np.isfinite(r_best_fit)):
        raise ValueError("最佳拟合反射率中出现 NaN 或 Inf，说明模型数值计算失败。")

    plot_fit_result(
        wavelength_nm=wavelength_nm,
        r_target=r_target,
        r_fit=r_best_fit,
        d_best_nm=d_best_nm,
        chisqr=float(result.chisqr),
        output_path=output_path,
    )

    print("TMM 厚度反演完成。")
    print(f"目标曲线输入: {target_csv}")
    print(f"反演结果图片: {output_path}")
    print(f"Fitted d_pvk = {d_best_nm:.3f} nm")
    print(f"Chi-Square = {float(result.chisqr):.6f}")
    print(f"拟合状态: success={result.success}, nfev={result.nfev}")


if __name__ == "__main__":
    main()
