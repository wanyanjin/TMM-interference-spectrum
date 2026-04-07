"""Phase 04a 空气隙识别诊断沙盒。

本脚本使用 test_data/good-21.csv 与 test_data/bad-23.csv 两条代表原始谱，
先复用 step01 的绝对反射率标定链得到 850-1100 nm 的平滑绝对反射率，
再分别执行：
1. good-21 的 6 参数参考拟合
2. bad-23 的 6 参数基线拟合
3. bad-23 的 7 参数空气隙诊断拟合

目标不是把 Air_Gap 直接并入主流程，而是用单次沙盒诊断回答：
- 实验差分指纹是否与空气隙假设相位一致
- d_air 是否收敛到非零值
- 引入空气隙后 chi-square 是否显著改善
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matplotlib
import numpy as np
import pandas as pd
from lmfit import Parameters, conf_interval, minimize

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import step01_absolute_calibration as step01
import step02_tmm_inversion as step02


PHASE_NAME = "Phase 04a"
GOOD_SAMPLE_NAME = "good-21"
BAD_SAMPLE_NAME = "bad-23"
NOISE_LIMIT_PERCENT = 0.2
DAIR_INITIAL_NM = 5.0
IMPROVEMENT_EPSILON = 0.05
BOUNDARY_TOLERANCE_NM = 1e-6
INITIAL_TOLERANCE_NM = 1e-3


@dataclass
class CalibratedSpectrum:
    sample_name: str
    wavelength_nm: np.ndarray
    reflectance_raw: np.ndarray
    reflectance_smooth: np.ndarray


@dataclass
class FitSummary:
    label: str
    chisqr: float
    success: bool
    nfev: int
    d_bulk_nm: float
    d_rough_nm: float
    sigma_thickness_nm: float
    ito_alpha: float
    pvk_b_scale: float
    niox_k: float
    d_air_nm: float | None
    reflectance_fit: np.ndarray
    residual: np.ndarray
    result: object


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def calibrate_sample(
    sample_name: str,
    sample_csv: Path,
    mirror_wavelength_nm: np.ndarray,
    mirror_signal_raw: np.ndarray,
    excel_wavelength_nm: np.ndarray,
    excel_reflectance: np.ndarray,
) -> CalibratedSpectrum:
    """复用 step01 标定链，将原始计数谱转换为绝对反射率。"""
    sample_wavelength_raw, sample_signal_raw = step01.load_csv_spectrum(sample_csv)
    sample_wavelength_nm, sample_signal = step01.crop_spectrum(sample_wavelength_raw, sample_signal_raw)

    if sample_wavelength_nm.size == 0:
        raise ValueError(f"{sample_name} 在 850-1100 nm 内无有效数据。")

    step01.validate_interp_domain(sample_wavelength_nm, mirror_wavelength_nm, "银镜 CSV")
    step01.validate_interp_domain(sample_wavelength_nm, excel_wavelength_nm, "银镜 Excel 基准")

    mirror_signal_on_grid = np.interp(sample_wavelength_nm, mirror_wavelength_nm, mirror_signal_raw)
    mirror_reflectance_on_grid = np.interp(sample_wavelength_nm, excel_wavelength_nm, excel_reflectance)
    mirror_signal_norm = mirror_signal_on_grid * (
        step01.SAMPLE_EXPOSURE_MS / step01.MIRROR_EXPOSURE_MS
    )

    if np.any(np.isclose(mirror_signal_norm, 0.0)):
        raise ValueError(f"{sample_name} 的归一化银镜信号存在接近 0 的点。")

    reflectance_raw = (sample_signal / mirror_signal_norm) * mirror_reflectance_on_grid
    savgol_window = step01.compute_valid_savgol_window(
        size=reflectance_raw.size,
        desired_window=step01.DEFAULT_SAVGOL_WINDOW,
        polyorder=step01.DEFAULT_SAVGOL_POLYORDER,
    )
    reflectance_smooth = step01.savgol_filter(
        reflectance_raw,
        window_length=savgol_window,
        polyorder=step01.DEFAULT_SAVGOL_POLYORDER,
    )
    return CalibratedSpectrum(
        sample_name=sample_name,
        wavelength_nm=sample_wavelength_nm,
        reflectance_raw=reflectance_raw,
        reflectance_smooth=reflectance_smooth,
    )


def export_calibrated_csv(spectrum: CalibratedSpectrum, output_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "Wavelength": spectrum.wavelength_nm,
            "R_measured_raw": spectrum.reflectance_raw,
            "R_measured_smooth": spectrum.reflectance_smooth,
        }
    )
    frame.to_csv(output_path, index=False)


def build_material_interpolators(
    project_root: Path,
) -> tuple[Callable[[np.ndarray], np.ndarray], Callable[[np.ndarray], np.ndarray]]:
    pvk_csv = project_root / "data" / "processed" / "CsFAPI_nk_extended.csv"
    ito_path = project_root / "resources" / "ITO_20 Ohm_105 nm_e1e2.mat"

    ito_wavelength_nm, ito_e1, ito_e2 = step02.load_ito_dispersion(ito_path)
    ito_nk = step02.convert_dielectric_to_nk(ito_e1, ito_e2)
    get_ito_nk = step02.build_ito_interpolator(ito_wavelength_nm, ito_nk)

    pvk_wavelength_nm, pvk_n, pvk_k = step02.load_pvk_dispersion(pvk_csv)
    get_pvk_nk = step02.build_pvk_interpolator(pvk_wavelength_nm, pvk_n, pvk_k)
    return get_ito_nk, get_pvk_nk


def build_six_parameter_defaults() -> Parameters:
    params = Parameters()
    params.add(
        "d_bulk",
        value=step02.INITIAL_PVK_BULK_THICKNESS_NM,
        min=step02.MIN_PVK_BULK_THICKNESS_NM,
        max=step02.MAX_PVK_BULK_THICKNESS_NM,
    )
    params.add(
        "d_rough",
        value=step02.INITIAL_PVK_ROUGHNESS_THICKNESS_NM,
        min=step02.MIN_PVK_ROUGHNESS_THICKNESS_NM,
        max=step02.MAX_PVK_ROUGHNESS_THICKNESS_NM,
    )
    params.add(
        "ito_alpha",
        value=step02.INITIAL_ITO_ALPHA,
        min=step02.MIN_ITO_ALPHA,
        max=step02.MAX_ITO_ALPHA,
    )
    params.add(
        "sigma_thickness",
        value=step02.INITIAL_THICKNESS_SIGMA_NM,
        min=step02.MIN_THICKNESS_SIGMA_NM,
        max=step02.MAX_THICKNESS_SIGMA_NM,
    )
    params.add(
        "pvk_b_scale",
        value=step02.INITIAL_PVK_B_SCALE,
        min=step02.MIN_PVK_B_SCALE,
        max=step02.MAX_PVK_B_SCALE,
    )
    params.add(
        "niox_k",
        value=step02.INITIAL_NIOX_K,
        min=step02.MIN_NIOX_K,
        max=step02.MAX_NIOX_K,
    )
    return params


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
    """计算插入空气隙后的宏观反射率。

    这里显式锁定空气隙位于 SAM / PVK 界面：
    Glass -> ITO -> NiOx -> SAM -> Air_Gap -> PVK_Bulk -> PVK_Roughness -> Air
    不是 NiOx / SAM 界面。
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


