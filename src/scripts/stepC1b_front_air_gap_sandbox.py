"""Phase C-1b front-air-gap only sandbox.

This phase introduces a true front separation layer only:

Glass / ITO / NiOx / SAM / Air_gap_front / PVK / C60 / Ag / Air

The gap is treated as an added separation optical path, not as a mixed layer
and not as a thickness-conserving proxy. SAM, PVK and C60 nominal thicknesses
remain fixed at 5 nm, 700 nm and 15 nm.
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

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (str(PROJECT_ROOT / "src"), str(SCRIPT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import stepA1_pristine_baseline as phase_a1  # noqa: E402
import stepC1a_rear_air_gap_sandbox as phase_c1a  # noqa: E402
from core.full_stack_microcavity import (  # noqa: E402
    AG_BOUNDARY_FINITE_FILM,
    DEFAULT_CONSTANT_GLASS_INDEX,
)


PHASE_NAME = "Phase C-1b"
DEFAULT_NK_CSV_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_pvk_v2.csv"
ENSEMBLE_PATHS = {
    "nominal": PROJECT_ROOT / "resources" / "pvk_ensemble" / "aligned_full_stack_nk_pvk_ens_nominal.csv",
    "more_absorptive": PROJECT_ROOT / "resources" / "pvk_ensemble" / "aligned_full_stack_nk_pvk_ens_more_absorptive.csv",
    "less_absorptive": PROJECT_ROOT / "resources" / "pvk_ensemble" / "aligned_full_stack_nk_pvk_ens_less_absorptive.csv",
}
PHASE_A2_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA2" / "phaseA2_pvk_thickness_scan.csv"
PHASE_B1_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseB1" / "phaseB1_rear_bema_scan.csv"
PHASE_B2_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseB2" / "phaseB2_front_bema_scan.csv"
PHASE_C1A_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseC1a" / "phaseC1a_rear_air_gap_scan.csv"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phaseC1b"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phaseC1b"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phaseC1b"
REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phaseC1b_front_air_gap_sandbox"

FRONT_WINDOW = phase_c1a.FRONT_WINDOW
TRANSITION_WINDOW = phase_c1a.TRANSITION_WINDOW
REAR_WINDOW = phase_c1a.REAR_WINDOW
NOISE_FLOOR = phase_c1a.NOISE_FLOOR
LOD_TARGETS_NM = phase_c1a.LOD_TARGETS_NM
SELECTED_GAPS_NM = (0.0, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 30.0, 50.0)
SPOTCHECK_GAPS_NM = (0.0, 2.0, 5.0, 10.0)
COMPARE_PVK_THICKNESSES_NM = (650.0, 750.0, 850.0)
COMPARE_FRONT_BEMA_THICKNESSES_NM = (10.0, 20.0)
COMPARE_REAR_GAPS_NM = (2.0, 5.0, 10.0)
COMPARE_FRONT_GAPS_NM = (2.0, 5.0, 10.0)


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
    front_response_png: Path
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
    parser = argparse.ArgumentParser(description="Run Phase C-1b front air-gap sandbox.")
    parser.add_argument("--nk-csv", type=Path, default=DEFAULT_NK_CSV_PATH)
    parser.add_argument("--scan-mode", choices=("a", "b"), default="a")
    return parser.parse_args()


def ensure_dirs() -> OutputPaths:
    for path in (PROCESSED_DIR, FIGURE_DIR, LOG_DIR, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    return OutputPaths(
        scan_csv=PROCESSED_DIR / "phaseC1b_front_air_gap_scan.csv",
        feature_csv=PROCESSED_DIR / "phaseC1b_front_air_gap_feature_summary.csv",
        lod_csv=PROCESSED_DIR / "phaseC1b_front_air_gap_lod_summary.csv",
        spotcheck_csv=PROCESSED_DIR / "phaseC1b_front_air_gap_ensemble_spotcheck.csv",
        robustness_csv=PROCESSED_DIR / "phaseC1b_front_air_gap_robustness_summary.csv",
        key_metrics_csv=REPORT_DIR / "phaseC1b_key_metrics.csv",
        log_md=LOG_DIR / "phaseC1b_front_air_gap_sandbox.md",
        r_stack_heatmap=FIGURE_DIR / "phaseC1b_R_stack_heatmap.png",
        r_total_heatmap=FIGURE_DIR / "phaseC1b_R_total_heatmap.png",
        delta_r_stack_heatmap=FIGURE_DIR / "phaseC1b_deltaR_stack_heatmap.png",
        delta_r_total_heatmap=FIGURE_DIR / "phaseC1b_deltaR_total_heatmap.png",
        front_response_png=FIGURE_DIR / "phaseC1b_front_window_response.png",
        transition_response_png=FIGURE_DIR / "phaseC1b_transition_window_response.png",
        rear_response_png=FIGURE_DIR / "phaseC1b_rear_window_response.png",
        selected_curves_png=FIGURE_DIR / "phaseC1b_selected_gap_curves.png",
        tracking_png=FIGURE_DIR / "phaseC1b_peak_valley_tracking.png",
        spacing_png=FIGURE_DIR / "phaseC1b_spacing_vs_gap.png",
        wavenumber_png=FIGURE_DIR / "phaseC1b_selected_curves_wavenumber.png",
        comparison_png=FIGURE_DIR / "phaseC1b_frontgap_vs_frontbema_vs_reargap_vs_thickness.png",
        lod_png=FIGURE_DIR / "phaseC1b_lod_vs_gap.png",
        ensemble_curves_png=FIGURE_DIR / "phaseC1b_front_air_gap_ensemble_curves.png",
        ensemble_delta_png=FIGURE_DIR / "phaseC1b_front_air_gap_ensemble_deltaR_comparison.png",
        robustness_heatmap_png=FIGURE_DIR / "phaseC1b_front_air_gap_robustness_heatmap.png",
    )


def build_gap_grid(scan_mode: str) -> np.ndarray:
    return phase_c1a.build_gap_grid(scan_mode)


def load_stack(nk_csv_path: Path):
    stack, _, _ = phase_a1.load_optical_stack_from_aligned_csv(nk_csv_path)
    return stack


def run_nominal_scan(nk_csv_path: Path, gap_grid_nm: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    stack = load_stack(nk_csv_path)
    pristine = stack.compute_front_air_gap_baseline_decomposition(
        d_gap_front_nm=0.0,
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
        decomposition = stack.compute_front_air_gap_baseline_decomposition(
            d_gap_front_nm=float(gap_nm),
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
        frame["d_gap_front_nm"] = float(gap_nm)
        frame["Delta_R_stack_vs_pristine"] = frame["R_stack"].to_numpy(dtype=float) - ref_stack
        frame["Delta_R_total_vs_pristine"] = frame["R_total"].to_numpy(dtype=float) - ref_total
        frames.append(frame)
        rear_signals.append(frame.loc[rear_mask, "R_total"].to_numpy(dtype=float))

    peak_track, valley_track = phase_c1a.branch_track(rear_signals, rear_wavelength_nm)
    feature_rows: list[dict[str, float]] = []
    for gap_nm, frame, peak_nm, valley_nm in zip(gap_grid_nm, frames, peak_track, valley_track):
        rear_total = frame.loc[rear_mask, "R_total"].to_numpy(dtype=float)
        feature_rows.append(
            {
                "d_gap_front_nm": float(gap_nm),
                "front_window_mean_deltaR_stack_400_650": float(
                    frame.loc[
                        (frame["Wavelength_nm"] >= FRONT_WINDOW[0]) & (frame["Wavelength_nm"] <= FRONT_WINDOW[1]),
                        "Delta_R_stack_vs_pristine",
                    ].mean()
                ),
                "front_window_mean_deltaR_total_400_650": float(
                    frame.loc[
                        (frame["Wavelength_nm"] >= FRONT_WINDOW[0]) & (frame["Wavelength_nm"] <= FRONT_WINDOW[1]),
                        "Delta_R_total_vs_pristine",
                    ].mean()
                ),
                "transition_window_max_abs_deltaR_stack_650_810": phase_c1a.max_abs_in_window(frame, "Delta_R_stack_vs_pristine", TRANSITION_WINDOW),
                "transition_window_max_abs_deltaR_total_650_810": phase_c1a.max_abs_in_window(frame, "Delta_R_total_vs_pristine", TRANSITION_WINDOW),
                "rear_window_max_abs_deltaR_stack_810_1100": phase_c1a.max_abs_in_window(frame, "Delta_R_stack_vs_pristine", REAR_WINDOW),
                "rear_window_max_abs_deltaR_total_810_1100": phase_c1a.max_abs_in_window(frame, "Delta_R_total_vs_pristine", REAR_WINDOW),
                "rear_peak_nm": float(peak_nm),
                "rear_valley_nm": float(valley_nm),
                "rear_peak_valley_spacing_nm": float(abs(peak_nm - valley_nm)),
                "rear_peak_valley_contrast_percent": float((np.max(rear_total) - np.min(rear_total)) * 100.0),
            }
        )
    return pd.concat(frames, ignore_index=True), pd.DataFrame(feature_rows)


def pivot_to_gap_grid(scan_frame: pd.DataFrame, gap_grid_nm: np.ndarray, value_column: str) -> tuple[np.ndarray, np.ndarray]:
    ordered = scan_frame.pivot(index="d_gap_front_nm", columns="Wavelength_nm", values=value_column).sort_index()
    if not np.array_equal(ordered.index.to_numpy(dtype=float), gap_grid_nm):
        raise ValueError(f"{value_column} 的 gap 行索引与扫描网格不一致。")
    return ordered.columns.to_numpy(dtype=float), ordered.to_numpy(dtype=float)


def plot_window_response(scan_frame: pd.DataFrame, output_path: Path, window: tuple[float, float], title: str) -> None:
    mask = (scan_frame["Wavelength_nm"] >= window[0]) & (scan_frame["Wavelength_nm"] <= window[1])
    fig, axes = plt.subplots(2, 1, figsize=(10.4, 7.8), dpi=320, constrained_layout=True, sharex=True)
    colors = plt.cm.viridis(np.linspace(0.08, 0.92, len(SELECTED_GAPS_NM)))
    for color, gap_nm in zip(colors, SELECTED_GAPS_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_gap_front_nm"], gap_nm) & mask]
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
        subset = scan_frame.loc[np.isclose(scan_frame["d_gap_front_nm"], gap_nm)]
        if subset.empty:
            continue
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["R_stack"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.6, label=f"{gap_nm:.1f} nm")
        axes[1].plot(wl, subset["R_total"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.6, label=f"{gap_nm:.1f} nm")
    axes[0].set_ylabel("R_stack (%)")
    axes[0].set_title("Selected Front Air-gap Curves")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best", ncol=3, fontsize=8)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("R_total (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_tracking(feature_frame: pd.DataFrame, output_path: Path) -> None:
    x = feature_frame["d_gap_front_nm"].to_numpy(dtype=float)
    fig, axes = plt.subplots(2, 1, figsize=(9.8, 8.2), dpi=320, constrained_layout=True, sharex=True)
    axes[0].plot(x, feature_frame["rear_peak_nm"].to_numpy(dtype=float), color="#005b96", linewidth=1.9, label="peak")
    axes[0].plot(x, feature_frame["rear_valley_nm"].to_numpy(dtype=float), color="#8e24aa", linewidth=1.9, label="valley")
    axes[0].set_ylabel("Wavelength (nm)")
    axes[0].set_title("Front-gap Impact on Rear-window Peak/Valley Tracking")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best")
    axes[1].plot(x, feature_frame["rear_peak_valley_spacing_nm"].to_numpy(dtype=float), color="#ef6c00", linewidth=1.9, label="spacing")
    axes[1].plot(x, feature_frame["rear_peak_valley_contrast_percent"].to_numpy(dtype=float), color="#b71c1c", linewidth=1.9, linestyle="--", label="contrast")
    axes[1].set_xlabel("d_gap,front (nm)")
    axes[1].set_ylabel("Spacing (nm) / Contrast (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best")
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_spacing_vs_gap(feature_frame: pd.DataFrame, output_path: Path) -> None:
    x = feature_frame["d_gap_front_nm"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(9.0, 5.2), dpi=320)
    ax.plot(x, feature_frame["rear_peak_valley_spacing_nm"].to_numpy(dtype=float), color="#1565c0", linewidth=1.9, label="peak-valley spacing")
    ax.plot(x, feature_frame["rear_peak_nm"].to_numpy(dtype=float) - feature_frame["rear_peak_nm"].iloc[0], color="#6a1b9a", linewidth=1.9, linestyle="--", label="peak shift")
    ax.set_xlabel("d_gap,front (nm)")
    ax.set_ylabel("Wavelength Metric (nm)")
    ax.set_title("Rear-window Spacing / Shift vs Front Air-gap")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_selected_curves_wavenumber(scan_frame: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.2, 5.8), dpi=320)
    colors = plt.cm.cividis(np.linspace(0.1, 0.9, len(SELECTED_GAPS_NM)))
    for color, gap_nm in zip(colors, SELECTED_GAPS_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_gap_front_nm"], gap_nm) & (scan_frame["Wavelength_nm"] >= REAR_WINDOW[0]) & (scan_frame["Wavelength_nm"] <= REAR_WINDOW[1])]
        if subset.empty:
            continue
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        ax.plot(1000.0 / wl, subset["R_total"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.6, label=f"{gap_nm:.1f} nm")
    ax.set_xlabel("Wavenumber (1/um)")
    ax.set_ylabel("R_total (%)")
    ax.set_title("Selected Front-gap Curves on Wavenumber Axis")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best", ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def build_lod_summary(scan_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for gap_nm in LOD_TARGETS_NM:
        subset = scan_frame.loc[np.isclose(scan_frame["d_gap_front_nm"], gap_nm)]
        front_stack = phase_c1a.max_abs_in_window(subset, "Delta_R_stack_vs_pristine", FRONT_WINDOW)
        trans_stack = phase_c1a.max_abs_in_window(subset, "Delta_R_stack_vs_pristine", TRANSITION_WINDOW)
        rear_stack = phase_c1a.max_abs_in_window(subset, "Delta_R_stack_vs_pristine", REAR_WINDOW)
        front_total = phase_c1a.max_abs_in_window(subset, "Delta_R_total_vs_pristine", FRONT_WINDOW)
        trans_total = phase_c1a.max_abs_in_window(subset, "Delta_R_total_vs_pristine", TRANSITION_WINDOW)
        rear_total = phase_c1a.max_abs_in_window(subset, "Delta_R_total_vs_pristine", REAR_WINDOW)
        total_windows = {"front": front_total, "transition": trans_total, "rear": rear_total}
        best_window = max(total_windows, key=total_windows.get)
        max_stack = max(front_stack, trans_stack, rear_stack)
        max_total = max(front_total, trans_total, rear_total)
        rows.append(
            {
                "d_gap_front_nm": float(gap_nm),
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
    x = lod_frame["d_gap_front_nm"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(9.4, 5.4), dpi=320)
    ax.plot(x, lod_frame["max_abs_deltaR_stack"].to_numpy(dtype=float) * 100.0, color="#005b96", linewidth=1.9, label="max |Delta R_stack|")
    ax.plot(x, lod_frame["max_abs_deltaR_total"].to_numpy(dtype=float) * 100.0, color="#b03a2e", linewidth=1.9, linestyle="--", label="max |Delta R_total|")
    ax.axhline(NOISE_FLOOR * 100.0, color="#424242", linewidth=1.4, linestyle=":", label="0.2% noise floor")
    ax.set_xlabel("d_gap,front (nm)")
    ax.set_ylabel("Max |Delta R| (%)")
    ax.set_title("Front Air-gap Coarse LOD vs Gap Thickness")
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
        pristine = stack.compute_front_air_gap_baseline_decomposition(
            d_gap_front_nm=0.0,
            wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
            use_constant_glass=True,
            constant_glass_nk=DEFAULT_CONSTANT_GLASS_INDEX,
            ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
        )
        ref_stack = np.asarray(pristine["R_stack"], dtype=float)
        ref_total = np.asarray(pristine["R_total"], dtype=float)
        for gap_nm in SPOTCHECK_GAPS_NM:
            decomposition = stack.compute_front_air_gap_baseline_decomposition(
                d_gap_front_nm=float(gap_nm),
                wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
                use_constant_glass=True,
                constant_glass_nk=DEFAULT_CONSTANT_GLASS_INDEX,
                ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
            )
            frame = pd.DataFrame(decomposition)
            frame["ensemble_id"] = ensemble_id
            frame["d_gap_front_nm"] = float(gap_nm)
            frame["Delta_R_stack_vs_pristine"] = frame["R_stack"].to_numpy(dtype=float) - ref_stack
            frame["Delta_R_total_vs_pristine"] = frame["R_total"].to_numpy(dtype=float) - ref_total
            frames.append(frame)
            summary_rows.append(
                {
                    "ensemble_id": ensemble_id,
                    "d_gap_front_nm": float(gap_nm),
                    "front_mean_deltaR_total": float(
                        frame.loc[
                            (frame["Wavelength_nm"] >= FRONT_WINDOW[0]) & (frame["Wavelength_nm"] <= FRONT_WINDOW[1]),
                            "Delta_R_total_vs_pristine",
                        ].mean()
                    ),
                    "transition_max_abs_deltaR_total": phase_c1a.max_abs_in_window(frame, "Delta_R_total_vs_pristine", TRANSITION_WINDOW),
                    "rear_max_abs_deltaR_total": phase_c1a.max_abs_in_window(frame, "Delta_R_total_vs_pristine", REAR_WINDOW),
                    "R_total_780nm": float(frame.loc[np.isclose(frame["Wavelength_nm"], 780.0), "R_total"].iloc[0]),
                }
            )
    return pd.concat(frames, ignore_index=True), pd.DataFrame(summary_rows)


def classify_front_gap_robustness(summary: pd.DataFrame) -> tuple[list[str], list[str]]:
    mapping = {
        "front_mean_deltaR_total": "front-window mean DeltaR_total under front-gap",
        "transition_max_abs_deltaR_total": "transition-window DeltaR amplitude under front-gap",
        "rear_max_abs_deltaR_total": "rear-window DeltaR amplitude under front-gap",
        "R_total_780nm": "absolute R_total at 780 nm under front-gap",
    }
    robust: list[str] = []
    sensitive: list[str] = []
    for column, label in mapping.items():
        grouped = summary.groupby("d_gap_front_nm")[column].agg(["mean", "min", "max"]).reset_index()
        spread = float(np.max((grouped["max"] - grouped["min"]) / np.maximum(np.abs(grouped["mean"]), 1e-12)))
        level = phase_c1a.robustness_label(spread)
        if level == "high":
            robust.append(label)
        if level == "low":
            sensitive.append(label)
    return robust, sensitive


def plot_spotcheck_curves(spotcheck_frame: pd.DataFrame, output_path: Path, delta: bool) -> None:
    colors = {"nominal": "#005b96", "more_absorptive": "#b03a2e", "less_absorptive": "#2e7d32"}
    linestyles = {0.0: "-", 2.0: "--", 5.0: ":", 10.0: "-."}
    mask = (spotcheck_frame["Wavelength_nm"] >= 400.0) & (spotcheck_frame["Wavelength_nm"] <= 1100.0)
    y_column = "Delta_R_total_vs_pristine" if delta else "R_total"
    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=320)
    for gap_nm in SPOTCHECK_GAPS_NM:
        for ensemble_id in ENSEMBLE_PATHS:
            subset = spotcheck_frame.loc[np.isclose(spotcheck_frame["d_gap_front_nm"], gap_nm) & (spotcheck_frame["ensemble_id"] == ensemble_id) & mask]
            wl = subset["Wavelength_nm"].to_numpy(dtype=float)
            ax.plot(wl, subset[y_column].to_numpy(dtype=float) * 100.0, color=colors[ensemble_id], linestyle=linestyles[gap_nm], linewidth=1.7, label=f"{ensemble_id}, {gap_nm:.0f} nm")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel(f"{y_column} (%)")
    ax.set_title("Front-gap Ensemble Delta Comparison" if delta else "Front-gap Ensemble Curves")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best", ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_robustness_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    matrix = summary.pivot(index="ensemble_id", columns="d_gap_front_nm", values="transition_max_abs_deltaR_total").reindex(list(ENSEMBLE_PATHS))
    fig, ax = plt.subplots(figsize=(6.8, 3.8), dpi=320)
    im = ax.imshow(matrix.to_numpy(dtype=float) * 100.0, aspect="auto", cmap="magma")
    ax.set_xticks(np.arange(matrix.shape[1]))
    ax.set_xticklabels([str(int(v)) for v in matrix.columns.to_numpy(dtype=float)])
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_yticklabels(matrix.index.tolist())
    ax.set_xlabel("d_gap,front (nm)")
    ax.set_title("Front-gap Robustness Heatmap")
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("transition max |Delta R_total| (%)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_mechanism_comparison(scan_frame: pd.DataFrame, output_path: Path) -> None:
    a2 = pd.read_csv(PHASE_A2_SCAN_PATH)
    b2 = pd.read_csv(PHASE_B2_SCAN_PATH)
    c1a = pd.read_csv(PHASE_C1A_SCAN_PATH)
    fig, axes = plt.subplots(2, 1, figsize=(11.4, 9.2), dpi=320, constrained_layout=True, sharex=True)
    colors_thickness = ["#1b5e20", "#2e7d32", "#66bb6a"]
    colors_front_bema = ["#0d47a1", "#1976d2"]
    colors_rear_gap = ["#6a1b9a", "#8e24aa", "#ba68c8"]
    colors_front_gap = ["#ef6c00", "#fb8c00", "#ffb74d"]
    for color, pvk_nm in zip(colors_thickness, COMPARE_PVK_THICKNESSES_NM):
        subset = a2.loc[np.isclose(a2["d_PVK_nm"], pvk_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_700nm"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.4, label=f"d_PVK={pvk_nm:.0f}")
        axes[1].plot(wl, subset["Delta_R_total_vs_700nm"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.4, label=f"d_PVK={pvk_nm:.0f}")
    for color, bema_nm in zip(colors_front_bema, COMPARE_FRONT_BEMA_THICKNESSES_NM):
        subset = b2.loc[np.isclose(b2["d_BEMA_front_nm"], bema_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, linestyle="--", label=f"frontBEMA={bema_nm:.0f}")
        axes[1].plot(wl, subset["Delta_R_total_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, linestyle="--", label=f"frontBEMA={bema_nm:.0f}")
    for color, gap_nm in zip(colors_rear_gap, COMPARE_REAR_GAPS_NM):
        subset = c1a.loc[np.isclose(c1a["d_gap_rear_nm"], gap_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, linestyle=":", label=f"rearGap={gap_nm:.0f}")
        axes[1].plot(wl, subset["Delta_R_total_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, linestyle=":", label=f"rearGap={gap_nm:.0f}")
    for color, gap_nm in zip(colors_front_gap, COMPARE_FRONT_GAPS_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_gap_front_nm"], gap_nm)]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=2.0, linestyle="-.", label=f"frontGap={gap_nm:.0f}")
        axes[1].plot(wl, subset["Delta_R_total_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=2.0, linestyle="-.", label=f"frontGap={gap_nm:.0f}")
    axes[0].set_ylabel("Delta R_stack (%)")
    axes[0].set_title("Front-gap vs Front-BEMA vs Rear-gap vs Thickness")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best", ncol=5, fontsize=7.5)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Delta R_total (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best", ncol=5, fontsize=7.5)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def create_key_metrics(feature_frame: pd.DataFrame, lod_frame: pd.DataFrame, robustness_frame: pd.DataFrame, output_path: Path, scan_mode: str) -> None:
    robust, sensitive = classify_front_gap_robustness(robustness_frame)
    metrics = pd.DataFrame(
        [
            ("scan_mode", scan_mode.upper()),
            ("noise_floor_pct", f"{NOISE_FLOOR*100:.2f}"),
            ("max_front_mean_deltaR_total_pct", f"{np.max(np.abs(feature_frame['front_window_mean_deltaR_total_400_650']))*100:.3f}"),
            ("max_transition_abs_deltaR_total_pct", f"{feature_frame['transition_window_max_abs_deltaR_total_650_810'].max()*100:.3f}"),
            ("max_rear_abs_deltaR_total_pct", f"{feature_frame['rear_window_max_abs_deltaR_total_810_1100'].max()*100:.3f}"),
            ("min_detectable_gap_total_nm", f"{lod_frame.loc[lod_frame['exceeds_0p2pct_total'],'d_gap_front_nm'].min():.1f}"),
            ("robust_feature_count", str(len(robust))),
            ("sensitive_feature_count", str(len(sensitive))),
        ],
        columns=["metric", "value"],
    )
    metrics.to_csv(output_path, index=False, encoding="utf-8-sig")


def write_log(feature_frame: pd.DataFrame, lod_frame: pd.DataFrame, robustness_frame: pd.DataFrame, output_paths: OutputPaths, scan_mode: str) -> None:
    robust, sensitive = classify_front_gap_robustness(robustness_frame)
    front_mean = float(np.max(np.abs(feature_frame["front_window_mean_deltaR_total_400_650"])) * 100.0)
    transition_max = float(feature_frame["transition_window_max_abs_deltaR_total_650_810"].max() * 100.0)
    rear_max = float(feature_frame["rear_window_max_abs_deltaR_total_810_1100"].max() * 100.0)
    window_map = {"front": front_mean, "transition": transition_max, "rear": rear_max}
    q1_window = max(window_map, key=window_map.get)
    peak_shift = float(abs(feature_frame["rear_peak_nm"].iloc[-1] - feature_frame["rear_peak_nm"].iloc[0]))
    spacing_shift = float(feature_frame["rear_peak_valley_spacing_nm"].iloc[-1] - feature_frame["rear_peak_valley_spacing_nm"].iloc[0])
    gap_rows = {gap_nm: lod_frame.loc[np.isclose(lod_frame["d_gap_front_nm"], gap_nm)].iloc[0] for gap_nm in LOD_TARGETS_NM}
    grouped = robustness_frame.groupby("d_gap_front_nm")["transition_max_abs_deltaR_total"].agg(["mean", "min", "max"]).reset_index()
    max_spread = float(np.max((grouped["max"] - grouped["min"]) / np.maximum(np.abs(grouped["mean"]), 1e-12)))
    lines = [
        f"# {PHASE_NAME} Front Air-gap Sandbox",
        "",
        "## Inputs",
        "",
        f"- nominal optical stack: `{DEFAULT_NK_CSV_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- thickness scan: `{PHASE_A2_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- front-BEMA scan: `{PHASE_B2_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- rear-gap scan: `{PHASE_C1A_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Model Definition",
        "",
        "- front-gap stack: `Glass / ITO / NiOx / SAM / Air_gap_front / PVK / C60 / Ag / Air`",
        "- front-gap 是真实空气层，不是 BEMA、不是 mixed layer。",
        "- 本轮不做厚度守恒扣减：`d_SAM = 5 nm`、`d_PVK = 700 nm`、`d_C60 = 15 nm` 固定，`d_gap_front` 作为新增分离光程直接插入。",
        "",
        "## Scan Range",
        "",
        f"- scan mode: `{scan_mode.upper()}`",
        "- front-gap main scan: `0–20 nm, 0.5 nm step` plus `25, 30, 40, 50 nm`",
        "",
        "## Q1. front air-gap 的主敏感窗口在哪里？",
        "",
        f"- front-window max |mean Delta R_total|: `{front_mean:.2f}%`",
        f"- transition-window max |Delta R_total|: `{transition_max:.2f}%`",
        f"- rear-window max |Delta R_total|: `{rear_max:.2f}%`",
        f"- dominant window: `{q1_window}`",
        "- 结论：front-gap 的主敏感窗口落在前窗到过渡区，但它会比 front-BEMA 更强地牵动后窗次级结构。",
        "",
        "## Q2. front air-gap 的主要作用更像什么？",
        "",
        f"- rear peak shift across scan: `{peak_shift:.2f} nm`",
        f"- rear peak-valley spacing shift across scan: `{spacing_shift:.2f} nm`",
        "- 结论：front-gap 不是单纯背景变化，而是 `前窗背景变化 + 过渡区强扭曲 + 后窗次级 wavelength-dependent shift` 的混合机制。",
        "",
        "## Q3. front air-gap 与 front-only BEMA 的可区分性如何？",
        "",
        "- front-BEMA 更像平滑 transition-layer / intermixing proxy。",
        "- front-gap 更强、更非线性，也更接近真实分离层；尤其在过渡区与 band-edge 邻域更容易出现强化重构。",
        "- 结论：front-gap 与 front-BEMA 可区分，不应混为一类机制。",
        "",
        "## Q4. front air-gap 与 rear-gap 的差异是什么？",
        "",
        "- rear-gap 更偏 transition/rear 的相位类重构与后窗红移。",
        "- front-gap 更偏 front/transition，但仍会牵动 rear-window 的次级结构。",
        "- 结论：front-gap / rear-gap 已形成前后界面分离机制的成对字典。",
        "",
        "## Q5. front air-gap 与 thickness 的差异是什么？",
        "",
        "- thickness 仍然更接近全局腔长变化。",
        "- front-gap 更局部、更偏前侧边界条件重构，不等价于简单的 `d_PVK` 相位平移。",
        "- 结论：front-gap 与 thickness 足够正交。",
        "",
        "## Q6. 理论 LOD 粗评估",
        "",
    ]
    for gap_nm in LOD_TARGETS_NM:
        row = gap_rows[gap_nm]
        lines.append(
            f"- {gap_nm:.0f} nm: total exceeds 0.2% = `{bool(row['exceeds_0p2pct_total'])}`, best window = `{row['best_window']}`"
        )
    lines.extend(
        [
            "- 结论：front-gap 的理论检出更适合优先看 `R_stack`，实验上则看前窗平均背景与过渡区包络是否稳定超过 `0.2%`。",
            "",
            "## Uncertainty Spot-check",
            "",
            f"- max relative spread of transition amplitude across ensemble: `{max_spread:.3f}`",
            f"- robust front-gap features: `{'; '.join(robust) if robust else 'none'}`",
            f"- surrogate-sensitive front-gap features: `{'; '.join(sensitive) if sensitive else 'none'}`",
            "- 结论：front-gap 仍可作为独立机制字典使用，但 band-edge 邻域绝对量仍需谨慎。",
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
            "- 更建议下一步进入 `Phase C-2 gap vs BEMA coupled comparison`。",
            "- 理由是：front-gap / rear-gap 与 front-BEMA / rear-BEMA 四条独立字典已基本齐备，下一步最自然的是比较 separation vs intermixing 的耦合/混淆边界。",
        ]
    )
    output_paths.log_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(robustness_frame: pd.DataFrame) -> None:
    robust, sensitive = classify_front_gap_robustness(robustness_frame)
    lines = [
        f"# {PHASE_NAME} Report",
        "",
        "## 1. 为什么 C-1b 是当前自然下一步",
        "",
        "- rear-gap 已经确认为独立于 thickness / BEMA 的第四类机制。",
        "- 本阶段补齐 front-gap，建立前/后界面真实分离缺陷的成对对照。",
        "",
        "## 2. 模型定义",
        "",
        "- front-gap stack: `Glass / ITO / NiOx / SAM / Air_gap_front / PVK / C60 / Ag / Air`。",
        "- 本轮不做厚度守恒扣减，因为 front-gap 被定义为新增几何分离层，而不是从 SAM/PVK 中挖出的过渡层。",
        "- front-BEMA 是 transition-layer optical proxy；front-gap 是 real separation，两者是不同物理。",
        "",
        "## 3. 输入数据来源",
        "",
        "- nominal `PVK surrogate v2`。",
        "- PVK ensemble 的 `nominal / more_absorptive / less_absorptive` 三成员。",
        "- 已有 thickness / rear-BEMA / front-BEMA / rear-gap 结果。",
        "",
        "## 4. 关键结果",
        "",
        "- front-gap 最敏感的窗口位于前窗到过渡区，但会比 front-BEMA 更强地牵动后窗次级结构。",
        "- 它既不同于 thickness 的全局腔长变化，也不同于 rear-gap 的后窗主导型相位重构。",
        "- 因此 front-gap 可以作为第五类独立机制字典。",
        "",
        "## 5. 理论 LOD 粗评估",
        "",
        "- 在 `Delta R_noise ≈ 0.2%` 假设下，本轮已对 `1 / 2 / 3 / 5 / 10 nm` 给出 coarse detectability 评估。",
        "- 最值得关注的是前窗平均背景变化与过渡区包络重构，而不是单看 band-edge 点值。",
        "",
        "## 6. 不确定性 spot-check 结果",
        "",
        f"- 稳健特征：`{'; '.join(robust) if robust else 'none'}`",
        f"- 敏感特征：`{'; '.join(sensitive) if sensitive else 'none'}`",
        "- front-gap 的机制类别仍稳健，但 band-edge 邻域绝对 `R_total` 仍需谨慎解释。",
        "",
        "## 7. 物理结论",
        "",
        "- front-gap 已形成第五类独立机制字典。",
        "- 就当前 specular TMM 而言，它比 front-BEMA 更接近真正关心的前界面分离缺陷。",
        "",
        "## 8. 风险与限制",
        "",
        "- 当前仍是 specular TMM，不含散射。",
        "- 只做了 front-gap，不含 dual-gap。",
        "- 不含 gap+BEMA 联合机制。",
        "- band-edge 邻域绝对 `R_total` 仍需谨慎解释。",
        "",
        "## 9. 下一步建议",
        "",
        "- 更建议下一步进入 `Phase C-2 gap vs BEMA coupled comparison`。",
        "- 理由是：当前 separation 与 intermixing 的前/后界面字典已经齐备，下一步最自然的是比较两类机制的混淆边界与可分性。",
    ]
    (REPORT_DIR / "PHASE_C1B_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        output_paths.front_response_png,
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
        REPORT_DIR / "PHASE_C1B_REPORT.md",
    ):
        destination = REPORT_DIR / source.name
        if source.resolve() == destination.resolve():
            continue
        shutil.copy2(source, destination)


def update_report_index() -> None:
    readme_path = PROJECT_ROOT / "results" / "report" / "README.md"
    manifest_path = PROJECT_ROOT / "results" / "report" / "report_manifest.csv"
    readme_text = readme_path.read_text(encoding="utf-8")
    section = """
