"""Build PPT-ready Phase A->C report assets from existing processed results.

This script does not run new physics simulations. It only redraws and curates
R_total-focused figures plus short slide texts/manifests for presentation use.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import sys

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import FancyArrowPatch, Rectangle


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


ASSET_ROOT = PROJECT_ROOT / "results" / "report" / "ppt_phaseAtoC_assets"
BASELINE_DIR = ASSET_ROOT / "01_baseline"
THICKNESS_DIR = ASSET_ROOT / "02_thickness"
REAR_BEMA_DIR = ASSET_ROOT / "03_rear_bema"
FRONT_BEMA_DIR = ASSET_ROOT / "04_front_bema"
REAR_GAP_DIR = ASSET_ROOT / "05_rear_gap"
FRONT_GAP_DIR = ASSET_ROOT / "06_front_gap"
SUMMARY_DIR = ASSET_ROOT / "07_summary"
APPENDIX_DIR = ASSET_ROOT / "appendix_pvk_surrogate_fix"

PHASE_A1_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA1" / "phaseA1_pristine_baseline.csv"
PHASE_A1_2_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA1_2" / "phaseA1_2_pristine_baseline.csv"
PHASE_A1_2_COMPARE_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA1_2" / "pvk_v1_v2_local_comparison.csv"
PHASE_A2_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA2" / "phaseA2_pvk_thickness_scan.csv"
PHASE_B1_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseB1" / "phaseB1_rear_bema_scan.csv"
PHASE_B2_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseB2" / "phaseB2_front_bema_scan.csv"
PHASE_C1A_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseC1a" / "phaseC1a_rear_air_gap_scan.csv"
PHASE_C1B_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseC1b" / "phaseC1b_front_air_gap_scan.csv"

PHASE_A1_2_REPORT = PROJECT_ROOT / "results" / "report" / "phaseA1_2_pvk_surrogate_and_pristine" / "PHASE_A1_2_REPORT.md"
PHASE_A2_REPORT = PROJECT_ROOT / "results" / "report" / "phaseA2_pvk_thickness_scan" / "PHASE_A2_REPORT.md"
PHASE_A2_1_REPORT = PROJECT_ROOT / "results" / "report" / "phaseA2_1_pvk_uncertainty_ensemble" / "PHASE_A2_1_REPORT.md"
PHASE_B1_REPORT = PROJECT_ROOT / "results" / "report" / "phaseB1_rear_bema_sandbox" / "PHASE_B1_REPORT.md"
PHASE_B2_REPORT = PROJECT_ROOT / "results" / "report" / "phaseB2_front_bema_sandbox" / "PHASE_B2_REPORT.md"
PHASE_C1A_REPORT = PROJECT_ROOT / "results" / "report" / "phaseC1a_rear_air_gap_sandbox" / "PHASE_C1A_REPORT.md"
PHASE_C1B_REPORT = PROJECT_ROOT / "results" / "report" / "phaseC1b_front_air_gap_sandbox" / "PHASE_C1B_REPORT.md"

WINDOWS = [
    ("front", 400.0, 650.0, "#f6efe1"),
    ("transition", 650.0, 810.0, "#eaf2fb"),
    ("rear", 810.0, 1100.0, "#eef7ec"),
]


@dataclass(frozen=True)
class SlidePaths:
    directory: Path
    main_png: Path
    secondary_png: Path
    text_md: Path
    source_md: Path


LAYER_BASE = [
    {"id": "air_left", "label": "Air", "thickness": "", "color": "#f7f7f7", "width": 0.78},
    {"id": "glass", "label": "Glass", "thickness": "1 mm", "color": "#dfe8f5", "width": 1.18},
    {"id": "ito", "label": "ITO", "thickness": "100 nm", "color": "#e8f0cf", "width": 0.84},
    {"id": "niox", "label": "NiOx", "thickness": "45 nm", "color": "#f7d8bf", "width": 0.78},
    {"id": "sam", "label": "SAM", "thickness": "5 nm", "color": "#f2f2c2", "width": 0.62},
    {"id": "pvk", "label": "PVK", "thickness": "700 nm", "color": "#d8e8cf", "width": 1.34},
    {"id": "c60", "label": "C60", "thickness": "15 nm", "color": "#e4d8f5", "width": 0.72},
    {"id": "ag", "label": "Ag", "thickness": "100 nm", "color": "#d9d9d9", "width": 0.76},
    {"id": "air_right", "label": "Air", "thickness": "", "color": "#f7f7f7", "width": 0.78},
]


def configure_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "#fafafa",
            "axes.edgecolor": "#4d4d4d",
            "axes.labelcolor": "#222222",
            "axes.titlesize": 18,
            "axes.titleweight": "bold",
            "axes.labelweight": "bold",
            "axes.labelsize": 13,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "legend.fontsize": 10,
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
            "font.weight": "bold",
            "grid.color": "#bcbcbc",
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
        }
    )


def ensure_dirs() -> None:
    for path in (
        ASSET_ROOT,
        BASELINE_DIR,
        THICKNESS_DIR,
        REAR_BEMA_DIR,
        FRONT_BEMA_DIR,
        REAR_GAP_DIR,
        FRONT_GAP_DIR,
        SUMMARY_DIR,
        APPENDIX_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def slide_paths(directory: Path) -> SlidePaths:
    return SlidePaths(
        directory=directory,
        main_png=directory / "main_figure.png",
        secondary_png=directory / "secondary_figure.png",
        text_md=directory / "slide_text.md",
        source_md=directory / "source_manifest.md",
    )


def apply_window_background(ax: plt.Axes) -> None:
    for label, start, end, color in WINDOWS:
        ax.axvspan(start, end, color=color, zorder=0)
        ax.text(
            (start + end) * 0.5,
            0.985,
            label,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=11,
            fontweight="bold",
            color="#555555",
        )


def finalize_axes(ax: plt.Axes, ylabel: str, title: str) -> None:
    ax.set_xlim(400.0, 1100.0)
    ax.set_xlabel("Wavelength (nm)", fontweight="bold")
    ax.set_ylabel(ylabel, fontweight="bold")
    ax.set_title(title, fontweight="bold")
    ax.grid(True)


def save_and_alias(fig: plt.Figure, path: Path, alias: Path | None = None) -> None:
    fig.savefig(path, dpi=320, bbox_inches="tight")
    plt.close(fig)
    if alias is not None and alias.resolve() != path.resolve():
        shutil.copy2(path, alias)


def render_heatmap(
    frame: pd.DataFrame,
    param_column: str,
    value_column: str,
    output_path: Path,
    title: str,
    y_label: str,
) -> None:
    pivot = frame.pivot(index=param_column, columns="Wavelength_nm", values=value_column).sort_index()
    wl = pivot.columns.to_numpy(dtype=float)
    params = pivot.index.to_numpy(dtype=float)
    values = pivot.to_numpy(dtype=float) * 100.0
    vmax = float(np.max(np.abs(values)))
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    fig, ax = plt.subplots(figsize=(11.6, 6.0), dpi=320)
    im = ax.imshow(
        values,
        origin="lower",
        aspect="auto",
        extent=[float(wl.min()), float(wl.max()), float(params.min()), float(params.max())],
        cmap="RdBu_r",
        norm=norm,
    )
    for _, start, end, _color in WINDOWS:
        ax.axvline(start, color="#aaaaaa", linewidth=0.8, linestyle=":")
        ax.axvline(end, color="#aaaaaa", linewidth=0.8, linestyle=":")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax, pad=0.015)
    cbar.set_label("Delta R_total (%)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def render_selected_curves(
    frame: pd.DataFrame,
    param_column: str,
    selected_values: list[float],
    output_path: Path,
    title: str,
    legend_title: str,
) -> None:
    fig, ax = plt.subplots(figsize=(11.2, 5.8), dpi=320)
    apply_window_background(ax)
    colors = plt.cm.viridis(np.linspace(0.12, 0.9, len(selected_values)))
    for color, value in zip(colors, selected_values):
        subset = frame.loc[np.isclose(frame[param_column], value)]
        if subset.empty:
            continue
        ax.plot(
            subset["Wavelength_nm"].to_numpy(dtype=float),
            subset["R_total"].to_numpy(dtype=float) * 100.0,
            linewidth=2.2,
            color=color,
            label=f"{value:g} nm",
        )
    finalize_axes(ax, "R_total (%)", title)
    legend = ax.legend(title=legend_title, loc="best", ncol=min(len(selected_values), 3))
    if legend is not None:
        plt.setp(legend.get_texts(), fontweight="bold")
        if legend.get_title() is not None:
            legend.get_title().set_fontweight("bold")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def render_baseline_curve(frame: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.2, 5.8), dpi=320)
    apply_window_background(ax)
    ax.plot(
        frame["Wavelength_nm"].to_numpy(dtype=float),
        frame["R_total"].to_numpy(dtype=float) * 100.0,
        color="#005b96",
        linewidth=2.4,
    )
    finalize_axes(ax, "R_total (%)", "Pristine baseline on the observable R_total")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def render_structure_schematic(output_path: Path) -> None:
    layers = [
        ("Air", "#f7f7f7"),
        ("Glass\n(1 mm)", "#dfe8f5"),
        ("ITO\n100 nm", "#e8f0cf"),
        ("NiOx\n45 nm", "#f7d8bf"),
        ("SAM\n5 nm", "#f2f2c2"),
        ("PVK\n700 nm", "#d8e8cf"),
        ("C60\n15 nm", "#e4d8f5"),
        ("Ag\n100 nm", "#d9d9d9"),
        ("Air", "#f7f7f7"),
    ]
    widths = [0.8, 1.2, 0.9, 0.8, 0.6, 1.4, 0.7, 0.8, 0.8]
    fig, ax = plt.subplots(figsize=(12.2, 4.4), dpi=320)
    ax.set_facecolor("white")
    x = 0.0
    for (label, color), width in zip(layers, widths):
        rect = Rectangle((x, 0.4), width, 1.4, facecolor=color, edgecolor="#666666", linewidth=1.1)
        ax.add_patch(rect)
        ax.text(x + width / 2.0, 1.1, label, ha="center", va="center", fontsize=13, fontweight="bold")
        x += width
    arrow = FancyArrowPatch((0.2, 2.15), (x - 0.2, 2.15), arrowstyle="->", mutation_scale=16, linewidth=1.8, color="#444444")
    ax.add_patch(arrow)
    ax.text(0.1, 2.35, "Incident light", fontsize=13, fontweight="bold", ha="left", va="bottom")
    ax.text(1.0, 0.15, "glass front surface = incoherent", fontsize=11.5, fontweight="bold", color="#444444")
    ax.text(4.2, 0.15, "thin-film stack = coherent", fontsize=11.5, fontweight="bold", color="#444444")
    ax.text(6.3, 2.35, "observable = R_total", fontsize=13, fontweight="bold", color="#005b96", ha="left")
    ax.set_xlim(-0.1, x + 0.1)
    ax.set_ylim(0.0, 2.7)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def save_structure_pair(fig: plt.Figure, png_path: Path, svg_path: Path) -> None:
    fig.savefig(png_path, dpi=320, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)


def draw_common_structure_header(ax: plt.Axes, total_width: float) -> None:
    arrow = FancyArrowPatch((0.2, 2.15), (total_width - 0.2, 2.15), arrowstyle="->", mutation_scale=16, linewidth=1.8, color="#444444")
    ax.add_patch(arrow)
    ax.text(0.1, 2.35, "Incident light", fontsize=13, fontweight="bold", ha="left", va="bottom")
    ax.text(total_width - 0.1, 2.35, "observable = R_total", fontsize=13, fontweight="bold", color="#005b96", ha="right", va="bottom")
    ax.text(0.95, 0.15, "glass front surface = incoherent", fontsize=11.5, fontweight="bold", color="#444444", ha="left")
    ax.text(total_width * 0.48, 0.15, "thin-film stack = coherent", fontsize=11.5, fontweight="bold", color="#444444", ha="left")


def render_mechanism_structure(
    *,
    png_path: Path,
    svg_path: Path,
    mechanism: str,
    cue_text: str,
    footer_note: str,
) -> None:
    layers: list[dict[str, object]] = [dict(item) for item in LAYER_BASE]
    highlight_ids: set[str] = set()
    annotation_target = None
    note_color = "#bf5b04"
    gap_face = "#ffffff"
    gap_edge = "#d95f02"
    bema_face = "#fff0d8"
    bema_edge = "#cc6d1f"
    red_outline = "#cf4d32"

    if mechanism == "baseline":
        footer_note = "pristine full-device baseline"
    elif mechanism == "thickness":
        highlight_ids = {"pvk"}
        annotation_target = ("pvk", "PVK thickness scan\n$d_{PVK}$ = variable", red_outline)
    elif mechanism == "rear_bema":
        insert_at = next(i for i, layer in enumerate(layers) if layer["id"] == "c60")
        layers[insert_at:insert_at] = [
            {"id": "pvk_bulk", "label": "PVK_bulk", "thickness": "", "color": "#d8e8cf", "width": 1.05},
            {"id": "rear_bema", "label": "BEMA\n(PVK/C60)", "thickness": "", "color": bema_face, "width": 0.62},
        ]
        next(i for i, layer in enumerate(layers) if layer["id"] == "c60")
        layers[[layer["id"] for layer in layers].index("c60")]["label"] = "C60_bulk"
        layers[[layer["id"] for layer in layers].index("pvk") : [layer["id"] for layer in layers].index("pvk") + 1] = []
        highlight_ids = {"rear_bema"}
        annotation_target = ("rear_bema", "rear-only intermixing\n50/50 PVK + C60", bema_edge)
    elif mechanism == "front_bema":
        insert_at = next(i for i, layer in enumerate(layers) if layer["id"] == "pvk")
        layers[insert_at:insert_at] = [
            {"id": "front_bema", "label": "BEMA_front\n(NiOx/PVK proxy)", "thickness": "", "color": bema_face, "width": 0.78},
            {"id": "pvk_bulk", "label": "PVK_bulk", "thickness": "", "color": "#d8e8cf", "width": 1.02},
        ]
        layers[[layer["id"] for layer in layers].index("pvk") : [layer["id"] for layer in layers].index("pvk") + 1] = []
        highlight_ids = {"front_bema"}
        annotation_target = ("front_bema", "front-only transition-layer proxy\n50/50 NiOx + PVK", bema_edge)
    elif mechanism == "rear_gap":
        insert_at = next(i for i, layer in enumerate(layers) if layer["id"] == "c60")
        layers[insert_at:insert_at] = [
            {"id": "rear_gap", "label": "Air gap\n(rear)", "thickness": "", "color": gap_face, "width": 0.52},
        ]
        highlight_ids = {"rear_gap"}
        annotation_target = ("rear_gap", "real separation layer\nat rear interface", gap_edge)
    elif mechanism == "front_gap":
        insert_at = next(i for i, layer in enumerate(layers) if layer["id"] == "pvk")
        layers[insert_at:insert_at] = [
            {"id": "front_gap", "label": "Air gap\n(front)", "thickness": "", "color": gap_face, "width": 0.52},
        ]
        highlight_ids = {"front_gap"}
        annotation_target = ("front_gap", "real separation layer\nat front interface", gap_edge)

    fig, ax = plt.subplots(figsize=(12.4, 4.5), dpi=320)
    ax.set_facecolor("white")
    x = 0.0
    centers: dict[str, tuple[float, float, float]] = {}
    for layer in layers:
        width = float(layer["width"])
        layer_id = str(layer["id"])
        face = str(layer["color"])
        edge = "#666666"
        lw = 1.15
        if layer_id in highlight_ids:
            edge = red_outline if "bema" not in layer_id and "gap" not in layer_id else (gap_edge if "gap" in layer_id else bema_edge)
            lw = 2.2
        rect = Rectangle((x, 0.42), width, 1.38, facecolor=face, edgecolor=edge, linewidth=lw)
        ax.add_patch(rect)
        label = str(layer["label"])
        thickness = str(layer["thickness"])
        text = label if not thickness else f"{label}\n{thickness}"
        ax.text(x + width / 2.0, 1.11, text, ha="center", va="center", fontsize=12.5, fontweight="bold")
        centers[layer_id] = (x + width / 2.0, x, x + width)
        x += width

    draw_common_structure_header(ax, x)
    ax.text(x * 0.5, 1.97, footer_note, fontsize=12, fontweight="bold", color="#666666", ha="center", va="center")
    if annotation_target is not None:
        target_id, label_text, color = annotation_target
        cx, x0, x1 = centers[target_id]
        ax.annotate(
            label_text,
            xy=(cx, 1.82),
            xytext=(cx, 2.55),
            ha="center",
            va="bottom",
            fontsize=14.5,
            fontweight="bold",
            color=color,
            arrowprops={"arrowstyle": "-|>", "color": color, "lw": 1.9},
        )
    ax.text(x * 0.5, -0.02, cue_text, fontsize=12, fontweight="bold", color=note_color, ha="center", va="top")
    ax.set_xlim(-0.1, x + 0.1)
    ax.set_ylim(-0.18, 2.85)
    ax.axis("off")
    fig.tight_layout()
    save_structure_pair(fig, png_path, svg_path)


def render_structure_overview(png_path: Path, svg_path: Path) -> None:
    fig, axes = plt.subplots(1, 5, figsize=(15.4, 4.7), dpi=320)
    specs = [
        ("Thickness", "PVK", "#cf4d32", "PVK\nvaried"),
        ("Rear-BEMA", "rear BEMA", "#cc6d1f", "mix"),
        ("Front-BEMA", "front BEMA", "#cc6d1f", "proxy"),
        ("Rear-gap", "rear gap", "#d95f02", "gap"),
        ("Front-gap", "front gap", "#d95f02", "gap"),
    ]
    for ax, (title, kind, color, badge) in zip(axes, specs):
        ax.set_facecolor("white")
        x = 0.0
        local_layers = [dict(item) for item in LAYER_BASE]
        highlights = {"pvk"} if kind == "PVK" else set()
        if kind == "rear BEMA":
            idx = next(i for i, l in enumerate(local_layers) if l["id"] == "c60")
            local_layers[idx:idx] = [{"id": "rear_bema", "label": "", "thickness": "", "color": "#fff0d8", "width": 0.34}]
            highlights = {"rear_bema"}
        elif kind == "front BEMA":
            idx = next(i for i, l in enumerate(local_layers) if l["id"] == "pvk")
            local_layers[idx:idx] = [{"id": "front_bema", "label": "", "thickness": "", "color": "#fff0d8", "width": 0.36}]
            highlights = {"front_bema"}
        elif kind == "rear gap":
            idx = next(i for i, l in enumerate(local_layers) if l["id"] == "c60")
            local_layers[idx:idx] = [{"id": "rear_gap", "label": "", "thickness": "", "color": "#ffffff", "width": 0.28}]
            highlights = {"rear_gap"}
        elif kind == "front gap":
            idx = next(i for i, l in enumerate(local_layers) if l["id"] == "pvk")
            local_layers[idx:idx] = [{"id": "front_gap", "label": "", "thickness": "", "color": "#ffffff", "width": 0.28}]
            highlights = {"front_gap"}
        centers = {}
        for layer in local_layers:
            width = float(layer["width"]) * 0.64
            layer_id = str(layer["id"])
            edge = color if layer_id in highlights else "#777777"
            lw = 2.0 if layer_id in highlights else 0.8
            rect = Rectangle((x, 0.38), width, 0.88, facecolor=str(layer["color"]), edgecolor=edge, linewidth=lw)
            ax.add_patch(rect)
            centers[layer_id] = x + width / 2.0
            x += width
        if highlights:
            hid = next(iter(highlights))
            ax.text(centers[hid], 1.48, badge, ha="center", va="bottom", fontsize=10.5, fontweight="bold", color=color)
            ax.plot([centers[hid], centers[hid]], [1.28, 1.44], color=color, linewidth=1.3)
        ax.set_title(title, fontsize=12.5, fontweight="bold", pad=8)
        ax.set_xlim(-0.05, x + 0.05)
        ax.set_ylim(0.12, 1.72)
        ax.axis("off")
    fig.suptitle("Structure overview of the five single-factor mechanisms", fontsize=18, fontweight="bold", y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save_structure_pair(fig, png_path, svg_path)


def render_summary_matrix(output_path: Path) -> None:
    rows = [
        ["Thickness", "d_PVK", "rear", "global fringe phase / peak-valley shift"],
        ["Rear-BEMA", "rear-only BEMA", "rear", "local envelope / amplitude perturbation"],
        ["Front-BEMA", "front-only BEMA", "front + transition", "background + slope/envelope distortion"],
        ["Rear-gap", "rear air-gap", "transition + rear", "phase-like reconstruction / nonlinear response"],
        ["Front-gap", "front air-gap", "front + transition", "front background + transition reconstruction + rear secondary coupling"],
    ]
    fig, ax = plt.subplots(figsize=(12.6, 4.8), dpi=320)
    ax.axis("off")
    table = ax.table(
        cellText=rows,
        colLabels=["Mechanism", "Modified factor", "Main sensitive window", "Fingerprint on R_total"],
        colColours=["#d9e6f2"] * 4,
        cellLoc="left",
        loc="center",
        colWidths=[0.14, 0.19, 0.21, 0.46],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11.5)
    table.scale(1, 2.0)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#777777")
        if row == 0:
            cell.set_text_props(weight="bold", color="#222222")
        else:
            cell.set_facecolor("#fbfbfb" if row % 2 else "#f3f3f3")
    ax.set_title("Five single-factor dictionaries on the observable R_total", fontsize=18, fontweight="bold", pad=18)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def render_appendix_local_zoom(compare_frame: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10.8, 7.6), dpi=320, constrained_layout=True, sharex=True)
    wl = compare_frame["Wavelength_nm"].to_numpy(dtype=float)
    axes[0].plot(wl, compare_frame["k_v1"].to_numpy(dtype=float), color="#b03a2e", linewidth=2.0, label="v1")
    axes[0].plot(wl, compare_frame["k_v2"].to_numpy(dtype=float), color="#005b96", linewidth=2.0, label="v2")
    axes[0].axvline(750.0, color="#666666", linestyle=":", linewidth=1.0)
    axes[0].set_ylabel("k", fontweight="bold")
    axes[0].set_title("PVK band-edge surrogate fix near the 749/750 nm seam", fontweight="bold")
    axes[0].grid(True)
    axes[0].legend(loc="best")
    axes[1].plot(wl, compare_frame["eps2_v1"].to_numpy(dtype=float), color="#b03a2e", linewidth=2.0, label="eps2 v1")
    axes[1].plot(wl, compare_frame["eps2_v2"].to_numpy(dtype=float), color="#005b96", linewidth=2.0, label="eps2 v2")
    axes[1].axvline(750.0, color="#666666", linestyle=":", linewidth=1.0)
    axes[1].set_xlabel("Wavelength (nm)", fontweight="bold")
    axes[1].set_ylabel("eps2", fontweight="bold")
    axes[1].grid(True)
    axes[1].legend(loc="best")
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def render_appendix_pristine_compare(v1_frame: pd.DataFrame, v2_frame: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.2, 5.8), dpi=320)
    apply_window_background(ax)
    ax.plot(v1_frame["Wavelength_nm"].to_numpy(dtype=float), v1_frame["R_total"].to_numpy(dtype=float) * 100.0, color="#b03a2e", linewidth=2.0, label="PVK v1 pristine")
    ax.plot(v2_frame["Wavelength_nm"].to_numpy(dtype=float), v2_frame["R_total"].to_numpy(dtype=float) * 100.0, color="#005b96", linewidth=2.0, label="PVK v2 pristine")
    finalize_axes(ax, "R_total (%)", "Pristine R_total before and after the PVK surrogate fix")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def write_text(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def copy_alias(source: Path, destination: Path) -> None:
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)


def build_baseline_assets() -> None:
    slide = slide_paths(BASELINE_DIR)
    frame = pd.read_csv(PHASE_A1_2_PATH)
    schematic = BASELINE_DIR / "baseline_structure_schematic.png"
    structure_png = BASELINE_DIR / "structure_schematic.png"
    structure_svg = BASELINE_DIR / "structure_schematic.svg"
    curve = BASELINE_DIR / "baseline_rtotal_curve.png"
    render_mechanism_structure(
        png_path=structure_png,
        svg_path=structure_svg,
        mechanism="baseline",
        cue_text="pristine full-device baseline",
        footer_note="pristine full-device baseline",
    )
    copy_alias(structure_png, schematic)
    render_baseline_curve(frame, curve)
    copy_alias(structure_png, slide.main_png)
    copy_alias(curve, slide.secondary_png)
    write_text(
        slide.text_md,
        """