def fit_six_parameter_model(
    label: str,
    wavelength_nm: np.ndarray,
    r_target: np.ndarray,
    get_ito_nk: Callable[[np.ndarray], np.ndarray],
    get_pvk_nk: Callable[[np.ndarray], np.ndarray],
) -> FitSummary:
    params = build_six_parameter_defaults()
    result = minimize(
        step02.residual,
        params,
        args=(wavelength_nm, r_target, get_ito_nk, get_pvk_nk),
        method="leastsq",
    )

    r_fit = step02.calc_macro_reflectance(
        float(result.params["d_bulk"].value),
        float(result.params["d_rough"].value),
        float(result.params["ito_alpha"].value),
        float(result.params["sigma_thickness"].value),
        float(result.params["pvk_b_scale"].value),
        float(result.params["niox_k"].value),
        wavelength_nm,
        get_ito_nk,
        get_pvk_nk,
    )
    residual = r_fit - r_target

    return FitSummary(
        label=label,
        chisqr=float(result.chisqr),
        success=bool(result.success),
        nfev=int(result.nfev),
        d_bulk_nm=float(result.params["d_bulk"].value),
        d_rough_nm=float(result.params["d_rough"].value),
        sigma_thickness_nm=float(result.params["sigma_thickness"].value),
        ito_alpha=float(result.params["ito_alpha"].value),
        pvk_b_scale=float(result.params["pvk_b_scale"].value),
        niox_k=float(result.params["niox_k"].value),
        d_air_nm=None,
        reflectance_fit=r_fit,
        residual=residual,
        result=result,
    )


