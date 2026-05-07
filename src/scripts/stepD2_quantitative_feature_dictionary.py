"""Phase D-2 quantitative spectral-feature dictionary for automated routing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import shutil

import matplotlib
import numpy as np
import pandas as pd
import pywt
from matplotlib.colors import TwoSlopeNorm
from scipy import signal, stats
from scipy.signal import find_peaks, hilbert
from sklearn.decomposition import PCA
import umap

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHASE_NAME = "Phase D-2"
PHASE_D1_DIR = PROJECT_ROOT / "data" / "processed" / "phaseD1"
PHASE_D1_REPORT = PROJECT_ROOT / "results" / "report" / "phaseD1_airgap_discrimination_database" / "PHASE_D1_REPORT.md"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phaseD2"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phaseD2"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phaseD2"
REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phaseD2_quantitative_feature_dictionary"

WINDOW_ANALYSIS = (500.0, 1055.0)
WINDOW_FRONT = (500.0, 650.0)
WINDOW_TRANSITION = (650.0, 810.0)
WINDOW_REAR = (810.0, 1055.0)
THICKNESS_WINDOW = (675.0, 725.0)
SHIFT_SEARCH_NM = np.arange(-30.0, 31.0, 1.0, dtype=float)
WAVELET_NAME = "cmor1.5-1.0"
WAVELET_SCALES = np.geomspace(2.0, 64.0, 32)

ROUTING_FAMILIES = [
    "thickness_nuisance",
    "front_roughness_nuisance",
    "rear_roughness_nuisance",
    "front_gap_on_background",
    "rear_gap_on_background",
]
FAMILY_LABELS = {
    "background_anchor": "Background anchor",
    "thickness_nuisance": "Thickness nuisance",
    "front_roughness_nuisance": "Front roughness",
    "rear_roughness_nuisance": "Rear roughness",
    "front_gap_on_background": "Front gap",
    "rear_gap_on_background": "Rear gap",
}
FAMILY_COLORS = {
    "background_anchor": "#9e9e9e",
    "thickness_nuisance": "#1565c0",
    "front_roughness_nuisance": "#ef6c00",
    "rear_roughness_nuisance": "#00897b",
    "front_gap_on_background": "#6a1b9a",
    "rear_gap_on_background": "#c62828",
}
TEMPLATE_SHORT_NAMES = {
    "thickness_nuisance": "thickness",
    "front_roughness_nuisance": "front_roughness",
    "rear_roughness_nuisance": "rear_roughness",
    "front_gap_on_background": "front_gap",
    "rear_gap_on_background": "rear_gap",
}


@dataclass(frozen=True)
class OutputPaths:
    feature_database_csv: Path
    family_templates_csv: Path
    separability_summary_csv: Path
    thickness_heatmap_png: Path
    thickness_selected_curves_png: Path
    frequency_scatter_png: Path
    wavelet_scatter_png: Path
    template_scatter_png: Path
    top_feature_boxplots_png: Path
    family_embedding_pca_png: Path
    family_embedding_umap_png: Path
    rear_fft_examples_png: Path
    wavelet_examples_png: Path
    log_md: Path
    report_md: Path
    report_readme: Path


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Build Phase D-2 quantitative feature dictionary.").parse_args()


def ensure_output_dirs() -> OutputPaths:
    for path in (PROCESSED_DIR, FIGURE_DIR, LOG_DIR, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    return OutputPaths(
        feature_database_csv=PROCESSED_DIR / "phaseD2_quantitative_feature_database.csv",
        family_templates_csv=PROCESSED_DIR / "phaseD2_family_templates.csv",
        separability_summary_csv=PROCESSED_DIR / "phaseD2_feature_separability_summary.csv",
        thickness_heatmap_png=FIGURE_DIR / "phaseD2_thickness_local_deltaRtotal_heatmap.png",
        thickness_selected_curves_png=FIGURE_DIR / "phaseD2_thickness_local_selected_curves.png",
        frequency_scatter_png=FIGURE_DIR / "phaseD2_frequency_feature_scatter.png",
        wavelet_scatter_png=FIGURE_DIR / "phaseD2_wavelet_feature_scatter.png",
        template_scatter_png=FIGURE_DIR / "phaseD2_template_similarity_scatter.png",
        top_feature_boxplots_png=FIGURE_DIR / "phaseD2_top_feature_boxplots.png",
        family_embedding_pca_png=FIGURE_DIR / "phaseD2_family_embedding_pca.png",
        family_embedding_umap_png=FIGURE_DIR / "phaseD2_family_embedding_umap.png",
        rear_fft_examples_png=FIGURE_DIR / "phaseD2_rear_fft_examples.png",
        wavelet_examples_png=FIGURE_DIR / "phaseD2_wavelet_examples.png",
        log_md=LOG_DIR / "phaseD2_quantitative_feature_dictionary.md",
        report_md=REPORT_DIR / "PHASE_D2_REPORT.md",
        report_readme=REPORT_DIR / "README.md",
    )


def rms(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    return float(np.sqrt(np.mean(np.square(values))))


def safe_ratio(num: float, den: float) -> float:
    return float(num / max(abs(den), 1e-12))


def window_mask(x: np.ndarray, window: tuple[float, float]) -> np.ndarray:
    return (x >= window[0]) & (x <= window[1])


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return 0.0 if denom <= 1e-12 else float(np.dot(a, b) / denom)


def ncc_max(a: np.ndarray, b: np.ndarray) -> float:
    a0 = np.asarray(a, dtype=float) - float(np.mean(a))
    b0 = np.asarray(b, dtype=float) - float(np.mean(b))
    denom = float(np.linalg.norm(a0) * np.linalg.norm(b0))
    if denom <= 1e-12:
        return 0.0
    return float(np.max(signal.correlate(a0, b0, mode="full", method="fft") / denom))


def resample_uniform_k(wavelength_nm: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    wl = np.asarray(wavelength_nm, dtype=float)
    val = np.asarray(values, dtype=float)
    k = 1.0 / wl
    k_uniform = np.linspace(float(k.min()), float(k.max()), wl.size)
    return k_uniform, np.interp(k_uniform, k, val)


def preprocess_fft_signal(values: np.ndarray) -> np.ndarray:
    return signal.detrend(np.asarray(values, dtype=float), type="linear") * np.hanning(len(values))


def pearson_corr(a: np.ndarray, b: np.ndarray) -> float:
    if np.std(a) <= 1e-12 or np.std(b) <= 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def shifted_window_signal(wavelength_nm: np.ndarray, values: np.ndarray, shift_nm: float) -> tuple[np.ndarray, np.ndarray]:
    query = wavelength_nm - shift_nm
    valid = (query >= float(wavelength_nm.min())) & (query <= float(wavelength_nm.max()))
    shifted = np.interp(query[valid], wavelength_nm, values)
    return valid, shifted


def rear_shift_metrics(wavelength_nm: np.ndarray, case_signal: np.ndarray, reference_signal: np.ndarray) -> dict[str, object]:
    rear_mask = window_mask(wavelength_nm, WINDOW_REAR)
    rear_wl = wavelength_nm[rear_mask]
    case_rear = np.asarray(case_signal[rear_mask], dtype=float)
    ref_rear = np.asarray(reference_signal[rear_mask], dtype=float)
    unaligned_rms = rms(case_rear - ref_rear)
    best_shift_nm = 0.0
    best_rms = unaligned_rms
    best_valid = np.ones_like(case_rear, dtype=bool)
    best_shifted = case_rear.copy()
    best_ref = ref_rear.copy()
    for shift_nm in SHIFT_SEARCH_NM:
        valid, shifted = shifted_window_signal(rear_wl, case_rear, float(shift_nm))
        if int(np.count_nonzero(valid)) < 8:
            continue
        candidate_ref = ref_rear[valid]
        candidate_rms = rms(shifted - candidate_ref)
        if candidate_rms < best_rms:
            best_shift_nm = float(shift_nm)
            best_rms = candidate_rms
            best_valid = valid
            best_shifted = shifted
            best_ref = candidate_ref
    explained = 1.0 if unaligned_rms <= 1e-12 else float(np.clip(1.0 - best_rms / unaligned_rms, 0.0, 1.0))
    corr_before = pearson_corr(case_rear, ref_rear)
    corr_after = pearson_corr(best_shifted, best_ref)
    aligned_residual = best_shifted - best_ref
    k_uniform, shifted_k = resample_uniform_k(rear_wl[best_valid], best_shifted)
    _, ref_k = resample_uniform_k(rear_wl[best_valid], best_ref)
    shifted_osc = signal.detrend(shifted_k, type="linear")
    ref_osc = signal.detrend(ref_k, type="linear")
    phase_diff = np.unwrap(np.angle(hilbert(shifted_osc)) - np.angle(hilbert(ref_osc)))
    if k_uniform.size >= 4 and np.std(phase_diff) > 1e-12:
        coeff = np.polyfit(k_uniform, phase_diff, deg=1)
        phase_slope_error = float(abs(coeff[0]) * (float(k_uniform.max()) - float(k_uniform.min())))
    else:
        phase_slope_error = 0.0
    return {
        "rear_best_shift_nm": best_shift_nm,
        "rear_shift_explained_fraction": explained,
        "rear_aligned_rms_residual": best_rms,
        "rear_unaligned_rms_residual": unaligned_rms,
        "rear_corr_before_shift": corr_before,
        "rear_corr_after_shift": corr_after,
        "rear_phase_slope_error": phase_slope_error,
        "rear_wavelength_nm": rear_wl,
        "rear_valid_wavelength_nm": rear_wl[best_valid],
        "rear_case_signal": case_rear,
        "rear_reference_signal": ref_rear,
        "rear_aligned_residual": aligned_residual,
        "rear_shifted_case": best_shifted,
        "rear_shifted_reference": best_ref,
    }


def rear_frequency_features(wavelength_nm: np.ndarray, reference_signal: np.ndarray, case_signal: np.ndarray, aligned_residual: np.ndarray) -> dict[str, object]:
    k_uniform, ref_k = resample_uniform_k(wavelength_nm, reference_signal)
    _, case_k = resample_uniform_k(wavelength_nm, case_signal)
    _, residual_k = resample_uniform_k(wavelength_nm, aligned_residual)
    ref_proc = preprocess_fft_signal(ref_k)
    case_proc = preprocess_fft_signal(case_k)
    residual_proc = preprocess_fft_signal(residual_k)
    freq = np.fft.rfftfreq(residual_proc.size, d=float(np.mean(np.diff(k_uniform))))
    ref_power = np.abs(np.fft.rfft(ref_proc)) ** 2
    case_power = np.abs(np.fft.rfft(case_proc)) ** 2
    power = np.abs(np.fft.rfft(residual_proc)) ** 2
    if power.size <= 1 or np.all(power[1:] <= 1e-18):
        return {
            "rear_dom_freq": 0.0,
            "rear_dom_freq_amplitude": 0.0,
            "rear_dom_freq_bandwidth": 0.0,
            "rear_spectral_centroid": 0.0,
            "rear_spectral_entropy": 0.0,
            "rear_sideband_energy_fraction": 0.0,
            "rear_second_peak_to_first_peak_ratio": 0.0,
            "rear_fft_freq": freq,
            "rear_fft_power": power,
            "rear_fft_reference_power": ref_power,
            "rear_fft_case_power": case_power,
        }
    pos_freq = freq[1:]
    pos_power = power[1:]
    peaks, _ = find_peaks(pos_power)
    if peaks.size == 0:
        peaks = np.array([int(np.argmax(pos_power))], dtype=int)
    ranked = peaks[np.argsort(pos_power[peaks])[::-1]]
    i0 = int(ranked[0])
    amp0 = float(pos_power[i0])
    half = amp0 * 0.5
    left = i0
    right = i0
    while left > 0 and pos_power[left] >= half:
        left -= 1
    while right < pos_power.size - 1 and pos_power[right] >= half:
        right += 1
    total_energy = float(np.sum(pos_power))
    prob = pos_power / max(total_energy, 1e-18)
    inband = (pos_freq >= pos_freq[left]) & (pos_freq <= pos_freq[right])
    return {
        "rear_dom_freq": float(pos_freq[i0]),
        "rear_dom_freq_amplitude": amp0,
        "rear_dom_freq_bandwidth": float(pos_freq[right] - pos_freq[left]),
        "rear_spectral_centroid": 0.0 if total_energy <= 1e-18 else float(np.sum(pos_freq * pos_power) / total_energy),
        "rear_spectral_entropy": float(-np.sum(prob * np.log(prob + 1e-18)) / np.log(prob.size)),
        "rear_sideband_energy_fraction": 0.0 if total_energy <= 1e-18 else float(np.sum(pos_power[~inband]) / total_energy),
        "rear_second_peak_to_first_peak_ratio": 0.0 if ranked.size < 2 else float(pos_power[int(ranked[1])] / max(amp0, 1e-12)),
        "rear_fft_freq": freq,
        "rear_fft_power": power,
        "rear_fft_reference_power": ref_power,
        "rear_fft_case_power": case_power,
    }


def wavelet_features(wavelength_nm: np.ndarray, delta_signal: np.ndarray) -> dict[str, object]:
    mask = window_mask(wavelength_nm, WINDOW_ANALYSIS)
    wl = wavelength_nm[mask]
    delta = np.asarray(delta_signal[mask], dtype=float)
    coef, _ = pywt.cwt(delta, WAVELET_SCALES, WAVELET_NAME)
    power = np.abs(coef) ** 2
    total_power = float(np.sum(power))
    total_power = 1.0 if total_power <= 1e-18 else total_power

    def region(window: tuple[float, float]) -> tuple[float, float, float]:
        region_mask = window_mask(wl, window)
        region_power = power[:, region_mask]
        energy = float(np.sum(region_power) / total_power)
        profile = np.sum(region_power, axis=1)
        if float(np.sum(profile)) <= 1e-18:
            return energy, 0.0, float(WAVELET_SCALES[0])
        prob = profile / np.sum(profile)
        entropy = float(-np.sum(prob * np.log(prob + 1e-18)) / np.log(prob.size))
        return energy, entropy, float(WAVELET_SCALES[int(np.argmax(profile))])

    front_energy, front_entropy, _ = region(WINDOW_FRONT)
    transition_energy, transition_entropy, transition_peak_scale = region(WINDOW_TRANSITION)
    rear_energy, rear_entropy, rear_peak_scale = region(WINDOW_REAR)
    return {
        "wavelet_energy_front": front_energy,
        "wavelet_energy_transition": transition_energy,
        "wavelet_energy_rear": rear_energy,
        "wavelet_entropy_front": front_entropy,
        "wavelet_entropy_transition": transition_entropy,
        "wavelet_entropy_rear": rear_entropy,
        "transition_peak_scale": transition_peak_scale,
        "rear_peak_scale": rear_peak_scale,
        "wavelet_wavelength_nm": wl,
        "wavelet_power": power,
    }


def build_family_templates(analysis_frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    template_rows: list[dict[str, object]] = []
    template_vectors: dict[str, np.ndarray] = {}
    for family in ROUTING_FAMILIES:
        subset = analysis_frame[analysis_frame["family"] == family].copy()
        if family == "front_gap_on_background":
            subset = subset[subset["d_gap_front_nm"] > 0.0]
        elif family == "rear_gap_on_background":
            subset = subset[subset["d_gap_rear_nm"] > 0.0]
        pivot = subset.pivot(index="case_id", columns="Wavelength_nm", values="Delta_R_total_vs_reference").sort_index(axis=1)
        mean_curve = pivot.to_numpy(dtype=float).mean(axis=0)
        std_curve = pivot.to_numpy(dtype=float).std(axis=0, ddof=0)
        template_vectors[family] = mean_curve
        for wl, mean_value, std_value in zip(pivot.columns.to_numpy(dtype=float), mean_curve, std_curve):
            template_rows.append({"family": family, "Wavelength_nm": float(wl), "mean_deltaR_total": float(mean_value), "std_deltaR_total": float(std_value)})
    return pd.DataFrame(template_rows), template_vectors


def build_feature_database(spectra_frame: pd.DataFrame, d1_feature_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    analysis_frame = spectra_frame[window_mask(spectra_frame["Wavelength_nm"].to_numpy(dtype=float), WINDOW_ANALYSIS)].copy()
    template_frame, template_vectors = build_family_templates(analysis_frame)
    feature_rows: list[dict[str, object]] = []
    diagnostics_rows: list[dict[str, object]] = []
    key_columns = ["case_id", "family", "anchor_id", "reference_case_id", "d_PVK_nm", "d_BEMA_front_nm", "d_BEMA_rear_nm", "d_gap_front_nm", "d_gap_rear_nm"]
    for meta in d1_feature_frame[key_columns].itertuples(index=False):
        mask = (
            (analysis_frame["case_id"] == str(meta.case_id))
            & (analysis_frame["family"] == str(meta.family))
            & (analysis_frame["anchor_id"] == str(meta.anchor_id))
            & (analysis_frame["reference_case_id"] == str(meta.reference_case_id))
            & np.isclose(analysis_frame["d_PVK_nm"].to_numpy(dtype=float), float(meta.d_PVK_nm))
            & np.isclose(analysis_frame["d_BEMA_front_nm"].to_numpy(dtype=float), float(meta.d_BEMA_front_nm))
            & np.isclose(analysis_frame["d_BEMA_rear_nm"].to_numpy(dtype=float), float(meta.d_BEMA_rear_nm))
            & np.isclose(analysis_frame["d_gap_front_nm"].to_numpy(dtype=float), float(meta.d_gap_front_nm))
            & np.isclose(analysis_frame["d_gap_rear_nm"].to_numpy(dtype=float), float(meta.d_gap_rear_nm))
        )
        subset = analysis_frame.loc[mask].sort_values("Wavelength_nm")
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        r_total = subset["R_total"].to_numpy(dtype=float)
        delta_r = subset["Delta_R_total_vs_reference"].to_numpy(dtype=float)
        reference = r_total - delta_r
        front_rms = rms(delta_r[window_mask(wl, WINDOW_FRONT)])
        transition_rms = rms(delta_r[window_mask(wl, WINDOW_TRANSITION)])
        rear_rms = rms(delta_r[window_mask(wl, WINDOW_REAR)])
        shift = rear_shift_metrics(wl, r_total, reference)
        freq = rear_frequency_features(
            wavelength_nm=np.asarray(shift["rear_valid_wavelength_nm"], dtype=float),
            reference_signal=np.asarray(shift["rear_shifted_reference"], dtype=float),
            case_signal=np.asarray(shift["rear_shifted_case"], dtype=float),
            aligned_residual=np.asarray(shift["rear_aligned_residual"], dtype=float),
        )
        wav = wavelet_features(wl, delta_r)
        row: dict[str, object] = {
            "case_key": f"{meta.case_id}|{meta.family}|{meta.anchor_id}|{meta.reference_case_id}",
            "case_id": str(meta.case_id),
            "family": str(meta.family),
            "anchor_id": str(meta.anchor_id),
            "reference_case_id": str(meta.reference_case_id),
            "d_PVK_nm": float(meta.d_PVK_nm),
            "d_BEMA_front_nm": float(meta.d_BEMA_front_nm),
            "d_BEMA_rear_nm": float(meta.d_BEMA_rear_nm),
            "d_gap_front_nm": float(meta.d_gap_front_nm),
            "d_gap_rear_nm": float(meta.d_gap_rear_nm),
            "front_rms_deltaR_500_650": front_rms,
            "transition_rms_deltaR_650_810": transition_rms,
            "rear_rms_deltaR_810_1055": rear_rms,
            "front_plus_transition_to_rear_ratio": safe_ratio(front_rms + transition_rms, rear_rms),
            "front_to_rear_ratio": safe_ratio(front_rms, rear_rms),
            "transition_to_rear_ratio": safe_ratio(transition_rms, rear_rms),
        }
        for pack in (shift, freq, wav):
            for key, value in pack.items():
                if not isinstance(value, np.ndarray):
                    row[key] = float(value)
        for family in ROUTING_FAMILIES:
            short = TEMPLATE_SHORT_NAMES[family]
            template = template_vectors[family]
            row[f"sim_to_{short}_template"] = cosine_similarity(delta_r, template)
            row[f"ncc_to_{short}_template"] = ncc_max(delta_r, template)
        feature_rows.append(row)
        diagnostics_rows.append(
            {
                "case_key": f"{meta.case_id}|{meta.family}|{meta.anchor_id}|{meta.reference_case_id}",
                "case_id": str(meta.case_id),
                "family": str(meta.family),
                "wavelength_nm": wl,
                "delta_r": delta_r,
                "rear_fft_freq": freq["rear_fft_freq"],
                "rear_fft_power": freq["rear_fft_power"],
                "rear_fft_reference_power": freq["rear_fft_reference_power"],
                "rear_fft_case_power": freq["rear_fft_case_power"],
                "wavelet_wavelength_nm": wav["wavelet_wavelength_nm"],
                "wavelet_power": wav["wavelet_power"],
            }
        )
    return pd.DataFrame(feature_rows), template_frame, pd.DataFrame(diagnostics_rows)


def build_separability_summary(feature_frame: pd.DataFrame) -> pd.DataFrame:
    route_frame = feature_frame[feature_frame["family"].isin(ROUTING_FAMILIES)].copy()
    ignore = {"case_key", "case_id", "family", "anchor_id", "reference_case_id"}
    feature_columns = [c for c in route_frame.columns if c not in ignore and route_frame[c].dtype != object]
    rows: list[dict[str, object]] = []
    for column in feature_columns:
        groups = [route_frame.loc[route_frame["family"] == family, column].to_numpy(dtype=float) for family in ROUTING_FAMILIES]
        f_score, p_value = stats.f_oneway(*groups)
        overall_mean = float(route_frame[column].mean())
        ss_between = float(sum(len(group) * (float(np.mean(group)) - overall_mean) ** 2 for group in groups))
        ss_total = float(np.sum((route_frame[column].to_numpy(dtype=float) - overall_mean) ** 2))
        row: dict[str, object] = {"feature_name": column, "anova_f_score": float(f_score), "anova_p_value": float(p_value), "eta_squared": 0.0 if ss_total <= 1e-18 else float(ss_between / ss_total)}
        for family in ROUTING_FAMILIES:
            family_values = route_frame.loc[route_frame["family"] == family, column].to_numpy(dtype=float)
            row[f"{family}_mean"] = float(np.mean(family_values))
            row[f"{family}_std"] = float(np.std(family_values, ddof=0))
        rows.append(row)
    summary = pd.DataFrame(rows).sort_values(["anova_f_score", "eta_squared"], ascending=False).reset_index(drop=True)
    summary["rank_by_f_score"] = np.arange(1, len(summary) + 1)
    summary["recommended_for_routing"] = summary["rank_by_f_score"] <= min(10, len(summary))
    return summary


def style_axis(axis: plt.Axes, *, bold: bool = False) -> None:
    axis.set_facecolor("white")
    axis.grid(True, linestyle="--", alpha=0.25)
    if bold:
        axis.xaxis.label.set_fontweight("bold")
        axis.yaxis.label.set_fontweight("bold")
        axis.title.set_fontweight("bold")


def apply_window_guides(axis: plt.Axes) -> None:
    for start, end in (WINDOW_FRONT, WINDOW_TRANSITION, WINDOW_REAR):
        axis.axvline(start, color="#aaaaaa", linewidth=0.8, linestyle=":")
        axis.axvline(end, color="#aaaaaa", linewidth=0.8, linestyle=":")


def plot_thickness_heatmap(spectra_frame: pd.DataFrame, output_path: Path) -> None:
    subset = spectra_frame[
        (spectra_frame["family"] == "thickness_nuisance")
        & (spectra_frame["Wavelength_nm"] >= THICKNESS_WINDOW[0])
        & (spectra_frame["Wavelength_nm"] <= THICKNESS_WINDOW[1])
    ].copy()
    pivot = subset.pivot(index="d_PVK_nm", columns="Wavelength_nm", values="Delta_R_total_vs_reference").sort_index()
    values = pivot.to_numpy(dtype=float) * 100.0
    vmax = float(np.max(np.abs(values)))
    fig, ax = plt.subplots(figsize=(11.6, 6.0), dpi=320)
    im = ax.imshow(
        values,
        origin="lower",
        aspect="auto",
        extent=[float(pivot.columns.min()), float(pivot.columns.max()), float(pivot.index.min()), float(pivot.index.max())],
        cmap="RdBu_r",
        norm=TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax),
    )
    ax.axvline(700.0, color="#212121", linewidth=1.0, linestyle="--")
    ax.set_xlabel("Wavelength (nm)", fontweight="bold")
    ax.set_ylabel("d_PVK (nm)", fontweight="bold")
    ax.set_title(f"{PHASE_NAME} Local Thickness Delta R_total vs 700 nm", fontweight="bold")
    cbar = fig.colorbar(im, ax=ax, pad=0.015)
    cbar.set_label("Delta R_total (%)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_thickness_selected_curves(spectra_frame: pd.DataFrame, output_path: Path) -> None:
    subset = spectra_frame[
        (spectra_frame["family"] == "thickness_nuisance")
        & (spectra_frame["Wavelength_nm"] >= THICKNESS_WINDOW[0])
        & (spectra_frame["Wavelength_nm"] <= THICKNESS_WINDOW[1])
    ].copy()
    selected = [675.0, 690.0, 700.0, 710.0, 725.0]
    colors = plt.cm.viridis(np.linspace(0.12, 0.9, len(selected)))
    fig, axes = plt.subplots(2, 1, figsize=(11.2, 7.2), dpi=320, sharex=True)
    for color, value in zip(colors, selected):
        curve = subset[np.isclose(subset["d_PVK_nm"], value)]
        axes[0].plot(curve["Wavelength_nm"], curve["R_total"] * 100.0, color=color, linewidth=2.0, label=f"{value:.0f} nm")
        axes[1].plot(curve["Wavelength_nm"], curve["Delta_R_total_vs_reference"] * 100.0, color=color, linewidth=2.0)
    axes[0].set_ylabel("R_total (%)", fontweight="bold")
    axes[0].set_title(f"{PHASE_NAME} Local Thickness Selected Curves", fontweight="bold")
    axes[0].legend(loc="best", ncol=3)
    axes[1].set_xlabel("Wavelength (nm)", fontweight="bold")
    axes[1].set_ylabel("Delta R_total (%)", fontweight="bold")
    for axis in axes:
        style_axis(axis, bold=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_feature_scatter(feature_frame: pd.DataFrame, output_path: Path, x_col: str, y_col: str, title: str, x_label: str, y_label: str) -> None:
    route_frame = feature_frame[feature_frame["family"].isin(ROUTING_FAMILIES)].copy()
    fig, ax = plt.subplots(figsize=(8.6, 6.5), dpi=320)
    for family in ROUTING_FAMILIES:
        subset = route_frame[route_frame["family"] == family]
        ax.scatter(subset[x_col], subset[y_col], s=52, alpha=0.82, color=FAMILY_COLORS[family], label=FAMILY_LABELS[family], edgecolors="white", linewidths=0.5)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    style_axis(ax)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_top_feature_boxplots(feature_frame: pd.DataFrame, separability_summary: pd.DataFrame, output_path: Path) -> None:
    route_frame = feature_frame[feature_frame["family"].isin(ROUTING_FAMILIES)].copy()
    top_features = separability_summary.head(4)["feature_name"].tolist()
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 9.0), dpi=320)
    for axis, feature_name in zip(axes.ravel(), top_features):
        data = [route_frame.loc[route_frame["family"] == family, feature_name].to_numpy(dtype=float) for family in ROUTING_FAMILIES]
        box = axis.boxplot(data, patch_artist=True, tick_labels=[FAMILY_LABELS[family] for family in ROUTING_FAMILIES], showfliers=False)
        for patch, family in zip(box["boxes"], ROUTING_FAMILIES):
            patch.set_facecolor(FAMILY_COLORS[family])
            patch.set_alpha(0.72)
        axis.tick_params(axis="x", rotation=18)
        axis.set_title(feature_name)
        style_axis(axis)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_embedding_single(embedding_xy: np.ndarray, families: pd.Series, output_path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(8.6, 6.8), dpi=320)
    for family in ROUTING_FAMILIES:
        mask = families == family
        ax.scatter(
            embedding_xy[mask, 0],
            embedding_xy[mask, 1],
            color=FAMILY_COLORS[family],
            s=52,
            alpha=0.86,
            label=FAMILY_LABELS[family],
            edgecolors="white",
            linewidths=0.5,
        )
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")
    style_axis(ax)
    handles, labels = ax.get_legend_handles_labels()
    fig.suptitle(title, y=0.982)
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.94), ncol=3, frameon=False)
    fig.subplots_adjust(top=0.81, left=0.11, right=0.98, bottom=0.11)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_embedding(feature_frame: pd.DataFrame, separability_summary: pd.DataFrame, pca_output_path: Path, umap_output_path: Path) -> None:
    route_frame = feature_frame[feature_frame["family"].isin(ROUTING_FAMILIES)].copy()
    top_features = separability_summary.head(min(12, len(separability_summary)))["feature_name"].tolist()
    matrix = route_frame[top_features].to_numpy(dtype=float)
    matrix = (matrix - matrix.mean(axis=0)) / np.maximum(matrix.std(axis=0), 1e-12)
    pca_xy = PCA(n_components=2, random_state=42).fit_transform(matrix)
    umap_xy = umap.UMAP(n_components=2, random_state=42, n_neighbors=min(15, len(route_frame) - 1), min_dist=0.2).fit_transform(matrix)
    families = route_frame["family"]
    plot_embedding_single(pca_xy, families, pca_output_path, f"{PHASE_NAME} Family Embedding: PCA")
    plot_embedding_single(umap_xy, families, umap_output_path, f"{PHASE_NAME} Family Embedding: UMAP")


def pick_example_cases(feature_frame: pd.DataFrame) -> dict[str, str]:
    subset = feature_frame[feature_frame["family"].isin(ROUTING_FAMILIES)].copy()
    scores = {
        "thickness_nuisance": subset["rear_shift_explained_fraction"] + np.abs(subset["rear_best_shift_nm"]) / 30.0,
        "front_roughness_nuisance": subset["wavelet_energy_front"] + subset["front_plus_transition_to_rear_ratio"],
        "rear_roughness_nuisance": subset["rear_sideband_energy_fraction"] - subset["rear_shift_explained_fraction"],
        "front_gap_on_background": subset["wavelet_energy_front"] + subset["sim_to_front_gap_template"] - 0.5 * subset["sim_to_rear_gap_template"],
        "rear_gap_on_background": subset["rear_sideband_energy_fraction"] + subset["rear_phase_slope_error"],
    }
    selected: dict[str, str] = {}
    for family in ROUTING_FAMILIES:
        family_subset = subset[subset["family"] == family]
        selected[family] = str(family_subset.iloc[int(np.argmax(np.asarray(scores[family][family_subset.index], dtype=float)))]["case_key"])
    return selected


def plot_rear_fft_examples(feature_frame: pd.DataFrame, diagnostics_frame: pd.DataFrame, output_path: Path) -> None:
    selected = pick_example_cases(feature_frame)
    diag_map = diagnostics_frame.set_index("case_key").to_dict(orient="index")
    fig, axes = plt.subplots(len(ROUTING_FAMILIES), 1, figsize=(10.8, 13.0), dpi=320, sharex=True)
    for axis, family in zip(axes, ROUTING_FAMILIES):
        diag = diag_map[selected[family]]
        freq = np.asarray(diag["rear_fft_freq"], dtype=float)
        ref_power = np.asarray(diag["rear_fft_reference_power"], dtype=float)
        case_power = np.asarray(diag["rear_fft_case_power"], dtype=float)
        residual_power = np.asarray(diag["rear_fft_power"], dtype=float)
        axis.plot(freq[1:], ref_power[1:], color="#616161", linewidth=1.3, label="reference")
        axis.plot(freq[1:], case_power[1:], color=FAMILY_COLORS[family], linewidth=1.4, label="case")
        axis.plot(freq[1:], residual_power[1:], color="#111111", linewidth=1.7, linestyle="--", label="aligned residual")
        axis.set_ylabel(FAMILY_LABELS[family])
        style_axis(axis)
    axes[0].legend(loc="upper right", ncol=3)
    axes[-1].set_xlabel("Frequency on uniform 1/lambda grid")
    fig.suptitle(f"{PHASE_NAME} Rear FFT Examples", y=0.995)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_wavelet_examples(feature_frame: pd.DataFrame, diagnostics_frame: pd.DataFrame, output_path: Path) -> None:
    selected = pick_example_cases(feature_frame)
    diag_map = diagnostics_frame.set_index("case_key").to_dict(orient="index")
    fig, axes = plt.subplots(len(ROUTING_FAMILIES), 1, figsize=(11.0, 13.5), dpi=320, sharex=True)
    image = None
    for axis, family in zip(axes, ROUTING_FAMILIES):
        diag = diag_map[selected[family]]
        wl = np.asarray(diag["wavelet_wavelength_nm"], dtype=float)
        power = np.asarray(diag["wavelet_power"], dtype=float)
        image = axis.imshow(power, aspect="auto", origin="lower", extent=[float(wl.min()), float(wl.max()), float(WAVELET_SCALES.min()), float(WAVELET_SCALES.max())], cmap="magma")
        apply_window_guides(axis)
        axis.set_ylabel(FAMILY_LABELS[family])
        style_axis(axis)
    axes[-1].set_xlabel("Wavelength (nm)")
    fig.colorbar(image, ax=axes, pad=0.01, label="Wavelet power")
    fig.suptitle(f"{PHASE_NAME} Wavelet Examples", y=0.995)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def validate_outputs(feature_frame: pd.DataFrame, d1_feature_frame: pd.DataFrame, template_frame: pd.DataFrame, separability_summary: pd.DataFrame) -> None:
    if len(feature_frame) != len(d1_feature_frame):
        raise ValueError("Phase D-2 feature row count does not match Phase D-1.")
    numeric = feature_frame.select_dtypes(include=[np.number]).to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("Phase D-2 feature table contains NaN/Inf.")
    if set(template_frame["family"].unique()) != set(ROUTING_FAMILIES):
        raise ValueError("Template table must contain the five routing families.")
    if not np.all((feature_frame["rear_shift_explained_fraction"] >= -1e-9) & (feature_frame["rear_shift_explained_fraction"] <= 1.0 + 1e-9)):
        raise ValueError("rear_shift_explained_fraction out of bounds.")
    if not np.all((feature_frame["rear_corr_before_shift"] >= -1.0 - 1e-9) & (feature_frame["rear_corr_before_shift"] <= 1.0 + 1e-9)):
        raise ValueError("rear_corr_before_shift out of bounds.")
    if not np.all((feature_frame["rear_corr_after_shift"] >= -1.0 - 1e-9) & (feature_frame["rear_corr_after_shift"] <= 1.0 + 1e-9)):
        raise ValueError("rear_corr_after_shift out of bounds.")
    energy_sum = feature_frame["wavelet_energy_front"] + feature_frame["wavelet_energy_transition"] + feature_frame["wavelet_energy_rear"]
    active_mask = feature_frame[["wavelet_energy_front", "wavelet_energy_transition", "wavelet_energy_rear"]].sum(axis=1).to_numpy(dtype=float) > 1e-12
    if not np.all((energy_sum[active_mask] > 0.90) & (energy_sum[active_mask] < 1.02)):
        raise ValueError("Wavelet energy partition check failed.")
    if not np.all(feature_frame["rear_second_peak_to_first_peak_ratio"] <= 1.0 + 1e-9):
        raise ValueError("Second peak ratio out of bounds.")
    if separability_summary.empty:
        raise ValueError("Separability summary is empty.")


def write_markdown_log(output_path: Path, feature_frame: pd.DataFrame, separability_summary: pd.DataFrame) -> None:
    top10 = separability_summary.head(10)[["rank_by_f_score", "feature_name", "anova_f_score", "eta_squared"]]
    weak = separability_summary.tail(min(8, len(separability_summary)))["feature_name"].tolist()
    top10_lines = "\n".join(
        f"- {int(row.rank_by_f_score)}. {row.feature_name}: F={float(row.anova_f_score):.3f}, eta^2={float(row.eta_squared):.3f}"
        for row in top10.itertuples(index=False)
    )
    text = f"""# {PHASE_NAME} quantitative feature dictionary