# 标题建议
完整器件 `R_total` baseline：后续所有机制比较的统一起点

# 主结论
先在完整器件结构上建立实验可见量 `R_total` 的理论基线，后续所有 Phase 都是在同一 baseline 上逐个引入单因素。

# 要点
- 观测对象固定为 `R_total`，对应厚玻璃前表面与后侧相干薄膜堆栈的级联结果。
- 同一 baseline 被后续 thickness、BEMA 和 air-gap 五类机制共享，保证比较口径一致。
- 三个窗口 `front / transition / rear` 为后续机制判别提供统一语言。

Structure cue: pristine full-device baseline.

# 讲稿提示
这一页先把讨论对象固定下来：不是单层材料，也不是某个局部界面，而是完整器件在实验上真正可见的 `R_total`。后面所有单因素扫描都不再改 baseline 定义，只比较“在同一个 baseline 上加入某一个因素后，`R_total` 会怎样变化”。
        """,
    )
    write_text(
        slide.source_md,
        f"""
# Source Manifest

- 原始 CSV：
  - `{PHASE_A1_2_PATH.relative_to(PROJECT_ROOT).as_posix()}`
- 参考报告：
  - `{PHASE_A1_2_REPORT.relative_to(PROJECT_ROOT).as_posix()}`
- 直接复用图：无
- 基于已有数据重绘：
  - `structure_schematic.png/.svg`：新绘制的 baseline 结构示意图
  - `baseline_structure_schematic.png`：与历史命名兼容的同图副本
  - `baseline_rtotal_curve.png`：基于 `phaseA1_2_pristine_baseline.csv` 仅重绘 `R_total`
