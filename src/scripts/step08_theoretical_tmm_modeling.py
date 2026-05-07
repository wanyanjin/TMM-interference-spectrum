"""Phase 08 theoretical TMM forward modeling pipeline.

This script freezes the best-fit parameters from Phase 07 and rebuilds the
measured-space reflectance curves with the same observation model. The aligned
stack ultimately traces the PVK optical constants back to [LIT-0001] within the
measured window, while Phase 07/08 only reuse the documented aligned stack.
"""

from __future__ import annotations

from dataclasses import dataclass
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
    FRONT_WINDOW_NM,
    MASKED_WINDOW_NM,
    REAR_WINDOW_NM,
    WINDOW_FRONT,
    WINDOW_MASKED,
    WINDOW_REAR,
    apply_front_scattering_observation_model,
    build_phase07_stack_model,
    calc_macro_reflectance,
    compute_rear_derivative_correlation,
    compute_window_scales,
    compute_zscore,
    interpolate_complex,
    load_phase07_sample_input,
)


PHASE_NAME = "Phase 08"
DEFAULT_PHASE07_SUMMARY_PATH = PROJECT_ROOT / "data" / "processed" / "phase07" / "phase07_fit_summary.csv"
DEFAULT_PHASE07_FIT_INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "phase07" / "fit_inputs"


@dataclass(frozen=True)
class Phase08Paths:
    processed_root: Path
    theory_curves: Path
    figures: Path
    logs: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 08 theoretical TMM forward modeling.")
    parser.add_argument("--phase07-summary", type=Path, default=DEFAULT_PHASE07_SUMMARY_PATH)
    parser.add_argument("--phase07-fit-input-dir", type=Path, default=DEFAULT_PHASE07_FIT_INPUT_DIR)
    parser.add_argument("--sample", action="append", dest="samples", default=None)
    return parser.parse_args()


def ensure_output_dirs() -> Phase08Paths:
    paths = Phase08Paths(
        processed_root=PROJECT_ROOT / "data" / "processed" / "phase08",
        theory_curves=PROJECT_ROOT / "data" / "processed" / "phase08" / "theory_curves",
        figures=PROJECT_ROOT / "results" / "figures" / "phase08",
        logs=PROJECT_ROOT / "results" / "logs" / "phase08",
    )
    for path in paths.__dict__.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def slugify_sample_name(sample_name: str) -> str:
    return sample_name.lower().replace(" ", "_").replace("-", "_")


def resolve_fit_input_path(sample_name: str, fit_input_dir: Path) -> Path:
    fit_input_path = fit_input_dir / f"phase07_{slugify_sample_name(sample_name)}_fit_input.csv"
    if not fit_input_path.exists():
        raise FileNotFoundError(f"未找到 {sample_name} 对应的 Phase 07 fit_input: {fit_input_path}")
    return fit_input_path


def filter_summary_frame(frame: pd.DataFrame, samples: list[str] | None) -> pd.DataFrame:
    if not samples:
        return frame
    selected = frame[frame["sample_name"].isin(samples)].copy()
    missing = sorted(set(samples) - set(selected["sample_name"].tolist()))
    if missing:
        raise ValueError(f"Phase 07 汇总中缺少样本: {missing}")
    return selected