## 1. Why rear-window FFT must use wavenumber

Rear fringes are approximately periodic in optical phase, not in wavelength itself. Direct FFT on wavelength smears the dominant period and mixes rigid shift with envelope distortion. Uniform `1/lambda` resampling restores near-stationary fringe spacing, so dominant frequency, bandwidth, and sideband energy become physically interpretable.

## 2. Which features best quantify thickness as rigid shift

`rear_best_shift_nm`, `rear_shift_explained_fraction`, `rear_corr_after_shift`, and low `rear_phase_slope_error`.

## 3. Which features best quantify roughness as amplitude / broadening perturbation

Front roughness: `front_plus_transition_to_rear_ratio`, `wavelet_energy_front`, `wavelet_entropy_front`.
Rear roughness: `rear_sideband_energy_fraction`, `rear_dom_freq_bandwidth`, `rear_spectral_entropy`.

## 4. Which features best quantify rear-gap as non-rigid reconstruction / sideband increase

`rear_sideband_energy_fraction`, `rear_second_peak_to_first_peak_ratio`, `rear_phase_slope_error`, `rear_spectral_entropy`.

## 5. Which features best quantify front-gap as front-window response plus secondary rear coupling

`front_rms_deltaR_500_650`, `wavelet_energy_front`, `sim_to_front_gap_template`, and non-zero rear complexity without rear-gap dominance.

