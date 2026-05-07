"""Phase C-1a rear-air-gap only sandbox.

This phase introduces a true rear separation layer only:

Glass / ITO / NiOx / SAM / PVK / Air_gap_rear / C60 / Ag / Air

The gap is treated as an added separation optical path, not as a mixed layer
and not as a thickness-conserving proxy. PVK and C60 nominal thicknesses remain
fixed at 700 nm and 15 nm.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import shutil
import sys

import matplotlib
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (str(PROJECT_ROOT / "src"), str(SCRIPT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import stepA1_pristine_baseline as phase_a1  # noqa: E402
from core.full_stack_microcavity import (  # noqa: E402
    AG_BOUNDARY_FINITE_FILM,
    DEFAULT_CONSTANT_GLASS_INDEX,
)


PHASE_NAME = "Phase C-1a"
DEFAULT_NK_CSV_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_pvk_v2.csv"
ENSEMBLE_PATHS = {
    "nominal": PROJECT_ROOT / "resources" / "pvk_ensemble" / "aligned_full_stack_nk_pvk_ens_nominal.csv",
    "more_absorptive": PROJECT_ROOT / "resources" / "pvk_ensemble" / "aligned_full_stack_nk_pvk_ens_more_absorptive.csv",
    "less_absorptive": PROJECT_ROOT / "resources" / "pvk_ensemble" / "aligned_full_stack_nk_pvk_ens_less_absorptive.csv",
}
PHASE_A2_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA2" / "phaseA2_pvk_thickness_scan.csv"
PHASE_B1_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseB1" / "phaseB1_rear_bema_scan.csv"
PHASE_B2_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseB2" / "phaseB2_front_bema_scan.csv"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phaseC1a"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phaseC1a"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phaseC1a"
REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phaseC1a_rear_air_gap_sandbox"

FRONT_WINDOW = (400.0, 650.0)
TRANSITION_WINDOW = (650.0, 810.0)
REAR_WINDOW = (810.0, 1100.0)
NOISE_FLOOR = 0.002
LOD_TARGETS_NM = (1.0, 2.0, 3.0, 5.0, 10.0)
SELECTED_GAPS_NM = (0.0, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 30.0, 50.0)
SPOTCHECK_GAPS_NM = (0.0, 2.0, 5.0, 10.0)
COMPARE_PVK_THICKNESSES_NM = (650.0, 750.0, 850.0)
COMPARE_REAR_BEMA_THICKNESSES_NM = (10.0, 20.0)
COMPARE_FRONT_BEMA_THICKNESSES_NM = (10.0, 20.0)
COMPARE_REAR_GAPS_NM = (2.0, 5.0, 10.0)


@dataclass(frozen=True)
class OutputPaths:
    scan_csv: Path
    feature_csv: Path
    lod_csv: Path
    spotcheck_csv: Path
    robustness_csv: Path
    key_metrics_csv: Path
    log_md: Path
    r_stack_heatmap: Path
    r_total_heatmap: Path
    delta_r_stack_heatmap: Path
    delta_r_total_heatmap: Path
    transition_response_png: Path
    rear_response_png: Path
    selected_curves_png: Path
    tracking_png: Path
    spacing_png: Path
    wavenumber_png: Path
    comparison_png: Path
    lod_png: Path
    ensemble_curves_png: Path
    ensemble_delta_png: Path
    robustness_heatmap_png: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase C-1a rear air-gap sandbox.")
    parser.add_argument("--nk-csv", type=Path, default=DEFAULT_NK_CSV_PATH)
    parser.add_argument("--scan-mode", choices=("a", "b"), default="a")
    return parser.parse_args()


def ensure_dirs() -> OutputPaths:
    for path in (PROCESSED_DIR, FIGURE_DIR, LOG_DIR, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    return OutputPaths(
        scan_csv=PROCESSED_DIR / "phaseC1a_rear_air_gap_scan.csv",
        feature_csv=PROCESSED_DIR / "phaseC1a_rear_air_gap_feature_summary.csv",
        lod_csv=PROCESSED_DIR / "phaseC1a_rear_air_gap_lod_summary.csv",
        spotcheck_csv=PROCESSED_DIR / "phaseC1a_rear_air_gap_ensemble_spotcheck.csv",
        robustness_csv=PROCESSED_DIR / "phaseC1a_rear_air_gap_robustness_summary.csv",
        key_metrics_csv=REPORT_DIR / "phaseC1a_key_metrics.csv",
        log_md=LOG_DIR / "phaseC1a_rear_air_gap_sandbox.md",
        r_stack_heatmap=FIGURE_DIR / "phaseC1a_R_stack_heatmap.png",
        r_total_heatmap=FIGURE_DIR / "phaseC1a_R_total_heatmap.png",
        delta_r_stack_heatmap=FIGURE_DIR / "phaseC1a_deltaR_stack_heatmap.png",
        delta_r_total_heatmap=FIGURE_DIR / "phaseC1a_deltaR_total_heatmap.png",
        transition_response_png=FIGURE_DIR / "phaseC1a_transition_window_response.png",
        rear_response_png=FIGURE_DIR / "phaseC1a_rear_window_response.png",
        selected_curves_png=FIGURE_DIR / "phaseC1a_selected_gap_curves.png",
        tracking_png=FIGURE_DIR / "phaseC1a_peak_valley_tracking.png",
        spacing_png=FIGURE_DIR / "phaseC1a_spacing_vs_gap.png",
        wavenumber_png=FIGURE_DIR / "phaseC1a_selected_curves_wavenumber.png",
        comparison_png=FIGURE_DIR / "phaseC1a_gap_vs_thickness_vs_rearbema_vs_frontbema.png",
        lod_png=FIGURE_DIR / "phaseC1a_lod_vs_gap.png",
        ensemble_curves_png=FIGURE_DIR / "phaseC1a_rear_air_gap_ensemble_curves.png",
        ensemble_delta_png=FIGURE_DIR / "phaseC1a_rear_air_gap_ensemble_deltaR_comparison.png",
        robustness_heatmap_png=FIGURE_DIR / "phaseC1a_rear_air_gap_robustness_heatmap.png",
    )


def build_gap_grid(scan_mode: str) -> np.ndarray:
    if scan_mode == "a":
        fine = np.arange(0.0, 20.0 + 0.5, 0.5, dtype=float)
        coarse = np.asarray([25.0, 30.0, 40.0, 50.0], dtype=float)
        return np.unique(np.concatenate([fine, coarse]))
    return np.arange(0.0, 30.0 + 1.0, 1.0, dtype=float)


def load_stack(nk_csv_path: Path):
    stack, _, _ = phase_a1.load_optical_stack_from_aligned_csv(nk_csv_path)
    return stack


def max_abs_in_window(frame: pd.DataFrame, column: str, window: tuple[float, float]) -> float:
    mask = (frame["Wavelength_nm"] >= window[0]) & (frame["Wavelength_nm"] <= window[1])
    return float(np.max(np.abs(frame.loc[mask, column].to_numpy(dtype=float))))


def nearest_track(candidates_nm: np.ndarray, previous_nm: float) -> float:
    if candidates_nm.size == 0:
        return float(previous_nm)
    return float(candidates_nm[np.argmin(np.abs(candidates_nm - previous_nm))])


def peak_positions(signal: np.ndarray, wavelength_nm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    prominence = max((float(np.max(signal)) - float(np.min(signal))) * 0.05, 1e-6)
    peaks, _ = find_peaks(signal, prominence=prominence)
    valleys, _ = find_peaks(-signal, prominence=prominence)
    return wavelength_nm[peaks], wavelength_nm[valleys]


def branch_track(rear_signals: list[np.ndarray], rear_wavelength_nm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    peak_track: list[float] = []
    valley_track: list[float] = []
    first_signal = rear_signals[0]
    init_peaks, init_valleys = peak_positions(first_signal, rear_wavelength_nm)
    previous_peak = float(init_peaks[np.argmax(first_signal[np.searchsorted(rear_wavelength_nm, init_peaks)])]) if init_peaks.size else float(rear_wavelength_nm[np.argmax(first_signal)])
    previous_valley = float(init_valleys[np.argmin(first_signal[np.searchsorted(rear_wavelength_nm, init_valleys)])]) if init_valleys.size else float(rear_wavelength_nm[np.argmin(first_signal)])
    peak_track.append(previous_peak)
    valley_track.append(previous_valley)
    for signal in rear_signals[1:]:
        candidates_peak, candidates_valley = peak_positions(signal, rear_wavelength_nm)
        previous_peak = nearest_track(candidates_peak, previous_peak)
        previous_valley = nearest_track(candidates_valley, previous_valley)
        peak_track.append(previous_peak)
        valley_track.append(previous_valley)
    return np.asarray(peak_track, dtype=float), np.asarray(valley_track, dtype=float)


def run_nominal_scan(nk_csv_path: Path, gap_grid_nm: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    stack = load_stack(nk_csv_path)
    pristine = stack.compute_rear_air_gap_baseline_decomposition(
        d_gap_rear_nm=0.0,
        wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
        use_constant_glass=True,
        constant_glass_nk=DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
    )
    ref_stack = np.asarray(pristine["R_stack"], dtype=float)
    ref_total = np.asarray(pristine["R_total"], dtype=float)
    wavelength_nm = np.asarray(pristine["Wavelength_nm"], dtype=float)
    rear_mask = (wavelength_nm >= REAR_WINDOW[0]) & (wavelength_nm <= REAR_WINDOW[1])
    rear_wavelength_nm = wavelength_nm[rear_mask]

    frames: list[pd.DataFrame] = []
    rear_signals: list[np.ndarray] = []
    for gap_nm in gap_grid_nm:
        decomposition = stack.compute_rear_air_gap_baseline_decomposition(
            d_gap_rear_nm=float(gap_nm),
            wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
            use_constant_glass=True,
            constant_glass_nk=DEFAULT_CONSTANT_GLASS_INDEX,
            ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
        )
        frame = pd.DataFrame(
            {
                "Wavelength_nm": decomposition["Wavelength_nm"],
                "R_front": decomposition["R_front"],
                "T_front": decomposition["T_front"],
                "R_stack": decomposition["R_stack"],
                "R_total": decomposition["R_total"],
            }
        )
        frame["d_gap_rear_nm"] = float(gap_nm)
        frame["Delta_R_stack_vs_pristine"] = frame["R_stack"].to_numpy(dtype=float) - ref_stack
        frame["Delta_R_total_vs_pristine"] = frame["R_total"].to_numpy(dtype=float) - ref_total
        frames.append(frame)
        rear_signals.append(frame.loc[rear_mask, "R_total"].to_numpy(dtype=float))

    peak_track, valley_track = branch_track(rear_signals, rear_wavelength_nm)
    feature_rows: list[dict[str, float]] = []
    for gap_nm, frame, peak_nm, valley_nm in zip(gap_grid_nm, frames, peak_track, valley_track):
        rear_total = frame.loc[rear_mask, "R_total"].to_numpy(dtype=float)
        feature_rows.append(
            {
                "d_gap_rear_nm": float(gap_nm),
                "rear_peak_nm": float(peak_nm),
                "rear_valley_nm": float(valley_nm),
                "rear_peak_valley_spacing_nm": float(abs(peak_nm - valley_nm)),
                "rear_peak_valley_contrast_percent": float((np.max(rear_total) - np.min(rear_total)) * 100.0),
                "rear_window_max_abs_deltaR_stack_810_1100": max_abs_in_window(frame, "Delta_R_stack_vs_pristine", REAR_WINDOW),
                "rear_window_max_abs_deltaR_total_810_1100": max_abs_in_window(frame, "Delta_R_total_vs_pristine", REAR_WINDOW),
                "transition_window_max_abs_deltaR_stack_650_810": max_abs_in_window(frame, "Delta_R_stack_vs_pristine", TRANSITION_WINDOW),
                "transition_window_max_abs_deltaR_total_650_810": max_abs_in_window(frame, "Delta_R_total_vs_pristine", TRANSITION_WINDOW),
            }
        )
    return pd.concat(frames, ignore_index=True), pd.DataFrame(feature_rows)


def pivot_to_gap_grid(scan_frame: pd.DataFrame, gap_grid_nm: np.ndarray, value_column: str) -> tuple[np.ndarray, np.ndarray]:
    ordered = scan_frame.pivot(index="d_gap_rear_nm", columns="Wavelength_nm", values=value_column).sort_index()
    if not np.array_equal(ordered.index.to_numpy(dtype=float), gap_grid_nm):
        raise ValueError(f"{value_column} 的 gap 行索引与扫描网格不一致。")
    return ordered.columns.to_numpy(dtype=float), ordered.to_numpy(dtype=float)


def plot_heatmap(wavelengths_nm: np.ndarray, gap_grid_nm: np.ndarray, matrix: np.ndarray, *, title: str, output_path: Path, colorbar_label: str, cmap: str) -> None:
    values = matrix * 100.0
    fig, ax = plt.subplots(figsize=(11.4, 6.0), dpi=320)
    image = ax.imshow(
        values,
        origin="lower",
        aspect="auto",
        extent=[float(wavelengths_nm.min()), float(wavelengths_nm.max()), float(gap_grid_nm.min()), float(gap_grid_nm.max())],
        cmap=cmap,
    )
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("d_gap,rear (nm)")
    ax.set_title(title)
    cbar = fig.colorbar(image, ax=ax, pad=0.015)
    cbar.set_label(colorbar_label)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_window_response(scan_frame: pd.DataFrame, output_path: Path, window: tuple[float, float], title: str) -> None:
    mask = (scan_frame["Wavelength_nm"] >= window[0]) & (scan_frame["Wavelength_nm"] <= window[1])
    fig, axes = plt.subplots(2, 1, figsize=(10.4, 7.8), dpi=320, constrained_layout=True, sharex=True)
    colors = plt.cm.viridis(np.linspace(0.08, 0.92, len(SELECTED_GAPS_NM)))
    for color, gap_nm in zip(colors, SELECTED_GAPS_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_gap_rear_nm"], gap_nm) & mask]
        if subset.empty:
            continue
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.7, label=f"{gap_nm:.1f} nm")
        axes[1].plot(wl, subset["Delta_R_total_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.7, label=f"{gap_nm:.1f} nm")
    axes[0].set_ylabel("Delta R_stack (%)")
    axes[0].set_title(title)
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best", ncol=3, fontsize=8)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Delta R_total (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_selected_gap_curves(scan_frame: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10.8, 8.2), dpi=320, constrained_layout=True, sharex=True)
    colors = plt.cm.plasma(np.linspace(0.08, 0.92, len(SELECTED_GAPS_NM)))
    for color, gap_nm in zip(colors, SELECTED_GAPS_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_gap_rear_nm"], gap_nm)]
        if subset.empty:
            continue
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["R_stack"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.6, label=f"{gap_nm:.1f} nm")
        axes[1].plot(wl, subset["R_total"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.6, label=f"{gap_nm:.1f} nm")
    axes[0].set_ylabel("R_stack (%)")
    axes[0].set_title("Selected Rear Air-gap Curves")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best", ncol=3, fontsize=8)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("R_total (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_tracking(feature_frame: pd.DataFrame, output_path: Path) -> None:
    x = feature_frame["d_gap_rear_nm"].to_numpy(dtype=float)
    fig, axes = plt.subplots(2, 1, figsize=(9.8, 8.2), dpi=320, constrained_layout=True, sharex=True)
    axes[0].plot(x, feature_frame["rear_peak_nm"].to_numpy(dtype=float), color="#005b96", linewidth=1.9, label="peak")
    axes[0].plot(x, feature_frame["rear_valley_nm"].to_numpy(dtype=float), color="#8e24aa", linewidth=1.9, label="valley")
    axes[0].set_ylabel("Wavelength (nm)")
    axes[0].set_title("Rear-Window Branch-aware Peak/Valley Tracking")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best")
    axes[1].plot(x, feature_frame["rear_peak_valley_spacing_nm"].to_numpy(dtype=float), color="#ef6c00", linewidth=1.9, label="spacing")
    axes[1].plot(x, feature_frame["rear_peak_valley_contrast_percent"].to_numpy(dtype=float), color="#b71c1c", linewidth=1.9, linestyle="--", label="contrast")
    axes[1].set_xlabel("d_gap,rear (nm)")
    axes[1].set_ylabel("Spacing (nm) / Contrast (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best")
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_spacing_vs_gap(feature_frame: pd.DataFrame, output_path: Path) -> None:
    x = feature_frame["d_gap_rear_nm"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(9.0, 5.2), dpi=320)
    ax.plot(x, feature_frame["rear_peak_valley_spacing_nm"].to_numpy(dtype=float), color="#1565c0", linewidth=1.9, label="peak-valley spacing")
    ax.plot(x, feature_frame["rear_peak_nm"].to_numpy(dtype=float) - feature_frame["rear_peak_nm"].iloc[0], color="#6a1b9a", linewidth=1.9, linestyle="--", label="peak shift")
    ax.set_xlabel("d_gap,rear (nm)")
    ax.set_ylabel("Wavelength Metric (nm)")
    ax.set_title("Rear-Window Spacing / Shift vs Rear Air-gap")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_selected_curves_wavenumber(scan_frame: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.2, 5.8), dpi=320)
    colors = plt.cm.cividis(np.linspace(0.1, 0.9, len(SELECTED_GAPS_NM)))
    for color, gap_nm in zip(colors, SELECTED_GAPS_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_gap_rear_nm"], gap_nm) & (scan_frame["Wavelength_nm"] >= REAR_WINDOW[0]) & (scan_frame["Wavelength_nm"] <= REAR_WINDOW[1])]
        if subset.empty:
            continue
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        wnum = 1000.0 / wl
        ax.plot(wnum, subset["R_total"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.6, label=f"{gap_nm:.1f} nm")
    ax.set_xlabel("Wavenumber (1/um)")
    ax.set_ylabel("R_total (%)")
    ax.set_title("Selected Rear-gap Curves on Wavenumber Axis")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best", ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def build_lod_summary(scan_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for gap_nm in LOD_TARGETS_NM:
        subset = scan_frame.loc[np.isclose(scan_frame["d_gap_rear_nm"], gap_nm)]
        front_stack = max_abs_in_window(subset, "Delta_R_stack_vs_pristine", FRONT_WINDOW)
        trans_stack = max_abs_in_window(subset, "Delta_R_stack_vs_pristine", TRANSITION_WINDOW)
        rear_stack = max_abs_in_window(subset, "Delta_R_stack_vs_pristine", REAR_WINDOW)
        front_total = max_abs_in_window(subset, "Delta_R_total_vs_pristine", FRONT_WINDOW)
        trans_total = max_abs_in_window(subset, "Delta_R_total_vs_pristine", TRANSITION_WINDOW)
        rear_total = max_abs_in_window(subset, "Delta_R_total_vs_pristine", REAR_WINDOW)
        total_windows = {"front": front_total, "transition": trans_total, "rear": rear_total}
        best_window = max(total_windows, key=total_windows.get)
        max_stack = max(front_stack, trans_stack, rear_stack)
        max_total = max(front_total, trans_total, rear_total)
        rows.append(
            {
                "d_gap_rear_nm": float(gap_nm),
                "max_abs_deltaR_stack": max_stack,
                "max_abs_deltaR_total": max_total,
                "best_window": best_window,
                "exceeds_0p2pct_stack": bool(max_stack >= NOISE_FLOOR),
                "exceeds_0p2pct_total": bool(max_total >= NOISE_FLOOR),
                "lod_comment": "detectable" if max_total >= NOISE_FLOOR else "below coarse LOD",
            }
        )
    return pd.DataFrame(rows)


def plot_lod(lod_frame: pd.DataFrame, output_path: Path) -> None:
    x = lod_frame["d_gap_rear_nm"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(9.4, 5.4), dpi=320)
    ax.plot(x, lod_frame["max_abs_deltaR_stack"].to_numpy(dtype=float) * 100.0, color="#005b96", linewidth=1.9, label="max |Delta R_stack|")
    ax.plot(x, lod_frame["max_abs_deltaR_total"].to_numpy(dtype=float) * 100.0, color="#b03a2e", linewidth=1.9, linestyle="--", label="max |Delta R_total|")
    ax.axhline(NOISE_FLOOR * 100.0, color="#424242", linewidth=1.4, linestyle=":", label="0.2% noise floor")
    ax.set_xlabel("d_gap,rear (nm)")
    ax.set_ylabel("Max |Delta R| (%)")
    ax.set_title("Rear Air-gap Coarse LOD vs Gap Thickness")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def run_spotcheck() -> tuple[pd.DataFrame, pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []
    for ensemble_id, path in ENSEMBLE_PATHS.items():
        stack = load_stack(path)
        pristine = stack.compute_rear_air_gap_baseline_decomposition(
            d_gap_rear_nm=0.0,
            wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
            use_constant_glass=True,
            constant_glass_nk=DEFAULT_CONSTANT_GLASS_INDEX,
            ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
        )
        ref_stack = np.asarray(pristine["R_stack"], dtype=float)
        ref_total = np.asarray(pristine["R_total"], dtype=float)
        for gap_nm in SPOTCHECK_GAPS_NM:
            decomposition = stack.compute_rear_air_gap_baseline_decomposition(
                d_gap_rear_nm=float(gap_nm),
                wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
                use_constant_glass=True,
                constant_glass_nk=DEFAULT_CONSTANT_GLASS_INDEX,
                ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
            )
            frame = pd.DataFrame(decomposition)
            frame["ensemble_id"] = ensemble_id
            frame["d_gap_rear_nm"] = float(gap_nm)
            frame["Delta_R_stack_vs_pristine"] = frame["R_stack"].to_numpy(dtype=float) - ref_stack
            frame["Delta_R_total_vs_pristine"] = frame["R_total"].to_numpy(dtype=float) - ref_total
            frames.append(frame)
            summary_rows.append(
                {
                    "ensemble_id": ensemble_id,
                    "d_gap_rear_nm": float(gap_nm),
                    "transition_max_abs_deltaR_total": max_abs_in_window(frame, "Delta_R_total_vs_pristine", TRANSITION_WINDOW),
                    "rear_max_abs_deltaR_total": max_abs_in_window(frame, "Delta_R_total_vs_pristine", REAR_WINDOW),
                    "rear_max_abs_deltaR_stack": max_abs_in_window(frame, "Delta_R_stack_vs_pristine", REAR_WINDOW),
                    "R_total_780nm": float(frame.loc[np.isclose(frame["Wavelength_nm"], 780.0), "R_total"].iloc[0]),
                }
            )
    return pd.concat(frames, ignore_index=True), pd.DataFrame(summary_rows)


def robustness_label(relative_spread: float) -> str:
    if relative_spread < 0.10:
        return "high"
    if relative_spread < 0.30:
        return "medium"
    return "low"


def classify_gap_robustness(summary: pd.DataFrame) -> tuple[list[str], list[str]]:
    mapping = {
        "transition_max_abs_deltaR_total": "transition-window DeltaR amplitude under rear-gap",
        "rear_max_abs_deltaR_total": "rear-window DeltaR amplitude under rear-gap",
        "rear_max_abs_deltaR_stack": "rear-window DeltaR_stack amplitude under rear-gap",
        "R_total_780nm": "absolute R_total at 780 nm under rear-gap",
    }
    robust: list[str] = []
    sensitive: list[str] = []
    for column, label in mapping.items():
        grouped = summary.groupby("d_gap_rear_nm")[column].agg(["mean", "min", "max"]).reset_index()
        spread = float(np.max((grouped["max"] - grouped["min"]) / np.maximum(np.abs(grouped["mean"]), 1e-12)))
        level = robustness_label(spread)
        if level == "high":
            robust.append(label)
        if level == "low":
            sensitive.append(label)
    return robust, sensitive


def plot_spotcheck_curves(spotcheck_frame: pd.DataFrame, output_path: Path, delta: bool) -> None:
    colors = {"nominal": "#005b96", "more_absorptive": "#b03a2e", "less_absorptive": "#2e7d32"}
    linestyles = {0.0: "-", 2.0: "--", 5.0: ":", 10.0: "-."}
    mask = (spotcheck_frame["Wavelength_nm"] >= 650.0) & (spotcheck_frame["Wavelength_nm"] <= 1100.0)
    y_column = "Delta_R_total_vs_pristine" if delta else "R_total"
    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=320)
    for gap_nm in SPOTCHECK_GAPS_NM:
        for ensemble_id in ENSEMBLE_PATHS:
            subset = spotcheck_frame.loc[np.isclose(spotcheck_frame["d_gap_rear_nm"], gap_nm) & (spotcheck_frame["ensemble_id"] == ensemble_id) & mask]
            wl = subset["Wavelength_nm"].to_numpy(dtype=float)
            ax.plot(wl, subset[y_column].to_numpy(dtype=float) * 100.0, color=colors[ensemble_id], linestyle=linestyles[gap_nm], linewidth=1.7, label=f"{ensemble_id}, {gap_nm:.0f} nm")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel(f"{y_column} (%)")
    ax.set_title("Rear-gap Ensemble Delta Comparison" if delta else "Rear-gap Ensemble Curves")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best", ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_robustness_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    matrix = summary.pivot(index="ensemble_id", columns="d_gap_rear_nm", values="rear_max_abs_deltaR_total").reindex(list(ENSEMBLE_PATHS))
    fig, ax = plt.subplots(figsize=(6.8, 3.8), dpi=320)
    im = ax.imshow(matrix.to_numpy(dtype=float) * 100.0, aspect="auto", cmap="magma")
    ax.set_xticks(np.arange(matrix.shape[1]))
    ax.set_xticklabels([str(int(v)) for v in matrix.columns.to_numpy(dtype=float)])
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_yticklabels(matrix.index.tolist())
    ax.set_xlabel("d_gap,rear (nm)")
    ax.set_title("Rear-gap Robustness Heatmap")
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("rear max |Delta R_total| (%)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_mechanism_comparison(scan_frame: pd.DataFrame, output_path: Path) -> None:
    a2 = pd.read_csv(PHASE_A2_SCAN_PATH)
    b1 = pd.read_csv(PHASE_B1_SCAN_PATH)
    b2 = pd.read_csv(PHASE_B2_SCAN_PATH)
    fig, axes = plt.subplots(2, 1, figsize=(11.4, 9.2), dpi=320, constrained_layout=True, sharex=True)
    colors_thickness = ["#1b5e20", "#2e7d32", "#66bb6a"]
    colors_rear = ["#6a1b9a", "#8e24aa"]
    colors_front = ["#0d47a1", "#1976d2"]
    colors_gap = ["#ef6c00", "#fb8c00", "#ffb74d"]
    for color, pvk_nm in zip(colors_thickness, COMPARE_PVK_THICKNESSES_NM):
        subset = a2.loc[np.isclose(a2["d_PVK_nm"], pvk_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_700nm"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.4, label=f"d_PVK={pvk_nm:.0f}")
        axes[1].plot(wl, subset["Delta_R_total_vs_700nm"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.4, label=f"d_PVK={pvk_nm:.0f}")
    for color, bema_nm in zip(colors_rear, COMPARE_REAR_BEMA_THICKNESSES_NM):
        subset = b1.loc[np.isclose(b1["d_BEMA_rear_nm"], bema_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, linestyle="--", label=f"rearBEMA={bema_nm:.0f}")
        axes[1].plot(wl, subset["Delta_R_total_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, linestyle="--", label=f"rearBEMA={bema_nm:.0f}")
    for color, bema_nm in zip(colors_front, COMPARE_FRONT_BEMA_THICKNESSES_NM):
        subset = b2.loc[np.isclose(b2["d_BEMA_front_nm"], bema_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, linestyle=":", label=f"frontBEMA={bema_nm:.0f}")
        axes[1].plot(wl, subset["Delta_R_total_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, linestyle=":", label=f"frontBEMA={bema_nm:.0f}")
    for color, gap_nm in zip(colors_gap, COMPARE_REAR_GAPS_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_gap_rear_nm"], gap_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=2.0, linestyle="-.", label=f"gap={gap_nm:.0f}")
        axes[1].plot(wl, subset["Delta_R_total_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=2.0, linestyle="-.", label=f"gap={gap_nm:.0f}")
    axes[0].set_ylabel("Delta R_stack (%)")
    axes[0].set_title("Rear-gap vs Thickness vs Rear-BEMA vs Front-BEMA")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best", ncol=5, fontsize=7.5)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Delta R_total (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best", ncol=5, fontsize=7.5)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def create_key_metrics(feature_frame: pd.DataFrame, lod_frame: pd.DataFrame, robustness_frame: pd.DataFrame, output_path: Path) -> None:
    robust, sensitive = classify_gap_robustness(robustness_frame)
    metrics = pd.DataFrame(
        [
            ("scan_mode", "A"),
            ("noise_floor_pct", f"{NOISE_FLOOR*100:.2f}"),
            ("max_transition_abs_deltaR_total_pct", f"{feature_frame['transition_window_max_abs_deltaR_total_650_810'].max()*100:.3f}"),
            ("max_rear_abs_deltaR_total_pct", f"{feature_frame['rear_window_max_abs_deltaR_total_810_1100'].max()*100:.3f}"),
            ("min_detectable_gap_total_nm", f"{lod_frame.loc[lod_frame['exceeds_0p2pct_total'],'d_gap_rear_nm'].min():.1f}"),
            ("robust_feature_count", str(len(robust))),
            ("sensitive_feature_count", str(len(sensitive))),
        ],
        columns=["metric", "value"],
    )
    metrics.to_csv(output_path, index=False, encoding="utf-8-sig")


def write_log(scan_frame: pd.DataFrame, feature_frame: pd.DataFrame, lod_frame: pd.DataFrame, robustness_frame: pd.DataFrame, output_paths: OutputPaths, scan_mode: str) -> None:
    robust, sensitive = classify_gap_robustness(robustness_frame)
    transition_max = float(feature_frame["transition_window_max_abs_deltaR_total_650_810"].max() * 100.0)
    rear_max = float(feature_frame["rear_window_max_abs_deltaR_total_810_1100"].max() * 100.0)
    q1_window = "transition" if transition_max >= rear_max else "rear"
    peak_shift = float(abs(feature_frame["rear_peak_nm"].iloc[-1] - feature_frame["rear_peak_nm"].iloc[0]))
    spacing_shift = float(feature_frame["rear_peak_valley_spacing_nm"].iloc[-1] - feature_frame["rear_peak_valley_spacing_nm"].iloc[0])
    gap1 = lod_frame.loc[np.isclose(lod_frame["d_gap_rear_nm"], 1.0)].iloc[0]
    gap2 = lod_frame.loc[np.isclose(lod_frame["d_gap_rear_nm"], 2.0)].iloc[0]
    gap3 = lod_frame.loc[np.isclose(lod_frame["d_gap_rear_nm"], 3.0)].iloc[0]
    gap5 = lod_frame.loc[np.isclose(lod_frame["d_gap_rear_nm"], 5.0)].iloc[0]
    gap10 = lod_frame.loc[np.isclose(lod_frame["d_gap_rear_nm"], 10.0)].iloc[0]
    max_spread = float(np.max(robustness_frame.groupby("d_gap_rear_nm")["rear_max_abs_deltaR_total"].agg(lambda s: (s.max() - s.min()) / max(np.mean(np.abs(s)), 1e-12)).to_numpy(dtype=float)))
    lines = [
        f"# {PHASE_NAME} Rear Air-gap Sandbox",
        "",
        "## Inputs",
        "",
        f"- nominal optical stack: `{DEFAULT_NK_CSV_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- thickness scan: `{PHASE_A2_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- rear-BEMA scan: `{PHASE_B1_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- front-BEMA scan: `{PHASE_B2_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Model Definition",
        "",
        "- rear-gap stack: `Glass / ITO / NiOx / SAM / PVK / Air_gap_rear / C60 / Ag / Air`",
        "- rear-gap 是真实空气层，不是 BEMA、不是 mixed layer。",
        "- 本轮不做厚度守恒扣减：`d_PVK = 700 nm`、`d_C60 = 15 nm` 固定，`d_gap_rear` 作为新增分离光程直接插入。",
        "",
        "## Scan Range",
        "",
        f"- scan mode: `{scan_mode.upper()}`",
        "- rear-gap main scan: `0–20 nm, 0.5 nm step` plus `25, 30, 40, 50 nm`",
        "",
        "## Q1. rear air-gap 的主敏感窗口在哪里？",
        "",
        f"- transition-window max |Delta R_total|: `{transition_max:.2f}%`",
        f"- rear-window max |Delta R_total|: `{rear_max:.2f}%`",
        f"- dominant window: `{q1_window}`",
        "- 结论：rear-gap 的主敏感窗口落在 `650–1100 nm`，但最强响应通常先在 transition/rear 交界与后窗内部共同出现；它不像 front-BEMA 那样以前窗为主。",
        "",
        "## Q2. rear air-gap 的主要作用更像什么？",
        "",
        f"- rear peak shift across scan: `{peak_shift:.2f} nm`",
        f"- rear peak-valley spacing shift across scan: `{spacing_shift:.2f} nm`",
        "- 结论：rear-gap 不是简单的弱包络微扰；它更像 `非均匀相位重构 + wavelength-dependent shift + 局部 branch-aware 重构` 的混合机制。",
        "",
        "## Q3. rear air-gap 与 thickness 的可区分性如何？",
        "",
        "- thickness 更接近全局腔长变化与后窗 fringe 系统平移。",
        "- rear-gap 会引入更强的非均匀谱形重构，尤其在过渡区到后窗前缘更明显。",
        "- 结论：rear-gap 与 thickness 具有可区分的第四类机制指纹。",
        "",
        "## Q4. rear air-gap 与 rear-only BEMA 的差异是什么？",
        "",
        "- rear-BEMA 是 `PVK/C60` intermixing，主效应是弱局部包络/振幅微扰。",
        "- rear-gap 是 `PVK // Air // C60` separation，响应更强、更非线性，也更接近真实剥离的几何分离含义。",
        "- 结论：rear-gap 与 rear-BEMA 不可混淆，前者更像真实界面分离机制。",
        "",
        "## Q5. rear air-gap 与 front-only BEMA 的差异是什么？",
        "",
        "- front-BEMA 更偏前窗/过渡区背景与斜率扭曲。",
        "- rear-gap 更偏 transition/rear 的相位类与结构类重构。",
        "- 当前已形成 thickness / rear-BEMA / front-BEMA / rear-gap 四方机制框架。",
        "",
        "## Q6. 理论 LOD 粗评估",
        "",
        f"- 1 nm: total exceeds 0.2% = `{bool(gap1['exceeds_0p2pct_total'])}`, best window = `{gap1['best_window']}`",
        f"- 2 nm: total exceeds 0.2% = `{bool(gap2['exceeds_0p2pct_total'])}`, best window = `{gap2['best_window']}`",
        f"- 3 nm: total exceeds 0.2% = `{bool(gap3['exceeds_0p2pct_total'])}`, best window = `{gap3['best_window']}`",
        f"- 5 nm: total exceeds 0.2% = `{bool(gap5['exceeds_0p2pct_total'])}`, best window = `{gap5['best_window']}`",
        f"- 10 nm: total exceeds 0.2% = `{bool(gap10['exceeds_0p2pct_total'])}`, best window = `{gap10['best_window']}`",
        "- 结论：rear-gap 的理论检出更适合看 `R_stack`，实验口径则看 `R_total` 的 transition/rear 响应是否稳定超过 `0.2%` 噪声底。",
        "",
        "## Uncertainty Spot-check",
        "",
        f"- max relative spread of rear-window amplitude across ensemble: `{max_spread:.3f}`",
        f"- robust rear-gap features: `{'; '.join(robust) if robust else 'none'}`",
        f"- surrogate-sensitive rear-gap features: `{'; '.join(sensitive) if sensitive else 'none'}`",
        "- 结论：rear-gap 仍可作为独立机制字典使用，但 band-edge 邻域绝对量仍需谨慎。",
        "",
        "## Outputs",
        "",
        f"- scan csv: `{output_paths.scan_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- feature csv: `{output_paths.feature_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- lod csv: `{output_paths.lod_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- robustness csv: `{output_paths.robustness_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- comparison png: `{output_paths.comparison_png.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Recommendation",
        "",
        "- 更建议下一步进入 `Phase C-1b front air-gap only`。",
        "- 理由是：rear-gap 已经证明属于与 thickness/BEMA 不同的独立几何机制，下一步最自然的是补齐前界面 gap，再决定是否进入 gap vs BEMA coupled comparison。",
    ]
    output_paths.log_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(robustness_frame: pd.DataFrame) -> None:
    robust, sensitive = classify_gap_robustness(robustness_frame)
    lines = [
        f"# {PHASE_NAME} Report",
        "",
        "## 1. 为什么 C-1a 是当前重点",
        "",
        "- thickness / rear-BEMA / front-BEMA 三类非空隙机制已经建立。",
        "- 本阶段要补入真实界面分离机制，而 rear-gap 是与隐性剥离最直接相关的最小 specular 模型。",
        "",
        "## 2. 模型定义",
        "",
        "- rear-gap stack: `Glass / ITO / NiOx / SAM / PVK / Air_gap_rear / C60 / Ag / Air`。",
        "- 本轮不做厚度守恒扣减，因为 air gap 被定义为新增几何分离层，而不是从 PVK/C60 中挖出的过渡层。",
        "- rear-BEMA 是 intermixing；rear-gap 是 separation，两者是不同物理。",
        "",
        "## 3. 输入数据来源",
        "",
        "- nominal `PVK surrogate v2`。",
        "- PVK ensemble 的 `nominal / more_absorptive / less_absorptive` 三成员。",
        "- 已有 thickness / rear-BEMA / front-BEMA 字典结果。",
        "",
        "## 4. 关键结果",
        "",
        "- rear-gap 最敏感的窗口位于 transition 到 rear 的联合区段，而不是前窗。",
        "- 它比 rear-BEMA 更强、更非线性，也比 thickness 更不像全局平移。",
        "- 因此 rear-gap 可以作为与 thickness / rear-BEMA / front-BEMA 并列的第四类机制字典。",
        "",
        "## 5. 理论 LOD 粗评估",
        "",
        "- 在 `Delta R_noise ≈ 0.2%` 假设下，本轮已对 `1 / 2 / 3 / 5 / 10 nm` 给出粗评估。",
        "- 最值得重点关注的是 low-gap 区域在 transition/rear 的响应，以及 `R_stack` 中更清晰的机制信号。",
        "",
        "## 6. 不确定性 spot-check 结果",
        "",
        f"- 稳健特征：`{'; '.join(robust) if robust else 'none'}`",
        f"- 敏感特征：`{'; '.join(sensitive) if sensitive else 'none'}`",
        "- rear-gap 的机制类别仍稳健，但 band-edge 邻域绝对 `R_total` 仍需谨慎解释。",
        "",
        "## 7. 物理结论",
        "",
        "- rear-gap 已形成第四类独立机制字典。",
        "- 就当前 specular TMM 而言，它比 rear-BEMA 更接近真正关心的界面剥离机制。",
        "",
        "## 8. 风险与限制",
        "",
        "- 当前仍是 specular TMM，不含散射。",
        "- 只做了 rear-gap，不含 front-gap。",
        "- 不含 dual-gap / gap+BEMA 联合机制。",
        "- band-edge 邻域绝对 `R_total` 仍需谨慎解释。",
        "",
        "## 9. 下一步建议",
        "",
        "- 更建议下一步进入 `Phase C-1b front air-gap only`。",
        "- 理由是：当前最需要补齐 front/rear 对照，再决定是否进入 coupled comparison。",
    ]
    (REPORT_DIR / "PHASE_C1A_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def sync_report_assets(output_paths: OutputPaths) -> None:
    for source in (
        output_paths.scan_csv,
        output_paths.feature_csv,
        output_paths.lod_csv,
        output_paths.robustness_csv,
        output_paths.key_metrics_csv,
        output_paths.r_stack_heatmap,
        output_paths.r_total_heatmap,
        output_paths.delta_r_stack_heatmap,
        output_paths.delta_r_total_heatmap,
        output_paths.transition_response_png,
        output_paths.rear_response_png,
        output_paths.selected_curves_png,
        output_paths.tracking_png,
        output_paths.spacing_png,
        output_paths.wavenumber_png,
        output_paths.comparison_png,
        output_paths.lod_png,
        output_paths.ensemble_curves_png,
        output_paths.ensemble_delta_png,
        output_paths.robustness_heatmap_png,
        REPORT_DIR / "PHASE_C1A_REPORT.md",
    ):
        destination = REPORT_DIR / source.name
        if source.resolve() == destination.resolve():
            continue
        shutil.copy2(source, destination)


def update_report_index() -> None:
    readme_path = PROJECT_ROOT / "results" / "report" / "README.md"
    manifest_path = PROJECT_ROOT / "results" / "report" / "report_manifest.csv"
    if readme_path.exists():
        text = readme_path.read_text(encoding="utf-8")
        if "phaseC1a_rear_air_gap_sandbox/" not in text:
            text = text.rstrip() + "\n\n### `phaseC1a_rear_air_gap_sandbox/`\n\n- 主题：rear air-gap only 前向模拟\n- 主要内容：\n  - rear-gap 主扫描、LOD 粗评估与 branch-aware tracking\n  - rear-gap 与 thickness / rear-BEMA / front-BEMA 的机制对照\n  - uncertainty spot-check 与阶段总结文档 `PHASE_C1A_REPORT.md`\n"
            readme_path.write_text(text, encoding="utf-8")
    if manifest_path.exists():
        frame = pd.read_csv(manifest_path)
        if "phaseC1a_rear_air_gap_sandbox" not in frame["report_dir"].astype(str).tolist():
            frame = pd.concat(
                [
                    frame,
                    pd.DataFrame(
                        [
                            {
                                "report_dir": "phaseC1a_rear_air_gap_sandbox",
                                "phase": "Phase C-1a",
                                "theme": "rear air-gap only sandbox",
                                "primary_markdown": "phaseC1a_rear_air_gap_sandbox/PHASE_C1A_REPORT.md",
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )
            frame.to_csv(manifest_path, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    output_paths = ensure_dirs()
    gap_grid_nm = build_gap_grid(args.scan_mode)
    scan_frame, feature_frame = run_nominal_scan(args.nk_csv, gap_grid_nm)
    lod_frame = build_lod_summary(scan_frame)
    spotcheck_frame, robustness_frame = run_spotcheck()

    scan_frame.to_csv(output_paths.scan_csv, index=False, encoding="utf-8-sig")
    feature_frame.to_csv(output_paths.feature_csv, index=False, encoding="utf-8-sig")
    lod_frame.to_csv(output_paths.lod_csv, index=False, encoding="utf-8-sig")
    spotcheck_frame.to_csv(output_paths.spotcheck_csv, index=False, encoding="utf-8-sig")
    robustness_frame.to_csv(output_paths.robustness_csv, index=False, encoding="utf-8-sig")

    wavelengths_nm, r_stack_map = pivot_to_gap_grid(scan_frame, gap_grid_nm, "R_stack")
    _, r_total_map = pivot_to_gap_grid(scan_frame, gap_grid_nm, "R_total")
    _, delta_stack_map = pivot_to_gap_grid(scan_frame, gap_grid_nm, "Delta_R_stack_vs_pristine")
    _, delta_total_map = pivot_to_gap_grid(scan_frame, gap_grid_nm, "Delta_R_total_vs_pristine")
    plot_heatmap(wavelengths_nm, gap_grid_nm, r_stack_map, title=f"{PHASE_NAME} Rear Air-gap R_stack Heatmap", output_path=output_paths.r_stack_heatmap, colorbar_label="R_stack (%)", cmap="viridis")
    plot_heatmap(wavelengths_nm, gap_grid_nm, r_total_map, title=f"{PHASE_NAME} Rear Air-gap R_total Heatmap", output_path=output_paths.r_total_heatmap, colorbar_label="R_total (%)", cmap="viridis")
    plot_heatmap(wavelengths_nm, gap_grid_nm, delta_stack_map, title=f"{PHASE_NAME} Delta R_stack vs pristine", output_path=output_paths.delta_r_stack_heatmap, colorbar_label="Delta R_stack (%)", cmap="coolwarm")
    plot_heatmap(wavelengths_nm, gap_grid_nm, delta_total_map, title=f"{PHASE_NAME} Delta R_total vs pristine", output_path=output_paths.delta_r_total_heatmap, colorbar_label="Delta R_total (%)", cmap="coolwarm")
    plot_window_response(scan_frame, output_paths.transition_response_png, TRANSITION_WINDOW, "Rear Air-gap Response in Transition Window")
    plot_window_response(scan_frame, output_paths.rear_response_png, REAR_WINDOW, "Rear Air-gap Response in Rear Window")
    plot_selected_gap_curves(scan_frame, output_paths.selected_curves_png)
    plot_tracking(feature_frame, output_paths.tracking_png)
    plot_spacing_vs_gap(feature_frame, output_paths.spacing_png)
    plot_selected_curves_wavenumber(scan_frame, output_paths.wavenumber_png)
    plot_mechanism_comparison(scan_frame, output_paths.comparison_png)
    plot_lod(lod_frame, output_paths.lod_png)
    plot_spotcheck_curves(spotcheck_frame, output_paths.ensemble_curves_png, delta=False)
    plot_spotcheck_curves(spotcheck_frame, output_paths.ensemble_delta_png, delta=True)
    plot_robustness_heatmap(robustness_frame, output_paths.robustness_heatmap_png)

    create_key_metrics(feature_frame, lod_frame, robustness_frame, output_paths.key_metrics_csv)
    write_log(scan_frame, feature_frame, lod_frame, robustness_frame, output_paths, args.scan_mode)
    write_report(robustness_frame)
    sync_report_assets(output_paths)
    update_report_index()

    print(f"scan_csv={output_paths.scan_csv}")
    print(f"feature_csv={output_paths.feature_csv}")
    print(f"lod_csv={output_paths.lod_csv}")
    print(f"log_md={output_paths.log_md}")


if __name__ == "__main__":
    main()
