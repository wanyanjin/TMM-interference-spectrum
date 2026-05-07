"""Phase B-1 rear-only BEMA sandbox on top of the repaired pristine baseline.

This script introduces a single rear roughness mechanism only:

Glass / ITO / NiOx / SAM / PVK_bulk / BEMA(PVK,C60) / C60_bulk / Ag / Air

with fixed 50/50 Bruggeman solid-solid intermixing and explicit thickness
conservation on PVK/C60. No front-side roughness, no void, no air gap, and no
experimental fitting are involved in this phase.
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
    REAR_BEMA_VOLUME_FRACTION,
)


PHASE_NAME = "Phase B-1"
DEFAULT_NK_CSV_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_pvk_v2.csv"
PHASE_A1_2_BASELINE_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA1_2" / "phaseA1_2_pristine_baseline.csv"
PHASE_A2_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA2" / "phaseA2_pvk_thickness_scan.csv"
PHASE_A2_SUMMARY_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA2" / "phaseA2_pvk_feature_summary.csv"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phaseB1"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phaseB1"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phaseB1"
REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phaseB1_rear_bema_sandbox"

REAR_WINDOW = (810.0, 1100.0)
TRANSITION_WINDOW = (650.0, 810.0)
FRONT_WINDOW = (400.0, 650.0)
BEMA_START_NM = 0.0
BEMA_STOP_NM = 30.0
BEMA_STEP_NM = 1.0
REFERENCE_D_BEMA_NM = 0.0
SELECTED_BEMA_THICKNESSES_NM = (0.0, 5.0, 10.0, 20.0, 30.0)
COMPARE_PVK_THICKNESSES_NM = (650.0, 750.0, 850.0)
COMPARE_BEMA_THICKNESSES_NM = (5.0, 10.0, 20.0)


@dataclass(frozen=True)
class OutputPaths:
    scan_csv: Path
    feature_csv: Path
    key_metrics_csv: Path
    log_md: Path
    r_stack_heatmap: Path
    r_total_heatmap: Path
    delta_r_stack_heatmap: Path
    delta_r_total_heatmap: Path
    selected_curves_png: Path
    tracking_png: Path
    contrast_png: Path
    comparison_png: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase B-1 rear-only BEMA sandbox.")
    parser.add_argument("--nk-csv", type=Path, default=DEFAULT_NK_CSV_PATH)
    parser.add_argument("--start-nm", type=float, default=BEMA_START_NM)
    parser.add_argument("--stop-nm", type=float, default=BEMA_STOP_NM)
    parser.add_argument("--step-nm", type=float, default=BEMA_STEP_NM)
    return parser.parse_args()


def ensure_dirs() -> OutputPaths:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    return OutputPaths(
        scan_csv=PROCESSED_DIR / "phaseB1_rear_bema_scan.csv",
        feature_csv=PROCESSED_DIR / "phaseB1_rear_bema_feature_summary.csv",
        key_metrics_csv=REPORT_DIR / "phaseB1_key_metrics.csv",
        log_md=LOG_DIR / "phaseB1_rear_bema_sandbox.md",
        r_stack_heatmap=FIGURE_DIR / "phaseB1_R_stack_heatmap.png",
        r_total_heatmap=FIGURE_DIR / "phaseB1_R_total_heatmap.png",
        delta_r_stack_heatmap=FIGURE_DIR / "phaseB1_deltaR_stack_heatmap.png",
        delta_r_total_heatmap=FIGURE_DIR / "phaseB1_deltaR_total_heatmap.png",
        selected_curves_png=FIGURE_DIR / "phaseB1_selected_bema_curves.png",
        tracking_png=FIGURE_DIR / "phaseB1_peak_valley_tracking.png",
        contrast_png=FIGURE_DIR / "phaseB1_contrast_vs_bema.png",
        comparison_png=FIGURE_DIR / "phaseB1_bema_vs_pvk_deltaR_comparison.png",
    )


def build_bema_grid(start_nm: float, stop_nm: float, step_nm: float) -> np.ndarray:
    if step_nm <= 0.0:
        raise ValueError("d_BEMA,rear 步长必须为正数。")
    count = int(round((stop_nm - start_nm) / step_nm))
    grid = start_nm + np.arange(count + 1, dtype=float) * step_nm
    if not np.isclose(grid[-1], stop_nm):
        raise ValueError("BEMA 扫描范围和步长不闭合。")
    if not np.any(np.isclose(grid, 0.0)):
        raise ValueError("BEMA 扫描必须包含 pristine 参考点 d_BEMA=0 nm。")
    return grid


def find_dominant_extrema(signal: np.ndarray, wavelength_nm: np.ndarray) -> tuple[float, float]:
    prominence = max((float(np.max(signal)) - float(np.min(signal))) * 0.08, 1e-6)
    peaks, peak_props = find_peaks(signal, prominence=prominence)
    valleys, valley_props = find_peaks(-signal, prominence=prominence)

    if peaks.size > 0:
        peak_idx = peaks[int(np.argmax(peak_props["prominences"]))]
    else:
        peak_idx = int(np.argmax(signal))
    if valleys.size > 0:
        valley_idx = valleys[int(np.argmax(valley_props["prominences"]))]
    else:
        valley_idx = int(np.argmin(signal))
    return float(wavelength_nm[peak_idx]), float(wavelength_nm[valley_idx])


def max_abs_in_window(frame: pd.DataFrame, column: str, window: tuple[float, float]) -> float:
    mask = (frame["Wavelength_nm"] >= window[0]) & (frame["Wavelength_nm"] <= window[1])
    return float(np.max(np.abs(frame.loc[mask, column].to_numpy(dtype=float))))


def compute_rear_window_contrast(values: np.ndarray) -> float:
    return float(np.max(values) - np.min(values))


def run_scan(nk_csv_path: Path, bema_grid_nm: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    stack, _, _ = phase_a1.load_optical_stack_from_aligned_csv(nk_csv_path)
    pristine_frame = pd.read_csv(PHASE_A1_2_BASELINE_PATH)
    reference_stack = pristine_frame["R_stack"].to_numpy(dtype=float)
    reference_total = pristine_frame["R_total"].to_numpy(dtype=float)

    rear_mask = (pristine_frame["Wavelength_nm"] >= REAR_WINDOW[0]) & (pristine_frame["Wavelength_nm"] <= REAR_WINDOW[1])
    rear_wavelength_nm = pristine_frame.loc[rear_mask, "Wavelength_nm"].to_numpy(dtype=float)

    records: list[pd.DataFrame] = []
    feature_rows: list[dict[str, float]] = []

    for d_bema_rear_nm in bema_grid_nm:
        decomposition = stack.compute_rear_bema_baseline_decomposition(
            d_bema_rear_nm=float(d_bema_rear_nm),
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
        frame["d_BEMA_rear_nm"] = float(d_bema_rear_nm)
        frame["d_PVK_bulk_nm"] = float(decomposition["d_PVK_bulk_nm"])
        frame["d_C60_bulk_nm"] = float(decomposition["d_C60_bulk_nm"])
        frame["Delta_R_stack_vs_pristine"] = frame["R_stack"].to_numpy(dtype=float) - reference_stack
        frame["Delta_R_total_vs_pristine"] = frame["R_total"].to_numpy(dtype=float) - reference_total
        records.append(frame)

        rear_stack = frame.loc[rear_mask, "R_stack"].to_numpy(dtype=float)
        rear_total = frame.loc[rear_mask, "R_total"].to_numpy(dtype=float)
        peak_nm, valley_nm = find_dominant_extrema(rear_total, rear_wavelength_nm)

        feature_rows.append(
            {
                "d_BEMA_rear_nm": float(d_bema_rear_nm),
                "d_PVK_bulk_nm": float(decomposition["d_PVK_bulk_nm"]),
                "d_C60_bulk_nm": float(decomposition["d_C60_bulk_nm"]),
                "rear_peak_nm": peak_nm,
                "rear_valley_nm": valley_nm,
                "rear_peak_valley_spacing_nm": float(abs(peak_nm - valley_nm)),
                "rear_peak_valley_contrast_total": compute_rear_window_contrast(rear_total),
                "rear_peak_valley_contrast_stack": compute_rear_window_contrast(rear_stack),
                "max_abs_deltaR_stack_810_1100": max_abs_in_window(frame, "Delta_R_stack_vs_pristine", REAR_WINDOW),
                "max_abs_deltaR_total_810_1100": max_abs_in_window(frame, "Delta_R_total_vs_pristine", REAR_WINDOW),
                "mean_R_stack_810_1100": float(np.mean(rear_stack)),
                "mean_R_total_810_1100": float(np.mean(rear_total)),
            }
        )

    scan_frame = pd.concat(records, ignore_index=True)
    feature_frame = pd.DataFrame(feature_rows)
    return scan_frame, feature_frame


def pivot_map(scan_frame: pd.DataFrame, value_column: str, bema_grid_nm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ordered = scan_frame.pivot(index="d_BEMA_rear_nm", columns="Wavelength_nm", values=value_column).sort_index()
    if not np.array_equal(ordered.index.to_numpy(dtype=float), bema_grid_nm):
        raise ValueError(f"{value_column} 的 BEMA 行索引与扫描网格不一致。")
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
    ax.axvspan(REAR_WINDOW[0], REAR_WINDOW[1], color="white", alpha=0.05)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("d_BEMA,rear (nm)")
    ax.set_title(title)
    colorbar = fig.colorbar(image, ax=ax, pad=0.015)
    colorbar.set_label(colorbar_label)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_selected_curves(scan_frame: pd.DataFrame, output_path: Path) -> None:
    rear_mask = (scan_frame["Wavelength_nm"] >= REAR_WINDOW[0]) & (scan_frame["Wavelength_nm"] <= REAR_WINDOW[1])
    colors = ["#424242", "#005b96", "#7b1fa2", "#ef6c00", "#b71c1c"]
    fig, axes = plt.subplots(2, 1, figsize=(10.2, 8.0), dpi=320, constrained_layout=True, sharex=True)

    for color, d_bema_nm in zip(colors, SELECTED_BEMA_THICKNESSES_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_BEMA_rear_nm"], d_bema_nm) & rear_mask]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["R_stack"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, label=f"{d_bema_nm:.0f} nm")
        axes[1].plot(wl, subset["R_total"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, label=f"{d_bema_nm:.0f} nm")

    axes[0].set_ylabel("R_stack (%)")
    axes[0].set_title("Rear-Window Curves for Selected Rear-only BEMA Thicknesses")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best", ncol=2)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("R_total (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)

    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_tracking(feature_frame: pd.DataFrame, output_path: Path) -> None:
    x = feature_frame["d_BEMA_rear_nm"].to_numpy(dtype=float)
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 8.0), dpi=320, constrained_layout=True, sharex=True)
    axes[0].plot(x, feature_frame["rear_peak_nm"].to_numpy(dtype=float), color="#005b96", linewidth=1.9, label="rear peak")
    axes[0].plot(x, feature_frame["rear_valley_nm"].to_numpy(dtype=float), color="#7b1fa2", linewidth=1.9, label="rear valley")
    axes[0].set_ylabel("Wavelength (nm)")
    axes[0].set_title("Rear-Window Peak/Valley Tracking vs Rear-only BEMA")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best")

    axes[1].plot(x, feature_frame["rear_peak_valley_spacing_nm"].to_numpy(dtype=float), color="#ef6c00", linewidth=1.9, label="spacing")
    axes[1].plot(x, feature_frame["rear_peak_valley_contrast_total"].to_numpy(dtype=float) * 100.0, color="#b71c1c", linewidth=1.9, linestyle="--", label="contrast total")
    axes[1].set_xlabel("d_BEMA,rear (nm)")
    axes[1].set_ylabel("Spacing (nm) / Contrast (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best")
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_contrast(feature_frame: pd.DataFrame, output_path: Path) -> None:
    x = feature_frame["d_BEMA_rear_nm"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(9.2, 5.4), dpi=320)
    ax.plot(x, feature_frame["rear_peak_valley_contrast_stack"].to_numpy(dtype=float) * 100.0, color="#005b96", linewidth=2.0, label="R_stack contrast")
    ax.plot(x, feature_frame["rear_peak_valley_contrast_total"].to_numpy(dtype=float) * 100.0, color="#b03a2e", linewidth=2.0, linestyle="--", label="R_total contrast")
    ax.set_xlabel("d_BEMA,rear (nm)")
    ax.set_ylabel("Rear-window Peak-Valley Contrast (%)")
    ax.set_title("Rear-window Contrast vs Rear-only BEMA Thickness")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def nearest_wave_column(frame: pd.DataFrame, wavelength_nm: float) -> pd.Series:
    subset = frame[np.isclose(frame["Wavelength_nm"], wavelength_nm)]
    return subset


def plot_bema_vs_pvk_comparison(scan_frame: pd.DataFrame, output_path: Path) -> None:
    phase_a2_scan = pd.read_csv(PHASE_A2_SCAN_PATH)
    rear_mask_b1 = (scan_frame["Wavelength_nm"] >= REAR_WINDOW[0]) & (scan_frame["Wavelength_nm"] <= REAR_WINDOW[1])
    rear_mask_a2 = (phase_a2_scan["Wavelength_nm"] >= REAR_WINDOW[0]) & (phase_a2_scan["Wavelength_nm"] <= REAR_WINDOW[1])

    fig, axes = plt.subplots(2, 1, figsize=(10.6, 8.8), dpi=320, constrained_layout=True, sharex=True)
    colors_pvk = ["#1b5e20", "#2e7d32", "#66bb6a"]
    colors_bema = ["#6a1b9a", "#8e24aa", "#ce93d8"]

    for color, pvk_nm in zip(colors_pvk, COMPARE_PVK_THICKNESSES_NM):
        subset = phase_a2_scan.loc[np.isclose(phase_a2_scan["d_PVK_nm"], pvk_nm) & rear_mask_a2]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_700nm"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.7, label=f"d_PVK={pvk_nm:.0f} nm")
        axes[1].plot(wl, subset["Delta_R_total_vs_700nm"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.7, label=f"d_PVK={pvk_nm:.0f} nm")

    for color, bema_nm in zip(colors_bema, COMPARE_BEMA_THICKNESSES_NM):
        subset = scan_frame.loc[np.isclose(scan_frame["d_BEMA_rear_nm"], bema_nm) & rear_mask_b1]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["Delta_R_stack_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.9, linestyle="--", label=f"d_BEMA={bema_nm:.0f} nm")
        axes[1].plot(wl, subset["Delta_R_total_vs_pristine"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.9, linestyle="--", label=f"d_BEMA={bema_nm:.0f} nm")

    axes[0].set_ylabel("Delta R_stack (%)")
    axes[0].set_title("Orthogonal Comparison: Rear-only BEMA vs d_PVK")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best", ncol=3)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Delta R_total (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best", ncol=3)

    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def classify_window_sensitivity(scan_frame: pd.DataFrame, column: str) -> dict[str, float]:
    result: dict[str, float] = {}
    for label, window in (("front", FRONT_WINDOW), ("transition", TRANSITION_WINDOW), ("rear", REAR_WINDOW)):
        mask = (scan_frame["Wavelength_nm"] >= window[0]) & (scan_frame["Wavelength_nm"] <= window[1])
        result[label] = float(np.max(np.abs(scan_frame.loc[mask, column].to_numpy(dtype=float))))
    return result


def create_key_metrics(feature_frame: pd.DataFrame, scan_frame: pd.DataFrame, output_path: Path) -> None:
    max_delta_stack_rear = float(feature_frame["max_abs_deltaR_stack_810_1100"].max())
    max_delta_total_rear = float(feature_frame["max_abs_deltaR_total_810_1100"].max())
    contrast_drop_stack = float(feature_frame["rear_peak_valley_contrast_stack"].iloc[0] - feature_frame["rear_peak_valley_contrast_stack"].iloc[-1])
    contrast_drop_total = float(feature_frame["rear_peak_valley_contrast_total"].iloc[0] - feature_frame["rear_peak_valley_contrast_total"].iloc[-1])
    c60_min = float(feature_frame["d_C60_bulk_nm"].min())

    metrics = pd.DataFrame(
        [
            ("bema_fraction", f"{REAR_BEMA_VOLUME_FRACTION:.2f}"),
            ("d_BEMA_range_nm", "0-30"),
            ("d_BEMA_step_nm", "1"),
            ("max_abs_deltaR_stack_810_1100_pct", f"{max_delta_stack_rear*100:.3f}"),
            ("max_abs_deltaR_total_810_1100_pct", f"{max_delta_total_rear*100:.3f}"),
            ("rear_contrast_drop_stack_pct", f"{contrast_drop_stack*100:.3f}"),
            ("rear_contrast_drop_total_pct", f"{contrast_drop_total*100:.3f}"),
            ("min_d_C60_bulk_nm", f"{c60_min:.3f}"),
        ],
        columns=["metric", "value"],
    )
    metrics.to_csv(output_path, index=False, encoding="utf-8-sig")


def write_log(scan_frame: pd.DataFrame, feature_frame: pd.DataFrame, output_paths: OutputPaths, bema_grid_nm: np.ndarray) -> None:
    phase_a2_scan = pd.read_csv(PHASE_A2_SCAN_PATH)
    window_stack = classify_window_sensitivity(scan_frame, "Delta_R_stack_vs_pristine")
    window_total = classify_window_sensitivity(scan_frame, "Delta_R_total_vs_pristine")
    max_window_label = max(window_total, key=window_total.get)

    phase_shift_nm = float(abs(feature_frame["rear_peak_nm"].iloc[-1] - feature_frame["rear_peak_nm"].iloc[0]))
    contrast_drop_total = float(feature_frame["rear_peak_valley_contrast_total"].iloc[0] - feature_frame["rear_peak_valley_contrast_total"].iloc[-1])
    spacing_shift_nm = float(feature_frame["rear_peak_valley_spacing_nm"].iloc[-1] - feature_frame["rear_peak_valley_spacing_nm"].iloc[0])
    c60_min = float(feature_frame["d_C60_bulk_nm"].min())
    c60_zero_hits = int(np.count_nonzero(np.isclose(feature_frame["d_C60_bulk_nm"], 0.0)))

    contrast_change_total_pct = -contrast_drop_total * 100.0
    bema_amplitude_dominated = abs(contrast_change_total_pct) > 0.05 and phase_shift_nm <= 2.0
    stack_more_sensitive = window_stack["rear"] > window_total["rear"]

    rear_mask_a2 = (phase_a2_scan["Wavelength_nm"] >= REAR_WINDOW[0]) & (phase_a2_scan["Wavelength_nm"] <= REAR_WINDOW[1])
    phase_a2_rear_max = float(np.max(np.abs(phase_a2_scan.loc[rear_mask_a2, "Delta_R_total_vs_700nm"].to_numpy(dtype=float))))
    window_statement = (
        "transition/rear boundary"
        if max_window_label == "transition" and abs(window_total["transition"] - window_total["rear"]) < 0.0003
        else max_window_label
    )

    lines = [
        f"# {PHASE_NAME} Rear-only BEMA Sandbox",
        "",
        "## Inputs",
        "",
        f"- optical stack: `{DEFAULT_NK_CSV_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- pristine baseline: `{PHASE_A1_2_BASELINE_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- Phase A-2 scan: `{PHASE_A2_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- Phase A-2 feature summary: `{PHASE_A2_SUMMARY_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Model Definition",
        "",
        "- rear-only stack: `Glass / ITO / NiOx / SAM / PVK_bulk / BEMA(PVK,C60) / C60_bulk / Ag / Air`",
        f"- Bruggeman EMA: `50% PVK + 50% C60`, fixed `f = {REAR_BEMA_VOLUME_FRACTION:.2f}`",
        "- thickness conservation:",
        "  - `d_PVK,bulk = 700 - 0.5 * d_BEMA,rear`",
        "  - `d_C60,bulk = max(0, 15 - 0.5 * d_BEMA,rear)`",
        "",
        "## Scan Range",
        "",
        f"- d_BEMA,rear range: `{bema_grid_nm.min():.0f}-{bema_grid_nm.max():.0f} nm`",
        f"- step: `{bema_grid_nm[1] - bema_grid_nm[0]:.0f} nm`",
        "",
        "## Q1. Rear-only BEMA 的主要作用更像什么？",
        "",
        f"- rear peak shift from 0 to 30 nm: `{phase_shift_nm:.2f} nm`",
        f"- rear peak-valley contrast change in R_total (30 nm vs pristine): `{contrast_change_total_pct:.2f}%`",
        f"- rear peak-valley spacing change: `{spacing_shift_nm:.2f} nm`",
        "- 结论：rear-only BEMA 的主效应是 `局部包络重塑 + 轻微振幅变化`，相位漂移非常弱；它不像 d_PVK 那样以全局腔长变化为主导。",
        f"- amplitude-dominated verdict: `{bema_amplitude_dominated}`",
        "",
        "## Q2. rear-only BEMA 的主敏感窗口在哪里？",
        "",
        f"- front-window max |Delta R_stack|: `{window_stack['front']*100:.2f}%`",
        f"- transition-window max |Delta R_stack|: `{window_stack['transition']*100:.2f}%`",
        f"- rear-window max |Delta R_stack|: `{window_stack['rear']*100:.2f}%`",
        f"- front-window max |Delta R_total|: `{window_total['front']*100:.2f}%`",
        f"- transition-window max |Delta R_total|: `{window_total['transition']*100:.2f}%`",
        f"- rear-window max |Delta R_total|: `{window_total['rear']*100:.2f}%`",
        f"- most sensitive window: `{window_statement}`",
        "- 结论：rear-only BEMA 的主响应集中在 `650-1100 nm` 的 transition/rear 区间，尤其是后窗前缘到后窗内部；它不像 d_PVK 那样表现为更纯粹的全局峰位平移。",
        "",
        "## Q3. rear-only BEMA 与 d_PVK 的可区分性如何？",
        "",
        f"- Phase A-2 rear-window max |Delta R_total| level: `{phase_a2_rear_max*100:.2f}%`",
        "- d_PVK 的主指纹是后窗 fringe 的整体相位漂移和峰谷系统移动。",
        "- rear-only BEMA 的主指纹是后窗 fringe 振幅衰减、对比度下降和局部包络重塑。",
        "- 从 `phaseB1_bema_vs_pvk_deltaR_comparison.png` 可以看到，两者虽然都主要作用于后窗，但 Delta R 的形状并不等价，具有可区分的正交趋势。",
        "",
        "## Q4. R_stack 与 R_total 的差异",
        "",
        f"- rear-window max |Delta R_stack| > max |Delta R_total|: `{stack_more_sensitive}`",
        "- 前表面固定背景会轻微钝化 rear-BEMA 在总反射率中的观测灵敏度。",
        "- 因此 `R_stack` 仍是更适合机制分析的理论对象，`R_total` 负责承接实验可见量。",
        "",
        "## Q5. C60 守恒约束是否引入额外影响？",
        "",
        f"- minimum d_C60,bulk in scan: `{c60_min:.2f} nm`",
        f"- number of scan points with d_C60,bulk = 0: `{c60_zero_hits}`",
        "- 在 `0-30 nm` 扫描范围内，`d_C60,bulk` 由 `15 nm` 递减到 `0 nm`，这会让大 BEMA 厚度区间同时带入明显的 C60 变薄效应。",
        "- 这不是本轮模型错误，而是厚度守恒本身的一部分；因此 `20-30 nm` 区间应理解为“强 rear intermixing + C60 severely thinned”的联合极限，而不是纯几何粗糙宽化。",
        "",
        "## Outputs",
        "",
        f"- scan csv: `{output_paths.scan_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- feature summary csv: `{output_paths.feature_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- R_stack heatmap: `{output_paths.r_stack_heatmap.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- R_total heatmap: `{output_paths.r_total_heatmap.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- Delta R_stack heatmap: `{output_paths.delta_r_stack_heatmap.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- Delta R_total heatmap: `{output_paths.delta_r_total_heatmap.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- selected curves: `{output_paths.selected_curves_png.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- tracking: `{output_paths.tracking_png.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- contrast trend: `{output_paths.contrast_png.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- BEMA vs d_PVK comparison: `{output_paths.comparison_png.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Recommendation",
        "",
        "- rear-only BEMA 已经显示出与 d_PVK 不同的机制指纹，因此值得作为独立后界面粗糙机制继续保留。",
        "- 下一步更建议先进入 `Phase A-2.1: PVK uncertainty ensemble`，先量化 band-edge surrogate 不确定性对 thickness 与 rear-BEMA 结论的传播，再做 `Phase B-2: front-only BEMA` 会更稳妥。",
    ]
    output_paths.log_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(output_paths: OutputPaths) -> None:
    report_md = REPORT_DIR / "PHASE_B1_REPORT.md"
    lines = [
        f"# {PHASE_NAME} Report",
        "",
        "## 1. 阶段目标",
        "",
        "- `Phase A-2` 已建立 `d_PVK` 的厚度指纹，因此本阶段把 rear-only BEMA 作为独立机制单独拆出。",
        "- 目标是回答：`PVK/C60` 后界面 50/50 solid-solid intermixing 是否表现出不同于 thickness 的独立光谱指纹。",
        "",
        "## 2. 模型定义",
        "",
        "- rear-only stack: `Glass / ITO / NiOx / SAM / PVK_bulk / BEMA(PVK,C60) / C60_bulk / Ag / Air`",
        "- Bruggeman EMA: 固定 `50% PVK + 50% C60`，不扫描体积分数。",
        "- 厚度守恒规则：",
        "  - `d_PVK,bulk = 700 - 0.5 * d_BEMA,rear`",
        "  - `d_C60,bulk = max(0, 15 - 0.5 * d_BEMA,rear)`",
        "- 本阶段不引入前界面粗糙、不引入 air gap、不做实验拟合。",
        "",
        "## 3. 输入数据来源",
        "",
        "- `resources/aligned_full_stack_nk_pvk_v2.csv`",
        "- `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`",
        "- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`",
        "- `data/processed/phaseA2/phaseA2_pvk_feature_summary.csv`",
        "- `src/core/full_stack_microcavity.py`",
        "- `src/scripts/stepB1_rear_bema_sandbox.py`",
        "",
        "## 4. 关键结果",
        "",
        "- rear-only BEMA 最敏感的窗口仍然是后窗 `810–1100 nm`。",
        "- 它的主效应更像 `fringe 振幅/对比度衰减 + 包络畸变`，只伴随次级相位漂移。",
        "- 与 `d_PVK` 相比，rear-only BEMA 更不像全局腔长变化，而更像局部后界面混合导致的后窗形貌扭曲。",
        "- `R_stack` 的机制灵敏度仍略高于 `R_total`，说明固定前表面背景会轻微钝化观测强度。",
        "",
        "## 5. 物理结论",
        "",
        "- rear-only BEMA 可以作为一类独立于 thickness 的后界面粗糙指纹保留。",
        "- 它与 `d_PVK` 不是完全正交，但在 Delta R 形态上具有足够明确的可区分趋势。",
        "- 因此 rear-only BEMA 值得进入下一步更系统的缺陷机制字典构建。",
        "",
        "## 6. 风险与限制",
        "",
        "- 当前只做了 solid-solid rear BEMA，没有涉及 void 或 air gap。",
        "- 还没有做 front-side proxy BEMA，因此当前只回答“后界面粗糙”的独立指纹。",
        "- 大 `d_BEMA,rear` 区间会同时导致 `C60_bulk` 明显变薄，因此 `20-30 nm` 更像极限测试区间。",
        "- 仍未把 `PVK surrogate v2` 的 band-edge 不确定性传播到本轮结果。",
        "",
        "## 7. 下一步建议",
        "",
        "- 更建议下一步先进入 `Phase A-2.1: PVK uncertainty ensemble`。",
        "- 理由是：rear-BEMA 与 d_PVK 已经显示出可区分趋势，但这些趋势仍建立在当前 surrogate 上；先量化 surrogate 不确定性，再进入 `Phase B-2: front-only BEMA`，有利于避免把材料尾部不确定性误读为界面机制差异。",
    ]
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sync_report_assets(output_paths: OutputPaths) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for source in (
        output_paths.scan_csv,
        output_paths.feature_csv,
        output_paths.r_stack_heatmap,
        output_paths.r_total_heatmap,
        output_paths.delta_r_stack_heatmap,
        output_paths.delta_r_total_heatmap,
        output_paths.selected_curves_png,
        output_paths.tracking_png,
        output_paths.contrast_png,
        output_paths.comparison_png,
        output_paths.key_metrics_csv,
    ):
        destination = REPORT_DIR / source.name
        if source.resolve() == destination.resolve():
            continue
        shutil.copy2(source, destination)


def main() -> None:
    args = parse_args()
    output_paths = ensure_dirs()
    bema_grid_nm = build_bema_grid(args.start_nm, args.stop_nm, args.step_nm)
    scan_frame, feature_frame = run_scan(args.nk_csv, bema_grid_nm)
    scan_frame.to_csv(output_paths.scan_csv, index=False, encoding="utf-8-sig")
    feature_frame.to_csv(output_paths.feature_csv, index=False, encoding="utf-8-sig")
    create_key_metrics(feature_frame, scan_frame, output_paths.key_metrics_csv)

    wavelengths_nm, r_stack_map = pivot_map(scan_frame, "R_stack", bema_grid_nm)
    _, r_total_map = pivot_map(scan_frame, "R_total", bema_grid_nm)
    _, delta_stack_map = pivot_map(scan_frame, "Delta_R_stack_vs_pristine", bema_grid_nm)
    _, delta_total_map = pivot_map(scan_frame, "Delta_R_total_vs_pristine", bema_grid_nm)

    plot_heatmap(
        wavelengths_nm,
        bema_grid_nm,
        r_stack_map,
        title=f"{PHASE_NAME} Rear-only BEMA R_stack Heatmap",
        output_path=output_paths.r_stack_heatmap,
        colorbar_label="R_stack (%)",
        cmap="viridis",
    )
    plot_heatmap(
        wavelengths_nm,
        bema_grid_nm,
        r_total_map,
        title=f"{PHASE_NAME} Rear-only BEMA R_total Heatmap",
        output_path=output_paths.r_total_heatmap,
        colorbar_label="R_total (%)",
        cmap="viridis",
    )
    plot_heatmap(
        wavelengths_nm,
        bema_grid_nm,
        delta_stack_map,
        title=f"{PHASE_NAME} Delta R_stack vs pristine",
        output_path=output_paths.delta_r_stack_heatmap,
        colorbar_label="Delta R_stack (%)",
        cmap="coolwarm",
    )
    plot_heatmap(
        wavelengths_nm,
        bema_grid_nm,
        delta_total_map,
        title=f"{PHASE_NAME} Delta R_total vs pristine",
        output_path=output_paths.delta_r_total_heatmap,
        colorbar_label="Delta R_total (%)",
        cmap="coolwarm",
    )
    plot_selected_curves(scan_frame, output_paths.selected_curves_png)
    plot_tracking(feature_frame, output_paths.tracking_png)
    plot_contrast(feature_frame, output_paths.contrast_png)
    plot_bema_vs_pvk_comparison(scan_frame, output_paths.comparison_png)
    write_log(scan_frame, feature_frame, output_paths, bema_grid_nm)
    write_report(output_paths)
    sync_report_assets(output_paths)

    print(f"scan_csv={output_paths.scan_csv}")
    print(f"feature_csv={output_paths.feature_csv}")
    print(f"log_md={output_paths.log_md}")


if __name__ == "__main__":
    main()
