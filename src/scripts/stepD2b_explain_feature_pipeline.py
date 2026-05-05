"""Build Phase D-2 explainable feature-pipeline report assets.

This script does not run new physics simulations. It only reads the existing
Phase D-1 / D-2 databases and redraws PPT-friendly explanation figures plus a
short slide text for group-meeting reporting.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import textwrap

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHASE_NAME = "Phase D-2"

D1_RTOTAL_PATH = PROJECT_ROOT / "data" / "processed" / "phaseD1" / "phaseD1_rtotal_database.csv"
D2_FEATURE_PATH = PROJECT_ROOT / "data" / "processed" / "phaseD2" / "phaseD2_quantitative_feature_database.csv"
D2_TEMPLATE_PATH = PROJECT_ROOT / "data" / "processed" / "phaseD2" / "phaseD2_family_templates.csv"
D2_REPORT_PATH = PROJECT_ROOT / "results" / "report" / "phaseD2_quantitative_feature_dictionary" / "PHASE_D2_REPORT.md"
OUTPUT_DIR = PROJECT_ROOT / "results" / "report" / "phaseD2_quantitative_feature_dictionary" / "explain_feature_pipeline"

WINDOW_FRONT = (500.0, 650.0)
WINDOW_TRANSITION = (650.0, 810.0)
WINDOW_REAR = (810.0, 1055.0)

ROUTING_FAMILIES = [
    "thickness_nuisance",
    "front_roughness_nuisance",
    "rear_roughness_nuisance",
    "front_gap_on_background",
    "rear_gap_on_background",
]

META_COLUMNS = {
    "case_key",
    "case_id",
    "family",
    "anchor_id",
    "reference_case_id",
    "d_PVK_nm",
    "d_BEMA_front_nm",
    "d_BEMA_rear_nm",
    "d_gap_front_nm",
    "d_gap_rear_nm",
}

FEATURE_GROUPS = [
    {
        "title": "Windowed energy features",
        "input": r"$\Delta R_{total}(\lambda)$",
        "operation": "front / transition / rear window RMS",
        "output": "front_rms, rear_rms,\nfront/rear ratio",
        "question": "Where does the change mainly live?",
        "color": "#edf4ff",
    },
    {
        "title": "Rear-window shift features",
        "input": r"rear-window $R_{total}(\lambda)$",
        "operation": "reference vs case\nbest rigid alignment",
        "output": "best shift,\nexplained fraction,\nresidual",
        "question": "Does it behave like thickness shift?",
        "color": "#eef8ee",
    },
    {
        "title": "Rear-window spectral features",
        "input": "rear aligned residual",
        "operation": "uniform 1/lambda grid\nFFT-style analysis",
        "output": "dominant freq,\nbandwidth, sideband,\ncomplexity",
        "question": "Is there extra rear-window complexity?",
        "color": "#fff4e8",
    },
    {
        "title": "Wavelet features",
        "input": r"$\Delta R_{total}(\lambda)$",
        "operation": "localized scale-space\nenergy analysis",
        "output": "front/transition/rear\nenergy, entropy,\npeak scale",
        "question": "Where is the change concentrated, and is it locally reconstructed?",
        "color": "#f7efff",
    },
    {
        "title": "Template similarity features",
        "input": r"$\Delta R_{total}$ vs family templates",
        "operation": "compare with family\nmean templates",
        "output": "similarity to thickness /\nfront roughness /\nrear roughness /\nfront gap / rear gap",
        "question": "Which defect family does it look like overall?",
        "color": "#fff2f4",
    },
]


@dataclass(frozen=True)
class OutputPaths:
    pipeline_png: Path
    raw_vs_feature_png: Path
    groups_overview_png: Path
    slide_text_md: Path


def configure_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#7f8c8d",
            "axes.labelcolor": "#23313f",
            "text.color": "#23313f",
            "axes.titleweight": "bold",
            "axes.titlesize": 18,
            "axes.labelsize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )


def ensure_output_dir() -> OutputPaths:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OutputPaths(
        pipeline_png=OUTPUT_DIR / "feature_extraction_pipeline.png",
        raw_vs_feature_png=OUTPUT_DIR / "raw_vs_feature_based_analysis.png",
        groups_overview_png=OUTPUT_DIR / "feature_groups_overview.png",
        slide_text_md=OUTPUT_DIR / "slide_text.md",
    )


def draw_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    body: str,
    *,
    facecolor: str = "#f8f9fb",
    title_color: str = "#10243f",
    fontsize: int = 10,
) -> None:
    patch = Rectangle((x, y), width, height, linewidth=1.2, edgecolor="#8b98a5", facecolor=facecolor)
    ax.add_patch(patch)
    ax.text(x + width * 0.05, y + height * 0.83, title, fontsize=12, fontweight="bold", color=title_color, va="top", ha="left")
    ax.text(x + width * 0.05, y + height * 0.70, body, fontsize=fontsize, va="top", ha="left", linespacing=1.4)


def draw_arrow(ax: plt.Axes, x0: float, y0: float, x1: float, y1: float) -> None:
    arrow = FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=16, linewidth=1.4, color="#6c7a89")
    ax.add_patch(arrow)


def wrap_line(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def validate_inputs(feature_frame: pd.DataFrame, template_frame: pd.DataFrame, report_text: str) -> None:
    numeric_feature_columns = [column for column in feature_frame.columns if column not in META_COLUMNS]
    if len(numeric_feature_columns) != 38:
        raise ValueError(f"{PHASE_NAME} explain-feature task expects 38 numeric features, got {len(numeric_feature_columns)}.")
    if set(template_frame["family"].unique()) != set(ROUTING_FAMILIES):
        raise ValueError("Phase D-2 template table does not contain the five routing families.")
    required_phrases = [
        "先分类，再按 family 受限拟合",
        "family-specific full-spectrum fitting",
        "自动缺陷 routing",
    ]
    for phrase in required_phrases:
        if phrase not in report_text:
            raise ValueError(f"Required Phase D-2 report phrase missing: {phrase}")


def pick_example_case(rtotal_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    priority = [
        ("rear_gap_on_background", "rear-gap"),
        ("front_gap_on_background", "front-gap"),
        ("thickness_nuisance", "thickness"),
    ]
    for family, label in priority:
        subset = rtotal_frame[rtotal_frame["family"] == family].copy()
        if subset.empty:
            continue
        case_id = sorted(subset["case_id"].astype(str).unique())[0]
        chosen = subset[subset["case_id"] == case_id].sort_values("Wavelength_nm")
        reference_id = str(chosen["reference_case_id"].iloc[0])
        anchor_id = str(chosen["anchor_id"].iloc[0])
        anchor = rtotal_frame[
            (rtotal_frame["case_id"] == reference_id)
            & (rtotal_frame["family"] == "background_anchor")
            & (rtotal_frame["anchor_id"] == anchor_id)
        ].sort_values("Wavelength_nm")
        if not anchor.empty:
            return chosen, anchor, label
    raise ValueError("No usable Phase D-1 case/reference pair found for explanation figure.")


def add_window_guides(ax: plt.Axes) -> None:
    zones = [
        ("front", WINDOW_FRONT[0], WINDOW_FRONT[1], "#edf4ff"),
        ("transition", WINDOW_TRANSITION[0], WINDOW_TRANSITION[1], "#f5f1e8"),
        ("rear", WINDOW_REAR[0], WINDOW_REAR[1], "#eef8ee"),
    ]
    for label, start, end, color in zones:
        ax.axvspan(start, end, color=color, alpha=0.7, zorder=0)
        ax.text((start + end) * 0.5, 0.98, label, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=10, fontweight="bold", color="#5a6773")
    for start, end in [WINDOW_FRONT, WINDOW_TRANSITION, WINDOW_REAR]:
        ax.axvline(start, color="#c2c8cf", linestyle=":", linewidth=0.8)
        ax.axvline(end, color="#c2c8cf", linestyle=":", linewidth=0.8)


def build_feature_extraction_pipeline(paths: OutputPaths) -> None:
    fig, ax = plt.subplots(figsize=(17.5, 8.8), dpi=320)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.03, 0.96, f"{PHASE_NAME} Feature Extraction Pipeline", fontsize=22, fontweight="bold", ha="left", va="top")
    ax.text(0.03, 0.92, "Explain how 38 quantitative features are computed from the raw reflection curves.", fontsize=11, color="#566370", ha="left", va="top")

    draw_box(
        ax,
        0.03,
        0.25,
        0.16,
        0.52,
        "Input curves",
        "R_total(lambda)\n\nDelta_R_total(lambda)\n\nreference spectrum + case spectrum",
        facecolor="#f7f9fc",
    )

    card_x = 0.25
    card_w = 0.19
    card_h = 0.18
    y_positions = [0.77, 0.57, 0.37, 0.17]
    branch_specs = [
        (
            FEATURE_GROUPS[0]["title"],
            "Input: Delta_R_total\nCore: front / transition / rear windows\nOutput: front_rms, rear_rms,\nfront/rear ratio",
            FEATURE_GROUPS[0]["color"],
        ),
        (
            FEATURE_GROUPS[1]["title"],
            "Input: rear-window R_total\nCore: reference vs case,\nbest alignment\nOutput: best shift,\nexplained fraction, residual",
            FEATURE_GROUPS[1]["color"],
        ),
        (
            FEATURE_GROUPS[2]["title"],
            "Input: rear-window signal\nCore: uniform 1/lambda grid\n+ frequency analysis\nOutput: dominant freq,\nbandwidth, sideband, complexity",
            FEATURE_GROUPS[2]["color"],
        ),
        (
            FEATURE_GROUPS[3]["title"],
            "Input: Delta_R_total\nCore: localized scale-space\ndecomposition\nOutput: front / transition / rear\nenergy + entropy",
            FEATURE_GROUPS[3]["color"],
        ),
    ]
    for y, (title, body, color) in zip(y_positions, branch_specs):
        draw_box(ax, card_x, y, card_w, card_h, title, body, facecolor=color)
        draw_arrow(ax, 0.19, 0.51, card_x, y + card_h * 0.5)

    draw_box(
        ax,
        0.25,
        0.01,
        0.19,
        0.14,
        FEATURE_GROUPS[4]["title"],
        "Input: Delta_R_total\nCore: compare against\nfamily mean templates\nOutput: similarity to thickness /\nfront roughness / rear roughness /\nfront gap / rear gap",
        facecolor=FEATURE_GROUPS[4]["color"],
        fontsize=9,
    )
    draw_arrow(ax, 0.19, 0.51, 0.25, 0.08)

    draw_box(
        ax,
        0.51,
        0.27,
        0.18,
        0.48,
        "38 quantitative features",
        "3 window amplitudes\n+ 3 existing ratios\n+ 7 shift metrics\n+ 7 rear-spectrum metrics\n+ 8 wavelet metrics\n+ 10 template-similarity metrics",
        facecolor="#f6f3ff",
    )

    for y in [0.86, 0.66, 0.46, 0.26, 0.08]:
        draw_arrow(ax, 0.44, y, 0.51, 0.51)

    downstream_x = 0.76
    downstream_specs = [
        ("PCA / UMAP visualization", "low-dimensional map for quick family separation"),
        ("automatic routing", "use the feature layer to choose the likely defect family"),
        ("family-specific full-spectrum fitting", "send the routed case into the matching full-spectrum fitter"),
    ]
    for idx, (title, body) in enumerate(downstream_specs):
        y = 0.71 - idx * 0.23
        draw_box(ax, downstream_x, y, 0.20, 0.15, title, body, facecolor="#f8fafc")
        draw_arrow(ax, 0.69, 0.51, downstream_x, y + 0.075)

    fig.tight_layout()
    fig.savefig(paths.pipeline_png, dpi=320, bbox_inches="tight")
    plt.close(fig)


def build_raw_vs_feature_based_analysis(paths: OutputPaths, rtotal_frame: pd.DataFrame) -> None:
    case_frame, reference_frame, label = pick_example_case(rtotal_frame)
    wavelength_nm = case_frame["Wavelength_nm"].to_numpy(dtype=float)
    case_r = case_frame["R_total"].to_numpy(dtype=float) * 100.0
    delta_r = case_frame["Delta_R_total_vs_reference"].to_numpy(dtype=float) * 100.0
    ref_r = reference_frame["R_total"].to_numpy(dtype=float) * 100.0

    fig = plt.figure(figsize=(16.5, 8.5), dpi=320)
    outer = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0], wspace=0.08)

    left = outer[0, 0].subgridspec(2, 1, hspace=0.14)
    ax_r = fig.add_subplot(left[0, 0])
    ax_d = fig.add_subplot(left[1, 0], sharex=ax_r)
    right = fig.add_subplot(outer[0, 1])

    ax_r.plot(wavelength_nm, ref_r, color="#7f8c8d", linewidth=2.0, label="reference")
    ax_r.plot(wavelength_nm, case_r, color="#1565c0", linewidth=2.1, label=f"case ({label})")
    add_window_guides(ax_r)
    ax_r.set_title("Directly use raw spectra", loc="left", fontsize=18, fontweight="bold")
    ax_r.set_ylabel("R_total (%)")
    ax_r.grid(True, linestyle="--", alpha=0.22)
    ax_r.legend(loc="upper right", frameon=False)
    ax_r.text(0.02, 0.10, "high-dimensional", transform=ax_r.transAxes, fontsize=11, bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff3f3", edgecolor="#d7a4a4"))
    ax_r.text(0.31, 0.74, "hard to explain", transform=ax_r.transAxes, fontsize=11, bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff3f3", edgecolor="#d7a4a4"))

    ax_d.plot(wavelength_nm, delta_r, color="#c62828", linewidth=2.0)
    add_window_guides(ax_d)
    ax_d.axhline(0.0, color="#9aa5b1", linewidth=0.9)
    ax_d.set_xlabel("Wavelength (nm)")
    ax_d.set_ylabel("Delta_R_total (%)")
    ax_d.grid(True, linestyle="--", alpha=0.22)
    ax_d.text(0.03, 0.80, "noise-sensitive", transform=ax_d.transAxes, fontsize=11, bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff3f3", edgecolor="#d7a4a4"))
    ax_d.text(0.52, 0.12, "hard to route physically", transform=ax_d.transAxes, fontsize=11, bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff3f3", edgecolor="#d7a4a4"))

    right.axis("off")
    right.set_xlim(0, 1)
    right.set_ylim(0, 1)
    right.text(0.02, 0.96, "Use feature extraction first", fontsize=18, fontweight="bold", ha="left", va="top")
    draw_box(right, 0.05, 0.68, 0.24, 0.16, "5 feature groups", "window energy\nrear shift\nrear spectrum\nwavelet\ntemplate similarity", facecolor="#f4f8ff")
    draw_box(right, 0.39, 0.68, 0.20, 0.16, "38 features", "compact numbers with\nphysical meaning", facecolor="#f7efff")
    draw_box(right, 0.69, 0.68, 0.24, 0.16, "routing", "choose the likely family\nbefore full-spectrum fit", facecolor="#eef8ee")
    draw_arrow(right, 0.29, 0.76, 0.39, 0.76)
    draw_arrow(right, 0.59, 0.76, 0.69, 0.76)

    positives = [
        ("lower-dimensional", 0.10, 0.46),
        ("physically interpretable", 0.49, 0.46),
        ("good for classify-then-fit", 0.10, 0.30),
        ("better for automatic routing", 0.49, 0.30),
    ]
    for text, x, y in positives:
        right.text(x, y, text, fontsize=12, fontweight="bold", bbox=dict(boxstyle="round,pad=0.35", facecolor="#eff8ef", edgecolor="#97c19b"))

    right.text(
        0.05,
        0.10,
        "feature extraction is used for routing, not for replacing full-spectrum fitting",
        fontsize=12,
        fontweight="bold",
        color="#8b1e3f",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#fff5f7", edgecolor="#d8a4b2"),
    )

    fig.tight_layout()
    fig.savefig(paths.raw_vs_feature_png, dpi=320, bbox_inches="tight")
    plt.close(fig)


def build_feature_groups_overview(paths: OutputPaths) -> None:
    fig, ax = plt.subplots(figsize=(16.5, 9.0), dpi=320)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.03, 0.96, f"{PHASE_NAME} Feature Groups Overview", fontsize=22, fontweight="bold", ha="left", va="top")
    ax.text(0.03, 0.92, "Five complementary feature sources turn the spectrum into a routing-friendly description.", fontsize=11, color="#566370", ha="left", va="top")

    positions = [
        (0.05, 0.56),
        (0.37, 0.56),
        (0.69, 0.56),
        (0.05, 0.17),
        (0.37, 0.17),
    ]
    width = 0.26
    height = 0.28
    for (x, y), spec in zip(positions, FEATURE_GROUPS):
        body = (
            f"Input\n{wrap_line(spec['input'], 28)}\n\n"
            f"Output\n{wrap_line(spec['output'].replace(chr(10), ' '), 28)}\n\n"
            f"Question answered\n{wrap_line(spec['question'], 30)}"
        )
        draw_box(ax, x, y, width, height, spec["title"], body, facecolor=spec["color"], fontsize=10)

    draw_box(
        ax,
        0.69,
        0.17,
        0.26,
        0.28,
        "Summary route",
        "5 groups\n\n-> 38 quantitative features\n\n-> routing / embedding /\nfamily-specific fitting",
        facecolor="#f8fafc",
    )
    draw_arrow(ax, 0.31, 0.70, 0.69, 0.31)
    draw_arrow(ax, 0.63, 0.70, 0.69, 0.31)
    draw_arrow(ax, 0.31, 0.31, 0.69, 0.31)
    draw_arrow(ax, 0.63, 0.31, 0.69, 0.31)
    draw_arrow(ax, 0.95, 0.70, 0.82, 0.45)

    fig.tight_layout()
    fig.savefig(paths.groups_overview_png, dpi=320, bbox_inches="tight")
    plt.close(fig)


def build_slide_text(paths: OutputPaths) -> None:
    section1 = (
        "特征提取就是先不急着直接拟合整条反射谱，而是把谱里最有物理意义的变化压缩成一组更短、更好解释的数字。"
        "比如变化主要出现在前窗还是后窗，后窗是不是更像厚度导致的刚体平移，频谱里有没有额外侧带，"
        "以及整体上更像哪一类模板。这样做不是为了替代原始光谱，而是为了把复杂曲线先整理成可比较、可分类、可汇报的描述。"
    )
    section2 = (
        "如果直接拿原始反射谱去分类，难点不只是维度高，而是很难讲清楚为什么这样分。"
        "原始谱点数多、对噪声和局部起伏敏感，而且不同缺陷会同时改动多个波段，容易出现“数值上能分、物理上不好解释”的情况。"
        "先做特征提取，相当于先把谱里的关键信息按窗口、平移、频谱、小波和模板相似度整理出来，后面再做路由会更稳，也更适合组会说明。"
    )
    section3 = (
        "这一步一定要和全谱拟合分开理解。特征提取会主动压缩信息，所以它本身不是最终参数反演器，也不应该替代 full-spectrum fitting。"
        "它真正的角色是前置分流：先判断当前谱更像 thickness、roughness、front-gap 还是 rear-gap，再把样本送进对应的全谱拟合器。"
        "这样做牺牲了一部分细节，但换来了可解释、可路由和可自动化的入口层。"
    )
    meeting = (
        "特征提取就是把一条完整反射谱里最有物理意义的变化压缩成少量数字，用来先判断它更像哪一类缺陷。"
        "这一步会损失一部分细节信息，但它不是替代全谱拟合，而是为了先做自动分流，"
        "把样本送进更合适的 family-specific 全谱拟合器，从而让后续拟合更稳、更容易解释。"
    )
    if not (100 <= len(meeting) <= 150):
        raise ValueError(f"Group-meeting summary must be 100-150 Chinese characters, got {len(meeting)}.")

    text = f"""# Phase D-2 explain_feature_pipeline

本页图示对应 D-2 的 38 个量化特征，来源于已有数据库与现有 D-2 报告口径，不新增物理仿真，不改特征定义。

## 1. 什么是特征提取

{section1}

## 2. 为什么不直接用原始光谱

{section2}

## 3. 为什么特征提取不是替代全谱拟合

{section3}

## 4. 100-150 字组会总结

{meeting}
"""
    paths.slide_text_md.write_text(text, encoding="utf-8")


def main() -> None:
    configure_style()
    paths = ensure_output_dir()
    rtotal_frame = pd.read_csv(D1_RTOTAL_PATH)
    feature_frame = pd.read_csv(D2_FEATURE_PATH)
    template_frame = pd.read_csv(D2_TEMPLATE_PATH)
    report_text = D2_REPORT_PATH.read_text(encoding="utf-8")
    validate_inputs(feature_frame, template_frame, report_text)
    build_feature_extraction_pipeline(paths)
    build_raw_vs_feature_based_analysis(paths, rtotal_frame)
    build_feature_groups_overview(paths)
    build_slide_text(paths)


if __name__ == "__main__":
    main()