- 结构图实现方式：
  - 程序绘制（matplotlib），未使用 imagegen 位图生成
- 结构层序定义：
  - `Air / Glass / ITO / NiOx / SAM / PVK / C60 / Ag / Air`
- 代表参数：
  - pristine baseline
  - windows: front `400–650 nm`, transition `650–810 nm`, rear `810–1100 nm`
        """,
    )


def build_mechanism_assets(
    directory: Path,
    frame: pd.DataFrame,
    param_column: str,
    delta_column: str,
    selected_values: list[float],
    main_name: str,
    secondary_name: str,
    main_title: str,
    secondary_title: str,
    legend_title: str,
    y_label: str,
    structure_mode: str,
    structure_cue: str,
    structure_note: str,
    slide_text: str,
    source_manifest: str,
) -> None:
    slide = slide_paths(directory)
    main_path = directory / main_name
    secondary_path = directory / secondary_name
    structure_png = directory / "structure_schematic.png"
    structure_svg = directory / "structure_schematic.svg"
    render_mechanism_structure(
        png_path=structure_png,
        svg_path=structure_svg,
        mechanism=structure_mode,
        cue_text=structure_cue,
        footer_note=structure_note,
    )
    render_heatmap(frame, param_column, delta_column, main_path, main_title, y_label)
    render_selected_curves(frame, param_column, selected_values, secondary_path, secondary_title, legend_title)
    copy_alias(main_path, slide.main_png)
    copy_alias(secondary_path, slide.secondary_png)
    write_text(slide.text_md, slide_text)
    write_text(slide.source_md, source_manifest)


def build_summary_assets() -> None:
    slide = slide_paths(SUMMARY_DIR)
    matrix = SUMMARY_DIR / "mechanism_summary_matrix.png"
    overview_png = SUMMARY_DIR / "mechanism_structure_overview.png"
    overview_svg = SUMMARY_DIR / "mechanism_structure_overview.svg"
    render_summary_matrix(matrix)
    render_structure_overview(overview_png, overview_svg)
    copy_alias(matrix, slide.main_png)
    copy_alias(overview_png, slide.secondary_png)
    write_text(
        slide.text_md,
        """