def build_seven_parameter_defaults(bad_six_fit: FitSummary) -> Parameters:
    params = Parameters()
    params.add("d_bulk", value=bad_six_fit.d_bulk_nm, min=400.0, max=500.0)
    params.add("d_rough", value=bad_six_fit.d_rough_nm, min=0.0, max=100.0)
    params.add(
        "sigma_thickness",
        value=bad_six_fit.sigma_thickness_nm,
        min=0.0,
        max=60.0,
    )
    params.add("d_air", value=DAIR_INITIAL_NM, min=0.0, max=200.0)
    return params


def fit_seven_parameter_model(
    wavelength_nm: np.ndarray,
    r_target: np.ndarray,
    get_ito_nk: Callable[[np.ndarray], np.ndarray],
    get_pvk_nk: Callable[[np.ndarray], np.ndarray],
    bad_six_fit: FitSummary,
    good_six_fit: FitSummary,
) -> FitSummary:
    params = build_seven_parameter_defaults(bad_six_fit)

    def residual(params_obj: Parameters) -> np.ndarray:
        r_model = calc_macro_reflectance_with_air_gap(
            d_bulk_nm=params_obj["d_bulk"].value,
            d_rough_nm=params_obj["d_rough"].value,
            d_air_nm=params_obj["d_air"].value,
            ito_alpha=good_six_fit.ito_alpha,
            sigma_thickness_nm=params_obj["sigma_thickness"].value,
            pvk_b_scale=good_six_fit.pvk_b_scale,
            niox_k=good_six_fit.niox_k,
            wavelength_nm=wavelength_nm,
            get_ito_nk=get_ito_nk,
            get_pvk_nk=get_pvk_nk,
        )
        return r_model - r_target

    result = minimize(residual, params, method="leastsq")
    r_fit = calc_macro_reflectance_with_air_gap(
        d_bulk_nm=float(result.params["d_bulk"].value),
        d_rough_nm=float(result.params["d_rough"].value),
        d_air_nm=float(result.params["d_air"].value),
        ito_alpha=good_six_fit.ito_alpha,
        sigma_thickness_nm=float(result.params["sigma_thickness"].value),
        pvk_b_scale=good_six_fit.pvk_b_scale,
        niox_k=good_six_fit.niox_k,
        wavelength_nm=wavelength_nm,
        get_ito_nk=get_ito_nk,
        get_pvk_nk=get_pvk_nk,
    )
    residual_array = r_fit - r_target

    return FitSummary(
        label="bad-23 7-parameter fit",
        chisqr=float(result.chisqr),
        success=bool(result.success),
        nfev=int(result.nfev),
        d_bulk_nm=float(result.params["d_bulk"].value),
        d_rough_nm=float(result.params["d_rough"].value),
        sigma_thickness_nm=float(result.params["sigma_thickness"].value),
        ito_alpha=good_six_fit.ito_alpha,
        pvk_b_scale=good_six_fit.pvk_b_scale,
        niox_k=good_six_fit.niox_k,
        d_air_nm=float(result.params["d_air"].value),
        reflectance_fit=r_fit,
        residual=residual_array,
        result=result,
    )


