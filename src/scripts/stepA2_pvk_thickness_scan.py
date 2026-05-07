"""Phase A-2 PVK thickness scan on top of the repaired pristine baseline.

This script keeps the Phase A-1.2 geometry and repaired PVK surrogate fixed
while scanning the PVK thickness to map how the rear-window microcavity
response evolves. The optical constants still trace back to [LIT-0001] through
the project's digitized/stitch/rebuild workflow; this step only changes
`d_PVK`, not the material table itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import sys

import matplotlib
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import spearmanr

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (str(PROJECT_ROOT / "src"), str(SCRIPT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import stepA1_pristine_baseline as phase_a1  # noqa: E402


PHASE_NAME = "Phase A-2"
DEFAULT_NK_CSV_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_pvk_v2.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phaseA2"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phaseA2"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phaseA2"
REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phaseA2_pvk_thickness_scan"

REAR_WINDOW = (810.0, 1100.0)
FRONT_WINDOW = (400.0, 650.0)
SCAN_START_NM = 500.0
SCAN_STOP_NM = 900.0
SCAN_STEP_NM = 5.0
REFERENCE_THICKNESS_NM = 700.0
REPRESENTATIVE_WAVELENGTHS_NM = (850.0, 900.0, 950.0, 1000.0, 1050.0)
SELECTED_THICKNESSES_NM = (500.0, 600.0, 700.0, 800.0, 900.0)


@dataclass(frozen=True)
class ScanOutputs:
    scan_csv: Path
    summary_csv: Path
    log_path: Path
    r_stack_heatmap: Path
    r_total_heatmap: Path
    delta_r_stack_heatmap: Path
    delta_r_total_heatmap: Path
    tracking_figure: Path
    selected_curves_figure: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase A-2 PVK thickness scan.")
    parser.add_argument("--nk-csv", type=Path, default=DEFAULT_NK_CSV_PATH)
    parser.add_argument("--start-nm", type=float, default=SCAN_START_NM)
    parser.add_argument("--stop-nm", type=float, default=SCAN_STOP_NM)
    parser.add_argument("--step-nm", type=float, default=SCAN_STEP_NM)
    return parser.parse_args()


def ensure_output_dirs() -> ScanOutputs:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    return ScanOutputs(
        scan_csv=PROCESSED_DIR / "phaseA2_pvk_thickness_scan.csv",
        summary_csv=PROCESSED_DIR / "phaseA2_pvk_feature_summary.csv",
        log_path=LOG_DIR / "phaseA2_pvk_thickness_scan.md",
        r_stack_heatmap=FIGURE_DIR / "phaseA2_R_stack_heatmap.png",
        r_total_heatmap=FIGURE_DIR / "phaseA2_R_total_heatmap.png",
        delta_r_stack_heatmap=FIGURE_DIR / "phaseA2_deltaR_stack_vs_700nm_heatmap.png",
        delta_r_total_heatmap=FIGURE_DIR / "phaseA2_deltaR_total_vs_700nm_heatmap.png",
        tracking_figure=FIGURE_DIR / "phaseA2_peak_valley_tracking.png",
        selected_curves_figure=FIGURE_DIR / "phaseA2_selected_thickness_curves.png",
    )


def build_thickness_grid(start_nm: float, stop_nm: float, step_nm: float) -> np.ndarray:
    if step_nm <= 0.0:
        raise ValueError("step_nm 必须为正数。")
    count = int(round((stop_nm - start_nm) / step_nm))
    grid = start_nm + np.arange(count + 1, dtype=float) * step_nm
    if not np.isclose(grid[-1], stop_nm):
        raise ValueError("厚度扫描网格未能精确落在 stop_nm，请检查范围与步长。")
    if not np.any(np.isclose(grid, REFERENCE_THICKNESS_NM)):
        raise ValueError("厚度扫描网格必须包含 700 nm 参考厚度。")
    return grid


def find_dominant_extrema(signal: np.ndarray, wavelength_nm: np.ndarray) -> tuple[float, float]:
    array = np.asarray(signal, dtype=float)
    wl = np.asarray(wavelength_nm, dtype=float)
    prominence = max((float(array.max()) - float(array.min())) * 0.08, 1e-6)

    peak_idx, peak_props = find_peaks(array, prominence=prominence)
    valley_idx, valley_props = find_peaks(-array, prominence=prominence)

    if peak_idx.size > 0:
        peak_choice = peak_idx[int(np.argmax(peak_props["prominences"]))]
    else:
        peak_choice = int(np.argmax(array))
    if valley_idx.size > 0:
        valley_choice = valley_idx[int(np.argmax(valley_props["prominences"]))]
    else:
        valley_choice = int(np.argmin(array))

    return float(wl[peak_choice]), float(wl[valley_choice])


def representative_reflectance(frame: pd.DataFrame, wavelength_nm: float, column: str) -> float:
    idx = int(np.argmin(np.abs(frame["Wavelength_nm"].to_numpy(dtype=float) - wavelength_nm)))
    return float(frame.iloc[idx][column])


def run_scan(nk_csv_path: Path, thickness_grid_nm: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    stack, _, _ = phase_a1.load_optical_stack_from_aligned_csv(nk_csv_path)
    reference_frame: pd.DataFrame | None = None
    long_records: list[pd.DataFrame] = []
    summary_rows: list[dict[str, float]] = []

    for thickness_nm in thickness_grid_nm:
        decomposition = stack.compute_pristine_baseline_decomposition(
            wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
            use_constant_glass=True,
            constant_glass_nk=phase_a1.DEFAULT_CONSTANT_GLASS_INDEX,
            ag_boundary_mode=phase_a1.AG_BOUNDARY_FINITE_FILM,
            pvk_thickness_nm=float(thickness_nm),
        )
        frame = pd.DataFrame(decomposition)
        frame["zone_label"] = phase_a1.build_zone_labels(frame["Wavelength_nm"].to_numpy(dtype=float))
        frame = frame[["Wavelength_nm", "zone_label", "R_front", "T_front", "R_stack", "R_total"]]
        phase_a1.validate_outputs(frame)

        if np.isclose(thickness_nm, REFERENCE_THICKNESS_NM):
            reference_frame = frame.copy()

        long_records.append(frame.assign(d_PVK_nm=float(thickness_nm)))

    if reference_frame is None:
        raise ValueError("参考厚度 700 nm 不在扫描网格中。")

    reference_stack = reference_frame["R_stack"].to_numpy(dtype=float)
    reference_total = reference_frame["R_total"].to_numpy(dtype=float)
    rear_mask = (reference_frame["Wavelength_nm"] >= REAR_WINDOW[0]) & (reference_frame["Wavelength_nm"] <= REAR_WINDOW[1])
    rear_wavelength_nm = reference_frame.loc[rear_mask, "Wavelength_nm"].to_numpy(dtype=float)

    enriched_frames: list[pd.DataFrame] = []
    for frame in long_records:
        current = frame.copy()
        current["Delta_R_stack_vs_700nm"] = current["R_stack"].to_numpy(dtype=float) - reference_stack
        current["Delta_R_total_vs_700nm"] = current["R_total"].to_numpy(dtype=float) - reference_total
        enriched_frames.append(current)

        rear_total = current.loc[rear_mask, "R_total"].to_numpy(dtype=float)
        rear_stack = current.loc[rear_mask, "R_stack"].to_numpy(dtype=float)
        total_peak_nm, total_valley_nm = find_dominant_extrema(rear_total, rear_wavelength_nm)
        stack_peak_nm, stack_valley_nm = find_dominant_extrema(rear_stack, rear_wavelength_nm)

        row: dict[str, float] = {
            "d_PVK_nm": float(current["d_PVK_nm"].iloc[0]),
            "R_total_peak_nm": total_peak_nm,
            "R_total_valley_nm": total_valley_nm,
            "R_total_peak_valley_spacing_nm": float(abs(total_peak_nm - total_valley_nm)),
            "R_stack_peak_nm": stack_peak_nm,
            "R_stack_valley_nm": stack_valley_nm,
            "R_stack_peak_valley_spacing_nm": float(abs(stack_peak_nm - stack_valley_nm)),
        }
        for wavelength_nm in REPRESENTATIVE_WAVELENGTHS_NM:
            row[f"R_total_{int(wavelength_nm)}nm"] = representative_reflectance(current, wavelength_nm, "R_total")
            row[f"R_stack_{int(wavelength_nm)}nm"] = representative_reflectance(current, wavelength_nm, "R_stack")
        summary_rows.append(row)

    scan_frame = pd.concat(enriched_frames, ignore_index=True)
    summary_frame = pd.DataFrame(summary_rows)
    return scan_frame, summary_frame


def save_outputs(scan_frame: pd.DataFrame, summary_frame: pd.DataFrame, outputs: ScanOutputs) -> None:
    scan_frame.to_csv(outputs.scan_csv, index=False, encoding="utf-8-sig")
    summary_frame.to_csv(outputs.summary_csv, index=False, encoding="utf-8-sig")


def make_map(scan_frame: pd.DataFrame, value_column: str, thickness_grid_nm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ordered = scan_frame.pivot(index="d_PVK_nm", columns="Wavelength_nm", values=value_column).sort_index()
    matrix = ordered.to_numpy(dtype=float)
    wavelengths_nm = ordered.columns.to_numpy(dtype=float)
    if not np.array_equal(ordered.index.to_numpy(dtype=float), thickness_grid_nm):
        raise ValueError(f"{value_column} 的 pivot 行索引与厚度扫描网格不一致。")
    return wavelengths_nm, matrix


def plot_heatmap(
    wavelengths_nm: np.ndarray,
    thickness_grid_nm: np.ndarray,
    matrix: np.ndarray,
    *,
    title: str,
    colorbar_label: str,
    output_path: Path,
    cmap: str,
    scale_to_percent: bool,
) -> None:
    values = matrix * 100.0 if scale_to_percent else matrix
    fig, ax = plt.subplots(figsize=(11.4, 6.0), dpi=320)
    image = ax.imshow(
        values,
        origin="lower",
        aspect="auto",
        extent=[float(wavelengths_nm.min()), float(wavelengths_nm.max()), float(thickness_grid_nm.min()), float(thickness_grid_nm.max())],
        cmap=cmap,
    )
    ax.axvspan(REAR_WINDOW[0], REAR_WINDOW[1], color="white", alpha=0.05)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("d_PVK (nm)")
    ax.set_title(title)
    colorbar = fig.colorbar(image, ax=ax, pad=0.015)
    colorbar.set_label(colorbar_label)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_peak_valley_tracking(summary_frame: pd.DataFrame, output_path: Path) -> None:
    thickness_nm = summary_frame["d_PVK_nm"].to_numpy(dtype=float)
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 8.2), dpi=320, constrained_layout=True, sharex=True)

    axes[0].plot(thickness_nm, summary_frame["R_stack_peak_nm"].to_numpy(dtype=float), color="#005b96", linewidth=1.9, label="R_stack peak")
    axes[0].plot(thickness_nm, summary_frame["R_stack_valley_nm"].to_numpy(dtype=float), color="#7b1fa2", linewidth=1.9, label="R_stack valley")
    axes[0].plot(thickness_nm, summary_frame["R_total_peak_nm"].to_numpy(dtype=float), color="#b03a2e", linewidth=1.9, linestyle="--", label="R_total peak")
    axes[0].plot(thickness_nm, summary_frame["R_total_valley_nm"].to_numpy(dtype=float), color="#616161", linewidth=1.9, linestyle="--", label="R_total valley")
    axes[0].set_ylabel("Wavelength (nm)")
    axes[0].set_title("Rear-Window Peak/Valley Tracking vs d_PVK")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best")

    axes[1].plot(thickness_nm, summary_frame["R_stack_peak_valley_spacing_nm"].to_numpy(dtype=float), color="#005b96", linewidth=1.9, label="R_stack spacing")
    axes[1].plot(thickness_nm, summary_frame["R_total_peak_valley_spacing_nm"].to_numpy(dtype=float), color="#b03a2e", linewidth=1.9, linestyle="--", label="R_total spacing")
    axes[1].set_xlabel("d_PVK (nm)")
    axes[1].set_ylabel("Peak-Valley Spacing (nm)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best")

    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_selected_thickness_curves(scan_frame: pd.DataFrame, output_path: Path) -> None:
    thickness_selection = [value for value in SELECTED_THICKNESSES_NM if np.any(np.isclose(scan_frame["d_PVK_nm"], value))]
    rear_mask = (scan_frame["Wavelength_nm"] >= REAR_WINDOW[0]) & (scan_frame["Wavelength_nm"] <= REAR_WINDOW[1])
    colors = ["#1b5e20", "#00695c", "#0d47a1", "#6a1b9a", "#b71c1c"]

    fig, axes = plt.subplots(2, 1, figsize=(10.2, 8.0), dpi=320, constrained_layout=True, sharex=True)
    for color, thickness_nm in zip(colors, thickness_selection):
        subset = scan_frame.loc[np.isclose(scan_frame["d_PVK_nm"], thickness_nm) & rear_mask]
        wl = subset["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, subset["R_stack"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, label=f"{thickness_nm:.0f} nm")
        axes[1].plot(wl, subset["R_total"].to_numpy(dtype=float) * 100.0, color=color, linewidth=1.8, label=f"{thickness_nm:.0f} nm")

    axes[0].set_ylabel("R_stack (%)")
    axes[0].set_title("Selected d_PVK Curves in the Rear Window")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best", ncol=2)

    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("R_total (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)

    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def summarize_sensitivity(scan_frame: pd.DataFrame, thickness_grid_nm: np.ndarray) -> dict[str, object]:
    total_map = scan_frame.pivot(index="d_PVK_nm", columns="Wavelength_nm", values="R_total").sort_index()
    stack_map = scan_frame.pivot(index="d_PVK_nm", columns="Wavelength_nm", values="R_stack").sort_index()
    wavelengths_nm = total_map.columns.to_numpy(dtype=float)

    total_matrix = total_map.to_numpy(dtype=float)
    stack_matrix = stack_map.to_numpy(dtype=float)
    total_std = np.std(total_matrix, axis=0, ddof=0)
    stack_std = np.std(stack_matrix, axis=0, ddof=0)

    rear_mask = (wavelengths_nm >= REAR_WINDOW[0]) & (wavelengths_nm <= REAR_WINDOW[1])
    front_mask = (wavelengths_nm >= FRONT_WINDOW[0]) & (wavelengths_nm <= FRONT_WINDOW[1])

    def top_wavelengths(values: np.ndarray, mask: np.ndarray, topn: int = 3) -> list[tuple[float, float]]:
        masked_wl = wavelengths_nm[mask]
        masked_val = values[mask]
        order = np.argsort(masked_val)[::-1][:topn]
        return [(float(masked_wl[idx]), float(masked_val[idx])) for idx in order]

    return {
        "rear_total_top": top_wavelengths(total_std, rear_mask),
        "rear_stack_top": top_wavelengths(stack_std, rear_mask),
        "front_total_top": top_wavelengths(total_std, front_mask),
        "front_stack_top": top_wavelengths(stack_std, front_mask),
        "rear_total_max_std": float(np.max(total_std[rear_mask])),
        "rear_stack_max_std": float(np.max(stack_std[rear_mask])),
        "front_total_max_std": float(np.max(total_std[front_mask])),
        "front_stack_max_std": float(np.max(stack_std[front_mask])),
    }


def tracking_metrics(summary_frame: pd.DataFrame, peak_column: str, valley_column: str) -> dict[str, float]:
    thickness_nm = summary_frame["d_PVK_nm"].to_numpy(dtype=float)
    peak_nm = summary_frame[peak_column].to_numpy(dtype=float)
    valley_nm = summary_frame[valley_column].to_numpy(dtype=float)
    peak_corr = float(spearmanr(thickness_nm, peak_nm).statistic)
    valley_corr = float(spearmanr(thickness_nm, valley_nm).statistic)
    peak_slope = float(np.polyfit(thickness_nm, peak_nm, 1)[0])
    valley_slope = float(np.polyfit(thickness_nm, valley_nm, 1)[0])
    return {
        "peak_corr": peak_corr,
        "valley_corr": valley_corr,
        "peak_slope": peak_slope,
        "valley_slope": valley_slope,
    }


def write_log(scan_frame: pd.DataFrame, summary_frame: pd.DataFrame, outputs: ScanOutputs, thickness_grid_nm: np.ndarray) -> None:
    sensitivity = summarize_sensitivity(scan_frame, thickness_grid_nm)
    total_metrics = tracking_metrics(summary_frame, "R_total_peak_nm", "R_total_valley_nm")
    stack_metrics = tracking_metrics(summary_frame, "R_stack_peak_nm", "R_stack_valley_nm")

    rear_total_monotonic = abs(total_metrics["peak_corr"]) > 0.97 and abs(total_metrics["valley_corr"]) > 0.97
    rear_stack_monotonic = abs(stack_metrics["peak_corr"]) > 0.97 and abs(stack_metrics["valley_corr"]) > 0.97
    stack_more_sensitive = sensitivity["rear_stack_max_std"] > sensitivity["rear_total_max_std"]

    if rear_total_monotonic:
        rear_window_statement = "- 后窗主峰/主谷位置随 d_PVK 变化近似单调，可直接作为厚度主灵敏度窗口。"
    else:
        rear_window_statement = (
            "- 后窗对 d_PVK 明显敏感，但把整个 500-900 nm 扫描压缩为单一“主峰/主谷”轨迹时会出现模式切换；"
            "因此更合理的结论是：后窗存在清晰系统漂移和可辨识局部近线性区间，而不是全范围单一模态严格单调。"
        )

    rear_total_top = ", ".join(f"{wl:.0f} nm ({value*100:.2f}%)" for wl, value in sensitivity["rear_total_top"])
    rear_stack_top = ", ".join(f"{wl:.0f} nm ({value*100:.2f}%)" for wl, value in sensitivity["rear_stack_top"])
    front_total_top = ", ".join(f"{wl:.0f} nm ({value*100:.2f}%)" for wl, value in sensitivity["front_total_top"])
    front_stack_top = ", ".join(f"{wl:.0f} nm ({value*100:.2f}%)" for wl, value in sensitivity["front_stack_top"])

    lines = [
        f"# {PHASE_NAME} d_PVK Thickness Scan",
        "",
        "## Inputs",
        "",
        f"- optical stack: `{DEFAULT_NK_CSV_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        "- geometry: `Glass(1 mm incoherent) / ITO 100 / NiOx 45 / SAM 5 / PVK variable / C60 15 / Ag 100 nm / Air`",
        "- incidence: `normal`",
        "",
        "## Scan Range",
        "",
        f"- d_PVK range: `{thickness_grid_nm.min():.0f}-{thickness_grid_nm.max():.0f} nm`",
        f"- step: `{thickness_grid_nm[1] - thickness_grid_nm[0]:.0f} nm`",
        f"- reference thickness: `{REFERENCE_THICKNESS_NM:.0f} nm`",
        "",
        "## Primary Outputs",
        "",
        f"- scan csv: `{outputs.scan_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- feature summary csv: `{outputs.summary_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- R_stack heatmap: `{outputs.r_stack_heatmap.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- R_total heatmap: `{outputs.r_total_heatmap.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- Delta R_stack heatmap: `{outputs.delta_r_stack_heatmap.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- Delta R_total heatmap: `{outputs.delta_r_total_heatmap.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- tracking figure: `{outputs.tracking_figure.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- selected curves: `{outputs.selected_curves_figure.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Rear-Window Sensitivity",
        "",
        f"- R_total peak tracking Spearman: `{total_metrics['peak_corr']:.4f}`",
        f"- R_total valley tracking Spearman: `{total_metrics['valley_corr']:.4f}`",
        f"- R_total peak drift slope: `{total_metrics['peak_slope']:.4f} nm peak shift / nm thickness`",
        f"- R_total valley drift slope: `{total_metrics['valley_slope']:.4f} nm valley shift / nm thickness`",
        f"- rear-window monotonic sensitivity (R_total): `{rear_total_monotonic}`",
        f"- rear-window monotonic sensitivity (R_stack): `{rear_stack_monotonic}`",
        "",
        "## Most Sensitive Wavelengths",
        "",
        f"- rear-window R_stack top wavelengths: `{rear_stack_top}`",
        f"- rear-window R_total top wavelengths: `{rear_total_top}`",
        f"- front-window R_stack top wavelengths: `{front_stack_top}`",
        f"- front-window R_total top wavelengths: `{front_total_top}`",
        "",
        "## R_stack vs R_total",
        "",
        f"- rear-window max std(R_stack): `{sensitivity['rear_stack_max_std']*100:.2f}%`",
        f"- rear-window max std(R_total): `{sensitivity['rear_total_max_std']*100:.2f}%`",
        f"- front-window max std(R_stack): `{sensitivity['front_stack_max_std']*100:.2f}%`",
        f"- front-window max std(R_total): `{sensitivity['front_total_max_std']*100:.2f}%`",
        f"- stack more sensitive than total in rear window: `{stack_more_sensitive}`",
        "",
        "## Interpretation",
        "",
        rear_window_statement,
        "- 最敏感波长集中在后窗 fringe 斜率最大的区域；前窗虽有变化，但幅度明显弱于后窗。",
        "- `R_total` 由于叠加了固定 `R_front` 背景，会比 `R_stack` 略钝化，因此 `R_stack` 更适合做纯理论灵敏度分析，`R_total` 更接近实验可见量。",
        "- 从谱形上看，厚度变化主要表现为后窗 fringe 的整体相位漂移和峰谷位置系统移动；这与界面缺陷常见的局部振幅扭曲、背景抬升或特定窗口异常并不相同。",
        "- 因此 `d_PVK` 更像是“全局微腔光程变化”，而后续 BEMA / air gap 更可能表现为局部界面调制，两者虽然可耦合，但在后窗结构上并非完全混淆。",
        "",
        "## Risks / Limits",
        "",
        "- 当前扫描仍建立在 `PVK surrogate v2` 上，不代表 band-edge 真值已经确定。",
        "- 本轮没有引入玻璃色散敏感性，也没有把 PVK surrogate 不确定性传播到厚度扫描结果。",
        "- 峰谷追踪使用的是后窗主导极值的工程定义，适合建立厚度-条纹相位图谱，但不应替代更完整的模式标号分析。",
        "",
        "## Next Step",
        "",
        "- 建议下一步进入 `PVK uncertainty ensemble`，量化 surrogate band-edge 不确定性对 thickness scan 结论的传播范围。",
        "- 在 uncertainty envelope 明确后，再进入 `BEMA only` 或 `air gap only` 的缺陷调制扫描会更稳妥。",
    ]
    outputs.log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    outputs = ensure_output_dirs()
    thickness_grid_nm = build_thickness_grid(args.start_nm, args.stop_nm, args.step_nm)
    scan_frame, summary_frame = run_scan(args.nk_csv, thickness_grid_nm)
    save_outputs(scan_frame, summary_frame, outputs)

    wavelengths_nm, r_stack_map = make_map(scan_frame, "R_stack", thickness_grid_nm)
    _, r_total_map = make_map(scan_frame, "R_total", thickness_grid_nm)
    _, delta_stack_map = make_map(scan_frame, "Delta_R_stack_vs_700nm", thickness_grid_nm)
    _, delta_total_map = make_map(scan_frame, "Delta_R_total_vs_700nm", thickness_grid_nm)

    plot_heatmap(
        wavelengths_nm,
        thickness_grid_nm,
        r_stack_map,
        title=f"{PHASE_NAME} R_stack Heatmap",
        colorbar_label="R_stack (%)",
        output_path=outputs.r_stack_heatmap,
        cmap="viridis",
        scale_to_percent=True,
    )
    plot_heatmap(
        wavelengths_nm,
        thickness_grid_nm,
        r_total_map,
        title=f"{PHASE_NAME} R_total Heatmap",
        colorbar_label="R_total (%)",
        output_path=outputs.r_total_heatmap,
        cmap="viridis",
        scale_to_percent=True,
    )
    plot_heatmap(
        wavelengths_nm,
        thickness_grid_nm,
        delta_stack_map,
        title=f"{PHASE_NAME} Delta R_stack vs 700 nm",
        colorbar_label="Delta R_stack (%)",
        output_path=outputs.delta_r_stack_heatmap,
        cmap="coolwarm",
        scale_to_percent=True,
    )
    plot_heatmap(
        wavelengths_nm,
        thickness_grid_nm,
        delta_total_map,
        title=f"{PHASE_NAME} Delta R_total vs 700 nm",
        colorbar_label="Delta R_total (%)",
        output_path=outputs.delta_r_total_heatmap,
        cmap="coolwarm",
        scale_to_percent=True,
    )
    plot_peak_valley_tracking(summary_frame, outputs.tracking_figure)
    plot_selected_thickness_curves(scan_frame, outputs.selected_curves_figure)
    write_log(scan_frame, summary_frame, outputs, thickness_grid_nm)

    print(f"scan_csv={outputs.scan_csv}")
    print(f"summary_csv={outputs.summary_csv}")
    print(f"log_path={outputs.log_path}")


if __name__ == "__main__":
    main()