# 标题建议
五类单因素机制字典：统一落在 `R_total`

# 主结论
从 Phase A 到 C，我们已经建立了基于完整器件 `R_total` 的五类单因素机制字典，重点不在信号大小，而在不同机制的窗口分布与谱形特征差异。

# 要点
- thickness 主导后窗 fringe 的全局相位/峰谷位置漂移。
- BEMA 更接近 intermixing / transition-layer，gap 更接近 real separation。
- 真正可用于区分机制的核心不是单个点值，而是 `R_total` 的窗口分布与谱形形态。

Structure cue: five mechanisms are compared on the same full-device layer stack, with only one highlighted modification each time.

# 讲稿提示
可以把这一页当成整个 Phase A→C 的收束页。前面所有单因素扫描最后都汇到这张矩阵里：每一类机制究竟改了什么物理量、主要影响哪个窗口、在 `R_total` 上留下什么指纹。后续若要解释实验异常，先看它更像矩阵中的哪一类，而不是直接跳到联合拟合。
        """,
    )
    write_text(
        slide.source_md,
        """
# Source Manifest

- 原始来源：
  - `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
  - `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
  - `data/processed/phaseB2/phaseB2_front_bema_scan.csv`
  - `data/processed/phaseC1a/phaseC1a_rear_air_gap_scan.csv`
  - `data/processed/phaseC1b/phaseC1b_front_air_gap_scan.csv`