def build_confidence_interval_summary(fit: FitSummary) -> tuple[dict[str, str], str]:
    """提取 95% CI，失败则退回 stderr 近似。"""
    ci_summary: dict[str, str] = {}
    method_used = "profile_95"
    param_names = ["d_bulk", "d_rough", "sigma_thickness", "d_air"]

    try:
        ci_result = conf_interval(fit.result, fit.result, sigmas=[1.96], trace=False)
        for name in param_names:
            entries = ci_result.get(name, [])
            low = next((value for sigma, value in entries if sigma < 0), None)
            high = next((value for sigma, value in entries if sigma > 0), None)
            if low is None or high is None:
                raise ValueError(f"{name} 缺少 profile CI。")
            ci_summary[name] = f"[{low:.3f}, {high:.3f}]"
    except Exception:
        method_used = "stderr_approx_95"
        ci_summary = {}
        for name in param_names:
            parameter = fit.result.params[name]
            if parameter.stderr is None or not np.isfinite(parameter.stderr):
                ci_summary[name] = "CI unavailable"
                method_used = "partial_unavailable"
                continue
            low = parameter.value - 1.96 * parameter.stderr
            high = parameter.value + 1.96 * parameter.stderr
            ci_summary[name] = f"[{low:.3f}, {high:.3f}]"
    return ci_summary, method_used


def summarize_air_gap_status(bad_six_fit: FitSummary, bad_seven_fit: FitSummary) -> dict[str, object]:
    d_air_nm = float(bad_seven_fit.d_air_nm or 0.0)
    relative_improvement = 1.0 - (bad_seven_fit.chisqr / bad_six_fit.chisqr)
    stuck_at_lower = abs(d_air_nm - 0.0) <= BOUNDARY_TOLERANCE_NM
    stuck_at_initial = abs(d_air_nm - DAIR_INITIAL_NM) <= INITIAL_TOLERANCE_NM
    no_material_improvement = relative_improvement <= IMPROVEMENT_EPSILON
    not_supported = stuck_at_lower or (stuck_at_initial and no_material_improvement)
    return {
        "d_air_nm": d_air_nm,
        "relative_improvement": relative_improvement,
        "stuck_at_lower": stuck_at_lower,
        "stuck_at_initial": stuck_at_initial,
        "no_material_improvement": no_material_improvement,
        "not_supported": not_supported,
        "below_target": bad_seven_fit.chisqr < 0.01,
    }


