"""Phase B-2 front-only BEMA sandbox using a NiOx/PVK optical proxy.

This phase introduces only a front-side roughness proxy:

Glass / ITO / NiOx / SAM / BEMA_front(NiOx,PVK) / PVK_bulk / C60 / Ag / Air

with fixed 50/50 Bruggeman solid-solid intermixing, fixed SAM thickness, and
PVK thickness conservation:

    d_PVK,bulk = 700 - d_BEMA,front

No rear-side BEMA, no air gap, and no experimental fitting are involved.
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
    FRONT_BEMA_VOLUME_FRACTION,
)


PHASE_NAME = "Phase B-2"
DEFAULT_NK_CSV_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_pvk_v2.csv"
ENSEMBLE_PATHS = {
    "nominal": PROJECT_ROOT / "resources" / "pvk_ensemble" / "aligned_full_stack_nk_pvk_ens_nominal.csv",
    "more_absorptive": PROJECT_ROOT / "resources" / "pvk_ensemble" / "aligned_full_stack_nk_pvk_ens_more_absorptive.csv",
    "less_absorptive": PROJECT_ROOT / "resources" / "pvk_ensemble" / "aligned_full_stack_nk_pvk_ens_less_absorptive.csv",
}
PHASE_A2_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA2" / "phaseA2_pvk_thickness_scan.csv"
PHASE_B1_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseB1" / "phaseB1_rear_bema_scan.csv"
PHASE_A2_1_FEATURE_MATRIX_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA2_1" / "phaseA2_1_feature_robustness_matrix.csv"
PHASE_A2_1_THICKNESS_ROBUSTNESS_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA2_1" / "phaseA2_1_thickness_robustness_summary.csv"
PHASE_A2_1_REAR_BEMA_ROBUSTNESS_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA2_1" / "phaseA2_1_rear_bema_robustness_summary.csv"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phaseB2"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phaseB2"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phaseB2"
REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phaseB2_front_bema_sandbox"

FRONT_WINDOW = (400.0, 650.0)
TRANSITION_WINDOW = (650.0, 810.0)
REAR_WINDOW = (810.0, 1100.0)
BEMA_START_NM = 0.0
BEMA_STOP_NM = 30.0
BEMA_STEP_NM = 1.0
SELECTED_BEMA_THICKNESSES_NM = (0.0, 5.0, 10.0, 20.0, 30.0)
COMPARE_FRONT_BEMA_THICKNESSES_NM = (10.0, 20.0)
COMPARE_REAR_BEMA_THICKNESSES_NM = (10.0, 20.0)
COMPARE_PVK_THICKNESSES_NM = (650.0, 750.0, 850.0)
SPOTCHECK_BEMA_THICKNESSES_NM = (0.0, 10.0, 20.0)


@dataclass(frozen=True)
class OutputPaths:
    scan_csv: Path
    feature_csv: Path
    spotcheck_csv: Path
    robustness_csv: Path
    key_metrics_csv: Path
    log_md: Path
    r_stack_heatmap: Path
    r_total_heatmap: Path
    delta_r_stack_heatmap: Path
    delta_r_total_heatmap: Path
    front_window_png: Path
    transition_window_png: Path
    selected_curves_png: Path
    tracking_png: Path
    contrast_png: Path
    window_summary_png: Path
    comparison_png: Path
    ensemble_curves_png: Path
    ensemble_delta_png: Path
    robustness_heatmap_png: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase B-2 front-only BEMA sandbox.")
    parser.add_argument("--nk-csv", type=Path, default=DEFAULT_NK_CSV_PATH)
    parser.add_argument("--start-nm", type=float, default=BEMA_START_NM)
    parser.add_argument("--stop-nm", type=float, default=BEMA_STOP_NM)
    parser.add_argument("--step-nm", type=float, default=BEMA_STEP_NM)
    return parser.parse_args()


def ensure_dirs() -> OutputPaths:
    for path in (PROCESSED_DIR, FIGURE_DIR, LOG_DIR, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    return OutputPaths(
        scan_csv=PROCESSED_DIR / "phaseB2_front_bema_scan.csv",
        feature_csv=PROCESSED_DIR / "phaseB2_front_bema_feature_summary.csv",
        spotcheck_csv=PROCESSED_DIR / "phaseB2_front_bema_ensemble_spotcheck.csv",
        robustness_csv=PROCESSED_DIR / "phaseB2_front_bema_robustness_summary.csv",
        key_metrics_csv=REPORT_DIR / "phaseB2_key_metrics.csv",
        log_md=LOG_DIR / "phaseB2_front_bema_sandbox.md",
        r_stack_heatmap=FIGURE_DIR / "phaseB2_R_stack_heatmap.png",
        r_total_heatmap=FIGURE_DIR / "phaseB2_R_total_heatmap.png",
        delta_r_stack_heatmap=FIGURE_DIR / "phaseB2_deltaR_stack_heatmap.png",
        delta_r_total_heatmap=FIGURE_DIR / "phaseB2_deltaR_total_heatmap.png",
        front_window_png=FIGURE_DIR / "phaseB2_front_window_response.png",
        transition_window_png=FIGURE_DIR / "phaseB2_transition_window_response.png",
        selected_curves_png=FIGURE_DIR / "phaseB2_selected_bema_curves.png",
        tracking_png=FIGURE_DIR / "phaseB2_peak_valley_tracking.png",
        contrast_png=FIGURE_DIR / "phaseB2_contrast_vs_bema.png",
        window_summary_png=FIGURE_DIR / "phaseB2_window_sensitivity_summary.png",
        comparison_png=FIGURE_DIR / "phaseB2_front_vs_rear_vs_thickness_comparison.png",
        ensemble_curves_png=FIGURE_DIR / "phaseB2_front_bema_ensemble_curves.png",
        ensemble_delta_png=FIGURE_DIR / "phaseB2_front_bema_ensemble_deltaR_comparison.png",
        robustness_heatmap_png=FIGURE_DIR / "phaseB2_front_bema_robustness_heatmap.png",
    )


def build_bema_grid(start_nm: float, stop_nm: float, step_nm: float) -> np.ndarray:
    if step_nm <= 0.0:
        raise ValueError("d_BEMA,front 步长必须为正数。")
    count = int(round((stop_nm - start_nm) / step_nm))
    grid = start_nm + np.arange(count + 1, dtype=float) * step_nm
    if not np.isclose(grid[-1], stop_nm):
        raise ValueError("front-BEMA 扫描范围和步长不闭合。")
    if not np.any(np.isclose(grid, 0.0)):
        raise ValueError("front-BEMA 扫描必须包含 pristine 参考点 d_BEMA=0 nm。")
    return grid


def load_stack(nk_csv_path: Path):
    stack, _, _ = phase_a1.load_optical_stack_from_aligned_csv(nk_csv_path)
    return stack


def dominant_extrema(signal: np.ndarray, wavelength_nm: np.ndarray) -> tuple[float, float]:
    prominence = max((float(np.max(signal)) - float(np.min(signal))) * 0.08, 1e-6)
    peaks, peak_props = find_peaks(signal, prominence=prominence)
    valleys, valley_props = find_peaks(-signal, prominence=prominence)
    peak_idx = peaks[int(np.argmax(peak_props["prominences"]))] if peaks.size else int(np.argmax(signal))
    valley_idx = valleys[int(np.argmax(valley_props["prominences"]))] if valleys.size else int(np.argmin(signal))
    return float(wavelength_nm[peak_idx]), float(wavelength_nm[valley_idx])


def max_abs_in_window(frame: pd.DataFrame, column: str, window: tuple[float, float]) -> float:
    mask = (frame["Wavelength_nm"] >= window[0]) & (frame["Wavelength_nm"] <= window[1])
    return float(np.max(np.abs(frame.loc[mask, column].to_numpy(dtype=float))))


def mean_in_window(frame: pd.DataFrame, column: str, window: tuple[float, float]) -> float:
    mask = (frame["Wavelength_nm"] >= window[0]) & (frame["Wavelength_nm"] <= window[1])
    return float(np.mean(frame.loc[mask, column].to_numpy(dtype=float)))


def run_nominal_scan(nk_csv_path: Path, bema_grid_nm: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    stack = load_stack(nk_csv_path)
    pristine = stack.compute_front_bema_baseline_decomposition(
        d_bema_front_nm=0.0,
        wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
        use_constant_glass=True,
        constant_glass_nk=DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
    )
    reference_stack = np.asarray(pristine["R_stack"], dtype=float)
    reference_total = np.asarray(pristine["R_total"], dtype=float)
    wavelength_nm = np.asarray(pristine["Wavelength_nm"], dtype=float)
    rear_mask = (wavelength_nm >= REAR_WINDOW[0]) & (wavelength_nm <= REAR_WINDOW[1])
    rear_wavelength_nm = wavelength_nm[rear_mask]

    rows: list[pd.DataFrame] = []
    feature_rows: list[dict[str, float]] = []
    for d_bema_nm in bema_grid_nm:
        decomposition = stack.compute_front_bema_baseline_decomposition(
            d_bema_front_nm=float(d_bema_nm),
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
        frame["d_BEMA_front_nm"] = float(d_bema_nm)
        frame["d_PVK_bulk_nm"] = float(decomposition["d_PVK_bulk_nm"])
        frame["Delta_R_stack_vs_pristine"] = frame["R_stack"].to_numpy(dtype=float) - reference_stack
        frame["Delta_R_total_vs_pristine"] = frame["R_total"].to_numpy(dtype=float) - reference_total
        rows.append(frame)

        rear_total = frame.loc[rear_mask, "R_total"].to_numpy(dtype=float)
        peak_nm, valley_nm = dominant_extrema(rear_total, rear_wavelength_nm)
        feature_rows.append(
            {
                "d_BEMA_front_nm": float(d_bema_nm),
                "d_PVK_bulk_nm": float(decomposition["d_PVK_bulk_nm"]),
                "front_window_mean_deltaR_stack_400_650": mean_in_window(frame, "Delta_R_stack_vs_pristine", FRONT_WINDOW),
                "front_window_mean_deltaR_total_400_650": mean_in_window(frame, "Delta_R_total_vs_pristine", FRONT_WINDOW),
                "transition_window_max_abs_deltaR_stack_650_810": max_abs_in_window(frame, "Delta_R_stack_vs_pristine", TRANSITION_WINDOW),
                "transition_window_max_abs_deltaR_total_650_810": max_abs_in_window(frame, "Delta_R_total_vs_pristine", TRANSITION_WINDOW),
                "rear_window_max_abs_deltaR_stack_810_1100": max_abs_in_window(frame, "Delta_R_stack_vs_pristine", REAR_WINDOW),
                "rear_window_max_abs_deltaR_total_810_1100": max_abs_in_window(frame, "Delta_R_total_vs_pristine", REAR_WINDOW),
                "rear_peak_nm": peak_nm,
                "rear_valley_nm": valley_nm,
                "rear_peak_valley_spacing_nm": float(abs(peak_nm - valley_nm)),
                "rear_peak_valley_contrast_percent": float((np.max(rear_total) - np.min(rear_total)) * 100.0),
            }
        )

    return pd.concat(rows, ignore_index=True), pd.DataFrame(feature_rows)


def pivot_map(scan_frame: pd.DataFrame, value_column: str, bema_grid_nm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ordered = scan_frame.pivot(index="d_BEMA_front_nm", columns="Wavelength_nm", values=value_column).sort_index()
    if not np.array_equal(ordered.index.to_numpy(dtype=float), bema_grid_nm):
        raise ValueError(f"{value_column} 的 front-BEMA 行索引与扫描网格不一致。")
    return ordered.columns.to_numpy(dtype=float), ordered.to_numpy(dtype=float)


def plot_heatmap(
    wavelengths_nm: np.ndarray,
    bema_grid_nm: np.ndarray,
    matrix: np.ndarray,
    *,
    title: str,
    output_path: Path,
    colorbar_label: str,
    cmap: str,
    scale_to_percent: bool = True,
) -> None:
    values = matrix * 100.0 if scale_to_percent else matrix
    fig, ax = plt.subplots(figsize=(11.4, 6.0), dpi=320)
    image = ax.imshow(
        values,
        origin="lower",
        aspect="auto",
        extent=[float(wavelengths_nm.min()), float(wavelengths_nm.max()), float(bema_grid_nm.min()), float(bema_grid_nm.max())],
        cmap=cmap,
    )
    for x0, x1 in (FRONT_WINDOW, TRANSITION_WINDOW, REAR_WINDOW):
        ax.axvspan(x0, x1, color="white", alpha=0.04)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("d_BEMA,front (nm)")
    ax.set_title(title)
    cbar = fig.colorbar(image, ax=ax, pad=0.015)
    cbar.set_label(colorbar_label)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_window_response(scan_frame: pd.DataFrame, output_path: Path, window: tuple[float, float], title: str) -> None:
    mask = (scan_frame["Wavelength_nm"] >= window[0]) & (scan_frame["Wavelength_nm"] <= window[1])
    colors = ["#424242", "#005b96", "#7b1fa2", "#ef6c00", "#b71c1c"]
    fig, axes = plt.subplots(2, 1, figsize=(10.0, 7.8), dpi=320, constrained_layout=True, sharex=True)
    for color, d_bema_nm in zip(colors, SELECTED_BEMA_THICKNESSES_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_BEMA_front_nm"], d_bema_nm) & mask]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, label=f"{d_bema_nm:.0f} nm")
        axes[1].plot(wl, subset["Delta_R_total_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, label=f"{d_bema_nm:.0f} nm")
    axes[0].set_ylabel("Delta R_stack (%)")
    axes[0].set_title(title)
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best", ncol=2)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Delta R_total (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_selected_curves(scan_frame: pd.DataFrame, output_path: Path) -> None:
    colors = ["#424242", "#005b96", "#7b1fa2", "#ef6c00", "#b71c1c"]
    fig, axes = plt.subplots(2, 1, figsize=(10.6, 8.0), dpi=320, constrained_layout=True, sharex=True)
    for color, d_bema_nm in zip(colors, SELECTED_BEMA_THICKNESSES_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_BEMA_front_nm"], d_bema_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["R_stack"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.7, label=f"{d_bema_nm:.0f} nm")
        axes[1].plot(wl, subset["R_total"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.7, label=f"{d_bema_nm:.0f} nm")
    axes[0].set_ylabel("R_stack (%)")
    axes[0].set_title("Selected Front-only BEMA Curves")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best", ncol=2)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("R_total (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_tracking(feature_frame: pd.DataFrame, output_path: Path) -> None:
    x = feature_frame["d_BEMA_front_nm"].to_numpy(dtype=float)
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 8.0), dpi=320, constrained_layout=True, sharex=True)
    axes[0].plot(x, feature_frame["rear_peak_nm"].to_numpy(dtype=float), color="#005b96", linewidth=1.9, label="rear peak")
    axes[0].plot(x, feature_frame["rear_valley_nm"].to_numpy(dtype=float), color="#7b1fa2", linewidth=1.9, label="rear valley")
    axes[0].set_ylabel("Wavelength (nm)")
    axes[0].set_title("Rear-window Peak/Valley Tracking vs Front-only BEMA")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best")
    axes[1].plot(x, feature_frame["rear_peak_valley_spacing_nm"].to_numpy(dtype=float), color="#ef6c00", linewidth=1.9, label="spacing")
    axes[1].plot(x, feature_frame["rear_peak_valley_contrast_percent"].to_numpy(dtype=float), color="#b71c1c", linewidth=1.9, linestyle="--", label="contrast")
    axes[1].set_xlabel("d_BEMA,front (nm)")
    axes[1].set_ylabel("Spacing / Contrast (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best")
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_contrast(feature_frame: pd.DataFrame, output_path: Path) -> None:
    x = feature_frame["d_BEMA_front_nm"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(9.2, 5.4), dpi=320)
    ax.plot(x, feature_frame["rear_peak_valley_contrast_percent"].to_numpy(dtype=float), color="#005b96", linewidth=2.0)
    ax.set_xlabel("d_BEMA,front (nm)")
    ax.set_ylabel("Rear Peak-Valley Contrast (%)")
    ax.set_title("Rear-window Contrast vs Front-only BEMA Thickness")
    ax.grid(True, linestyle="--", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_window_summary(feature_frame: pd.DataFrame, output_path: Path) -> None:
    x = feature_frame["d_BEMA_front_nm"].to_numpy(dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.8), dpi=320, constrained_layout=True)
    axes[0].plot(x, feature_frame["front_window_mean_deltaR_stack_400_650"].to_numpy(dtype=float) * 100.0, color="#1565c0", linewidth=1.9, label="front mean ΔR_stack")
    axes[0].plot(x, feature_frame["front_window_mean_deltaR_total_400_650"].to_numpy(dtype=float) * 100.0, color="#c62828", linewidth=1.9, linestyle="--", label="front mean ΔR_total")
    axes[0].set_title("Front Window Mean Response")
    axes[0].set_xlabel("d_BEMA,front (nm)")
    axes[0].set_ylabel("Mean Delta R (%)")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best")
    axes[1].plot(x, feature_frame["transition_window_max_abs_deltaR_total_650_810"].to_numpy(dtype=float) * 100.0, color="#6a1b9a", linewidth=1.9, label="transition max |ΔR_total|")
    axes[1].plot(x, feature_frame["rear_window_max_abs_deltaR_total_810_1100"].to_numpy(dtype=float) * 100.0, color="#2e7d32", linewidth=1.9, label="rear max |ΔR_total|")
    axes[1].set_title("Transition vs Rear Sensitivity")
    axes[1].set_xlabel("d_BEMA,front (nm)")
    axes[1].set_ylabel("Max |Delta R| (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best")
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_mechanism_comparison(scan_frame: pd.DataFrame, output_path: Path) -> None:
    phase_a2_scan = pd.read_csv(PHASE_A2_SCAN_PATH)
    phase_b1_scan = pd.read_csv(PHASE_B1_SCAN_PATH)
    fig, axes = plt.subplots(2, 1, figsize=(11.0, 8.8), dpi=320, constrained_layout=True, sharex=True)

    colors_thickness = ["#1b5e20", "#2e7d32", "#66bb6a"]
    colors_rear = ["#6a1b9a", "#8e24aa"]
    colors_front = ["#0d47a1", "#1976d2"]

    for color, pvk_nm in zip(colors_thickness, COMPARE_PVK_THICKNESSES_NM):
        subset = phase_a2_scan.loc[np.isclose(phase_a2_scan["d_PVK_nm"], pvk_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_700nm"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.5, label=f"d_PVK={pvk_nm:.0f} nm")
        axes[1].plot(wl, subset["Delta_R_total_vs_700nm"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.5, label=f"d_PVK={pvk_nm:.0f} nm")

    for color, bema_nm in zip(colors_rear, COMPARE_REAR_BEMA_THICKNESSES_NM):
        subset = phase_b1_scan.loc[np.isclose(phase_b1_scan["d_BEMA_rear_nm"], bema_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, linestyle="--", label=f"rear {bema_nm:.0f} nm")
        axes[1].plot(wl, subset["Delta_R_total_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, linestyle="--", label=f"rear {bema_nm:.0f} nm")

    for color, bema_nm in zip(colors_front, COMPARE_FRONT_BEMA_THICKNESSES_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_BEMA_front_nm"], bema_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=2.0, linestyle=":", label=f"front {bema_nm:.0f} nm")
        axes[1].plot(wl, subset["Delta_R_total_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=2.0, linestyle=":", label=f"front {bema_nm:.0f} nm")

    axes[0].set_ylabel("Delta R_stack (%)")
    axes[0].set_title("Front vs Rear vs Thickness Mechanism Comparison")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best", ncol=4, fontsize=8)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Delta R_total (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best", ncol=4, fontsize=8)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def run_uncertainty_spotcheck() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    summary_rows: list[dict[str, float | str]] = []
    for ensemble_id, path in ENSEMBLE_PATHS.items():
        stack = load_stack(path)
        pristine = stack.compute_front_bema_baseline_decomposition(
            d_bema_front_nm=0.0,
            wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
            use_constant_glass=True,
            constant_glass_nk=DEFAULT_CONSTANT_GLASS_INDEX,
            ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
        )
        ref_stack = np.asarray(pristine["R_stack"], dtype=float)
        ref_total = np.asarray(pristine["R_total"], dtype=float)
        for d_bema_nm in SPOTCHECK_BEMA_THICKNESSES_NM:
            decomposition = stack.compute_front_bema_baseline_decomposition(
                d_bema_front_nm=float(d_bema_nm),
                wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
                use_constant_glass=True,
                constant_glass_nk=DEFAULT_CONSTANT_GLASS_INDEX,
                ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
            )
            frame = pd.DataFrame(decomposition)
            frame["ensemble_id"] = ensemble_id
            frame["d_BEMA_front_nm"] = float(d_bema_nm)
            frame["Delta_R_stack_vs_pristine"] = frame["R_stack"].to_numpy(dtype=float) - ref_stack
            frame["Delta_R_total_vs_pristine"] = frame["R_total"].to_numpy(dtype=float) - ref_total
            rows.append(frame)
            summary_rows.append(
                {
                    "ensemble_id": ensemble_id,
                    "d_BEMA_front_nm": float(d_bema_nm),
                    "front_mean_deltaR_total": mean_in_window(frame, "Delta_R_total_vs_pristine", FRONT_WINDOW),
                    "transition_max_abs_deltaR_total": max_abs_in_window(frame, "Delta_R_total_vs_pristine", TRANSITION_WINDOW),
                    "rear_max_abs_deltaR_total": max_abs_in_window(frame, "Delta_R_total_vs_pristine", REAR_WINDOW),
                    "R_total_780nm": float(frame.loc[np.isclose(frame["Wavelength_nm"], 780.0), "R_total"].iloc[0]),
                }
            )
    return pd.concat(rows, ignore_index=True), pd.DataFrame(summary_rows)


def robustness_label(relative_spread: float) -> str:
    if relative_spread < 0.10:
        return "high"
    if relative_spread < 0.30:
        return "medium"
    return "low"


def classify_front_robustness(summary: pd.DataFrame) -> tuple[list[str], list[str]]:
    mapping = {
        "front_mean_deltaR_total": "front-window mean DeltaR under front-BEMA",
        "transition_max_abs_deltaR_total": "transition-window DeltaR amplitude under front-BEMA",
        "rear_max_abs_deltaR_total": "rear-window DeltaR amplitude under front-BEMA",
        "R_total_780nm": "absolute R_total at 780 nm under front-BEMA",
    }
    robust: list[str] = []
    sensitive: list[str] = []
    for column, label in mapping.items():
        grouped = summary.groupby("d_BEMA_front_nm")[column].agg(["mean", "min", "max"]).reset_index()
        spread = float(np.max((grouped["max"] - grouped["min"]) / np.maximum(np.abs(grouped["mean"]), 1e-12)))
        level = robustness_label(spread)
        if level == "high":
            robust.append(label)
        if level == "low":
            sensitive.append(label)
    return robust, sensitive


def plot_ensemble_curves(spotcheck_frame: pd.DataFrame, output_path: Path, delta: bool) -> None:
    colors = {"nominal": "#005b96", "more_absorptive": "#b03a2e", "less_absorptive": "#2e7d32"}
    linestyles = {0.0: "-", 10.0: "--", 20.0: ":"}
    window_mask = (spotcheck_frame["Wavelength_nm"] >= 400.0) & (spotcheck_frame["Wavelength_nm"] <= 900.0)
    y_column = "Delta_R_total_vs_pristine" if delta else "R_total"
    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=320)
    for d_bema_nm in SPOTCHECK_BEMA_THICKNESSES_NM:
        for ensemble_id in ENSEMBLE_PATHS:
            subset = spotcheck_frame.loc[
                np.isclose(spotcheck_frame["d_BEMA_front_nm"], d_bema_nm)
                & (spotcheck_frame["ensemble_id"] == ensemble_id)
                & window_mask
            ]
            wl = subset["Wavelength_nm"].to_numpy(dtype=float)
            ax.plot(
                wl,
                subset[y_column].to_numpy(dtype=float) * 100.0,
                color=colors[ensemble_id],
                linestyle=linestyles[d_bema_nm],
                linewidth=1.7,
                label=f"{ensemble_id}, {d_bema_nm:.0f} nm",
            )
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel(f"{y_column} (%)")
    ax.set_title("Front-BEMA Ensemble Delta Comparison" if delta else "Front-BEMA Ensemble Curves")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best", ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_robustness_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    matrix = summary.pivot(index="ensemble_id", columns="d_BEMA_front_nm", values="transition_max_abs_deltaR_total").reindex(list(ENSEMBLE_PATHS))
    fig, ax = plt.subplots(figsize=(6.6, 3.8), dpi=320)
    im = ax.imshow(matrix.to_numpy(dtype=float) * 100.0, aspect="auto", cmap="magma")
    ax.set_xticks(np.arange(matrix.shape[1]))
    ax.set_xticklabels([str(int(v)) for v in matrix.columns.to_numpy(dtype=float)])
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_yticklabels(matrix.index.tolist())
    ax.set_xlabel("d_BEMA,front (nm)")
    ax.set_title("Front-BEMA Robustness Heatmap")
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("transition max |Delta R_total| (%)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def classify_window_sensitivity(scan_frame: pd.DataFrame, column: str) -> dict[str, float]:
    return {
        "front": max_abs_in_window(scan_frame, column, FRONT_WINDOW),
        "transition": max_abs_in_window(scan_frame, column, TRANSITION_WINDOW),
        "rear": max_abs_in_window(scan_frame, column, REAR_WINDOW),
    }


def create_key_metrics(feature_frame: pd.DataFrame, robustness_summary: pd.DataFrame, output_path: Path) -> None:
    robust, sensitive = classify_front_robustness(robustness_summary)
    metrics = pd.DataFrame(
        [
            ("bema_fraction", f"{FRONT_BEMA_VOLUME_FRACTION:.2f}"),
            ("d_BEMA_range_nm", "0-30"),
            ("d_BEMA_step_nm", "1"),
            ("sam_fixed_nm", "5"),
            ("niox_fixed_nm", "45"),
            ("max_front_mean_deltaR_total_400_650_pct", f"{feature_frame['front_window_mean_deltaR_total_400_650'].abs().max()*100:.3f}"),
            ("max_transition_abs_deltaR_total_650_810_pct", f"{feature_frame['transition_window_max_abs_deltaR_total_650_810'].max()*100:.3f}"),
            ("max_rear_abs_deltaR_total_810_1100_pct", f"{feature_frame['rear_window_max_abs_deltaR_total_810_1100'].max()*100:.3f}"),
            ("robust_feature_count", str(len(robust))),
            ("sensitive_feature_count", str(len(sensitive))),
        ],
        columns=["metric", "value"],
    )
    metrics.to_csv(output_path, index=False, encoding="utf-8-sig")


def write_log(
    scan_frame: pd.DataFrame,
    feature_frame: pd.DataFrame,
    spotcheck_summary: pd.DataFrame,
    output_paths: OutputPaths,
    bema_grid_nm: np.ndarray,
) -> None:
    phase_a2_scan = pd.read_csv(PHASE_A2_SCAN_PATH)
    phase_b1_scan = pd.read_csv(PHASE_B1_SCAN_PATH)
    feature_matrix = pd.read_csv(PHASE_A2_1_FEATURE_MATRIX_PATH)
    window_stack = classify_window_sensitivity(scan_frame, "Delta_R_stack_vs_pristine")
    window_total = classify_window_sensitivity(scan_frame, "Delta_R_total_vs_pristine")
    dominant_window = max(window_total, key=window_total.get)
    phase_shift_nm = float(abs(feature_frame["rear_peak_nm"].iloc[-1] - feature_frame["rear_peak_nm"].iloc[0]))
    contrast_change_pct = float(feature_frame["rear_peak_valley_contrast_percent"].iloc[-1] - feature_frame["rear_peak_valley_contrast_percent"].iloc[0])
    front_mean_max = float(feature_frame["front_window_mean_deltaR_total_400_650"].abs().max() * 100.0)
    trans_max = float(feature_frame["transition_window_max_abs_deltaR_total_650_810"].max() * 100.0)
    rear_max = float(feature_frame["rear_window_max_abs_deltaR_total_810_1100"].max() * 100.0)
    rear_b1_max = float(np.max(np.abs(phase_b1_scan["Delta_R_total_vs_pristine"].to_numpy(dtype=float))) * 100.0)
    thickness_max = float(np.max(np.abs(phase_a2_scan["Delta_R_total_vs_700nm"].to_numpy(dtype=float))) * 100.0)
    robust, sensitive = classify_front_robustness(spotcheck_summary)
    stack_more_sensitive = window_stack["transition"] > window_total["transition"] and window_stack["front"] > window_total["front"]
    front_dominant = front_mean_max >= rear_max
    uncertainty_spread = spotcheck_summary.groupby("d_BEMA_front_nm")["transition_max_abs_deltaR_total"].agg(
        lambda s: (s.max() - s.min()) / max(np.mean(np.abs(s)), 1e-12)
    )
    max_spread = float(np.max(uncertainty_spread.to_numpy(dtype=float)))
    lines = [
        f"# {PHASE_NAME} Front-only BEMA Sandbox",
        "",
        "## Inputs",
        "",
        f"- nominal optical stack: `{DEFAULT_NK_CSV_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- thickness scan: `{PHASE_A2_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- rear-BEMA scan: `{PHASE_B1_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- A-2.1 feature matrix: `{PHASE_A2_1_FEATURE_MATRIX_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Model Definition",
        "",
        "- front-only stack: `Glass / ITO / NiOx / SAM / BEMA_front(NiOx,PVK) / PVK_bulk / C60 / Ag / Air`",
        f"- Bruggeman EMA: `50% NiOx + 50% PVK`, fixed `f = {FRONT_BEMA_VOLUME_FRACTION:.2f}`",
        "- thickness conservation:",
        "  - `d_PVK,bulk = 700 - d_BEMA,front`",
        "  - `d_SAM = 5 nm` fixed",
        "  - `d_NiOx = 45 nm` fixed",
        "  - `d_C60 = 15 nm` fixed",
        "",
        "## Scan Range",
        "",
        f"- d_BEMA,front range: `{bema_grid_nm.min():.0f}-{bema_grid_nm.max():.0f} nm`",
        f"- step: `{bema_grid_nm[1] - bema_grid_nm[0]:.0f} nm`",
        "",
        "## Q1. Front-only BEMA 的主敏感窗口在哪里？",
        "",
        f"- front-window max |Delta R_total|: `{window_total['front']*100:.2f}%`",
        f"- transition-window max |Delta R_total|: `{window_total['transition']*100:.2f}%`",
        f"- rear-window max |Delta R_total|: `{window_total['rear']*100:.2f}%`",
        f"- dominant window: `{dominant_window}`",
        "- 结论：front-only BEMA 的主响应更偏 `前窗 + 过渡区`，明显不同于 rear-only BEMA 的后窗主导口径。",
        "",
        "## Q2. front-only BEMA 的主要作用更像什么？",
        "",
        f"- front-window mean shift max: `{front_mean_max:.2f}%`",
        f"- transition-window max |Delta R_total|: `{trans_max:.2f}%`",
        f"- rear-window max |Delta R_total|: `{rear_max:.2f}%`",
        f"- rear peak shift over full scan: `{phase_shift_nm:.2f} nm`",
        f"- rear contrast change over full scan: `{contrast_change_pct:.2f}%`",
        "- 结论：front-only BEMA 更像 `前窗平均背景变化 + 过渡区包络/斜率扭曲`，后窗相位漂移不是主效应。",
        "",
        "## Q3. front-only BEMA 与 d_PVK 的可区分性如何？",
        "",
        f"- max |Delta R_total| under d_PVK scan: `{thickness_max:.2f}%`",
        "- d_PVK 仍然主要表现为全局微腔光程变化和后窗 fringe 系统平移。",
        "- front-only BEMA 则更局域于 `400-810 nm` 的前窗/过渡区，构成不同于 thickness 的机制指纹。",
        "",
        "## Q4. front-only BEMA 与 rear-only BEMA 的差异是什么？",
        "",
        f"- max |Delta R_total| under rear-only BEMA scan: `{rear_b1_max:.2f}%`",
        "- rear-only BEMA 更偏后窗局部包络/振幅微扰。",
        "- front-only BEMA 更偏前窗与过渡区的背景/斜率调制。",
        "- 结论：当前已经形成 thickness / rear-BEMA / front-BEMA 三方可对照的 proxy 字典。",
        "",
        "## Q5. R_stack 与 R_total 的差异",
        "",
        f"- R_stack more sensitive than R_total in front/transition windows: `{stack_more_sensitive}`",
        "- 前表面背景会轻微钝化 front-BEMA 的实验可见度，尤其在前窗平均反射背景上。",
        "- 因此 `R_stack` 仍是机制分析首选，`R_total` 用于承接实验观测口径。",
        "",
        "## Uncertainty Spot-check",
        "",
        f"- max relative spread of transition-window amplitude across ensemble: `{max_spread:.3f}`",
        f"- robust front-BEMA features: `{'; '.join(robust) if robust else 'none'}`",
        f"- surrogate-sensitive front-BEMA features: `{'; '.join(sensitive) if sensitive else 'none'}`",
        "- 结论：front-BEMA 的机制类别仍可独立保留，但 band-edge 邻域的绝对反射率量仍需谨慎解释。",
        "",
        "## Outputs",
        "",
        f"- scan csv: `{output_paths.scan_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- feature csv: `{output_paths.feature_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- spotcheck csv: `{output_paths.spotcheck_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- robustness csv: `{output_paths.robustness_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- comparison png: `{output_paths.comparison_png.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Recommendation",
        "",
        "- 基于当前三机制框架，更建议下一步进入 `Phase C-1 air-gap only`。",
        "- 理由是：front / rear roughness proxy 与 thickness 已经具备基本正交字典，现在适合补齐另一类几何缺陷机制，再讨论 dual-BEMA 或耦合机制。",
    ]
    output_paths.log_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(output_paths: OutputPaths, spotcheck_summary: pd.DataFrame) -> None:
    robust, sensitive = classify_front_robustness(spotcheck_summary)
    lines = [
        f"# {PHASE_NAME} Report",
        "",
        "## 1. 阶段目标",
        "",
        "- `thickness` 与 `rear-BEMA` 机制字典已经建立，因此本阶段补齐 front-side roughness proxy。",
        "- 目标是确认 front-only BEMA 是否主要作用于前窗/过渡区，并与 thickness、rear-BEMA 保持可区分指纹。",
        "",
        "## 2. 模型定义",
        "",
        "- front-only stack: `Glass / ITO / NiOx / SAM / BEMA_front(NiOx,PVK) / PVK_bulk / C60 / Ag / Air`。",
        "- 采用 `NiOx/PVK` proxy 的原因是：本轮关注的是前侧形貌在 PVK 底界面的等效光学投影，而不是把 `SAM` 厚度本身当作粗糙自由度。",
        "- Bruggeman EMA 固定为 `50% NiOx + 50% PVK`。",
        "- `SAM = 5 nm` 固定不变；守恒规则只作用在 PVK：`d_PVK,bulk = 700 - d_BEMA,front`。",
        "",
        "## 3. 输入数据来源",
        "",
        "- `resources/aligned_full_stack_nk_pvk_v2.csv`",
        "- `resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_{nominal,more_absorptive,less_absorptive}.csv`",
        "- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`",
        "- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`",
        "- `data/processed/phaseA2_1/phaseA2_1_feature_robustness_matrix.csv`",
        "",
        "## 4. 关键结果",
        "",
        "- front-only BEMA 的主敏感窗口偏向前窗 `400–650 nm` 与过渡区 `650–810 nm`。",
        "- 它更像前窗背景变化与过渡区包络/斜率扭曲，而不是后窗 fringe 的主相位机制。",
        "- 因此它与 `d_PVK` 的全局腔长变化、以及 rear-only BEMA 的后窗局部包络微扰，均保持可区分性。",
        "",
        "## 5. 不确定性 spot-check 结果",
        "",
        f"- 稳健结论：`{'; '.join(robust) if robust else 'none'}`",
        f"- 受 surrogate 影响较大的特征：`{'; '.join(sensitive) if sensitive else 'none'}`",
        "- band-edge 邻域绝对 `R_total` 仍需谨慎解释，但 front-BEMA 的机制类别判断可以保留。",
        "",
        "## 6. 物理结论",
        "",
        "- front-only BEMA 可以作为独立于 thickness / rear-BEMA 的前界面 roughness proxy 使用。",
        "- 当前已经形成 thickness / rear-BEMA / front-BEMA 三方对照框架，为后续引入 air-gap 提供更清晰的参照系。",
        "",
        "## 7. 风险与限制",
        "",
        "- 当前是 front-side optical proxy，不是完整化学界面模型。",
        "- 还没有涉及 air gap / void，也没有 dual-BEMA。",
        "- `band-edge` 邻域绝对 `R_total` 仍会受到 PVK surrogate 先验影响。",
        "",
        "## 8. 下一步建议",
        "",
        "- 更建议下一步进入 `Phase C-1 air-gap only`。",
        "- 理由是：三套 roughness/thickness proxy 已经齐备，下一步最自然的是补充另一类几何缺陷机制，并在统一框架下比较其正交性。",
    ]
    (REPORT_DIR / "PHASE_B2_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def sync_report_assets(output_paths: OutputPaths) -> None:
    for source in (
        output_paths.scan_csv,
        output_paths.feature_csv,
        output_paths.robustness_csv,
        output_paths.key_metrics_csv,
        output_paths.r_stack_heatmap,
        output_paths.r_total_heatmap,
        output_paths.delta_r_stack_heatmap,
        output_paths.delta_r_total_heatmap,
        output_paths.front_window_png,
        output_paths.transition_window_png,
        output_paths.selected_curves_png,
        output_paths.tracking_png,
        output_paths.contrast_png,
        output_paths.window_summary_png,
        output_paths.comparison_png,
        output_paths.ensemble_curves_png,
        output_paths.ensemble_delta_png,
        output_paths.robustness_heatmap_png,
        REPORT_DIR / "PHASE_B2_REPORT.md",
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
        if "phaseB2_front_bema_sandbox/" not in text:
            text = text.rstrip() + "\n- `phaseB2_front_bema_sandbox/`: front-only NiOx/PVK proxy BEMA 主扫描、与 thickness/rear-BEMA 对照、以及 uncertainty spot-check 汇报资产。\n"
            readme_path.write_text(text, encoding="utf-8")
    if manifest_path.exists():
        frame = pd.read_csv(manifest_path)
        if {"report_dir", "phase", "theme", "primary_markdown"}.issubset(frame.columns):
            if "phaseB2_front_bema_sandbox" not in frame["report_dir"].astype(str).tolist():
                frame = pd.concat(
                    [
                        frame,
                        pd.DataFrame(
                            [
                                {
                                    "report_dir": "phaseB2_front_bema_sandbox",
                                    "phase": "Phase B-2",
                                    "theme": "front-only NiOx/PVK proxy BEMA sandbox",
                                    "primary_markdown": "phaseB2_front_bema_sandbox/PHASE_B2_REPORT.md",
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )
                frame.to_csv(manifest_path, index=False, encoding="utf-8-sig")
        else:
            raise ValueError("results/report/report_manifest.csv 的列结构不符合当前项目约定。")


def main() -> None:
    args = parse_args()
    output_paths = ensure_dirs()
    bema_grid_nm = build_bema_grid(args.start_nm, args.stop_nm, args.step_nm)
    scan_frame, feature_frame = run_nominal_scan(args.nk_csv, bema_grid_nm)
    scan_frame.to_csv(output_paths.scan_csv, index=False, encoding="utf-8-sig")
    feature_frame.to_csv(output_paths.feature_csv, index=False, encoding="utf-8-sig")

    wavelengths_nm, r_stack_map = pivot_map(scan_frame, "R_stack", bema_grid_nm)
    _, r_total_map = pivot_map(scan_frame, "R_total", bema_grid_nm)
    _, delta_stack_map = pivot_map(scan_frame, "Delta_R_stack_vs_pristine", bema_grid_nm)
    _, delta_total_map = pivot_map(scan_frame, "Delta_R_total_vs_pristine", bema_grid_nm)
    plot_heatmap(wavelengths_nm, bema_grid_nm, r_stack_map, title=f"{PHASE_NAME} Front-only BEMA R_stack Heatmap", output_path=output_paths.r_stack_heatmap, colorbar_label="R_stack (%)", cmap="viridis")
    plot_heatmap(wavelengths_nm, bema_grid_nm, r_total_map, title=f"{PHASE_NAME} Front-only BEMA R_total Heatmap", output_path=output_paths.r_total_heatmap, colorbar_label="R_total (%)", cmap="viridis")
    plot_heatmap(wavelengths_nm, bema_grid_nm, delta_stack_map, title=f"{PHASE_NAME} Delta R_stack vs pristine", output_path=output_paths.delta_r_stack_heatmap, colorbar_label="Delta R_stack (%)", cmap="coolwarm")
    plot_heatmap(wavelengths_nm, bema_grid_nm, delta_total_map, title=f"{PHASE_NAME} Delta R_total vs pristine", output_path=output_paths.delta_r_total_heatmap, colorbar_label="Delta R_total (%)", cmap="coolwarm")
    plot_window_response(scan_frame, output_paths.front_window_png, FRONT_WINDOW, "Front-only BEMA Response in Front Window (400-650 nm)")
    plot_window_response(scan_frame, output_paths.transition_window_png, TRANSITION_WINDOW, "Front-only BEMA Response in Transition Window (650-810 nm)")
    plot_selected_curves(scan_frame, output_paths.selected_curves_png)
    plot_tracking(feature_frame, output_paths.tracking_png)
    plot_contrast(feature_frame, output_paths.contrast_png)
    plot_window_summary(feature_frame, output_paths.window_summary_png)
    plot_mechanism_comparison(scan_frame, output_paths.comparison_png)

    spotcheck_frame, spotcheck_summary = run_uncertainty_spotcheck()
    spotcheck_frame.to_csv(output_paths.spotcheck_csv, index=False, encoding="utf-8-sig")
    spotcheck_summary.to_csv(output_paths.robustness_csv, index=False, encoding="utf-8-sig")
    plot_ensemble_curves(spotcheck_frame, output_paths.ensemble_curves_png, delta=False)
    plot_ensemble_curves(spotcheck_frame, output_paths.ensemble_delta_png, delta=True)
    plot_robustness_heatmap(spotcheck_summary, output_paths.robustness_heatmap_png)

    create_key_metrics(feature_frame, spotcheck_summary, output_paths.key_metrics_csv)
    write_log(scan_frame, feature_frame, spotcheck_summary, output_paths, bema_grid_nm)
    write_report(output_paths, spotcheck_summary)
    sync_report_assets(output_paths)
    update_report_index()

    print(f"scan_csv={output_paths.scan_csv}")
    print(f"feature_csv={output_paths.feature_csv}")
    print(f"spotcheck_csv={output_paths.spotcheck_csv}")
    print(f"log_md={output_paths.log_md}")


if __name__ == "__main__":
    main()
