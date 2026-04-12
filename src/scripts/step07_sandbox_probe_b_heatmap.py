"""Phase 07 diagnostic sandbox probe B: rear-window d-n degeneracy heatmap."""

from __future__ import annotations

from pathlib import Path
import argparse
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

from core.phase07_dual_window import (  # noqa: E402
    Phase07SampleInput,
    build_phase07_stack_model,
    compute_window_scales,
    evaluate_stage2_model,
    load_phase07_sample_input,
    write_phase07_fit_input,
)


DEFAULT_HDR_CURVE_PATH = PROJECT_ROOT / "test_data" / "phase7_data" / "DEVICE-1-withAg-P1_hdr_curves.csv"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "data" / "processed" / "phase07" / "fit_results" / "phase07_device_1_withag_p1_fit_summary.csv"
FIT_INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "phase07" / "fit_inputs"
FIT_RESULT_DIR = PROJECT_ROOT / "data" / "processed" / "phase07" / "fit_results"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phase07"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phase07"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 07 rear-window degeneracy heatmap.")
    parser.add_argument("--hdr-curve", type=Path, default=DEFAULT_HDR_CURVE_PATH)
    parser.add_argument("--summary-csv", type=Path, default=DEFAULT_SUMMARY_PATH)
    return parser.parse_args()


def slugify_sample_name(sample_name: str) -> str:
    return sample_name.lower().replace(" ", "_").replace("-", "_")


def infer_with_ag(sample_name: str) -> bool:
    normalized = sample_name.lower()
    if "withoutag" in normalized:
        return False
    if "withag" in normalized:
        return True
    raise ValueError(f"无法从样本名推断 withAg/withoutAg: {sample_name}")


def ensure_dirs() -> None:
    FIT_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIT_RESULT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def make_rear_sample(sample_input: Phase07SampleInput) -> Phase07SampleInput:
    mask = sample_input.rear_mask
    return Phase07SampleInput(
        sample_name=sample_input.sample_name,
        with_ag=sample_input.with_ag,
        source_mode=sample_input.source_mode,
        source_path=sample_input.source_path,
        fit_input_path=sample_input.fit_input_path,
        wavelength_nm=sample_input.wavelength_nm[mask],
        reflectance=sample_input.reflectance[mask],
        window_label=sample_input.window_label[mask],
    )