- 参考报告：
  - `results/report/phaseA2_pvk_thickness_scan/PHASE_A2_REPORT.md`
  - `results/report/phaseB1_rear_bema_sandbox/PHASE_B1_REPORT.md`
  - `results/report/phaseB2_front_bema_sandbox/PHASE_B2_REPORT.md`
  - `results/report/phaseC1a_rear_air_gap_sandbox/PHASE_C1A_REPORT.md`
  - `results/report/phaseC1b_front_air_gap_sandbox/PHASE_C1B_REPORT.md`
- 直接复用图：无
- 基于已有结论重绘：
  - `mechanism_summary_matrix.png`
  - `mechanism_structure_overview.png/.svg`
- 结构图实现方式：
  - 程序绘制（matplotlib），未使用 imagegen 位图生成
- 代表参数：
  - thickness: `650 / 750 / 850 nm`
  - rear-BEMA: `10 / 20 / 30 nm`
  - front-BEMA: `10 / 20 nm`
  - rear-gap: `1 / 2 / 5 / 10 nm`
  - front-gap: `1 / 2 / 5 / 10 / 20 nm`
        """,
    )


def build_appendix_assets() -> None:
    slide = slide_paths(APPENDIX_DIR)
    v1 = pd.read_csv(PHASE_A1_PATH)
    v2 = pd.read_csv(PHASE_A1_2_PATH)
    compare = pd.read_csv(PHASE_A1_2_COMPARE_PATH)
    zoom = APPENDIX_DIR / "pvk_surrogate_fix_local_zoom.png"
    compare_png = APPENDIX_DIR / "pvk_surrogate_fix_pristine_compare.png"
    render_appendix_local_zoom(compare, zoom)
    render_appendix_pristine_compare(v1, v2, compare_png)
    copy_alias(zoom, slide.main_png)
    copy_alias(compare_png, slide.secondary_png)
    write_text(
        slide.text_md,
        """
