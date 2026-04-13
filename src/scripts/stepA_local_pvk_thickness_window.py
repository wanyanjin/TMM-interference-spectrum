"""Phase A-local PVK thickness-window fingerprint scan.

This script reuses the repaired full-stack forward model from Phase A while
restricting the PVK thickness scan to a realistic local-variation window:
700 +/- 25 nm. The PVK optical constants still originate from the stitched
surrogate table based on [LIT-0001]; this step only changes the PVK thickness.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
for candidate in (PROJECT_ROOT / "src", SCRIPT_DIR):
    path = str(candidate)
    if path not in sys.path:
        sys.path.insert(0, path)

import stepA1_pristine_baseline as phase_a1  # noqa: E402


PHASE_NAME = "Phase A-local"
INPUT_NK_CSV = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_pvk_v2.csv"
INPUT_OLD_SCAN_CSV = PROJECT_ROOT / "data" / "processed" / "phaseA2" / "phaseA2_pvk_thickness_scan.csv"
INPUT_PHASE_A2_REPORT = PROJECT_ROOT / "results" / "report" / "phaseA2_pvk_thickness_scan" / "PHASE_A2_REPORT.md"
INPUT_PHASE_A2_1_REPORT = PROJECT_ROOT / "results" / "report" / "phaseA2_1_pvk_uncertainty_ensemble" / "PHASE_A2_1_REPORT.md"
INPUT_PROJECT_STATE = PROJECT_ROOT / "docs" / "PROJECT_STATE.md"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phaseA_local"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phaseA_local"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phaseA_local"
REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phaseA_local_thickness_window"

WAVELENGTHS_NM = phase_a1.EXPECTED_WAVELENGTHS_NM
THICKNESS_GRID_NM = np.arange(675.0, 726.0, 1.0, dtype=float)
REFERENCE_THICKNESS_NM = 700.0
SELECTED_THICKNESSES_NM = (675.0, 690.0, 700.0, 710.0, 725.0)

FRONT_WINDOW_SHADE = (400.0, 650.0)
TRANSITION_WINDOW_SHADE = (650.0, 810.0)
REAR_WINDOW_SHADE = (810.0, 1100.0)

FRONT_SUMMARY_WINDOW = (500.0, 650.0)
TRANSITION_SUMMARY_WINDOW = (650.0, 810.0)
REAR_SUMMARY_WINDOW = (810.0, 1055.0)

ZONE_SHADES = (
    (FRONT_WINDOW_SHADE, "#e8f3ec", "front"),
    (TRANSITION_WINDOW_SHADE, "#fff2cc", "transition"),
    (REAR_WINDOW_SHADE, "#e7f0fa", "rear"),
)


@dataclass(frozen=True)
class Outputs:
    scan_csv: Path
    feature_csv: Path
    heatmap_png: Path
    curves_png: Path
    log_md: Path
    report_md: Path


def ensure_dirs() -> Outputs:
    for directory in (PROCESSED_DIR, FIGURE_DIR, LOG_DIR, REPORT_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    return Outputs(
        scan_csv=PROCESSED_DIR / "phaseA_local_thickness_scan.csv",
        feature_csv=PROCESSED_DIR / "phaseA_local_thickness_feature_summary.csv",
        heatmap_png=FIGURE_DIR / "phaseA_local_deltaRtotal_heatmap.png",
        curves_png=FIGURE_DIR / "phaseA_local_selected_curves.png",
        log_md=LOG_DIR / "phaseA_local_thickness_window.md",
        report_md=REPORT_DIR / "PHASE_A_LOCAL_REPORT.md",
    )


def window_mask(wavelength_nm: np.ndarray, bounds_nm: tuple[float, float]) -> np.ndarray:
    lower_nm, upper_nm = bounds_nm
    return (wavelength_nm >= lower_nm) & (wavelength_nm <= upper_nm)


def dominant_extrema(signal: np.ndarray, wavelength_nm: np.ndarray) -> tuple[float, float]:
    array = np.asarray(signal, dtype=float)
    grid = np.asarray(wavelength_nm, dtype=float)
    prominence = max((float(array.max()) - float(array.min())) * 0.10, 1e-8)
    peak_idx, peak_props = find_peaks(array, prominence=prominence)
    valley_idx, valley_props = find_peaks(-array, prominence=prominence)

    if peak_idx.size == 0:
        peak_choice = int(np.argmax(array))
    else:
        peak_choice = int(peak_idx[np.argmax(peak_props["prominences"])])
    if valley_idx.size == 0:
        valley_choice = int(np.argmin(array))
    else:
        valley_choice = int(valley_idx[np.argmax(valley_props["prominences"])])
    return float(grid[peak_choice]), float(grid[valley_choice])


def rms(values: np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    return float(np.sqrt(np.mean(array**2)))


def run_scan() -> tuple[pd.DataFrame, pd.DataFrame]:
    stack, _, _ = phase_a1.load_optical_stack_from_aligned_csv(INPUT_NK_CSV)

    reference_total: np.ndarray | None = None
    reference_wavelength_nm: np.ndarray | None = None
    long_frames: list[pd.DataFrame] = []

    for thickness_nm in THICKNESS_GRID_NM:
        decomposition = stack.compute_pristine_baseline_decomposition(
            wavelengths_nm=WAVELENGTHS_NM,
            use_constant_glass=True,
            constant_glass_nk=phase_a1.DEFAULT_CONSTANT_GLASS_INDEX,
            ag_boundary_mode=phase_a1.AG_BOUNDARY_FINITE_FILM,
            pvk_thickness_nm=float(thickness_nm),
        )
        frame = pd.DataFrame(
            {
                "Wavelength_nm": decomposition["Wavelength_nm"],
                "d_PVK_nm": float(thickness_nm),
                "R_total": decomposition["R_total"],
            }
        )

        if np.isclose(thickness_nm, REFERENCE_THICKNESS_NM):
            reference_total = frame["R_total"].to_numpy(dtype=float)
            reference_wavelength_nm = frame["Wavelength_nm"].to_numpy(dtype=float)
        long_frames.append(frame)

    if reference_total is None or reference_wavelength_nm is None:
        raise ValueError("reference thickness 700 nm was not generated")

    scan_frame = pd.concat(long_frames, ignore_index=True)
    if not np.array_equal(np.unique(scan_frame["Wavelength_nm"].to_numpy(dtype=float)), reference_wavelength_nm):
        raise ValueError("wavelength grid mismatch inside thickness scan")

    scan_frame["Delta_R_total_vs_700nm"] = (
        scan_frame["R_total"].to_numpy(dtype=float)
        - np.tile(reference_total, THICKNESS_GRID_NM.size)
    )

    summary_rows: list[dict[str, float]] = []
    for thickness_nm in THICKNESS_GRID_NM:
        subset = scan_frame.loc[np.isclose(scan_frame["d_PVK_nm"], thickness_nm)].copy()
        wavelengths_nm = subset["Wavelength_nm"].to_numpy(dtype=float)
        delta_total = subset["Delta_R_total_vs_700nm"].to_numpy(dtype=float)

        front_mask = window_mask(wavelengths_nm, FRONT_SUMMARY_WINDOW)
        transition_mask = window_mask(wavelengths_nm, TRANSITION_SUMMARY_WINDOW)
        rear_mask = window_mask(wavelengths_nm, REAR_SUMMARY_WINDOW)
        rear_peak_nm, rear_valley_nm = dominant_extrema(
            subset.loc[rear_mask, "R_total"].to_numpy(dtype=float),
            wavelengths_nm[rear_mask],
        )

        summary_rows.append(
            {
                "d_PVK_nm": float(thickness_nm),
                "front_rms_deltaR_500_650": rms(delta_total[front_mask]),
                "transition_rms_deltaR_650_810": rms(delta_total[transition_mask]),
                "rear_rms_deltaR_810_1055": rms(delta_total[rear_mask]),
                "rear_peak_nm": rear_peak_nm,
                "rear_valley_nm": rear_valley_nm,
                "rear_peak_valley_spacing_nm": float(abs(rear_peak_nm - rear_valley_nm)),
            }
        )

    return scan_frame, pd.DataFrame(summary_rows)


def save_data(scan_frame: pd.DataFrame, feature_frame: pd.DataFrame, outputs: Outputs) -> None:
    scan_frame.to_csv(outputs.scan_csv, index=False, encoding="utf-8-sig")
    feature_frame.to_csv(outputs.feature_csv, index=False, encoding="utf-8-sig")


def plot_heatmap(scan_frame: pd.DataFrame, outputs: Outputs) -> None:
    pivot = scan_frame.pivot(index="d_PVK_nm", columns="Wavelength_nm", values="Delta_R_total_vs_700nm").sort_index()
    wavelengths_nm = pivot.columns.to_numpy(dtype=float)
    thickness_nm = pivot.index.to_numpy(dtype=float)
    values_percent = pivot.to_numpy(dtype=float) * 100.0
    max_abs = float(np.max(np.abs(values_percent)))

    fig, ax = plt.subplots(figsize=(11.6, 5.8), dpi=320)
    image = ax.imshow(
        values_percent,
        origin="lower",
        aspect="auto",
        extent=[float(wavelengths_nm.min()), float(wavelengths_nm.max()), float(thickness_nm.min()), float(thickness_nm.max())],
        cmap="coolwarm",
        vmin=-max_abs,
        vmax=max_abs,
    )
    ax.set_xlabel("Wavelength (nm)", fontsize=12)
    ax.set_ylabel("d_PVK (nm)", fontsize=12)
    ax.set_title("Phase A-local Delta R_total vs 700 nm", fontsize=13)
    ax.tick_params(labelsize=10.5)
    colorbar = fig.colorbar(image, ax=ax, pad=0.015)
    colorbar.set_label("Delta R_total (%)", fontsize=11)
    colorbar.ax.tick_params(labelsize=10)
    fig.tight_layout()
    fig.savefig(outputs.heatmap_png, dpi=320, bbox_inches="tight")
    plt.close(fig)


def add_window_shading(axis: plt.Axes) -> None:
    for (lower_nm, upper_nm), color, label in ZONE_SHADES:
        axis.axvspan(lower_nm, upper_nm, color=color, alpha=0.85, zorder=0)
        center_nm = 0.5 * (lower_nm + upper_nm)
        axis.text(
            center_nm,
            0.98,
            label,
            ha="center",
            va="top",
            transform=axis.get_xaxis_transform(),
            fontsize=10,
            color="#455a64",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72, "pad": 1.8},
        )


def plot_selected_curves(scan_frame: pd.DataFrame, outputs: Outputs) -> None:
    fig, ax = plt.subplots(figsize=(11.6, 5.8), dpi=320)
    add_window_shading(ax)
    colors = {
        675.0: "#1f4e79",
        690.0: "#2e75b6",
        700.0: "#111111",
        710.0: "#c55a11",
        725.0: "#8b0000",
    }
    for thickness_nm in SELECTED_THICKNESSES_NM:
        subset = scan_frame.loc[np.isclose(scan_frame["d_PVK_nm"], thickness_nm)]
        ax.plot(
            subset["Wavelength_nm"].to_numpy(dtype=float),
            subset["R_total"].to_numpy(dtype=float) * 100.0,
            linewidth=2.0 if np.isclose(thickness_nm, 700.0) else 1.8,
            color=colors[float(thickness_nm)],
            label=f"{int(thickness_nm)} nm",
        )

    ax.set_xlim(400.0, 1100.0)
    ax.set_xlabel("Wavelength (nm)", fontsize=12)
    ax.set_ylabel("R_total (%)", fontsize=12)
    ax.set_title("Phase A-local Selected R_total Curves", fontsize=13)
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.tick_params(labelsize=10.5)
    ax.legend(loc="best", fontsize=10.5, frameon=True)
    fig.tight_layout()
    fig.savefig(outputs.curves_png, dpi=320, bbox_inches="tight")
    plt.close(fig)


def build_log_text(feature_frame: pd.DataFrame) -> str:
    reference_row = feature_frame.loc[np.isclose(feature_frame["d_PVK_nm"], REFERENCE_THICKNESS_NM)].iloc[0]
    front_max = float(feature_frame["front_rms_deltaR_500_650"].max() * 100.0)
    transition_max = float(feature_frame["transition_rms_deltaR_650_810"].max() * 100.0)
    rear_max = float(feature_frame["rear_rms_deltaR_810_1055"].max() * 100.0)
    spacing_min = float(feature_frame["rear_peak_valley_spacing_nm"].min())
    spacing_max = float(feature_frame["rear_peak_valley_spacing_nm"].max())

    lines = [
        "# Phase A-local Thickness Window",
        "",
        "## 1. 为什么本轮把 thickness 范围收窄到 700 ± 25 nm",
        "",
        "- 这次要代表的是器件局部褶皱、轻微起伏和小尺度膜厚不均，而不是整片器件从 500 nm 到 900 nm 的大范围工艺漂移。",
        "- 以 700 nm 为中心、只看 ±25 nm，更接近后续实际判别里会遇到的局部 thickness 扰动量级。",
        "",
        "## 2. 相比原始 500–900 nm 扫描，这一版更适合代表什么物理场景",
        "",
        "- 旧版更适合展示“厚度从明显偏薄到明显偏厚”的全局趋势。",
        "- 这一版更适合代表真实器件中局部位置之间只有几十纳米差异的厚度起伏场景。",
        "",
        "## 3. 在这个更现实的范围内，R_total 的主要变化集中在哪个窗口",
        "",
        f"- front 窗口的最大 RMS Delta R_total 约为 `{front_max:.3f}%`，变化最弱。",
        f"- transition 窗口的最大 RMS Delta R_total 约为 `{transition_max:.3f}%`，已经开始明显响应。",
        f"- rear 窗口的最大 RMS Delta R_total 约为 `{rear_max:.3f}%`，是最主要的变化区。",
        "",
        "## 4. 局部 thickness 变化最直观的谱形指纹是什么",
        "",
        "- 最直观的指纹不是新增孤立异常峰，而是 rear-window fringe 整体沿波长方向系统漂移。",
        f"- 在这组扫描里，rear peak-valley spacing 保持在 `{spacing_min:.1f}-{spacing_max:.1f} nm`，说明主要是条纹位置移动，而不是条纹类型突然改变。",
        f"- 700 nm 参考曲线本身的 rear peak / valley 位于 `{reference_row['rear_peak_nm']:.1f} nm` / `{reference_row['rear_valley_nm']:.1f} nm`，可作为后续判别的零点。",
        "",
        "## 5. 这一版图在后续区分 thickness / roughness / air-gap 时有什么作用",
        "",
        "- 它先给出一个更现实的 thickness 基线，告诉我们局部厚度起伏通常会把 rear-window 条纹整体推来推去。",
        "- 后续如果看到的是局部异常结构、包络被扭曲、或前窗也同步出现不成比例变化，就更像 roughness 或 air-gap，而不只是 thickness。",
        "- 因此这套图更适合作为后续机制判别里的“局部 thickness 字典”。",
        "",
    ]
    return "\n".join(lines)


def build_report_text(outputs: Outputs, feature_frame: pd.DataFrame) -> str:
    rear_max_row = feature_frame.loc[feature_frame["rear_rms_deltaR_810_1055"].idxmax()]
    transition_max_row = feature_frame.loc[feature_frame["transition_rms_deltaR_650_810"].idxmax()]

    lines = [
        "# Phase A-local Report",
        "",
        "## 1. 任务目标",
        "",
        "- 重新建立更接近真实器件局部厚度起伏的 PVK thickness 指纹图。",
        "- 仅扫描 `d_PVK = 675-725 nm`，以 `700 nm` 为参考，输出 `R_total` 与 `Delta_R_total`。",
        "",
        "## 2. 模型口径",
        "",
        "- `Air / Glass(1 mm, incoherent) / ITO 100 / NiOx 45 / SAM 5 / PVK variable / C60 15 / Ag 100 / Air`",
        "- normal incidence",
        "- wavelength range: `400-1100 nm`, step `1 nm`",
        "- optical constants: `resources/aligned_full_stack_nk_pvk_v2.csv`",
        "",
        "## 3. 为什么采用 700 ± 25 nm",
        "",
        "- 这次要代表的是局部膜厚起伏，而不是整个样品在极宽厚度区间内的全局偏差。",
        "- `700 ± 25 nm` 既保留了足够清楚的微腔调制，又更接近真实器件里局部褶皱或小尺度厚度不均的量级。",
        "",
        "## 4. 关键结果",
        "",
        f"- rear-window 的最强 RMS Delta R_total 出现在 `d_PVK = {rear_max_row['d_PVK_nm']:.0f} nm`，约为 `{rear_max_row['rear_rms_deltaR_810_1055']*100.0:.3f}%`。",
        f"- transition-window 的最强 RMS Delta R_total 出现在 `d_PVK = {transition_max_row['d_PVK_nm']:.0f} nm`，约为 `{transition_max_row['transition_rms_deltaR_650_810']*100.0:.3f}%`。",
        "- 热图显示主要变化集中在 transition / rear，尤其是 rear-window fringe 的系统漂移。",
        "- 代表曲线图显示前窗变化较小，厚度效应更像条纹整体平移，而不是新长出局部异常结构。",
        "",
        "## 5. 这套局部 thickness 字典对后续判别 air-gap 的意义",
        "",
        "- 它先给出一个现实 thickness 背景下的标准谱形，帮助区分“条纹整体漂移”和“局部异常调制”这两类机制。",
        "- 如果后续某组异常更像 rear-window 局部包络扭曲、非刚性变化或前窗联动异常，就不应直接归因于 thickness。",
        "- 因此这套结果适合作为后续区分 thickness / roughness / air-gap 的基线参照。",
        "",
        "## 6. 同步资产",
        "",
        f"- `{outputs.scan_csv.name}`",
        f"- `{outputs.feature_csv.name}`",
        f"- `{outputs.heatmap_png.name}`",
        f"- `{outputs.curves_png.name}`",
        f"- `{outputs.log_md.name}`",
        "",
    ]
    return "\n".join(lines)


def sync_report_assets(outputs: Outputs) -> None:
    for path in (outputs.scan_csv, outputs.feature_csv, outputs.heatmap_png, outputs.curves_png):
        shutil.copy2(path, REPORT_DIR / path.name)


def main() -> None:
    outputs = ensure_dirs()
    scan_frame, feature_frame = run_scan()
    save_data(scan_frame, feature_frame, outputs)
    plot_heatmap(scan_frame, outputs)
    plot_selected_curves(scan_frame, outputs)
    outputs.log_md.write_text(build_log_text(feature_frame) + "\n", encoding="utf-8")
    sync_report_assets(outputs)
    outputs.report_md.write_text(build_report_text(outputs, feature_frame) + "\n", encoding="utf-8")

    print(f"scan_csv={outputs.scan_csv}")
    print(f"feature_csv={outputs.feature_csv}")
    print(f"heatmap_png={outputs.heatmap_png}")
    print(f"curves_png={outputs.curves_png}")
    print(f"log_md={outputs.log_md}")
    print(f"report_md={outputs.report_md}")


if __name__ == "__main__":
    main()
