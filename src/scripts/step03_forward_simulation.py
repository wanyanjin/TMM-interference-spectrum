"""Phase 04 空气隙前向预测脚本。

本脚本将 Phase 03 的六参数最优基线固化为前向预测模型，用于扫描
SAM / PVK 界面引入纯空气间隙后，850-1500 nm 波段的绝对反射率 R
与差分反射率 ΔR 的演变特征。

实现原则：
1. 复用 step02_tmm_inversion.py 中已验证的 ITO/PVK 数据读取、BEMA 粗糙层、
   玻璃前表面非相干合成与 ITO 长波吸收补偿逻辑。
2. 仅在相干层堆栈中插入 Air_Gap 层。
3. 对 PVK 在 1100-1500 nm 的尾部折射率做受控 Cauchy 外推，并强制 k = 0。
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib
import numpy as np

# 保持终端环境下可稳定落图。
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import step02_tmm_inversion as step02


PHASE_NAME = "Phase 04"

WAVELENGTHS_NM = np.linspace(850.0, 1500.0, 651, dtype=float)
PVK_EXTRAPOLATION_FIT_MIN_NM = 1050.0
PVK_EXTRAPOLATION_FIT_MAX_NM = 1100.0
PVK_EXTRAPOLATION_MAX_NM = 1500.0

D_BULK_BASE_NM = 700.0
D_ROUGH_NM = 31.337
ITO_ALPHA = 13.313
SIGMA_THICKNESS_NM = 22.761
PVK_B_SCALE = 1.626
NIOX_K = 0.455

D_AIR_LIST_NM = [0.0, 2.0, 5.0, 10.0, 50.0, 100.0]
NOISE_LIMIT_PERCENT = 0.2


def cauchy_model(wavelength_nm: np.ndarray, a_param: float, b_param: float) -> np.ndarray:
    """Cauchy 模型，波长以 um 进入平方项。"""
    wavelength_um = np.asarray(wavelength_nm, dtype=np.float64) / 1000.0
    return a_param + b_param / (wavelength_um**2)


def fit_cauchy_tail(
    wavelength_nm: np.ndarray,
    refractive_index: np.ndarray,
) -> tuple[float, float]:
    """拟合 1050-1100 nm 尾段的两参数 Cauchy 模型。"""
    fit_mask = (wavelength_nm >= PVK_EXTRAPOLATION_FIT_MIN_NM) & (
        wavelength_nm <= PVK_EXTRAPOLATION_FIT_MAX_NM
    )
    fit_wavelength_nm = wavelength_nm[fit_mask]
    fit_refractive_index = refractive_index[fit_mask]

    if fit_wavelength_nm.size < 3:
        raise ValueError(
            "PVK 尾段数据点不足，无法执行 1050-1100 nm 的 Cauchy 外推拟合。"
        )

    # 线性最小二乘拟合 n = A + B / lambda_um^2。
    design_matrix = np.column_stack(
        [
            np.ones_like(fit_wavelength_nm, dtype=float),
            1.0 / ((fit_wavelength_nm / 1000.0) ** 2),
        ]
    )
    solution, *_ = np.linalg.lstsq(design_matrix, fit_refractive_index, rcond=None)
    a_param, b_param = solution
    return float(a_param), float(b_param)


def build_pvk_extrapolating_interpolator(
    pvk_csv_path: Path,
) -> tuple[Callable[[np.ndarray], np.ndarray], float, float]:
    """构造支持 1100-1500 nm 尾部外推的 PVK 复折射率插值器。

    [LIT-0001] 的原始椭偏测量窗口到 1000 nm。当前仓库中的
    `CsFAPI_nk_extended.csv` 已将近红外透明区外推到 1100 nm。
    本脚本进一步只在 1100 nm 以上做受控尾部外推，且强制 k = 0。
    """
    wavelength_nm, refractive_index, extinction_coefficient = step02.load_pvk_dispersion(pvk_csv_path)
    a_param, b_param = fit_cauchy_tail(wavelength_nm, refractive_index)

    def get_pvk_nk(query_wavelength_nm: np.ndarray) -> np.ndarray:
        query = np.asarray(query_wavelength_nm, dtype=float)
        if query.size == 0:
            return np.asarray([], dtype=np.complex128)
        if query.min() < wavelength_nm.min():
            raise ValueError(
                "PVK 扩展光谱不支持低于源数据下边界的查询: "
                f"query_min={query.min():.2f} nm, source_min={wavelength_nm.min():.2f} nm"
            )
        if query.max() > PVK_EXTRAPOLATION_MAX_NM:
            raise ValueError(
                "PVK 外推上边界不足: "
                f"query_max={query.max():.2f} nm, extrapolation_max={PVK_EXTRAPOLATION_MAX_NM:.2f} nm"
            )

        real_part = np.empty_like(query, dtype=float)
        imag_part = np.zeros_like(query, dtype=float)

        in_domain_mask = query <= wavelength_nm.max()
        if np.any(in_domain_mask):
            real_part[in_domain_mask] = np.interp(query[in_domain_mask], wavelength_nm, refractive_index)
            imag_part[in_domain_mask] = np.interp(
                query[in_domain_mask],
                wavelength_nm,
                extinction_coefficient,
            )

        tail_mask = ~in_domain_mask
        if np.any(tail_mask):
            real_part[tail_mask] = cauchy_model(query[tail_mask], a_param, b_param)
            imag_part[tail_mask] = 0.0

        return real_part + 1j * imag_part

    return get_pvk_nk, a_param, b_param


def calc_macro_reflectance_with_air_gap(
    d_bulk_nm: float,
    d_rough_nm: float,
    d_air_nm: float,
    ito_alpha: float,
    sigma_thickness_nm: float,
    pvk_b_scale: float,
    niox_k: float,
    wavelength_nm: np.ndarray,
    get_ito_nk: Callable[[np.ndarray], np.ndarray],
    get_pvk_nk: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    """计算插入 Air_Gap 后的宏观反射率。

    玻璃前表面继续按非相干处理；后侧薄膜堆栈保持相干 TMM。
    相干层结构为：
    Glass -> ITO -> NiOx -> SAM -> Air_Gap -> PVK_Bulk -> PVK_Roughness -> Air
    """
    wavelength = np.asarray(wavelength_nm, dtype=float)
    ito_base_nk = get_ito_nk(wavelength)
    ito_nk = step02.apply_dispersive_absorption_correction(ito_base_nk, wavelength, ito_alpha)

    pvk_base_nk = get_pvk_nk(wavelength)
    n_base = np.real(pvk_base_nk)
    k_base = np.imag(pvk_base_nk)
    n_anchor = float(np.real(get_pvk_nk(np.array([1000.0], dtype=float)))[0])
    n_new = n_anchor + pvk_b_scale * (n_base - n_anchor)
    pvk_pert_nk = n_new + 1j * k_base
    pvk_rough_nk = step02.calc_bema_rough_nk(pvk_pert_nk)
    niox_nk = 2.1 + 1j * niox_k
    r_front = ((step02.GLASS_INDEX - step02.AIR_INDEX) / (step02.GLASS_INDEX + step02.AIR_INDEX)) ** 2

    def calc_single_reflectance(single_d_bulk_nm: float) -> np.ndarray:
        r_coh = np.empty_like(wavelength, dtype=float)

        for index, wl_nm in enumerate(wavelength):
            n_list = [
                step02.GLASS_INDEX + 0.0j,
                ito_nk[index],
                niox_nk,
                step02.SAM_NK,
                step02.AIR_INDEX + 0.0j,
                pvk_pert_nk[index],
                pvk_rough_nk[index],
                step02.AIR_INDEX + 0.0j,
            ]
            d_list = [
                np.inf,
                step02.ITO_THICKNESS_NM,
                step02.NIOX_THICKNESS_NM,
                step02.SAM_THICKNESS_NM,
                d_air_nm,
                single_d_bulk_nm,
                d_rough_nm,
                np.inf,
            ]
            tmm_result = step02.coh_tmm("s", n_list, d_list, 0.0, wl_nm)
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


def plot_air_gap_prediction(
    wavelength_nm: np.ndarray,
    reflectance_map: dict[float, np.ndarray],
    differential_map: dict[float, np.ndarray],
    output_path: Path,
) -> None:
    """绘制 Phase 04 空气隙预测 1x2 面板图。"""
    figure, axes = plt.subplots(1, 2, figsize=(14, 5.6), dpi=300, sharex=True)
    colors = plt.cm.coolwarm(np.linspace(0.08, 0.92, len(reflectance_map)))

    absolute_ax = axes[0]
    differential_ax = axes[1]

    for color, (d_air_nm, reflectance) in zip(colors, reflectance_map.items()):
        absolute_ax.plot(
            wavelength_nm,
            reflectance * 100.0,
            color=color,
            linewidth=2.0,
            label=f"d_air = {d_air_nm:.1f} nm",
        )

    diff_items = [(gap, curve) for gap, curve in differential_map.items() if gap > 0.0]
    for color, (d_air_nm, differential) in zip(colors[1:], diff_items):
        differential_ax.plot(
            wavelength_nm,
            differential * 100.0,
            color=color,
            linewidth=2.0,
            label=f"d_air = {d_air_nm:.1f} nm",
        )

    absolute_ax.set_title(f"{PHASE_NAME}: Absolute Reflectance")
    absolute_ax.set_xlabel("Wavelength (nm)")
    absolute_ax.set_ylabel("Absolute Reflectance (%)")
    absolute_ax.set_xlim(float(wavelength_nm.min()), float(wavelength_nm.max()))
    absolute_ax.grid(True, linestyle="--", alpha=0.35)
    absolute_ax.legend(fontsize=9)

    differential_ax.axhline(
        NOISE_LIMIT_PERCENT,
        color="#616161",
        linewidth=1.4,
        linestyle="--",
        label="Typical Spectrometer Noise Limit",
    )
    differential_ax.axhline(
        -NOISE_LIMIT_PERCENT,
        color="#616161",
        linewidth=1.4,
        linestyle="--",
    )
    differential_ax.set_title(f"{PHASE_NAME}: Differential Reflectance")
    differential_ax.set_xlabel("Wavelength (nm)")
    differential_ax.set_ylabel("ΔR (%)")
    differential_ax.set_xlim(float(wavelength_nm.min()), float(wavelength_nm.max()))
    differential_ax.grid(True, linestyle="--", alpha=0.35)
    differential_ax.legend(fontsize=9)

    figure.tight_layout()
    figure.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    pvk_csv_path = project_root / "data" / "processed" / "CsFAPI_nk_extended.csv"
    ito_path = project_root / "resources" / "ITO_20 Ohm_105 nm_e1e2.mat"
    output_path = project_root / "results" / "figures" / "phase04_air_gap_prediction.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ito_wavelength_nm, ito_e1, ito_e2 = step02.load_ito_dispersion(ito_path)
    step02.validate_interp_domain(WAVELENGTHS_NM, ito_wavelength_nm, "ITO 数据库")
    ito_nk = step02.convert_dielectric_to_nk(ito_e1, ito_e2)
    get_ito_nk = step02.build_ito_interpolator(ito_wavelength_nm, ito_nk)

    get_pvk_nk, cauchy_a, cauchy_b = build_pvk_extrapolating_interpolator(pvk_csv_path)
    n_1100_table = float(np.real(get_pvk_nk(np.array([1100.0], dtype=float)))[0])
    n_1101_tail = float(np.real(get_pvk_nk(np.array([1101.0], dtype=float)))[0])

    reflectance_map: dict[float, np.ndarray] = {}
    for d_air_nm in D_AIR_LIST_NM:
        reflectance_map[d_air_nm] = calc_macro_reflectance_with_air_gap(
            d_bulk_nm=D_BULK_BASE_NM,
            d_rough_nm=D_ROUGH_NM,
            d_air_nm=d_air_nm,
            ito_alpha=ITO_ALPHA,
            sigma_thickness_nm=SIGMA_THICKNESS_NM,
            pvk_b_scale=PVK_B_SCALE,
            niox_k=NIOX_K,
            wavelength_nm=WAVELENGTHS_NM,
            get_ito_nk=get_ito_nk,
            get_pvk_nk=get_pvk_nk,
        )

    baseline_reflectance = reflectance_map[0.0]
    differential_map = {
        d_air_nm: reflectance - baseline_reflectance
        for d_air_nm, reflectance in reflectance_map.items()
    }

    plot_air_gap_prediction(
        wavelength_nm=WAVELENGTHS_NM,
        reflectance_map=reflectance_map,
        differential_map=differential_map,
        output_path=output_path,
    )

    delta_2nm_percent = float(np.max(np.abs(differential_map[2.0])) * 100.0)
    delta_5nm_percent = float(np.max(np.abs(differential_map[5.0])) * 100.0)

    print(f"{PHASE_NAME} 前向预测完成。")
    print(f"Python executable: {Path(__import__('sys').executable).resolve()}")
    print(f"Script path: {Path(__file__).resolve()}")
    print(
        "PVK >1100 nm extrapolation: SUCCESS "
        f"(fit window = {PVK_EXTRAPOLATION_FIT_MIN_NM:.0f}-{PVK_EXTRAPOLATION_FIT_MAX_NM:.0f} nm, "
        f"A = {cauchy_a:.8f}, B = {cauchy_b:.8f} um^2)"
    )
    print(
        "PVK tail continuity check: "
        f"n(1100 nm) = {n_1100_table:.6f}, n(1101 nm) = {n_1101_tail:.6f}, "
        f"delta = {n_1101_tail - n_1100_table:+.6e}"
    )
    print(f"Output figure: {output_path}")
    print(
        f"d_air = 2.0 nm -> max(|ΔR|) = {delta_2nm_percent:.4f}% ; "
        f"exceeds 0.2% limit = {delta_2nm_percent > NOISE_LIMIT_PERCENT}"
    )
    print(
        f"d_air = 5.0 nm -> max(|ΔR|) = {delta_5nm_percent:.4f}% ; "
        f"exceeds 0.2% limit = {delta_5nm_percent > NOISE_LIMIT_PERCENT}"
    )


if __name__ == "__main__":
    main()