# 标题建议
Appendix: PVK surrogate seam fix

# 主结论
`749/750 nm` 的 seam artifact 已在材料层修复，影响主要局限于 band-edge 邻域，后窗 fringe 保真保持不变。

# 要点
- 修复发生在 PVK `n-k` surrogate 层，而不是在反射谱层做后处理平滑。
- `R_total` 的非物理跳变被压低为连续过渡，没有破坏后窗微腔结构。
- 该修复是后续 thickness / BEMA / gap 机制比较的前提条件。

# 讲稿提示
这一页只作为附录使用，目的是向听众交代：后续所有 Phase 的比较不是建立在带有工程接缝伪影的材料表上，而是建立在已经修复过 band-edge seam 的 `PVK surrogate v2` 上。因此正文里看到的 gap 或 BEMA 指纹，不是 `749/750 nm` 接缝的人为放大。
        """,
    )
    write_text(
        slide.source_md,
        f"""
# Source Manifest

- 原始 CSV：
  - `{PHASE_A1_PATH.relative_to(PROJECT_ROOT).as_posix()}`
  - `{PHASE_A1_2_PATH.relative_to(PROJECT_ROOT).as_posix()}`
  - `{PHASE_A1_2_COMPARE_PATH.relative_to(PROJECT_ROOT).as_posix()}`
- 参考报告：
  - `{PHASE_A1_2_REPORT.relative_to(PROJECT_ROOT).as_posix()}`
- 直接复用图：无
- 基于已有数据重绘：
  - `pvk_surrogate_fix_local_zoom.png`
  - `pvk_surrogate_fix_pristine_compare.png`
- 代表参数：
  - seam region: `730–770 nm`
  - pristine comparison: v1 vs v2
        """,
    )


def write_top_manifest() -> None:
    content = """
# Phase A→C PPT Asset Manifest

## 整体主线

1. 先用完整器件结构 TMM 建立实验可见量 `R_total` 的理论 baseline。
2. 然后逐个只引入一个因素，比较其对 `R_total` 的影响。
3. 最终形成五类单因素机制字典：
   - thickness
   - rear-BEMA
   - front-BEMA
   - rear-gap
   - front-gap

## 页面对照

### 01 Baseline
- 主图：`01_baseline/main_figure.png`
- 次图：`01_baseline/secondary_figure.png`
- 建议讲法：先固定完整器件、固定观测量 `R_total`，为后续所有单因素比较建立统一参考。

### 02 Thickness
- 主图：`02_thickness/main_figure.png`
- 次图：`02_thickness/secondary_figure.png`
- 建议讲法：强调 `d_PVK` 主导后窗 fringe 的全局相位/峰谷位置漂移，本质是全局 cavity length change。

### 03 Rear-BEMA
- 主图：`03_rear_bema/main_figure.png`
- 次图：`03_rear_bema/secondary_figure.png`
- 建议讲法：强调 rear-BEMA 主要改变后窗局部包络/振幅，不像 thickness 那样做整体 fringe 平移。

### 04 Front-BEMA
- 主图：`04_front_bema/main_figure.png`
- 次图：`04_front_bema/secondary_figure.png`
- 建议讲法：强调 front-BEMA 主要作用在 front + transition，是 transition-layer / intermixing proxy，不是 real gap。

### 05 Rear-gap
- 主图：`05_rear_gap/main_figure.png`
- 次图：`05_rear_gap/secondary_figure.png`
- 建议讲法：强调 rear-gap 是真实 rear-interface separation，表现为 transition + rear 的相位类重构和非线性响应。

### 06 Front-gap
- 主图：`06_front_gap/main_figure.png`
- 次图：`06_front_gap/secondary_figure.png`
- 建议讲法：强调 front-gap 主要作用在 front → transition，但会次级牵动 rear-window，且比 front-BEMA 更强、更非线性。

### 07 Summary
- 主图：`07_summary/main_figure.png`
- 次图：`07_summary/secondary_figure.png`
- 建议讲法：用矩阵收束五类机制，重点不是信号大小，而是窗口分布和谱形特征差异。

### Appendix: PVK surrogate fix
- 主图：`appendix_pvk_surrogate_fix/main_figure.png`
- 次图：`appendix_pvk_surrogate_fix/secondary_figure.png`
- 建议讲法：只在附录中解释 `749/750 nm` seam fix，说明正文结论建立在已修复的 surrogate 上。
"""
    write_text(ASSET_ROOT / "00_manifest.md", content)


def update_report_index() -> None:
    readme_path = PROJECT_ROOT / "results" / "report" / "README.md"
    manifest_path = PROJECT_ROOT / "results" / "report" / "report_manifest.csv"
    readme_text = readme_path.read_text(encoding="utf-8")
    section = """
### `ppt_phaseAtoC_assets/`

- 主题：Phase A→C 的 PPT 汇报资产整理
- 主要内容：
  - 基于既有 `data/processed` 结果重绘的 `R_total-only` 主汇报图
  - 每页的 `slide_text.md` 与 `source_manifest.md`
  - 一份总 `00_manifest.md` 用于快速组装明日 PPT
""".strip()
    if "ppt_phaseAtoC_assets" not in readme_text:
        readme_path.write_text(readme_text.rstrip() + "\n\n" + section + "\n", encoding="utf-8")
    manifest = pd.read_csv(manifest_path)
    if "ppt_phaseAtoC_assets" not in manifest["report_dir"].tolist():
        manifest = pd.concat(
            [
                manifest,
                pd.DataFrame(
                    [
                        {
                            "report_dir": "ppt_phaseAtoC_assets",
                            "phase": "Phase A→C",
                            "theme": "PPT-ready R_total-only asset pack",
                            "primary_markdown": "ppt_phaseAtoC_assets/00_manifest.md",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")


def main() -> None:
    configure_style()
    ensure_dirs()

    build_baseline_assets()

    thickness_frame = pd.read_csv(PHASE_A2_SCAN_PATH)
    build_mechanism_assets(
        directory=THICKNESS_DIR,
        frame=thickness_frame,
        param_column="d_PVK_nm",
        delta_column="Delta_R_total_vs_700nm",
        selected_values=[650.0, 700.0, 750.0, 850.0],
        main_name="thickness_deltaRtotal_heatmap.png",
        secondary_name="thickness_selected_rtotal_curves.png",
        main_title="PVK thickness fingerprint on R_total",
        secondary_title="Selected R_total curves under PVK thickness variation",
        legend_title="d_PVK",
        y_label="d_PVK (nm)",
        structure_mode="thickness",
        structure_cue="only PVK thickness is varied.",
        structure_note="only PVK thickness is varied",
        slide_text="""