def main() -> int:
    args = parse_args()
    ensure_dirs()

    hdr_curve_path = args.hdr_curve.resolve()
    summary_path = args.summary_csv.resolve()
    sample_name = hdr_curve_path.stem.replace("_hdr_curves", "")
    sample_slug = slugify_sample_name(sample_name)

    fit_input_path = FIT_INPUT_DIR / f"phase07_{sample_slug}_probe_b_fit_input.csv"
    sample_input = write_phase07_fit_input(
        source_table_path=hdr_curve_path,
        output_path=fit_input_path,
        sample_name=sample_name,
        with_ag=infer_with_ag(sample_name),
    )
    sample_input = load_phase07_sample_input(
        fit_input_path=fit_input_path,
        sample_name=sample_name,
        source_mode="hdr_csv",
        source_path=hdr_curve_path,
        with_ag=infer_with_ag(sample_name),
    )
    summary = pd.read_csv(summary_path).iloc[0]
    rear_sample = make_rear_sample(sample_input)
    stage1_params = {
        "d_ITO": float(summary["d_ITO"]),
        "d_NiOx": float(summary["d_NiOx"]),
        "sigma_front_rms_nm": float(summary["sigma_front_rms_nm"]),
    }
    fixed_stage2 = {
        "d_rough": float(summary["d_rough"]),
        "sigma_thickness": float(summary["sigma_thickness"]),
        "ito_alpha": float(summary["ito_alpha"]),
        "niox_k": float(summary["niox_k"]),
    }
    model = build_phase07_stack_model()
    window_scales = compute_window_scales(rear_sample)

    d_bulk_grid = np.arange(600.0, 800.0 + 1e-9, 2.0, dtype=float)
    pvk_scale_grid = np.arange(0.5, 2.5 + 1e-9, 0.05, dtype=float)
    cost_map = np.empty((pvk_scale_grid.size, d_bulk_grid.size), dtype=float)

    valley_trace: list[tuple[float, float, float]] = []
    global_best = (None, None, float("inf"))
    for row_index, pvk_b_scale in enumerate(pvk_scale_grid):
        row_best = (None, float("inf"))
        for col_index, d_bulk in enumerate(d_bulk_grid):
            stage2_params = {
                "d_bulk": float(d_bulk),
                "pvk_b_scale": float(pvk_b_scale),
                **fixed_stage2,
            }
            _, _, rear_cost, _, _ = evaluate_stage2_model(
                sample_input=rear_sample,
                model=model,
                stage1_params=stage1_params,
                stage2_params=stage2_params,
                window_scales=window_scales,
                use_rear_only=True,
            )
            cost_map[row_index, col_index] = rear_cost
            if rear_cost < row_best[1]:
                row_best = (d_bulk, rear_cost)
            if rear_cost < global_best[2]:
                global_best = (d_bulk, pvk_b_scale, rear_cost)
        valley_trace.append((float(pvk_b_scale), float(row_best[0]), float(row_best[1])))

    valley_array = np.asarray(valley_trace, dtype=float)
    slope, intercept = np.polyfit(valley_array[:, 0], valley_array[:, 1], deg=1)

    heatmap_csv_path = FIT_RESULT_DIR / f"phase07_{sample_slug}_probe_b_heatmap.csv"
    figure_path = FIGURE_DIR / f"phase07_{sample_slug}_sandbox_probe_b_heatmap.png"
    log_path = LOG_DIR / f"phase07_{sample_slug}_sandbox_probe_b_heatmap.md"

    heatmap_frame = pd.DataFrame(cost_map, index=np.round(pvk_scale_grid, 4), columns=np.round(d_bulk_grid, 4))
    heatmap_frame.index.name = "pvk_b_scale"
    heatmap_frame.columns.name = "d_bulk_nm"
    heatmap_frame.to_csv(heatmap_csv_path, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(9.0, 5.8), dpi=320)
    im = ax.imshow(
        cost_map,
        origin="lower",
        aspect="auto",
        extent=[d_bulk_grid.min(), d_bulk_grid.max(), pvk_scale_grid.min(), pvk_scale_grid.max()],
        cmap="viridis",
    )
    fig.colorbar(im, ax=ax, label="Rear Z-Score Cost")
    ax.plot(valley_array[:, 1], valley_array[:, 0], color="#ffffff", linewidth=1.8, linestyle="--", label="Valley trace")
    ax.scatter([global_best[0]], [global_best[1]], color="#ff6f00", s=45, label="Global min", zorder=3)
    ax.set_xlabel("d_bulk (nm)")
    ax.set_ylabel("pvk_b_scale")
    ax.set_title(f"Phase 07 Probe B Heatmap: {sample_name}")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(figure_path, dpi=320, bbox_inches="tight")
    plt.close(fig)

    lines = [
        f"# Phase 07 Sandbox Probe B: {sample_name}",
        "",
        "## Setup",
        "",
        f"- stage1_locked_d_ITO: `{stage1_params['d_ITO']:.6f}`",
        f"- stage1_locked_d_NiOx: `{stage1_params['d_NiOx']:.6f}`",
        f"- stage1_locked_sigma_front_rms_nm: `{stage1_params['sigma_front_rms_nm']:.6f}`",
        f"- fixed_d_rough: `{fixed_stage2['d_rough']:.6f}`",
        f"- fixed_sigma_thickness: `{fixed_stage2['sigma_thickness']:.6f}`",
        f"- fixed_ito_alpha: `{fixed_stage2['ito_alpha']:.6f}`",
        f"- fixed_niox_k: `{fixed_stage2['niox_k']:.6f}`",
        "- grid_d_bulk: `600-800 nm, step 2 nm`",
        "- grid_pvk_b_scale: `0.5-2.5, step 0.05`",
        "",
        "## Results",
        "",
        f"- global_min_d_bulk_nm: `{float(global_best[0]):.6f}`",
        f"- global_min_pvk_b_scale: `{float(global_best[1]):.6f}`",
        f"- global_min_rear_cost: `{float(global_best[2]):.6f}`",
        f"- valley_linear_fit: `d_bulk ≈ {slope:.4f} * pvk_b_scale + {intercept:.4f}`",
        "",
        "## Outputs",
        "",
        f"- heatmap_csv: `{heatmap_csv_path}`",
        f"- figure: `{figure_path}`",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"global_min_d_bulk_nm={float(global_best[0]):.6f}")
    print(f"global_min_pvk_b_scale={float(global_best[1]):.6f}")
    print(f"global_min_rear_cost={float(global_best[2]):.6f}")
    print(f"valley_linear_fit=d_bulk≈{slope:.4f}*pvk_b_scale+{intercept:.4f}")
    print(f"figure_path={figure_path}")
    print(f"log_path={log_path}")
    print(f"heatmap_csv_path={heatmap_csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