## 6. Which features have the strongest separability

{top10_lines}

## 7. Which features look unstable or low-value

Less useful or unstable in this run: {", ".join(weak)}.
"""
    output_path.write_text(text, encoding="utf-8")


def write_report(output_path: Path, feature_frame: pd.DataFrame, separability_summary: pd.DataFrame) -> None:
    meta_cols = {"case_key", "case_id", "family", "anchor_id", "reference_case_id", "d_PVK_nm", "d_BEMA_front_nm", "d_BEMA_rear_nm", "d_gap_front_nm", "d_gap_rear_nm"}
    n_features = len([c for c in feature_frame.columns if c not in meta_cols])
    top10 = separability_summary.head(10)["feature_name"].tolist()
    route_frame = feature_frame[feature_frame["family"].isin(ROUTING_FAMILIES)].copy()
    front_vs_rear = [name for name in top10 if ("front" in name or "rear" in name)][:6]
    diff_thickness_reargap = sorted(
        ((abs(float(route_frame.loc[route_frame["family"] == "thickness_nuisance", name].mean()) - float(route_frame.loc[route_frame["family"] == "rear_gap_on_background", name].mean())), name) for name in top10),
        reverse=True,
    )
    diff_rough_gap = sorted(
        ((abs(float(route_frame.loc[route_frame["family"].isin(["front_roughness_nuisance", "rear_roughness_nuisance"]), name].mean()) - float(route_frame.loc[route_frame["family"].isin(["front_gap_on_background", "rear_gap_on_background"]), name].mean())), name) for name in top10),
        reverse=True,
    )
    text = f"""# {PHASE_NAME} REPORT