def plot_diagnostic_panel(
    wavelength_nm: np.ndarray,
    good_spectrum: CalibratedSpectrum,
    bad_spectrum: CalibratedSpectrum,
    good_six_fit: FitSummary,
    bad_six_fit: FitSummary,
    bad_seven_fit: FitSummary,
    ci_summary: dict[str, str],
    air_gap_status: dict[str, object],
    output_path: Path,
) -> None:
    delta_r_exp = (bad_spectrum.reflectance_smooth - good_spectrum.reflectance_smooth) * 100.0
    delta_r_theory = (bad_seven_fit.reflectance_fit - good_six_fit.reflectance_fit) * 100.0

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300, sharex="col")
    ax_fit, ax_delta = axes[0]
    ax_residual, ax_text = axes[1]

    ax_fit.plot(
        wavelength_nm,
        bad_spectrum.reflectance_smooth * 100.0,
        color="#424242",
        linewidth=2.5,
        label="Bad-23 Measured Smooth",
    )
    ax_fit.plot(
        wavelength_nm,
        bad_six_fit.reflectance_fit * 100.0,
        color="#ef6c00",
        linewidth=2.0,
        linestyle="--",
        label="Bad-23 6-Parameter Fit",
    )
    ax_fit.plot(
        wavelength_nm,
        bad_seven_fit.reflectance_fit * 100.0,
        color="#1565c0",
        linewidth=2.0,
        linestyle="-.",
        label="Bad-23 7-Parameter Fit",
    )
    ax_fit.set_title("Bad-23: 6p vs 7p Fit Comparison")
    ax_fit.set_ylabel("Absolute Reflectance (%)")
    ax_fit.grid(True, linestyle="--", alpha=0.35)
    ax_fit.legend(fontsize=9)

    ax_delta.fill_between(
        wavelength_nm,
        -NOISE_LIMIT_PERCENT,
        NOISE_LIMIT_PERCENT,
        color="#bdbdbd",
        alpha=0.25,
        label="Spectrometer Noise Window",
    )
    ax_delta.axhline(0.0, color="black", linewidth=1.2, linestyle="--")
    ax_delta.plot(
        wavelength_nm,
        delta_r_exp,
        color="#6a1b9a",
        linewidth=2.0,
        label="ΔR_exp = Bad - Good",
    )
    ax_delta.plot(
        wavelength_nm,
        delta_r_theory,
        color="#00897b",
        linewidth=2.0,
        linestyle="--",
        label="ΔR_theory = Bad_7p - Good_6p",
    )
    ax_delta.set_title("Differential Fingerprint")
    ax_delta.set_ylabel("ΔR (%)")
    ax_delta.grid(True, linestyle="--", alpha=0.35)
    ax_delta.legend(fontsize=9)

    ax_residual.axhline(0.0, color="black", linewidth=1.2, linestyle="--")
    ax_residual.plot(
        wavelength_nm,
        bad_six_fit.residual * 100.0,
        color="#ef6c00",
        linewidth=1.8,
        label="Residual 6p",
    )
    ax_residual.plot(
        wavelength_nm,
        bad_seven_fit.residual * 100.0,
        color="#1565c0",
        linewidth=1.8,
        label="Residual 7p",
    )
    ax_residual.set_title("Residual Comparison")
    ax_residual.set_xlabel("Wavelength (nm)")
    ax_residual.set_ylabel("Residual (%)")
    ax_residual.grid(True, linestyle="--", alpha=0.35)
    ax_residual.legend(fontsize=9)

    improvement_ratio = air_gap_status["relative_improvement"] * 100.0
    text_lines = [
        f"{PHASE_NAME} Parameter Summary",
        f"chi-square 6p = {bad_six_fit.chisqr:.6f}",
        f"chi-square 7p = {bad_seven_fit.chisqr:.6f}",
        f"improvement = {improvement_ratio:.2f}%",
        f"d_air = {air_gap_status['d_air_nm']:.3f} nm",
        f"d_air 95% CI = {ci_summary.get('d_air', 'CI unavailable')}",
        f"d_bulk = {bad_seven_fit.d_bulk_nm:.3f} nm",
        f"d_bulk 95% CI = {ci_summary.get('d_bulk', 'CI unavailable')}",
        f"d_rough = {bad_seven_fit.d_rough_nm:.3f} nm",
        f"d_rough 95% CI = {ci_summary.get('d_rough', 'CI unavailable')}",
        f"sigma = {bad_seven_fit.sigma_thickness_nm:.3f} nm",
        f"sigma 95% CI = {ci_summary.get('sigma_thickness', 'CI unavailable')}",
        f"stuck@lower = {air_gap_status['stuck_at_lower']}",
        f"stuck@initial = {air_gap_status['stuck_at_initial']}",
        f"chi^2 < 0.01 = {air_gap_status['below_target']}",
    ]
    ax_text.axis("off")
    ax_text.text(
        0.02,
        0.98,
        "\n".join(text_lines),
        va="top",
        ha="left",
        fontsize=10,
        family="monospace",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9, "edgecolor": "#666666"},
    )

    ax_residual.set_xlim(float(wavelength_nm.min()), float(wavelength_nm.max()))
    ax_delta.set_xlim(float(wavelength_nm.min()), float(wavelength_nm.max()))
    ax_fit.set_xlim(float(wavelength_nm.min()), float(wavelength_nm.max()))
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_diagnostic_log(
    log_path: Path,
    good_csv: Path,
    bad_csv: Path,
    calibrated_good_path: Path,
    calibrated_bad_path: Path,
    good_six_fit: FitSummary,
    bad_six_fit: FitSummary,
    bad_seven_fit: FitSummary,
    ci_summary: dict[str, str],
    ci_method: str,
    air_gap_status: dict[str, object],
) -> None:
    if air_gap_status["not_supported"] or bad_seven_fit.chisqr >= 0.01:
        conclusion = (
            "空气隙单因子解释不足。需要优先检查 ITO 退化、PVK 色散漂移、"
            "或其他界面/层退化。"
        )
    else:
        conclusion = "空气隙假设获得支持：d_air 收敛为非零值，且 chi-square 明显改善。"

    log_text = f"""# {PHASE_NAME} Air Gap Diagnostic

## Inputs

- good raw: `{good_csv}`
- bad raw: `{bad_csv}`
- good calibrated: `{calibrated_good_path}`
- bad calibrated: `{calibrated_bad_path}`

## Good-21 6-Parameter Fit

- success: `{good_six_fit.success}`
- chi-square: `{good_six_fit.chisqr:.6f}`
- d_bulk: `{good_six_fit.d_bulk_nm:.3f} nm`
- d_rough: `{good_six_fit.d_rough_nm:.3f} nm`
- sigma_thickness: `{good_six_fit.sigma_thickness_nm:.3f} nm`
- ito_alpha: `{good_six_fit.ito_alpha:.6f}`
- pvk_b_scale: `{good_six_fit.pvk_b_scale:.6f}`
- niox_k: `{good_six_fit.niox_k:.6f}`

## Bad-23 6-Parameter Fit

- success: `{bad_six_fit.success}`
- chi-square: `{bad_six_fit.chisqr:.6f}`
- d_bulk: `{bad_six_fit.d_bulk_nm:.3f} nm`
- d_rough: `{bad_six_fit.d_rough_nm:.3f} nm`
- sigma_thickness: `{bad_six_fit.sigma_thickness_nm:.3f} nm`
- ito_alpha: `{bad_six_fit.ito_alpha:.6f}`
- pvk_b_scale: `{bad_six_fit.pvk_b_scale:.6f}`
- niox_k: `{bad_six_fit.niox_k:.6f}`

## Bad-23 7-Parameter Fit

- success: `{bad_seven_fit.success}`
- chi-square: `{bad_seven_fit.chisqr:.6f}`
- relative improvement: `{air_gap_status['relative_improvement'] * 100.0:.2f}%`
- d_bulk: `{bad_seven_fit.d_bulk_nm:.3f} nm`
- d_bulk 95% CI: `{ci_summary.get('d_bulk', 'CI unavailable')}`
- d_rough: `{bad_seven_fit.d_rough_nm:.3f} nm`
- d_rough 95% CI: `{ci_summary.get('d_rough', 'CI unavailable')}`
- sigma_thickness: `{bad_seven_fit.sigma_thickness_nm:.3f} nm`
- sigma_thickness 95% CI: `{ci_summary.get('sigma_thickness', 'CI unavailable')}`
- d_air: `{air_gap_status['d_air_nm']:.3f} nm`
- d_air 95% CI: `{ci_summary.get('d_air', 'CI unavailable')}`
- CI method: `{ci_method}`
- stuck at lower bound: `{air_gap_status['stuck_at_lower']}`
- stuck at initial value: `{air_gap_status['stuck_at_initial']}`
- no material improvement: `{air_gap_status['no_material_improvement']}`
- chi-square below 0.01: `{air_gap_status['below_target']}`

## Conclusion

- {conclusion}
"""
    log_path.write_text(log_text, encoding="utf-8")