# 标题建议
Thickness dictionary on `R_total`

# 主结论
`d_PVK` 主要通过后窗 fringe 的全局相位/峰谷位置系统漂移来调制 `R_total`。

# 要点
- modified factor: `d_PVK`
- main sensitive window: `rear window`
- fingerprint: `rear-window fringe global phase / peak-valley shift`
- interpretation: `global cavity length change`

Structure cue: only PVK thickness is varied.

# 讲稿提示
这一页只改一个变量：PVK 厚度。可以看到最显著的变化集中在后窗，且形态上更像整套 fringe 的位置系统漂移，而不是某个局部窗口的包络扭曲。所以 thickness 的物理含义更接近全局光程变化，是后续区分各类界面缺陷的第一条基准线。
        """,
        source_manifest=f"""
# Source Manifest

- 原始 CSV：
  - `{PHASE_A2_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`
- 参考报告：
  - `{PHASE_A2_REPORT.relative_to(PROJECT_ROOT).as_posix()}`
  - `{PHASE_A2_1_REPORT.relative_to(PROJECT_ROOT).as_posix()}`
- 直接复用图：无
- 基于已有数据重绘：
  - `structure_schematic.png/.svg`
  - `thickness_deltaRtotal_heatmap.png`
  - `thickness_selected_rtotal_curves.png`
- 结构图实现方式：
  - 程序绘制（matplotlib），未使用 imagegen 位图生成
- 结构层序定义：
  - `Air / Glass / ITO / NiOx / SAM / PVK / C60 / Ag / Air`
- phase 物理对应：
  - 仅高亮 `PVK`，表示 `d_PVK` 为唯一变化量
- 代表参数：
  - thickness: `650 / 700 / 750 / 850 nm`
  - observable: `R_total`
        """,
    )

    rear_bema_frame = pd.read_csv(PHASE_B1_SCAN_PATH)
    build_mechanism_assets(
        directory=REAR_BEMA_DIR,
        frame=rear_bema_frame,
        param_column="d_BEMA_rear_nm",
        delta_column="Delta_R_total_vs_pristine",
        selected_values=[0.0, 10.0, 20.0, 30.0],
        main_name="rear_bema_deltaRtotal_heatmap.png",
        secondary_name="rear_bema_selected_rtotal_curves.png",
        main_title="Rear-only BEMA fingerprint on R_total",
        secondary_title="Selected R_total curves under rear-only BEMA",
        legend_title="d_BEMA,rear",
        y_label="d_BEMA,rear (nm)",
        structure_mode="rear_bema",
        structure_cue="a mixed BEMA layer is inserted at the PVK/C60 rear interface.",
        structure_note="rear-interface intermixing proxy",
        slide_text="""
# 标题建议
Rear-interface BEMA dictionary on `R_total`

# 主结论
rear-only BEMA 主要在后窗留下局部包络/振幅微扰，不像 thickness 那样驱动全局 fringe 相位平移。

# 要点
- modified factor: `rear-only BEMA`
- main sensitive window: `rear window`
- fingerprint: `local envelope / amplitude perturbation`
- interpretation: `rear-interface intermixing rather than real separation`

Structure cue: a mixed BEMA layer is inserted at the PVK/C60 rear interface.

# 讲稿提示
这页和 thickness 最好连着讲。两者都主要影响后窗，但形态完全不同：thickness 更像整体 fringe 位移，rear-BEMA 更像后窗局部包络和振幅被扰动。所以 rear-BEMA 更接近 intermixing / transition-layer 缺陷，而不是真实几何分离。
        """,
        source_manifest=f"""
# Source Manifest

- 原始 CSV：
  - `{PHASE_B1_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`
- 参考报告：
  - `{PHASE_B1_REPORT.relative_to(PROJECT_ROOT).as_posix()}`
- 直接复用图：无
- 基于已有数据重绘：
  - `structure_schematic.png/.svg`
  - `rear_bema_deltaRtotal_heatmap.png`
  - `rear_bema_selected_rtotal_curves.png`
- 结构图实现方式：
  - 程序绘制（matplotlib），未使用 imagegen 位图生成
- 结构层序定义：
  - `Air / Glass / ITO / NiOx / SAM / PVK_bulk / BEMA(PVK/C60) / C60_bulk / Ag / Air`
- phase 物理对应：
  - 高亮后界面 BEMA 混合层，表示 rear-only intermixing
- 代表参数：
  - rear-BEMA: `0 / 10 / 20 / 30 nm`
  - observable: `R_total`
        """,
    )

    front_bema_frame = pd.read_csv(PHASE_B2_SCAN_PATH)
    build_mechanism_assets(
        directory=FRONT_BEMA_DIR,
        frame=front_bema_frame,
        param_column="d_BEMA_front_nm",
        delta_column="Delta_R_total_vs_pristine",
        selected_values=[0.0, 10.0, 20.0],
        main_name="front_bema_deltaRtotal_heatmap.png",
        secondary_name="front_bema_selected_rtotal_curves.png",
        main_title="Front-only BEMA fingerprint on R_total",
        secondary_title="Selected R_total curves under front-only BEMA",
        legend_title="d_BEMA,front",
        y_label="d_BEMA,front (nm)",
        structure_mode="front_bema",
        structure_cue="a front-side transition-layer proxy is inserted near the SAM/PVK interface.",
        structure_note="front-only transition-layer proxy",
        slide_text="""
# 标题建议
Front-interface BEMA proxy on `R_total`

# 主结论
front-only BEMA 主要改变前窗背景与过渡区包络/斜率，是 front-side optical transition-layer proxy，而不是 air-gap。

# 要点
- modified factor: `front-only BEMA`
- main sensitive window: `front + transition`
- fingerprint: `front background change + transition envelope/slope distortion`
- interpretation: `front-interface transition-layer optical proxy`

Structure cue: a front-side transition-layer proxy is inserted near the SAM/PVK interface.

# 讲稿提示
这里要特别强调它不是 gap。front-BEMA 的物理含义是前界面 intermixing / transition-layer proxy，所以它更像平滑地改背景、改过渡区斜率，而不是引入真实分离层后的强非线性结构重构。这一点和后面的 front-gap 要明确区分开。
        """,
        source_manifest=f"""
# Source Manifest