def compute_phase08_forward_curve(
    sample_name: str,
    summary_row: pd.Series,
    fit_input_dir: Path,
    model,
) -> tuple[pd.DataFrame, dict[str, object]]:
    fit_input_path = resolve_fit_input_path(sample_name, fit_input_dir)
    sample_input = load_phase07_sample_input(
        fit_input_path=fit_input_path,
        sample_name=sample_name,
        source_mode=str(summary_row["source_mode"]),
        source_path=fit_input_path,
        with_ag=bool(summary_row["with_ag"]),
    )
    wavelengths = sample_input.wavelength_nm
    window_scales = compute_window_scales(sample_input)

    params = {
        "d_ITO": float(summary_row["d_ITO"]),
        "d_NiOx": float(summary_row["d_NiOx"]),
        "sigma_front_rms_nm": float(summary_row["sigma_front_rms_nm"]),
        "d_bulk": float(summary_row["d_bulk"]),
        "d_rough": float(summary_row["d_rough"]),
        "sigma_thickness": float(summary_row["sigma_thickness"]),
        "ito_alpha": float(summary_row["ito_alpha"]),
        "pvk_b_scale": float(summary_row["pvk_b_scale"]),
        "niox_k": float(summary_row["niox_k"]),
    }

    physical_reflectance = calc_macro_reflectance(
        model=model,
        wavelengths_nm=wavelengths,
        with_ag=sample_input.with_ag,
        d_ITO_nm=params["d_ITO"],
        d_NiOx_nm=params["d_NiOx"],
        d_bulk_nm=params["d_bulk"],
        d_rough_nm=params["d_rough"],
        sigma_thickness_nm=params["sigma_thickness"],
        ito_alpha=params["ito_alpha"],
        pvk_b_scale=params["pvk_b_scale"],
        niox_k=params["niox_k"],
    )
    glass_nk = interpolate_complex(model.wavelength_nm, model.n_glass, wavelengths)
    collected_reflectance, front_scatter = apply_front_scattering_observation_model(
        glass_nk=glass_nk,
        wavelength_nm=wavelengths,
        sigma_front_rms_nm=params["sigma_front_rms_nm"],
        stack_reflectance=physical_reflectance,
    )
    residual = collected_reflectance - sample_input.reflectance
    rear_mask = sample_input.rear_mask
    rear_z_measured = np.full(wavelengths.shape, np.nan, dtype=float)
    rear_z_theory = np.full(wavelengths.shape, np.nan, dtype=float)
    rear_z_measured[rear_mask] = compute_zscore(sample_input.reflectance[rear_mask])
    rear_z_theory[rear_mask] = compute_zscore(collected_reflectance[rear_mask])

    front_scale = next(scale.scale_value for scale in window_scales if scale.label == WINDOW_FRONT)
    rear_scale = next(scale.scale_value for scale in window_scales if scale.label == WINDOW_REAR)

    curve_frame = pd.DataFrame(
        {
            "Wavelength_nm": wavelengths,
            "Absolute_Reflectance_Measured": sample_input.reflectance,
            "Absolute_Reflectance_Theory": collected_reflectance,
            "Absolute_Reflectance_Physical": physical_reflectance,
            "Residual": residual,
            "Front_Scatter_Factor": front_scatter,
            "Rear_ZScore_Measured": rear_z_measured,
            "Rear_ZScore_Theory": rear_z_theory,
            "window_label": sample_input.window_label,
        }
    )

    front_mask = sample_input.front_mask
    masked_mask = sample_input.masked_mask
    summary_payload = {
        "sample_name": sample_name,
        "with_ag": bool(sample_input.with_ag),
        "source_mode": sample_input.source_mode,
        "fit_input_path": fit_input_path.as_posix(),
        "window_front_scale": front_scale,
        "window_rear_scale": rear_scale,
        "front_rmse": float(np.sqrt(np.mean(residual[front_mask] ** 2))),
        "masked_rmse": float(np.sqrt(np.mean(residual[masked_mask] ** 2))),
        "rear_rmse": float(np.sqrt(np.mean(residual[rear_mask] ** 2))),
        "full_rmse": float(np.sqrt(np.mean(residual**2))),
        "rear_derivative_correlation": float(
            compute_rear_derivative_correlation(sample_input=sample_input, modeled_reflectance=collected_reflectance)
        ),
        "reflectance_min_measured": float(np.min(sample_input.reflectance)),
        "reflectance_max_measured": float(np.max(sample_input.reflectance)),
        "reflectance_min_theory": float(np.min(collected_reflectance)),
        "reflectance_max_theory": float(np.max(collected_reflectance)),
    }
    summary_payload.update(params)
    return curve_frame, summary_payload


def add_window_background(axis: plt.Axes) -> None:
    axis.axvspan(FRONT_WINDOW_NM[0], FRONT_WINDOW_NM[1], color="#e8f3ec", alpha=0.85)
    axis.axvspan(MASKED_WINDOW_NM[0], MASKED_WINDOW_NM[1], color="#fff2cc", alpha=0.9)
    axis.axvspan(REAR_WINDOW_NM[0], REAR_WINDOW_NM[1], color="#e7f0fa", alpha=0.9)