def main() -> None:
    project_root = get_project_root()
    good_csv = project_root / "test_data" / "good-21.csv"
    bad_csv = project_root / "test_data" / "bad-23.csv"
    mirror_csv = project_root / "test_data" / "Ag-mirro.csv"
    reference_excel = project_root / "resources" / "GCC-1022系列xlsx.xlsx"

    processed_dir = project_root / "data" / "processed" / "phase04a"
    figure_path = project_root / "results" / "figures" / "phase04a_air_gap_diagnostic.png"
    log_path = project_root / "results" / "logs" / "phase04a_air_gap_diagnostic.md"
    processed_dir.mkdir(parents=True, exist_ok=True)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    mirror_wavelength_raw, mirror_signal_raw = step01.load_csv_spectrum(mirror_csv)
    mirror_wavelength_nm, mirror_signal = step01.crop_spectrum(mirror_wavelength_raw, mirror_signal_raw)
    excel_wavelength_raw, excel_reflectance_raw = step01.load_excel_reference(reference_excel)
    excel_wavelength_nm, excel_reflectance = step01.crop_spectrum(excel_wavelength_raw, excel_reflectance_raw)

    good_spectrum = calibrate_sample(
        sample_name=GOOD_SAMPLE_NAME,
        sample_csv=good_csv,
        mirror_wavelength_nm=mirror_wavelength_nm,
        mirror_signal_raw=mirror_signal,
        excel_wavelength_nm=excel_wavelength_nm,
        excel_reflectance=excel_reflectance,
    )
    bad_spectrum = calibrate_sample(
        sample_name=BAD_SAMPLE_NAME,
        sample_csv=bad_csv,
        mirror_wavelength_nm=mirror_wavelength_nm,
        mirror_signal_raw=mirror_signal,
        excel_wavelength_nm=excel_wavelength_nm,
        excel_reflectance=excel_reflectance,
    )

    if good_spectrum.wavelength_nm.size != bad_spectrum.wavelength_nm.size or not np.allclose(
        good_spectrum.wavelength_nm,
        bad_spectrum.wavelength_nm,
        atol=1e-12,
        rtol=0.0,
    ):
        raise ValueError("good / bad calibrated CSV 的波长网格不一致，终止诊断。")

    calibrated_good_path = processed_dir / "good-21_calibrated.csv"
    calibrated_bad_path = processed_dir / "bad-23_calibrated.csv"
    export_calibrated_csv(good_spectrum, calibrated_good_path)
    export_calibrated_csv(bad_spectrum, calibrated_bad_path)

    get_ito_nk, get_pvk_nk = build_material_interpolators(project_root)

    good_six_fit = fit_six_parameter_model(
        label="good-21 6-parameter fit",
        wavelength_nm=good_spectrum.wavelength_nm,
        r_target=good_spectrum.reflectance_smooth,
        get_ito_nk=get_ito_nk,
        get_pvk_nk=get_pvk_nk,
    )
    bad_six_fit = fit_six_parameter_model(
        label="bad-23 6-parameter fit",
        wavelength_nm=bad_spectrum.wavelength_nm,
        r_target=bad_spectrum.reflectance_smooth,
        get_ito_nk=get_ito_nk,
        get_pvk_nk=get_pvk_nk,
    )
    bad_seven_fit = fit_seven_parameter_model(
        wavelength_nm=bad_spectrum.wavelength_nm,
        r_target=bad_spectrum.reflectance_smooth,
        get_ito_nk=get_ito_nk,
        get_pvk_nk=get_pvk_nk,
        bad_six_fit=bad_six_fit,
        good_six_fit=good_six_fit,
    )

    ci_summary, ci_method = build_confidence_interval_summary(bad_seven_fit)
    air_gap_status = summarize_air_gap_status(bad_six_fit, bad_seven_fit)

    plot_diagnostic_panel(
        wavelength_nm=bad_spectrum.wavelength_nm,
        good_spectrum=good_spectrum,
        bad_spectrum=bad_spectrum,
        good_six_fit=good_six_fit,
        bad_six_fit=bad_six_fit,
        bad_seven_fit=bad_seven_fit,
        ci_summary=ci_summary,
        air_gap_status=air_gap_status,
        output_path=figure_path,
    )
    write_diagnostic_log(
        log_path=log_path,
        good_csv=good_csv,
        bad_csv=bad_csv,
        calibrated_good_path=calibrated_good_path,
        calibrated_bad_path=calibrated_bad_path,
        good_six_fit=good_six_fit,
        bad_six_fit=bad_six_fit,
        bad_seven_fit=bad_seven_fit,
        ci_summary=ci_summary,
        ci_method=ci_method,
        air_gap_status=air_gap_status,
    )

    print(f"{PHASE_NAME} 诊断完成。")
    print(f"Good calibrated CSV: {calibrated_good_path}")
    print(f"Bad calibrated CSV: {calibrated_bad_path}")
    print(f"Diagnostic figure: {figure_path}")
    print(f"Diagnostic log: {log_path}")
    print(f"Good chi-square (6p): {good_six_fit.chisqr:.6f}")
    print(f"Bad chi-square (6p): {bad_six_fit.chisqr:.6f}")
    print(f"Bad chi-square (7p): {bad_seven_fit.chisqr:.6f}")
    print(f"d_air_opt = {air_gap_status['d_air_nm']:.6f} nm")
    print(f"d_air stuck at lower bound = {air_gap_status['stuck_at_lower']}")
    print(f"d_air stuck at initial value = {air_gap_status['stuck_at_initial']}")
    print(f"chi-square below 0.01 = {air_gap_status['below_target']}")


if __name__ == "__main__":
    main()