- 原始 CSV：
  - `{PHASE_B2_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`
- 参考报告：
  - `{PHASE_B2_REPORT.relative_to(PROJECT_ROOT).as_posix()}`
- 直接复用图：无
- 基于已有数据重绘：
  - `structure_schematic.png/.svg`
  - `front_bema_deltaRtotal_heatmap.png`
  - `front_bema_selected_rtotal_curves.png`
- 结构图实现方式：
  - 程序绘制（matplotlib），未使用 imagegen 位图生成
- 结构层序定义：
  - `Air / Glass / ITO / NiOx / SAM / BEMA_front(NiOx/PVK proxy) / PVK_bulk / C60 / Ag / Air`
- phase 物理对应：
  - 高亮前界面 proxy BEMA 层，表示 front-side transition-layer/intermixing proxy
- 代表参数：
  - front-BEMA: `0 / 10 / 20 nm`
  - observable: `R_total`
        """,
    )

    rear_gap_frame = pd.read_csv(PHASE_C1A_SCAN_PATH)
    build_mechanism_assets(
        directory=REAR_GAP_DIR,
        frame=rear_gap_frame,
        param_column="d_gap_rear_nm",
        delta_column="Delta_R_total_vs_pristine",
        selected_values=[0.0, 1.0, 2.0, 5.0, 10.0],
        main_name="rear_gap_deltaRtotal_heatmap.png",
        secondary_name="rear_gap_selected_rtotal_curves.png",
        main_title="Rear air-gap fingerprint on R_total",
        secondary_title="Selected R_total curves under rear air-gap",
        legend_title="d_gap,rear",
        y_label="d_gap,rear (nm)",
        structure_mode="rear_gap",
        structure_cue="a real air separation layer is inserted at the PVK/C60 rear interface.",
        structure_note="real separation layer at rear interface",
        slide_text="""
# 标题建议
Rear-interface real separation on `R_total`

# 主结论
rear-gap 在 transition + rear 窗口引起更强、更非线性的相位类重构，不像 thickness 的全局平移，也强于 rear-BEMA 的局部包络微扰。

# 要点
- modified factor: `rear air-gap`
- main sensitive window: `transition + rear`
- fingerprint: `phase-like reconstruction / nonlinear response`
- interpretation: `rear-interface real separation layer`

Structure cue: a real air separation layer is inserted at the PVK/C60 rear interface.

# 讲稿提示
这页可以作为正文重点页之一。rear-gap 和 rear-BEMA 都在后界面，但前者是 real separation，后者是 intermixing。rear-gap 在 `R_total` 上更强、更非线性，也更像真正关心的隐性剥离模型，因此它和 rear-BEMA 不能混成一个“后界面缺陷”去讲。
        """,
        source_manifest=f"""
# Source Manifest

- 原始 CSV：
  - `{PHASE_C1A_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`
- 参考报告：
  - `{PHASE_C1A_REPORT.relative_to(PROJECT_ROOT).as_posix()}`
- 直接复用图：无
- 基于已有数据重绘：
  - `structure_schematic.png/.svg`
  - `rear_gap_deltaRtotal_heatmap.png`
  - `rear_gap_selected_rtotal_curves.png`
- 结构图实现方式：
  - 程序绘制（matplotlib），未使用 imagegen 位图生成
- 结构层序定义：
  - `Air / Glass / ITO / NiOx / SAM / PVK / Air gap / C60 / Ag / Air`
- phase 物理对应：
  - 高亮后界面真实空气隙，表示 rear-interface real separation
- 代表参数：
  - rear-gap: `0 / 1 / 2 / 5 / 10 nm`
  - observable: `R_total`
        """,
    )

    front_gap_frame = pd.read_csv(PHASE_C1B_SCAN_PATH)
    build_mechanism_assets(
        directory=FRONT_GAP_DIR,
        frame=front_gap_frame,
        param_column="d_gap_front_nm",
        delta_column="Delta_R_total_vs_pristine",
        selected_values=[0.0, 1.0, 2.0, 5.0, 10.0, 20.0],
        main_name="front_gap_deltaRtotal_heatmap.png",
        secondary_name="front_gap_selected_rtotal_curves.png",
        main_title="Front air-gap fingerprint on R_total",
        secondary_title="Selected R_total curves under front air-gap",
        legend_title="d_gap,front",
        y_label="d_gap,front (nm)",
        structure_mode="front_gap",
        structure_cue="a real air separation layer is inserted at the SAM/PVK front interface.",
        structure_note="real separation layer at front interface",
        slide_text="""
# 标题建议
Front-interface real separation on `R_total`

# 主结论
front-gap 主要作用在 front → transition，但会次级牵动 rear-window，因此它比 front-BEMA 更强、更非线性，也更接近真实前界面分离层。

# 要点
- modified factor: `front air-gap`
- main sensitive window: `front → transition`
- fingerprint: `front background change + transition reconstruction + secondary rear coupling`
- interpretation: `front-interface real separation layer`

Structure cue: a real air separation layer is inserted at the SAM/PVK front interface.

# 讲稿提示
front-gap 和 front-BEMA 都主要影响前窗到过渡区，但两者不能混淆。front-BEMA 更像平滑的 transition-layer proxy；front-gap 则是 real separation，会产生更强的过渡区重构，并把影响次级传到后窗。这一页最好和上一页 rear-gap 成对讲，形成前/后界面 gap 的对照。
        """,
        source_manifest=f"""
# Source Manifest

- 原始 CSV：
  - `{PHASE_C1B_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`
- 参考报告：
  - `{PHASE_C1B_REPORT.relative_to(PROJECT_ROOT).as_posix()}`
- 直接复用图：无
- 基于已有数据重绘：
  - `structure_schematic.png/.svg`
  - `front_gap_deltaRtotal_heatmap.png`
  - `front_gap_selected_rtotal_curves.png`
- 结构图实现方式：
  - 程序绘制（matplotlib），未使用 imagegen 位图生成
- 结构层序定义：
  - `Air / Glass / ITO / NiOx / SAM / Air gap / PVK / C60 / Ag / Air`
- phase 物理对应：
  - 高亮前界面真实空气隙，表示 front-interface real separation
- 代表参数：
  - front-gap: `0 / 1 / 2 / 5 / 10 / 20 nm`
  - observable: `R_total`
        """,
    )

    build_summary_assets()
    build_appendix_assets()
    write_top_manifest()
    update_report_index()


if __name__ == "__main__":
    main()
