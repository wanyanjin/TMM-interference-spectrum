"""CLI entry for Phase 08 glass/PVK vs glass/Ag reference comparison."""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.reference_comparison import RuntimeConfig, parse_range, run_reference_comparison, tag_output_stem  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 08 glass/Ag reference comparison CLI")
    parser.add_argument("--sample-csv", required=True, help="Path to glass/PVK csv")
    parser.add_argument("--reference-csv", required=True, help="Path to glass/Ag csv")
    parser.add_argument("--ag-mirror-csv", default=None, help="Path to multi-frame direct Ag mirror csv")
    parser.add_argument("--background-csv", default=None, help="Path to multi-frame background csv")
    parser.add_argument(
        "--reference-type",
        default="glass_ag",
        choices=["glass_ag"],
        help="Reference type. First version only supports glass_ag.",
    )
    parser.add_argument(
        "--comparison-mode",
        default="single_reference",
        choices=["single_reference", "dual_reference"],
        help="Comparison mode.",
    )
    parser.add_argument("--drop-ag-frames", default="1", help="Comma-separated Ag frame indices to drop, e.g. 1")
    parser.add_argument(
        "--ag-background-align",
        default="pixel",
        choices=["pixel"],
        help="Background alignment strategy for Ag mirror.",
    )
    parser.add_argument(
        "--ag-reference-model",
        default="air_ag_air",
        choices=["air_ag_air"],
        help="Theoretical model for Ag mirror reference.",
    )
    parser.add_argument("--review-range", default="500-750", help="Review plot x-range (nm), e.g. 500-750")
    parser.add_argument(
        "--nk-csv",
        default=str(PROJECT_ROOT / "resources" / "aligned_full_stack_nk.csv"),
        help="Path to aligned full-stack nk csv",
    )
    parser.add_argument("--primary-range", default="400-750", help="Primary analysis range (nm), e.g. 400-750")
    parser.add_argument(
        "--extended-qc-range",
        default="750-931.443",
        help="Extended QC range (nm), e.g. 750-931.443",
    )
    parser.add_argument("--d-ag-nm", type=float, default=100.0)
    parser.add_argument("--d-pvk-fixed-nm", type=float, default=700.0)
    parser.add_argument("--d-pvk-scan-min", type=float, default=400.0)
    parser.add_argument("--d-pvk-scan-max", type=float, default=1000.0)
    parser.add_argument("--d-pvk-scan-step", type=float, default=1.0)
    parser.add_argument(
        "--output-root",
        default=str(PROJECT_ROOT),
        help="Repository root used to resolve output directories.",
    )
    parser.add_argument("--output-tag", default="", help="Optional suffix appended to generated filenames, e.g. pvk_x01")
    parser.add_argument("--smooth-for-plot", action="store_true")
    parser.add_argument("--smooth-window", type=int, default=11)
    parser.add_argument("--smooth-polyorder", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def smooth_for_plot(values: np.ndarray, enabled: bool, window: int, polyorder: int) -> np.ndarray:
    if not enabled:
        return values
    from scipy.signal import savgol_filter

    safe_window = max(5, int(window))
    if safe_window % 2 == 0:
        safe_window += 1
    safe_window = min(safe_window, values.size - (1 - values.size % 2))
    if safe_window < 5:
        return values
    safe_polyorder = min(int(polyorder), safe_window - 2)
    if safe_polyorder < 1:
        return values
    return savgol_filter(values, safe_window, safe_polyorder)


def plot_outputs(result: dict, config: RuntimeConfig) -> dict[str, str]:
    arrays = result["arrays"]
    wl = arrays["wavelength_nm"]
    primary_mask = arrays["primary_mask"]
    strict_mask = arrays["strict_mask"]
    ext_mask = arrays["extended_mask"]

    counts_sample = arrays["counts_sample"]
    counts_ref = arrays["counts_ref"]
    counts_sample_ms = arrays["counts_sample_ms"]
    counts_ref_ms = arrays["counts_ref_ms"]
    r_tmm_glass_ag = arrays["r_tmm_glass_ag"]
    r_tmm_ag_mirror = arrays["r_tmm_ag_mirror"]
    r_exp = arrays["r_exp"]
    r_exp_ag_mirror = arrays["r_exp_ag_mirror"]
    r_fixed = arrays["r_tmm_pvk_fixed"]
    r_best = arrays["r_tmm_pvk_best"]
    residual_fixed = arrays["residual_fixed"]
    residual_best = arrays["residual_best"]
    scan_values = arrays["scan_values"]
    scan_cost = arrays["scan_cost"]

    r_exp_plot = smooth_for_plot(r_exp, config.smooth_for_plot, config.smooth_window, config.smooth_polyorder)
    r_fixed_plot = smooth_for_plot(r_fixed, config.smooth_for_plot, config.smooth_window, config.smooth_polyorder)
    r_best_plot = smooth_for_plot(r_best, config.smooth_for_plot, config.smooth_window, config.smooth_polyorder)

    paths: dict[str, str] = {}
    review_min_nm = config.review_min_nm
    review_max_nm = config.review_max_nm
    review_mask = (wl >= review_min_nm) & (wl <= review_max_nm)

    def adaptive_ylim(series_list: list[np.ndarray], fallback: tuple[float, float]) -> tuple[float, float]:
        values: list[np.ndarray] = []
        for s in series_list:
            part = np.asarray(s, dtype=float)[review_mask]
            finite = part[np.isfinite(part)]
            if finite.size > 0:
                values.append(finite)
        if not values:
            return fallback
        merged = np.concatenate(values)
        vmin = float(np.min(merged))
        vmax = float(np.max(merged))
        if np.isclose(vmin, vmax):
            pad = max(0.02, 0.1 * max(abs(vmin), 1.0))
            return vmin - pad, vmax + pad
        span = vmax - vmin
        pad = max(0.01, 0.12 * span)
        return vmin - pad, vmax + pad

    raw_counts_path = config.output_figures_dir / f"{tag_output_stem('phase08_0429_raw_counts', config.output_tag)}.png"
    plt.figure(figsize=(12, 6), dpi=200)
    plt.plot(wl, counts_sample, label="Glass/PVK Counts")
    plt.plot(wl, counts_ref, label="Glass/Ag Counts")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Counts")
    plt.title("Raw Counts")
    plt.xlim(review_min_nm, review_max_nm)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig(raw_counts_path)
    plt.close()
    paths["raw_counts_png"] = raw_counts_path.as_posix()

    counts_ms_path = config.output_figures_dir / f"{tag_output_stem('phase08_0429_counts_per_ms', config.output_tag)}.png"
    plt.figure(figsize=(12, 6), dpi=200)
    plt.plot(wl, counts_sample_ms, label="Glass/PVK Counts/ms")
    plt.plot(wl, counts_ref_ms, label="Glass/Ag Counts/ms")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Counts/ms")
    plt.title("Exposure-Normalized Counts")
    plt.xlim(review_min_nm, review_max_nm)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig(counts_ms_path)
    plt.close()
    paths["counts_per_ms_png"] = counts_ms_path.as_posix()

    glass_ag_theory_path = config.output_figures_dir / f"{tag_output_stem('phase08_0429_glassAg_ref_theory', config.output_tag)}.png"
    plt.figure(figsize=(12, 6), dpi=200)
    plt.plot(wl, r_tmm_glass_ag, label="R_TMM_GlassAg")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance (0-1)")
    plt.title("TMM Reference Reflectance: Glass/Ag")
    plt.xlim(review_min_nm, review_max_nm)
    ymin, ymax = adaptive_ylim([r_tmm_glass_ag], (0.0, 1.0))
    plt.ylim(ymin, ymax)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig(glass_ag_theory_path)
    plt.close()
    paths["glass_ag_ref_theory_png"] = glass_ag_theory_path.as_posix()

    reflect_stem = (
        "phase08_0429_dual_reference_reflectance_exp_vs_tmm.png"
        if config.comparison_mode == "dual_reference"
        else "phase08_0429_reflectance_exp_vs_tmm.png"
    )
    reflect_name = tag_output_stem(reflect_stem.removesuffix(".png"), config.output_tag) + ".png"
    exp_vs_tmm_path = config.output_figures_dir / reflect_name
    plt.figure(figsize=(12, 6), dpi=220)
    plt.plot(wl, r_exp_plot, color="#1f77b4", linewidth=2.0, label="R_Exp by Glass/Ag")
    if r_exp_ag_mirror is not None:
        r_exp_ag_plot = smooth_for_plot(r_exp_ag_mirror, config.smooth_for_plot, config.smooth_window, config.smooth_polyorder)
        plt.plot(wl, r_exp_ag_plot, color="#ff7f0e", linewidth=2.0, label="R_Exp by Ag Mirror")
    plt.plot(wl, r_fixed_plot, color="#7f7f7f", linestyle="--", linewidth=1.8, label="R_TMM_GlassPVK_Fixed")
    plt.axvspan(config.primary_min_nm, config.primary_max_nm, alpha=0.08, color="green", label="Primary")
    plt.axvspan(config.extended_min_nm, config.extended_max_nm, alpha=0.08, color="orange", label="Extended QC")
    if config.comparison_mode == "single_reference":
        plt.scatter(
            wl[~strict_mask & primary_mask],
            r_exp_plot[~strict_mask & primary_mask],
            s=8,
            alpha=0.6,
            label="Primary non-strict points",
        )
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance (0-1)")
    plt.title("Experimental vs TMM Reflectance")
    plt.xlim(review_min_nm, review_max_nm)
    ylim_series = [r_exp_plot, r_fixed_plot]
    if r_exp_ag_mirror is not None:
        ylim_series.append(r_exp_ag_mirror)
    ymin, ymax = adaptive_ylim(ylim_series, (0.0, 1.0))
    plt.ylim(ymin, ymax)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig(exp_vs_tmm_path)
    plt.close()
    paths["reflectance_exp_vs_tmm_png"] = exp_vs_tmm_path.as_posix()

    residual_path = config.output_figures_dir / f"{tag_output_stem('phase08_0429_residual', config.output_tag)}.png"
    plt.figure(figsize=(12, 6), dpi=220)
    plt.plot(wl, residual_fixed, label="Residual Fixed")
    plt.plot(wl, residual_best, label="Residual BestD")
    plt.axhline(0.0, color="black", linewidth=1.0)
    plt.axvspan(config.primary_min_nm, config.primary_max_nm, alpha=0.08, color="green", label="Primary")
    plt.axvspan(config.extended_min_nm, config.extended_max_nm, alpha=0.08, color="orange", label="Extended QC")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Residual")
    plt.title("Residual Diagnostics")
    plt.xlim(review_min_nm, review_max_nm)
    ymin, ymax = adaptive_ylim([residual_fixed, residual_best], (-0.2, 0.2))
    plt.ylim(ymin, ymax)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig(residual_path)
    plt.close()
    paths["residual_png"] = residual_path.as_posix()

    if config.comparison_mode == "dual_reference":
        ag_qc_path = config.output_figures_dir / f"{tag_output_stem('phase08_0429_ag_bk_qc', config.output_tag)}.png"
        plt.figure(figsize=(12, 6), dpi=200)
        plt.plot(wl, counts_ref_ms, label="Glass/Ag Counts/ms", color="#1f77b4", alpha=0.8)
        if arrays["r_exp_ag_mirror"] is not None:
            ag_corr = np.asarray(result["arrays"]["r_exp_ag_mirror"])
            finite = np.isfinite(ag_corr)
            if np.any(finite):
                plt.text(0.02, 0.96, "Ag frame #1 dropped (saturation)\nBK aligned by pixel index", transform=plt.gca().transAxes, va="top")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Counts/ms")
        plt.title("Ag/BK QC Context")
        plt.xlim(review_min_nm, review_max_nm)
        plt.grid(alpha=0.3)
        plt.legend()
        plt.savefig(ag_qc_path)
        plt.close()
        paths["ag_bk_qc_png"] = ag_qc_path.as_posix()

    thickness_scan_path = config.output_figures_dir / f"{tag_output_stem('phase08_0429_thickness_scan', config.output_tag)}.png"
    plt.figure(figsize=(10, 5), dpi=220)
    plt.plot(scan_values, scan_cost, linewidth=1.8)
    plt.xlabel("d_PVK (nm)")
    plt.ylabel("Mean Squared Error (strict primary mask)")
    plt.title("PVK Thickness Scan")
    plt.grid(alpha=0.3)
    plt.savefig(thickness_scan_path)
    plt.close()
    paths["thickness_scan_png"] = thickness_scan_path.as_posix()

    return paths


def write_report(result: dict, config: RuntimeConfig, figure_paths: dict[str, str]) -> dict[str, str]:
    manifest = result["manifest"]
    metrics_csv = Path(result["paths"]["metrics_csv"])
    metrics_df = np.array([])
    try:
        import pandas as pd

        metrics_df = pd.read_csv(metrics_csv)
    except Exception:
        metrics_df = np.array([])

    summary_name = "phase08_0429_dual_reference_run_summary.md" if config.comparison_mode == "dual_reference" else "phase08_0429_run_summary.md"
    report_name = "phase08_0429_dual_reference_report.md" if config.comparison_mode == "dual_reference" else "phase08_0429_reference_comparison_report.md"
    summary_name = tag_output_stem(summary_name.removesuffix(".md"), config.output_tag) + ".md"
    report_name = tag_output_stem(report_name.removesuffix(".md"), config.output_tag) + ".md"
    summary_path = config.output_logs_dir / summary_name
    report_path = config.output_report_dir / report_name

    summary_lines = [
        "# Phase 08 Reference Comparison Run Summary",
        "",
        f"- Reference type: `{manifest['reference_type']}`",
        f"- Comparison mode: `{manifest.get('comparison_mode', 'single_reference')}`",
        f"- Exposure source sample/reference: `{manifest['sample_exposure_source']}` / `{manifest['reference_exposure_source']}`",
        f"- Primary range: `{manifest['primary_range_nm'][0]}-{manifest['primary_range_nm'][1]} nm`",
        f"- Extended QC range: `{manifest['extended_qc_range_nm'][0]}-{manifest['extended_qc_range_nm'][1]} nm`",
        f"- Strict floor counts: `{manifest['strict_floor_counts']}`",
        f"- best_d_PVK_nm: `{manifest['best_d_PVK_nm']}`",
        f"- diagnostic (fixed): `a={manifest['diagnostic_scale_a_fixed']:.6f}`, `b={manifest['diagnostic_offset_b_fixed']:.6e}`",
        f"- diagnostic (best_d): `a={manifest['diagnostic_scale_a_best_d']:.6f}`, `b={manifest['diagnostic_offset_b_best_d']:.6e}`",
        "- 注意：scale/offset 仅用于系统误差诊断，不作为物理模型结论。",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    report_lines = [
        "# Phase 08 0429 Reference Comparison Report",
        "",
        "## 1. 原始数据质量",
        "- 本次使用 `glass/PVK` 与 `glass/Ag`，并在 dual 模式引入 direct Ag mirror + bk 多帧校准。",
        "- 无 `.spe` 元数据，曝光时间来自文件名推断（`20ms`）。",
        "- 指标计算使用未平滑曲线；若启用平滑，仅用于图示辅助。",
        "",
        "## 2. 模型与公式",
        "- 参比模型（glass/Ag）：`Air / Glass(incoherent) / Ag / Air`",
        "- 参比模型（Ag mirror）：`Air / Ag / Air`",
        "- 样品模型：`Air / Glass(incoherent) / PVK / Air`",
        "- 实验反射率：`R_exp = (I_pvk/t_pvk)/(I_ag/t_ag) * R_TMM_glass_ag`",
        "",
        "## 3. 结果摘要",
        f"- `best_d_PVK_nm = {manifest['best_d_PVK_nm']:.3f}`",
        f"- `diagnostic_scale_a_fixed = {manifest['diagnostic_scale_a_fixed']:.6f}`",
        f"- `diagnostic_offset_b_fixed = {manifest['diagnostic_offset_b_fixed']:.6e}`",
        f"- `diagnostic_scale_a_best_d = {manifest['diagnostic_scale_a_best_d']:.6f}`",
        f"- `diagnostic_offset_b_best_d = {manifest['diagnostic_offset_b_best_d']:.6e}`",
        "",
        "## 4. 主结论范围",
        f"- 主结论仅基于 `{manifest['primary_range_nm'][0]}-{manifest['primary_range_nm'][1]} nm` 且 strict mask。",
        f"- `{manifest['extended_qc_range_nm'][0]}-{manifest['extended_qc_range_nm'][1]} nm` 仅作为扩展 QC。",
        "",
        "## 5. 关键图",
        f"- {figure_paths['reflectance_exp_vs_tmm_png']}",
        f"- {figure_paths['residual_png']}",
        f"- {figure_paths['thickness_scan_png']}",
    ]
    if "ag_bk_qc_png" in figure_paths:
        report_lines.append(f"- {figure_paths['ag_bk_qc_png']}")
    if getattr(metrics_df, "empty", True) is False:
        report_lines.extend(
            [
                "",
                "## 6. 指标表",
                "",
                "```text",
                metrics_df.to_string(index=False),
                "```",
            ]
        )
    report_lines.append("")
    report_lines.append("## 7. 诊断解释")
    report_lines.append("- 若 `a` 明显偏离 1 或 `b` 明显偏离 0，应优先排查参比口径/收光几何/背景项。")
    report_lines.append("- 本节诊断不替代物理模型判断。")
    report_lines.append("")

    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    return {
        "summary_md": summary_path.as_posix(),
        "report_md": report_path.as_posix(),
    }


def main() -> int:
    args = parse_args()
    primary_min, primary_max = parse_range(args.primary_range)
    ext_min, ext_max = parse_range(args.extended_qc_range)
    review_min, review_max = parse_range(args.review_range)
    drop_ag_frames = tuple(int(x.strip()) for x in str(args.drop_ag_frames).split(",") if x.strip())

    output_root = Path(args.output_root).resolve()
    processed_dir = output_root / "data" / "processed" / "phase08" / "reference_comparison"
    figures_dir = output_root / "results" / "figures" / "phase08" / "reference_comparison"
    logs_dir = output_root / "results" / "logs" / "phase08" / "reference_comparison"
    report_dir = output_root / "results" / "report" / "phase08_reference_comparison"

    config = RuntimeConfig(
        sample_csv=Path(args.sample_csv).resolve(),
        reference_csv=Path(args.reference_csv).resolve(),
        nk_csv=Path(args.nk_csv).resolve(),
        output_processed_dir=processed_dir,
        output_figures_dir=figures_dir,
        output_logs_dir=logs_dir,
        output_report_dir=report_dir,
        d_ag_nm=float(args.d_ag_nm),
        d_pvk_fixed_nm=float(args.d_pvk_fixed_nm),
        d_pvk_scan_min_nm=float(args.d_pvk_scan_min),
        d_pvk_scan_max_nm=float(args.d_pvk_scan_max),
        d_pvk_scan_step_nm=float(args.d_pvk_scan_step),
        primary_min_nm=primary_min,
        primary_max_nm=primary_max,
        extended_min_nm=ext_min,
        extended_max_nm=ext_max,
        smooth_for_plot=bool(args.smooth_for_plot),
        smooth_window=int(args.smooth_window),
        smooth_polyorder=int(args.smooth_polyorder),
        reference_type=str(args.reference_type),
        comparison_mode=str(args.comparison_mode),
        ag_mirror_csv=Path(args.ag_mirror_csv).resolve() if args.ag_mirror_csv else None,
        background_csv=Path(args.background_csv).resolve() if args.background_csv else None,
        drop_ag_frames=drop_ag_frames,
        ag_background_align=str(args.ag_background_align),
        ag_reference_model=str(args.ag_reference_model),
        review_min_nm=review_min,
        review_max_nm=review_max,
        output_tag=str(args.output_tag).strip() or None,
    )

    result = run_reference_comparison(config=config, dry_run=bool(args.dry_run))
    if args.dry_run:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    figure_paths = plot_outputs(result=result, config=config)
    report_paths = write_report(result=result, config=config, figure_paths=figure_paths)
    manifest_path = result["paths"]["manifest_json"]
    print("Phase 08 reference comparison completed.")
    print(f"manifest: {manifest_path}")
    print(f"report: {report_paths['report_md']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
