"""Phase 04b 空气隙定位与材料参数弛豫诊断。

本脚本针对更具代表性的 bad-20-2 光谱，执行两步诊断：
1. 固定 good-21 的材料参数，比较三种空气隙空间位置的 7 参数模型表现
2. 选择最佳空间位置后，释放材料参数做“10 参数”弛豫以继续压低残差
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matplotlib
import numpy as np
from lmfit import Parameters, minimize

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import step02_tmm_inversion as step02
import step04a_air_gap_diagnostic as step04a


PHASE_NAME = "Phase 04b"
GOOD_SAMPLE_NAME = "good-21"
BAD_SAMPLE_NAME = "bad-20-2"
NOISE_LIMIT_PERCENT = 0.2
DAIR_INITIAL_NM = 5.0
BOUNDARY_TOLERANCE_NM = 1e-6
INITIAL_TOLERANCE_NM = 1e-3
MAX_NFEV_LOCALIZATION = 180
MAX_NFEV_RELAXED = 260

LOCATION_L1 = "glass_ito"
LOCATION_L2 = "ito_niox"
LOCATION_L3 = "sam_pvk"
LOCATION_LABELS = {
    LOCATION_L1: "L1 Glass/ITO",
    LOCATION_L2: "L2 ITO/NiOx",
    LOCATION_L3: "L3 SAM/PVK",
}


@dataclass
class LocalizationFitSummary(step04a.FitSummary):
    location_key: str | None = None


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def calc_macro_reflectance_with_localized_air_gap(
    location_key: str,
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
    """计算不同界面位置引入空气隙后的宏观反射率。"""
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
            if location_key == LOCATION_L1:
                n_list = [
                    step02.GLASS_INDEX + 0.0j,
                    step02.AIR_INDEX + 0.0j,
                    ito_nk[index],
                    niox_nk,
                    step02.SAM_NK,
                    pvk_pert_nk[index],
                    pvk_rough_nk[index],
                    step02.AIR_INDEX + 0.0j,
                ]
                d_list = [
                    np.inf,
                    d_air_nm,
                    step02.ITO_THICKNESS_NM,
                    step02.NIOX_THICKNESS_NM,
                    step02.SAM_THICKNESS_NM,
                    single_d_bulk_nm,
                    d_rough_nm,
                    np.inf,
                ]
            elif location_key == LOCATION_L2:
                n_list = [
                    step02.GLASS_INDEX + 0.0j,
                    ito_nk[index],
                    step02.AIR_INDEX + 0.0j,
                    niox_nk,
                    step02.SAM_NK,
                    pvk_pert_nk[index],
                    pvk_rough_nk[index],
                    step02.AIR_INDEX + 0.0j,
                ]
                d_list = [
                    np.inf,
                    step02.ITO_THICKNESS_NM,
                    d_air_nm,
                    step02.NIOX_THICKNESS_NM,
                    step02.SAM_THICKNESS_NM,
                    single_d_bulk_nm,
                    d_rough_nm,
                    np.inf,
                ]
            elif location_key == LOCATION_L3:
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
            else:
                raise ValueError(f"未知空气隙位置: {location_key}")

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


def build_localization_defaults(bad_six_fit: step04a.FitSummary) -> Parameters:
    params = Parameters()
    params.add("d_bulk", value=bad_six_fit.d_bulk_nm, min=400.0, max=500.0)
    params.add("d_rough", value=bad_six_fit.d_rough_nm, min=0.0, max=100.0)
    params.add("sigma_thickness", value=bad_six_fit.sigma_thickness_nm, min=0.0, max=60.0)
    params.add("d_air", value=DAIR_INITIAL_NM, min=0.0, max=200.0)
    return params


def fit_localization_model(
    location_key: str,
    wavelength_nm: np.ndarray,
    r_target: np.ndarray,
    get_ito_nk: Callable[[np.ndarray], np.ndarray],
    get_pvk_nk: Callable[[np.ndarray], np.ndarray],
    bad_six_fit: step04a.FitSummary,
    good_six_fit: step04a.FitSummary,
) -> LocalizationFitSummary:
    params = build_localization_defaults(bad_six_fit)

    def residual(params_obj: Parameters) -> np.ndarray:
        r_model = calc_macro_reflectance_with_localized_air_gap(
            location_key=location_key,
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

    result = minimize(residual, params, method="least_squares", max_nfev=MAX_NFEV_LOCALIZATION)
    r_fit = calc_macro_reflectance_with_localized_air_gap(
        location_key=location_key,
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

    return LocalizationFitSummary(
        label=f"{LOCATION_LABELS[location_key]} 7-parameter fit",
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
        location_key=location_key,
    )


def build_relaxation_defaults(best_fit: LocalizationFitSummary, good_six_fit: step04a.FitSummary) -> Parameters:
    params = Parameters()
    params.add("d_bulk", value=best_fit.d_bulk_nm, min=400.0, max=500.0)
    params.add("d_rough", value=best_fit.d_rough_nm, min=0.0, max=100.0)
    params.add("sigma_thickness", value=best_fit.sigma_thickness_nm, min=0.0, max=60.0)
    params.add("d_air", value=float(best_fit.d_air_nm or DAIR_INITIAL_NM), min=0.0, max=200.0)
    params.add(
        "ito_alpha",
        value=good_six_fit.ito_alpha,
        min=good_six_fit.ito_alpha * 0.85,
        max=good_six_fit.ito_alpha * 1.15,
    )
    params.add(
        "pvk_b_scale",
        value=good_six_fit.pvk_b_scale,
        min=good_six_fit.pvk_b_scale * 0.85,
        max=good_six_fit.pvk_b_scale * 1.15,
    )
    params.add(
        "niox_k",
        value=good_six_fit.niox_k,
        min=good_six_fit.niox_k * 0.85,
        max=good_six_fit.niox_k * 1.15,
    )
    return params


def fit_relaxed_model(
    best_location_key: str,
    wavelength_nm: np.ndarray,
    r_target: np.ndarray,
    get_ito_nk: Callable[[np.ndarray], np.ndarray],
    get_pvk_nk: Callable[[np.ndarray], np.ndarray],
    best_fit: LocalizationFitSummary,
    good_six_fit: step04a.FitSummary,
) -> LocalizationFitSummary:
    params = build_relaxation_defaults(best_fit, good_six_fit)

    def residual(params_obj: Parameters) -> np.ndarray:
        r_model = calc_macro_reflectance_with_localized_air_gap(
            location_key=best_location_key,
            d_bulk_nm=params_obj["d_bulk"].value,
            d_rough_nm=params_obj["d_rough"].value,
            d_air_nm=params_obj["d_air"].value,
            ito_alpha=params_obj["ito_alpha"].value,
            sigma_thickness_nm=params_obj["sigma_thickness"].value,
            pvk_b_scale=params_obj["pvk_b_scale"].value,
            niox_k=params_obj["niox_k"].value,
            wavelength_nm=wavelength_nm,
            get_ito_nk=get_ito_nk,
            get_pvk_nk=get_pvk_nk,
        )
        return r_model - r_target

    result = minimize(residual, params, method="least_squares", max_nfev=MAX_NFEV_RELAXED)
    r_fit = calc_macro_reflectance_with_localized_air_gap(
        location_key=best_location_key,
        d_bulk_nm=float(result.params["d_bulk"].value),
        d_rough_nm=float(result.params["d_rough"].value),
        d_air_nm=float(result.params["d_air"].value),
        ito_alpha=float(result.params["ito_alpha"].value),
        sigma_thickness_nm=float(result.params["sigma_thickness"].value),
        pvk_b_scale=float(result.params["pvk_b_scale"].value),
        niox_k=float(result.params["niox_k"].value),
        wavelength_nm=wavelength_nm,
        get_ito_nk=get_ito_nk,
        get_pvk_nk=get_pvk_nk,
    )
    residual_array = r_fit - r_target

    return LocalizationFitSummary(
        label=f"{LOCATION_LABELS[best_location_key]} 10-parameter relaxed fit",
        chisqr=float(result.chisqr),
        success=bool(result.success),
        nfev=int(result.nfev),
        d_bulk_nm=float(result.params["d_bulk"].value),
        d_rough_nm=float(result.params["d_rough"].value),
        sigma_thickness_nm=float(result.params["sigma_thickness"].value),
        ito_alpha=float(result.params["ito_alpha"].value),
        pvk_b_scale=float(result.params["pvk_b_scale"].value),
        niox_k=float(result.params["niox_k"].value),
        d_air_nm=float(result.params["d_air"].value),
        reflectance_fit=r_fit,
        residual=residual_array,
        result=result,
        location_key=best_location_key,
    )


def summarize_stuck_state(d_air_nm: float, baseline_chisqr: float, new_chisqr: float) -> dict[str, bool]:
    relative_improvement = 1.0 - (new_chisqr / baseline_chisqr)
    return {
        "stuck_at_lower": abs(d_air_nm) <= BOUNDARY_TOLERANCE_NM,
        "stuck_at_initial": abs(d_air_nm - DAIR_INITIAL_NM) <= INITIAL_TOLERANCE_NM,
        "no_material_improvement": relative_improvement <= 0.05,
    }


def compute_material_drift_percent(value: float, base_value: float) -> float:
    return ((value / base_value) - 1.0) * 100.0


def plot_phase04b_panel(
    wavelength_nm: np.ndarray,
    good_spectrum: step04a.CalibratedSpectrum,
    good_six_fit: step04a.FitSummary,
    bad_spectrum: step04a.CalibratedSpectrum,
    bad_six_fit: step04a.FitSummary,
    localization_fits: list[LocalizationFitSummary],
    best_fit: LocalizationFitSummary,
    relaxed_fit: LocalizationFitSummary,
    output_path: Path,
) -> None:
    delta_r_exp = (bad_spectrum.reflectance_smooth - good_spectrum.reflectance_smooth) * 100.0
    # As requested, fingerprint against the best 10p theory.
    # The good reference remains the measured good-21 baseline fit.
    # The best model should align the 1060 nm bump more tightly than the 7p localization step.
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.2), dpi=300)
    ax_bar, ax_fit, ax_delta = axes

    bar_labels = ["6p Baseline", "L1", "L2", "L3"]
    bar_values = [
        bad_six_fit.chisqr,
        next(f.chisqr for f in localization_fits if f.location_key == LOCATION_L1),
        next(f.chisqr for f in localization_fits if f.location_key == LOCATION_L2),
        next(f.chisqr for f in localization_fits if f.location_key == LOCATION_L3),
    ]
    bar_colors = ["#9e9e9e", "#90caf9", "#64b5f6", "#1565c0"]
    ax_bar.bar(bar_labels, bar_values, color=bar_colors)
    ax_bar.set_title("Spatial Localization χ² Comparison")
    ax_bar.set_ylabel("Chi-Square")
    ax_bar.grid(True, axis="y", linestyle="--", alpha=0.35)

    ax_fit.plot(
        wavelength_nm,
        bad_spectrum.reflectance_smooth * 100.0,
        color="#424242",
        linewidth=2.3,
        label="Bad-20-2 Measured Smooth",
    )
    ax_fit.plot(
        wavelength_nm,
        best_fit.reflectance_fit * 100.0,
        color="#ef6c00",
        linewidth=2.0,
        linestyle="--",
        label=f"Best 7p ({LOCATION_LABELS[best_fit.location_key]})",
    )
    ax_fit.plot(
        wavelength_nm,
        relaxed_fit.reflectance_fit * 100.0,
        color="#1565c0",
        linewidth=2.0,
        linestyle="-.",
        label="Best 10p Relaxed Fit",
    )
    ax_fit.set_title("Best 7p vs 10p Fit")
    ax_fit.set_xlabel("Wavelength (nm)")
    ax_fit.set_ylabel("Absolute Reflectance (%)")
    ax_fit.grid(True, linestyle="--", alpha=0.35)
    ax_fit.legend(fontsize=9)

    delta_r_theory = (relaxed_fit.reflectance_fit - good_six_fit.reflectance_fit) * 100.0

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
        label="ΔR_theory = Best 10p - Good",
    )
    ax_delta.set_title("Delta R Fingerprint")
    ax_delta.set_xlabel("Wavelength (nm)")
    ax_delta.set_ylabel("ΔR (%)")
    ax_delta.grid(True, linestyle="--", alpha=0.35)
    ax_delta.legend(fontsize=9)

    for axis in axes:
        axis.set_xlim(float(wavelength_nm.min()), float(wavelength_nm.max()))

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_phase04b_log(
    log_path: Path,
    localization_fits: list[LocalizationFitSummary],
    bad_six_fit: step04a.FitSummary,
    relaxed_fit: LocalizationFitSummary,
    good_six_fit: step04a.FitSummary,
) -> None:
    best_fit = min(localization_fits, key=lambda item: item.chisqr)
    lines = [
        f"# {PHASE_NAME} Localization Diagnostic",
        "",
        "## Spatial Localization (7p, materials locked to good-21)",
        "",
    ]
    for fit in localization_fits:
        stuck = summarize_stuck_state(float(fit.d_air_nm or 0.0), bad_six_fit.chisqr, fit.chisqr)
        lines.extend(
            [
                f"- {LOCATION_LABELS[fit.location_key]}: chi-square = `{fit.chisqr:.6f}`, d_air = `{float(fit.d_air_nm or 0.0):.3f} nm`, "
                f"stuck_lower = `{stuck['stuck_at_lower']}`, stuck_initial = `{stuck['stuck_at_initial']}`",
            ]
        )

    ito_drift = compute_material_drift_percent(relaxed_fit.ito_alpha, good_six_fit.ito_alpha)
    pvk_drift = compute_material_drift_percent(relaxed_fit.pvk_b_scale, good_six_fit.pvk_b_scale)
    niox_drift = compute_material_drift_percent(relaxed_fit.niox_k, good_six_fit.niox_k)
    lines.extend(
        [
            "",
            "## Best Localization + 10p Relaxation",
            "",
            f"- best location = `{LOCATION_LABELS[best_fit.location_key]}`",
            f"- chi-square 6p baseline = `{bad_six_fit.chisqr:.6f}`",
            f"- chi-square best 7p = `{best_fit.chisqr:.6f}`",
            f"- chi-square 10p relaxed = `{relaxed_fit.chisqr:.6f}`",
            f"- d_air (10p) = `{float(relaxed_fit.d_air_nm or 0.0):.3f} nm`",
            f"- ITO Alpha drift = `{ito_drift:+.2f}%`",
            f"- PVK B-Scale drift = `{pvk_drift:+.2f}%`",
            f"- NiOx k drift = `{niox_drift:+.2f}%`",
        ]
    )
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    project_root = get_project_root()
    good_csv = project_root / "test_data" / "good-21.csv"
    bad_csv = project_root / "test_data" / "bad-20-2.csv"
    mirror_csv = project_root / "test_data" / "Ag-mirro.csv"
    reference_excel = project_root / "resources" / "GCC-1022系列xlsx.xlsx"

    processed_dir = project_root / "data" / "processed" / "phase04b"
    figure_path = project_root / "results" / "figures" / "phase04b_localization.png"
    log_path = project_root / "results" / "logs" / "phase04b_localization.md"
    processed_dir.mkdir(parents=True, exist_ok=True)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    mirror_wavelength_raw, mirror_signal_raw = step04a.step01.load_csv_spectrum(mirror_csv)
    mirror_wavelength_nm, mirror_signal = step04a.step01.crop_spectrum(mirror_wavelength_raw, mirror_signal_raw)
    excel_wavelength_raw, excel_reflectance_raw = step04a.step01.load_excel_reference(reference_excel)
    excel_wavelength_nm, excel_reflectance = step04a.step01.crop_spectrum(excel_wavelength_raw, excel_reflectance_raw)

    good_spectrum = step04a.calibrate_sample(
        sample_name=GOOD_SAMPLE_NAME,
        sample_csv=good_csv,
        mirror_wavelength_nm=mirror_wavelength_nm,
        mirror_signal_raw=mirror_signal,
        excel_wavelength_nm=excel_wavelength_nm,
        excel_reflectance=excel_reflectance,
    )
    bad_spectrum = step04a.calibrate_sample(
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
        raise ValueError("good-21 / bad-20-2 的波长网格不一致。")

    step04a.export_calibrated_csv(good_spectrum, processed_dir / "good-21_calibrated.csv")
    step04a.export_calibrated_csv(bad_spectrum, processed_dir / "bad-20-2_calibrated.csv")

    get_ito_nk, get_pvk_nk = step04a.build_material_interpolators(project_root)
    good_six_fit = step04a.fit_six_parameter_model(
        label="good-21 6-parameter fit",
        wavelength_nm=good_spectrum.wavelength_nm,
        r_target=good_spectrum.reflectance_smooth,
        get_ito_nk=get_ito_nk,
        get_pvk_nk=get_pvk_nk,
    )
    bad_six_fit = step04a.fit_six_parameter_model(
        label="bad-20-2 6-parameter fit",
        wavelength_nm=bad_spectrum.wavelength_nm,
        r_target=bad_spectrum.reflectance_smooth,
        get_ito_nk=get_ito_nk,
        get_pvk_nk=get_pvk_nk,
    )

    localization_fits = [
        fit_localization_model(
            location_key=location_key,
            wavelength_nm=bad_spectrum.wavelength_nm,
            r_target=bad_spectrum.reflectance_smooth,
            get_ito_nk=get_ito_nk,
            get_pvk_nk=get_pvk_nk,
            bad_six_fit=bad_six_fit,
            good_six_fit=good_six_fit,
        )
        for location_key in [LOCATION_L1, LOCATION_L2, LOCATION_L3]
    ]
    best_fit = min(localization_fits, key=lambda item: item.chisqr)
    relaxed_fit = fit_relaxed_model(
        best_location_key=str(best_fit.location_key),
        wavelength_nm=bad_spectrum.wavelength_nm,
        r_target=bad_spectrum.reflectance_smooth,
        get_ito_nk=get_ito_nk,
        get_pvk_nk=get_pvk_nk,
        best_fit=best_fit,
        good_six_fit=good_six_fit,
    )

    plot_phase04b_panel(
        wavelength_nm=bad_spectrum.wavelength_nm,
        good_spectrum=good_spectrum,
        good_six_fit=good_six_fit,
        bad_spectrum=bad_spectrum,
        bad_six_fit=bad_six_fit,
        localization_fits=localization_fits,
        best_fit=best_fit,
        relaxed_fit=relaxed_fit,
        output_path=figure_path,
    )
    write_phase04b_log(
        log_path=log_path,
        localization_fits=localization_fits,
        bad_six_fit=bad_six_fit,
        relaxed_fit=relaxed_fit,
        good_six_fit=good_six_fit,
    )

    print(f"{PHASE_NAME} localization complete.")
    print(f"Diagnostic figure: {figure_path}")
    print(f"Diagnostic log: {log_path}")
    print(f"Good chi-square (6p): {good_six_fit.chisqr:.6f}")
    print(f"Bad chi-square (6p): {bad_six_fit.chisqr:.6f}")
    for fit in localization_fits:
        print(
            f"{LOCATION_LABELS[fit.location_key]} -> chi-square = {fit.chisqr:.6f}, "
            f"d_air = {float(fit.d_air_nm or 0.0):.6f} nm"
        )
    print(
        f"Best 10p relaxed ({LOCATION_LABELS[relaxed_fit.location_key]}) -> "
        f"chi-square = {relaxed_fit.chisqr:.6f}, d_air = {float(relaxed_fit.d_air_nm or 0.0):.6f} nm"
    )


if __name__ == "__main__":
    main()
