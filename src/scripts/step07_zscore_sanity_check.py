"""Phase 07 rear-window sanity check and Z-score fit runner."""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.phase07_dual_window import (  # noqa: E402
    Phase07Config,
    build_phase07_stack_model,
    estimate_rear_window_thickness,
    export_fit_curve_table,
    export_fit_summary_table,
    fit_dual_window_sample,
    load_phase07_sample_input,
    plot_dual_window_zoom,
    plot_measured_vs_fitted_full_spectrum,
    plot_rear_basin_scan,
    plot_rear_window_sanity_check,
    plot_residual_diagnostics,
    plot_stage1_front_fit,
    write_optimizer_log,
    write_phase07_fit_input,
)


DEFAULT_HDR_CURVE_PATH = (
    PROJECT_ROOT / "test_data" / "phase7_data" / "DEVICE-1-withAg-P1_hdr_curves.csv"
)


def ensure_output_dirs() -> dict[str, Path]:
    output_dirs = {
        "fit_inputs": PROJECT_ROOT / "data" / "processed" / "phase07" / "fit_inputs",
        "fit_results": PROJECT_ROOT / "data" / "processed" / "phase07" / "fit_results",
        "figures": PROJECT_ROOT / "results" / "figures" / "phase07",
        "logs": PROJECT_ROOT / "results" / "logs" / "phase07",
    }
    for path in output_dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return output_dirs


def slugify_sample_name(sample_name: str) -> str:
    return sample_name.lower().replace(" ", "_").replace("-", "_")


def infer_with_ag(sample_name: str) -> bool:
    normalized = sample_name.lower()
    if "withoutag" in normalized:
        return False
    if "withag" in normalized:
        return True
    raise ValueError(f"无法从样本名推断 withAg/withoutAg: {sample_name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 07 sanity check + Z-score fit.")
    parser.add_argument(
        "--hdr-curve",
        type=Path,
        default=DEFAULT_HDR_CURVE_PATH,
        help="Path to *_hdr_curves.csv.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    hdr_curve_path = args.hdr_curve.resolve()
    if not hdr_curve_path.exists():
        raise FileNotFoundError(f"未找到输入文件: {hdr_curve_path}")

    output_dirs = ensure_output_dirs()
    sample_name = hdr_curve_path.stem.replace("_hdr_curves", "")
    sample_slug = slugify_sample_name(sample_name)
    with_ag = infer_with_ag(sample_name)
    fit_input_path = output_dirs["fit_inputs"] / f"phase07_{sample_slug}_fit_input.csv"

    sample_input = write_phase07_fit_input(
        source_table_path=hdr_curve_path,
        output_path=fit_input_path,
        sample_name=sample_name,
        with_ag=with_ag,
    )
    sample_input = load_phase07_sample_input(
        fit_input_path=fit_input_path,
        sample_name=sample_name,
        source_mode="hdr_csv",
        source_path=hdr_curve_path,
        with_ag=with_ag,
    )

    model = build_phase07_stack_model()
    sanity_check = estimate_rear_window_thickness(sample_input, model)

    sanity_plot_path = output_dirs["figures"] / f"phase07_{sample_slug}_rear_sanity_check.png"
    plot_rear_window_sanity_check(sample_input, sanity_check, sanity_plot_path)

    fit_result = fit_dual_window_sample(
        sample_input=sample_input,
        model=model,
        config=Phase07Config.default(),
    )

    curve_table_path = output_dirs["fit_results"] / f"phase07_{sample_slug}_fit_curve.csv"
    summary_table_path = output_dirs["fit_results"] / f"phase07_{sample_slug}_fit_summary.csv"
    optimizer_log_path = output_dirs["logs"] / f"phase07_{sample_slug}_zscore_fit_log.md"
    full_plot_path = output_dirs["figures"] / f"phase07_{sample_slug}_full_fit.png"
    dual_plot_path = output_dirs["figures"] / f"phase07_{sample_slug}_dual_window_zoom.png"
    stage1_plot_path = output_dirs["figures"] / f"phase07_{sample_slug}_stage1_front_fit.png"
    residual_plot_path = output_dirs["figures"] / f"phase07_{sample_slug}_residual_diagnostics.png"
    basin_plot_path = output_dirs["figures"] / f"phase07_{sample_slug}_rear_basin_scan.png"

    export_fit_curve_table(fit_result, curve_table_path)
    export_fit_summary_table(fit_result, summary_table_path)
    write_optimizer_log(fit_result, optimizer_log_path)
    plot_measured_vs_fitted_full_spectrum(fit_result, full_plot_path)
    plot_dual_window_zoom(fit_result, dual_plot_path)
    plot_stage1_front_fit(fit_result, stage1_plot_path)
    plot_residual_diagnostics(fit_result, residual_plot_path)
    plot_rear_basin_scan(fit_result, basin_plot_path)

    sanity_log_path = output_dirs["logs"] / f"phase07_{sample_slug}_rear_sanity_check.md"
    sanity_lines = [
        f"# Phase 07 Rear-Window Sanity Check: {sample_name}",
        "",
        f"- hdr_curve_path: `{hdr_curve_path}`",
        f"- fit_input_path: `{fit_input_path}`",
        f"- smoothing_window_length: `{sanity_check.smoothing_window_length}`",
        f"- smoothing_polyorder: `{sanity_check.smoothing_polyorder}`",
        f"- lambda_peak_nm: `{sanity_check.lambda_peak_nm:.6f}`",
        f"- lambda_valley_nm: `{sanity_check.lambda_valley_nm:.6f}`",
        f"- n_avg_pvk: `{sanity_check.n_avg_pvk:.6f}`",
        f"- d_estimate_nm: `{sanity_check.d_estimate_nm:.6f}`",
        "",
        "## Fit Outputs",
        "",
        f"- full_plot: `{full_plot_path}`",
        f"- dual_window_plot: `{dual_plot_path}`",
        f"- stage1_front_plot: `{stage1_plot_path}`",
        f"- residual_plot: `{residual_plot_path}`",
        f"- basin_plot: `{basin_plot_path}`",
    ]
    sanity_log_path.write_text("\n".join(sanity_lines) + "\n", encoding="utf-8")

    print(f"sample_name={sample_name}")
    print(f"lambda_peak_nm={sanity_check.lambda_peak_nm:.6f}")
    print(f"lambda_valley_nm={sanity_check.lambda_valley_nm:.6f}")
    print(f"n_avg_pvk={sanity_check.n_avg_pvk:.6f}")
    print(f"d_estimate_nm={sanity_check.d_estimate_nm:.6f}")
    print(f"rear_sanity_plot={sanity_plot_path}")
    print(f"stage1_front_plot={stage1_plot_path}")
    print(f"dual_window_plot={dual_plot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
