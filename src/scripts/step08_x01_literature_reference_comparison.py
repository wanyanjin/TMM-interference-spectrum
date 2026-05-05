"""Phase 08 x=0.1 literature optical-constant extraction and dual-reference comparison."""

from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import sys

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core import literature_x01_nk as lit_x01  # noqa: E402


DOCX_PATH = PROJECT_ROOT / "resources" / "1-s2.0-S0927024818304446-mmc1.docx"
BASE_NK_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk.csv"
EPSILON_OUTPUT_PATH = PROJECT_ROOT / "resources" / "digitized" / "lit_x01_csfapi_epsilon_table_s3.csv"
NK_OUTPUT_PATH = PROJECT_ROOT / "resources" / "digitized" / "lit_x01_csfapi_nk_table_s3.csv"
ALIGNED_OUTPUT_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_phase08_x01.csv"

SAMPLE_CSV = PROJECT_ROOT / "test_data" / "0429" / "glass-PVK-withoutfliter-20ms 2026 四月 29 14_45_45.csv"
REFERENCE_CSV = PROJECT_ROOT / "test_data" / "0429" / "glass-Ag-withoutfliter-20ms 2026 四月 29 14_42_25.csv"
AG_MIRROR_CSV = PROJECT_ROOT / "test_data" / "0429" / "Ag-withoutfliter-20ms 2026 四月 29 15_14_48.csv"
BACKGROUND_CSV = PROJECT_ROOT / "test_data" / "0429" / "bk-20ms 2026 四月 29 15_31_12.csv"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures" / "phase08" / "reference_comparison"
REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phase08_reference_comparison"
LOGS_DIR = PROJECT_ROOT / "results" / "logs" / "phase08" / "reference_comparison"
COMPARE_METRICS_PATH = PROCESSED_DIR / "phase08_0429_dual_reference_pvk_source_comparison_metrics.csv"
COMPARE_FIG_PATH = FIGURES_DIR / "phase08_0429_dual_reference_pvk_source_comparison.png"
CURRENT_PVK_FIG_PATH = FIGURES_DIR / "phase08_0429_dual_reference_pvk_source_current_pvk.png"
X01_PVK_FIG_PATH = FIGURES_DIR / "phase08_0429_dual_reference_pvk_source_pvk_x01.png"
COMPARE_REPORT_PATH = REPORT_DIR / "phase08_0429_dual_reference_pvk_source_comparison.md"

BASELINE_TAG = "current_pvk"
X01_TAG = "pvk_x01"


def run_cli(nk_csv: Path, output_tag: str) -> None:
    cmd = [
        str(PROJECT_ROOT / ".venv" / "bin" / "python"),
        str(PROJECT_ROOT / "src" / "cli" / "reference_comparison.py"),
        "--sample-csv",
        str(SAMPLE_CSV),
        "--reference-csv",
        str(REFERENCE_CSV),
        "--comparison-mode",
        "dual_reference",
        "--ag-mirror-csv",
        str(AG_MIRROR_CSV),
        "--background-csv",
        str(BACKGROUND_CSV),
        "--nk-csv",
        str(nk_csv),
        "--review-range",
        "500-750",
        "--output-tag",
        output_tag,
    ]
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = "/private/tmp/.mpl"
    subprocess.run(cmd, cwd=PROJECT_ROOT, env=env, check=True, text=True)


def build_compare_panel(ax: plt.Axes, calibrated_df: pd.DataFrame, title: str) -> None:
    review_mask = (calibrated_df["Wavelength_nm"] >= 500.0) & (calibrated_df["Wavelength_nm"] <= 750.0)
    wl = calibrated_df.loc[review_mask, "Wavelength_nm"].to_numpy(dtype=float)
    r_glass_ag = calibrated_df.loc[review_mask, "R_Exp_GlassPVK_by_GlassAg"].to_numpy(dtype=float)
    r_ag_mirror = calibrated_df.loc[review_mask, "R_Exp_GlassPVK_by_AgMirror"].to_numpy(dtype=float)
    r_tmm_fixed = calibrated_df.loc[review_mask, "R_TMM_GlassPVK_Fixed"].to_numpy(dtype=float)

    series = [r_glass_ag[np.isfinite(r_glass_ag)], r_ag_mirror[np.isfinite(r_ag_mirror)], r_tmm_fixed[np.isfinite(r_tmm_fixed)]]
    merged = np.concatenate([arr for arr in series if arr.size > 0])
    ymin = float(np.min(merged))
    ymax = float(np.max(merged))
    span = ymax - ymin
    pad = max(0.01, 0.12 * span) if span > 0 else 0.02

    ax.plot(wl, r_glass_ag, color="#1f77b4", linewidth=2.0, label="R_Exp by Glass/Ag")
    ax.plot(wl, r_ag_mirror, color="#ff7f0e", linewidth=2.0, label="R_Exp by Ag Mirror")
    ax.plot(wl, r_tmm_fixed, color="#7f7f7f", linestyle="--", linewidth=1.8, label="R_TMM_GlassPVK_Fixed")
    ax.set_title(title)
    ax.set_xlim(500.0, 750.0)
    ax.set_ylim(ymin - pad, ymax + pad)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Reflectance (0-1)")
    ax.grid(alpha=0.3)


def save_single_source_figure(calibrated_df: pd.DataFrame, title: str, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6), dpi=220)
    build_compare_panel(ax, calibrated_df, title)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    fig.savefig(output_path)
    plt.close(fig)


def summarize_metrics(metrics_df: pd.DataFrame, source_label: str) -> pd.DataFrame:
    primary = metrics_df[metrics_df["Band"] == "400_750_primary"].copy()
    primary.insert(0, "PVK_Source", source_label)
    return primary