def plot_phase08_theory_curve(sample_name: str, curve_frame: pd.DataFrame, output_path: Path) -> None:
    wavelengths = curve_frame["Wavelength_nm"].to_numpy(dtype=float)
    measured = curve_frame["Absolute_Reflectance_Measured"].to_numpy(dtype=float)
    theory = curve_frame["Absolute_Reflectance_Theory"].to_numpy(dtype=float)
    physical = curve_frame["Absolute_Reflectance_Physical"].to_numpy(dtype=float)
    residual = curve_frame["Residual"].to_numpy(dtype=float)
    scatter = curve_frame["Front_Scatter_Factor"].to_numpy(dtype=float)
    rear_z_measured = curve_frame["Rear_ZScore_Measured"].to_numpy(dtype=float)
    rear_z_theory = curve_frame["Rear_ZScore_Theory"].to_numpy(dtype=float)

    fig, axes = plt.subplots(3, 1, figsize=(11.5, 10.0), dpi=320, constrained_layout=True)

    add_window_background(axes[0])
    axes[0].plot(wavelengths, measured * 100.0, color="#424242", linewidth=2.3, label="Measured")
    axes[0].plot(wavelengths, theory * 100.0, color="#005b96", linewidth=1.8, linestyle="--", label="Phase 08 theory")
    axes[0].plot(wavelengths, physical * 100.0, color="#b03a2e", linewidth=1.4, linestyle=":", label="Unattenuated stack")
    axes[0].set_ylabel("Absolute Reflectance (%)")
    axes[0].set_title(f"{PHASE_NAME} Theoretical TMM Modeling: {sample_name}")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best")

    axes[1].plot(wavelengths, residual * 100.0, color="#7b1e3a", linewidth=1.5)
    axes[1].axhline(0.0, color="#616161", linewidth=1.0, linestyle="--")
    add_window_background(axes[1])
    axes[1].set_ylabel("Residual (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    scatter_axis = axes[1].twinx()
    front_mask = curve_frame["window_label"].to_numpy(dtype=object) == WINDOW_FRONT
    scatter_axis.plot(wavelengths[front_mask], scatter[front_mask], color="#2e7d32", linewidth=1.4, alpha=0.75)
    scatter_axis.set_ylabel("Front Scatter Factor")

    rear_mask = np.isfinite(rear_z_measured) & np.isfinite(rear_z_theory)
    axes[2].plot(wavelengths[rear_mask], rear_z_measured[rear_mask], color="#424242", linewidth=2.0, label="Rear z(measured)")
    axes[2].plot(wavelengths[rear_mask], rear_z_theory[rear_mask], color="#005b96", linewidth=1.7, linestyle="--", label="Rear z(theory)")
    axes[2].set_xlim(REAR_WINDOW_NM[0], REAR_WINDOW_NM[1])
    axes[2].set_xlabel("Wavelength (nm)")
    axes[2].set_ylabel("Z-Score")
    axes[2].grid(True, linestyle="--", alpha=0.25)
    axes[2].legend(loc="best")

    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def write_batch_log(rows: list[dict[str, object]], output_path: Path) -> None:
    lines = [
        f"# {PHASE_NAME} Theoretical TMM Modeling Batch Log",
        "",
        "## Scope",
        "",
        "- Inputs: `data/processed/phase07/phase07_fit_summary.csv` + `data/processed/phase07/fit_inputs/*.csv`",
        "- Optical stack: `resources/aligned_full_stack_nk.csv`",
        "- Observation model: reuses Phase 07 front-surface Debye-Waller attenuation and rear-window z-score diagnostics",
        "",
        "## Samples",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row['sample_name']}",
                "",
                f"- full_rmse: `{row['full_rmse']:.6f}`",
                f"- front_rmse: `{row['front_rmse']:.6f}`",
                f"- masked_rmse: `{row['masked_rmse']:.6f}`",
                f"- rear_rmse: `{row['rear_rmse']:.6f}`",
                f"- rear_derivative_correlation: `{row['rear_derivative_correlation']:.6f}`",
                f"- d_bulk: `{row['d_bulk']:.6f}` nm",
                f"- d_rough: `{row['d_rough']:.6f}` nm",
                f"- sigma_front_rms_nm: `{row['sigma_front_rms_nm']:.6f}` nm",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dirs = ensure_output_dirs()

    summary_path = args.phase07_summary.resolve()
    fit_input_dir = args.phase07_fit_input_dir.resolve()
    summary_frame = pd.read_csv(summary_path)
    summary_frame = filter_summary_frame(summary_frame, args.samples)
    if summary_frame.empty:
        raise ValueError(f"{summary_path} 中没有可执行的样本。")

    model = build_phase07_stack_model()
    batch_rows: list[dict[str, object]] = []
    manifest_rows: list[dict[str, object]] = []

    for _, summary_row in summary_frame.iterrows():
        sample_name = str(summary_row["sample_name"])
        sample_slug = slugify_sample_name(sample_name)
        curve_frame, batch_row = compute_phase08_forward_curve(
            sample_name=sample_name,
            summary_row=summary_row,
            fit_input_dir=fit_input_dir,
            model=model,
        )
        curve_path = output_dirs.theory_curves / f"phase08_{sample_slug}_theory_curve.csv"
        figure_path = output_dirs.figures / f"phase08_{sample_slug}_theory_vs_measured.png"
        curve_frame.to_csv(curve_path, index=False, encoding="utf-8-sig")
        plot_phase08_theory_curve(sample_name=sample_name, curve_frame=curve_frame, output_path=figure_path)

        batch_row["theory_curve_path"] = curve_path.as_posix()
        batch_row["figure_path"] = figure_path.as_posix()
        batch_rows.append(batch_row)
        manifest_rows.append(
            {
                "sample_name": sample_name,
                "phase07_summary_path": summary_path.as_posix(),
                "phase07_fit_input_dir": fit_input_dir.as_posix(),
                "phase08_theory_curve_path": curve_path.as_posix(),
                "phase08_figure_path": figure_path.as_posix(),
            }
        )

    batch_summary_path = output_dirs.processed_root / "phase08_theory_summary.csv"
    manifest_path = output_dirs.processed_root / "phase08_source_manifest.csv"
    log_path = output_dirs.logs / "phase08_theoretical_tmm_modeling.md"
    pd.DataFrame(batch_rows).to_csv(batch_summary_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(manifest_rows).to_csv(manifest_path, index=False, encoding="utf-8-sig")
    write_batch_log(batch_rows, log_path)

    print(f"batch_summary_path={batch_summary_path}")
    print(f"manifest_path={manifest_path}")
    print(f"log_path={log_path}")
    print(f"sample_count={len(batch_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