## 1. 阶段目标

从 D-1 的描述性判别数据库推进到可计算、可排序、可路由的特征字典，为自动缺陷 routing 和 family-specific 全谱拟合建立输入层。

## 2. 特征设计逻辑

- 窗口能量：看响应长在哪个窗口。
- rear rigid-shift：看后窗是否像厚度刚体平移。
- rear 频谱：看主频、展宽、侧带和复杂度。
- wavelet / 时频：看局域复杂重构。
- template similarity：把 family mean signature 变成可直接比较的路由特征。

## 3. 关键结果

- thickness 最像 rear-window rigid shift。
- roughness 更像 envelope / amplitude perturbation。
- rear-gap 更像非刚性重构与侧带增加。
- front-gap 更像前窗新增响应加次级 rear 耦合。
- 当前结果已经支持“先分类，再按 family 受限拟合”的路线。

## 4. 推荐算法路线

1. 轻量 hand-crafted feature + tree model
2. 两阶段 routing
3. 低维 embedding + family classification
4. family-specific full-spectrum fitting

## 5. 限制

- 仍未引入 composition variation
- 仍为 specular TMM
- 仍基于 proxy roughness
- 频谱特征对窗口长度和预处理敏感

## 6. 最终汇报

1. 一共提取了 {n_features} 个新增特征。
2. 我认为最有效的前 10 个特征是：{", ".join(top10)}。
3. 哪些特征更适合区分 front vs rear：{", ".join(front_vs_rear)}。
4. 哪些特征更适合区分 thickness vs rear-gap：{", ".join(name for _, name in diff_thickness_reargap[:6])}。
5. 哪些特征更适合区分 roughness vs gap：{", ".join(name for _, name in diff_rough_gap[:6])}。
6. 推荐的自动 routing 路线：先做 hand-crafted feature routing，再做 family-specific full-spectrum fitting。
7. 当前仍缺的物理维度：composition variation、真实粗糙形貌、非镜面散射、实验噪声与工艺漂移。
"""
    output_path.write_text(text, encoding="utf-8")


def write_report_readme(output_path: Path) -> None:
    output_path.write_text("# Phase D-2 Quantitative Feature Dictionary\n\nReport assets for the quantitative routing feature layer.\n", encoding="utf-8")


def sync_report_assets(paths: OutputPaths) -> None:
    for asset in [
        paths.feature_database_csv,
        paths.family_templates_csv,
        paths.separability_summary_csv,
        paths.thickness_heatmap_png,
        paths.thickness_selected_curves_png,
        paths.frequency_scatter_png,
        paths.wavelet_scatter_png,
        paths.template_scatter_png,
        paths.top_feature_boxplots_png,
        paths.family_embedding_pca_png,
        paths.family_embedding_umap_png,
        paths.rear_fft_examples_png,
        paths.wavelet_examples_png,
        paths.log_md,
    ]:
        shutil.copy2(asset, REPORT_DIR / asset.name)


def main() -> None:
    parse_args()
    paths = ensure_output_dirs()
    if not PHASE_D1_REPORT.exists():
        raise FileNotFoundError(PHASE_D1_REPORT)
    spectra_frame = pd.read_csv(PHASE_D1_DIR / "phaseD1_rtotal_database.csv")
    d1_feature_frame = pd.read_csv(PHASE_D1_DIR / "phaseD1_feature_database.csv")
    pd.read_csv(PHASE_D1_DIR / "phaseD1_case_manifest.csv")
    pd.read_csv(PHASE_D1_DIR / "phaseD1_discrimination_summary.csv")
    feature_frame, template_frame, diagnostics_frame = build_feature_database(spectra_frame, d1_feature_frame)
    separability_summary = build_separability_summary(feature_frame)
    validate_outputs(feature_frame, d1_feature_frame, template_frame, separability_summary)
    feature_frame.to_csv(paths.feature_database_csv, index=False)
    template_frame.to_csv(paths.family_templates_csv, index=False)
    separability_summary.to_csv(paths.separability_summary_csv, index=False)
    plot_thickness_heatmap(spectra_frame, paths.thickness_heatmap_png)
    plot_thickness_selected_curves(spectra_frame, paths.thickness_selected_curves_png)
    plot_feature_scatter(feature_frame, paths.frequency_scatter_png, "rear_sideband_energy_fraction", "rear_phase_slope_error", f"{PHASE_NAME} Frequency Feature Scatter", "Rear sideband energy fraction", "Rear phase slope error (rad)")
    plot_feature_scatter(feature_frame, paths.wavelet_scatter_png, "wavelet_energy_front", "wavelet_energy_rear", f"{PHASE_NAME} Wavelet Feature Scatter", "Wavelet energy front", "Wavelet energy rear")
    plot_feature_scatter(feature_frame, paths.template_scatter_png, "sim_to_front_gap_template", "sim_to_rear_gap_template", f"{PHASE_NAME} Template Similarity Scatter", "Similarity to front-gap template", "Similarity to rear-gap template")
    plot_top_feature_boxplots(feature_frame, separability_summary, paths.top_feature_boxplots_png)
    plot_embedding(feature_frame, separability_summary, paths.family_embedding_pca_png, paths.family_embedding_umap_png)
    plot_rear_fft_examples(feature_frame, diagnostics_frame, paths.rear_fft_examples_png)
    plot_wavelet_examples(feature_frame, diagnostics_frame, paths.wavelet_examples_png)
    write_markdown_log(paths.log_md, feature_frame, separability_summary)
    write_report(paths.report_md, feature_frame, separability_summary)
    write_report_readme(paths.report_readme)
    sync_report_assets(paths)


if __name__ == "__main__":
    main()