def main() -> int:
    EPSILON_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    epsilon_df = lit_x01.extract_x01_epsilon_from_docx(DOCX_PATH)
    nk_df = lit_x01.epsilon_to_nk_table(epsilon_df)

    epsilon_df.to_csv(EPSILON_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    nk_df.to_csv(NK_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    aligned_df = lit_x01.build_phase08_x01_aligned_nk(BASE_NK_PATH, NK_OUTPUT_PATH)
    aligned_df.to_csv(ALIGNED_OUTPUT_PATH, index=False, encoding="utf-8-sig")

    run_cli(BASE_NK_PATH, BASELINE_TAG)
    run_cli(ALIGNED_OUTPUT_PATH, X01_TAG)

    baseline_calibrated = pd.read_csv(PROCESSED_DIR / f"phase08_0429_dual_reference_calibrated_reflectance_{BASELINE_TAG}.csv")
    x01_calibrated = pd.read_csv(PROCESSED_DIR / f"phase08_0429_dual_reference_calibrated_reflectance_{X01_TAG}.csv")
    baseline_metrics = pd.read_csv(PROCESSED_DIR / f"phase08_0429_dual_reference_error_metrics_{BASELINE_TAG}.csv")
    x01_metrics = pd.read_csv(PROCESSED_DIR / f"phase08_0429_dual_reference_error_metrics_{X01_TAG}.csv")
    baseline_manifest = json.loads((PROCESSED_DIR / f"phase08_0429_dual_reference_manifest_{BASELINE_TAG}.json").read_text(encoding="utf-8"))
    x01_manifest = json.loads((PROCESSED_DIR / f"phase08_0429_dual_reference_manifest_{X01_TAG}.json").read_text(encoding="utf-8"))

    compare_metrics = pd.concat(
        [
            summarize_metrics(baseline_metrics, "current_pvk"),
            summarize_metrics(x01_metrics, "pvk_x01"),
        ],
        ignore_index=True,
    )
    compare_metrics.to_csv(COMPARE_METRICS_PATH, index=False, encoding="utf-8-sig")

    fig, axes = plt.subplots(2, 1, figsize=(12, 10), dpi=220, sharex=True)
    build_compare_panel(axes[0], baseline_calibrated, "Current PVK source")
    build_compare_panel(axes[1], x01_calibrated, "Literature x=0.1 (Table S3)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    fig.savefig(COMPARE_FIG_PATH)
    plt.close(fig)

    save_single_source_figure(
        baseline_calibrated,
        "Current PVK source: measured reflectance vs TMM",
        CURRENT_PVK_FIG_PATH,
    )
    save_single_source_figure(
        x01_calibrated,
        "Literature x=0.1 source: measured reflectance vs TMM",
        X01_PVK_FIG_PATH,
    )

    report_lines = [
        "# Phase 08 x=0.1 Literature PVK Source Comparison",
        "",
        "## 1. 数据来源",
        f"- 文献补充材料：`{DOCX_PATH.as_posix()}`",
        "- 采用 `Table S3` 中 `FA0.9Cs0.1PbI3` 的 `Photon Energy / ε1 / ε2` 数据。",
        f"- 提取行数：`{len(epsilon_df)}`",
        f"- 文献波长覆盖：`{nk_df['Wavelength_nm'].min():.3f}-{nk_df['Wavelength_nm'].max():.3f} nm`",
        "",
        "## 2. 生成文件",
        f"- epsilon 表：`{EPSILON_OUTPUT_PATH.as_posix()}`",
        f"- nk 表：`{NK_OUTPUT_PATH.as_posix()}`",
        f"- Phase08 专用 aligned nk：`{ALIGNED_OUTPUT_PATH.as_posix()}`",
        f"- 对比图：`{COMPARE_FIG_PATH.as_posix()}`",
        f"- 当前 PVK 单独图：`{CURRENT_PVK_FIG_PATH.as_posix()}`",
        f"- x=0.1 单独图：`{X01_PVK_FIG_PATH.as_posix()}`",
        f"- 对比指标：`{COMPARE_METRICS_PATH.as_posix()}`",
        "",
        "## 3. 运行口径",
        f"- 基线 nk：`{baseline_manifest['nk_csv']}`",
        f"- x=0.1 nk：`{x01_manifest['nk_csv']}`",
        "- 双参比保持一致：`glass/Ag` 与 `Ag mirror + bk`。",
        "- 主审查波段：`500-750 nm`；指标主体仍保留 CLI 的 primary 定义与 thickness scan。",
        "",
        "## 4. 400-750 nm primary 指标摘录",
        "",
        "```text",
        compare_metrics.to_string(index=False),
        "```",
        "",
        "## 5. 关键结论入口",
        f"- 基线 dual 报告：`{(REPORT_DIR / f'phase08_0429_dual_reference_report_{BASELINE_TAG}.md').as_posix()}`",
        f"- x=0.1 dual 报告：`{(REPORT_DIR / f'phase08_0429_dual_reference_report_{X01_TAG}.md').as_posix()}`",
        "- 本报告只做当前 PVK 来源与文献 x=0.1 来源的并排对照，不替代各自单独 manifest/report。",
    ]
    COMPARE_REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print("Phase 08 x=0.1 literature reference comparison completed.")
    print(f"epsilon_csv: {EPSILON_OUTPUT_PATH}")
    print(f"nk_csv: {NK_OUTPUT_PATH}")
    print(f"aligned_nk_csv: {ALIGNED_OUTPUT_PATH}")
    print(f"compare_figure: {COMPARE_FIG_PATH}")
    print(f"compare_report: {COMPARE_REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