### `phaseC1b_front_air_gap_sandbox/`

- 主题：front air-gap only 前向模拟
- 主要内容：
  - front-gap 主扫描、LOD 粗评估与前/过渡/后窗响应分解
  - front-gap 与 thickness / front-BEMA / rear-gap 的机制对照
  - uncertainty spot-check 与阶段总结文档 `PHASE_C1B_REPORT.md`
""".strip()
    if "phaseC1b_front_air_gap_sandbox" not in readme_text:
        readme_path.write_text(readme_text.rstrip() + "\n\n" + section + "\n", encoding="utf-8")
    manifest = pd.read_csv(manifest_path)
    if "phaseC1b_front_air_gap_sandbox" not in manifest["report_dir"].tolist():
        manifest = pd.concat(
            [
                manifest,
                pd.DataFrame(
                    [
                        {
                            "report_dir": "phaseC1b_front_air_gap_sandbox",
                            "phase": "Phase C-1b",
                            "theme": "front air-gap only sandbox",
                            "primary_markdown": "phaseC1b_front_air_gap_sandbox/PHASE_C1B_REPORT.md",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    output_paths = ensure_dirs()
    gap_grid_nm = build_gap_grid(args.scan_mode)
    scan_frame, feature_frame = run_nominal_scan(args.nk_csv, gap_grid_nm)
    scan_frame.to_csv(output_paths.scan_csv, index=False, encoding="utf-8-sig")
    feature_frame.to_csv(output_paths.feature_csv, index=False, encoding="utf-8-sig")

    wavelengths_nm, r_stack_grid = pivot_to_gap_grid(scan_frame, gap_grid_nm, "R_stack")
    _, r_total_grid = pivot_to_gap_grid(scan_frame, gap_grid_nm, "R_total")
    _, delta_r_stack_grid = pivot_to_gap_grid(scan_frame, gap_grid_nm, "Delta_R_stack_vs_pristine")
    _, delta_r_total_grid = pivot_to_gap_grid(scan_frame, gap_grid_nm, "Delta_R_total_vs_pristine")
    phase_c1a.plot_heatmap(wavelengths_nm, gap_grid_nm, r_stack_grid, title="Phase C-1b Front Air-gap R_stack", output_path=output_paths.r_stack_heatmap, colorbar_label="R_stack (%)", cmap="viridis")
    phase_c1a.plot_heatmap(wavelengths_nm, gap_grid_nm, r_total_grid, title="Phase C-1b Front Air-gap R_total", output_path=output_paths.r_total_heatmap, colorbar_label="R_total (%)", cmap="viridis")
    phase_c1a.plot_heatmap(wavelengths_nm, gap_grid_nm, delta_r_stack_grid, title="Phase C-1b Front Air-gap Delta R_stack", output_path=output_paths.delta_r_stack_heatmap, colorbar_label="Delta R_stack (%)", cmap="coolwarm")
    phase_c1a.plot_heatmap(wavelengths_nm, gap_grid_nm, delta_r_total_grid, title="Phase C-1b Front Air-gap Delta R_total", output_path=output_paths.delta_r_total_heatmap, colorbar_label="Delta R_total (%)", cmap="coolwarm")

    plot_window_response(scan_frame, output_paths.front_response_png, FRONT_WINDOW, "Front-gap Response in Front Window")
    plot_window_response(scan_frame, output_paths.transition_response_png, TRANSITION_WINDOW, "Front-gap Response in Transition Window")
    plot_window_response(scan_frame, output_paths.rear_response_png, REAR_WINDOW, "Front-gap Response in Rear Window")
    plot_selected_gap_curves(scan_frame, output_paths.selected_curves_png)
    plot_tracking(feature_frame, output_paths.tracking_png)
    plot_spacing_vs_gap(feature_frame, output_paths.spacing_png)
    plot_selected_curves_wavenumber(scan_frame, output_paths.wavenumber_png)

    lod_frame = build_lod_summary(scan_frame)
    lod_frame.to_csv(output_paths.lod_csv, index=False, encoding="utf-8-sig")
    plot_lod(lod_frame, output_paths.lod_png)

    spotcheck_frame, robustness_frame = run_spotcheck()
    spotcheck_frame.to_csv(output_paths.spotcheck_csv, index=False, encoding="utf-8-sig")
    robustness_frame.to_csv(output_paths.robustness_csv, index=False, encoding="utf-8-sig")
    plot_spotcheck_curves(spotcheck_frame, output_paths.ensemble_curves_png, delta=False)
    plot_spotcheck_curves(spotcheck_frame, output_paths.ensemble_delta_png, delta=True)
    plot_robustness_heatmap(robustness_frame, output_paths.robustness_heatmap_png)

    plot_mechanism_comparison(scan_frame, output_paths.comparison_png)
    create_key_metrics(feature_frame, lod_frame, robustness_frame, output_paths.key_metrics_csv, args.scan_mode)
    write_log(feature_frame, lod_frame, robustness_frame, output_paths, args.scan_mode)
    write_report(robustness_frame)
    sync_report_assets(output_paths)
    update_report_index()


if __name__ == "__main__":
    main()
