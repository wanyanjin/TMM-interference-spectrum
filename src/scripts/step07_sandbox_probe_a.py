"""Phase 07 diagnostic sandbox probe A: front-window absorption hypothesis."""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

import matplotlib
import numpy as np
from scipy.optimize import minimize_scalar

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.phase07_dual_window import (  # noqa: E402
    Phase07OpticalModel,
    Phase07SampleInput,
    apply_front_scattering_observation_model,
    build_front_residual,
    build_phase07_stack_model,
    compute_cost_from_normalized_residual,
    compute_window_scales,
    load_phase07_sample_input,
    write_phase07_fit_input,
    calc_macro_reflectance,
)


DEFAULT_HDR_CURVE_PATH = PROJECT_ROOT / "test_data" / "phase7_data" / "DEVICE-1-withAg-P1_hdr_curves.csv"
FIT_INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "phase07" / "fit_inputs"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phase07"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phase07"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 07 front-window absorption probe.")
    parser.add_argument("--hdr-curve", type=Path, default=DEFAULT_HDR_CURVE_PATH)
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
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def make_front_sample(sample_input: Phase07SampleInput) -> Phase07SampleInput:
    mask = sample_input.front_mask
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


def make_modified_model(base_model: Phase07OpticalModel, target: str, extra_k: float) -> Phase07OpticalModel:
    mask = (base_model.wavelength_nm >= 500.0) & (base_model.wavelength_nm <= 650.0)
    n_ito = base_model.n_ito.copy()
    n_niox = base_model.n_niox.copy()
    if target == "niox":
        n_niox[mask] = np.real(n_niox[mask]) + 1j * (np.imag(n_niox[mask]) + extra_k)
    elif target == "ito":
        n_ito[mask] = np.real(n_ito[mask]) + 1j * (np.imag(n_ito[mask]) + extra_k)
    else:
        raise ValueError(f"未知 target: {target}")
    return Phase07OpticalModel(
        wavelength_nm=base_model.wavelength_nm,
        n_glass=base_model.n_glass,
        n_ito=n_ito,
        n_niox=n_niox,
        n_pvk=base_model.n_pvk,
        n_c60=base_model.n_c60,
        n_ag=base_model.n_ag,
    )


def evaluate_front_probe(
    sample_input: Phase07SampleInput,
    model: Phase07OpticalModel,
    extra_k: float,
    target: str,
) -> tuple[float, np.ndarray, np.ndarray]:
    probe_model = make_modified_model(model, target, extra_k)
    front_sample = make_front_sample(sample_input)
    scales = compute_window_scales(front_sample)
    physical = calc_macro_reflectance(
        model=probe_model,
        wavelengths_nm=front_sample.wavelength_nm,
        with_ag=front_sample.with_ag,
        d_ITO_nm=100.0,
        d_NiOx_nm=45.0,
        d_bulk_nm=700.0,
        d_rough_nm=0.0,
        sigma_thickness_nm=0.0,
        ito_alpha=0.0,
        pvk_b_scale=1.0,
        niox_k=0.0,
    )
    collected, _ = apply_front_scattering_observation_model(
        glass_nk=np.interp(front_sample.wavelength_nm, probe_model.wavelength_nm, np.real(probe_model.n_glass))
        + 1j * np.interp(front_sample.wavelength_nm, probe_model.wavelength_nm, np.imag(probe_model.n_glass)),
        wavelength_nm=front_sample.wavelength_nm,
        sigma_front_rms_nm=0.0,
        stack_reflectance=physical,
    )
    normalized = build_front_residual(front_sample, collected, scales)
    cost = compute_cost_from_normalized_residual(np.where(front_sample.front_mask, normalized, np.nan))
    return cost, collected, physical


def optimize_probe_parameter(sample_input: Phase07SampleInput, model: Phase07OpticalModel, target: str) -> dict[str, object]:
    objective = lambda x: evaluate_front_probe(sample_input, model, float(x), target)[0]
    result = minimize_scalar(objective, bounds=(0.0, 1.0), method="bounded", options={"xatol": 1e-3})
    best_cost, best_collected, best_physical = evaluate_front_probe(sample_input, model, float(result.x), target)
    return {
        "target": target,
        "best_extra_k": float(result.x),
        "best_cost": float(best_cost),
        "best_collected": best_collected,
        "best_physical": best_physical,
    }


def main() -> int:
    args = parse_args()
    ensure_dirs()

    hdr_curve_path = args.hdr_curve.resolve()
    sample_name = hdr_curve_path.stem.replace("_hdr_curves", "")
    sample_slug = slugify_sample_name(sample_name)
    fit_input_path = FIT_INPUT_DIR / f"phase07_{sample_slug}_probe_a_fit_input.csv"
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
    front_sample = make_front_sample(sample_input)
    model = build_phase07_stack_model()

    baseline_cost, baseline_collected, baseline_physical = evaluate_front_probe(sample_input, model, 0.0, "niox")
    niox_result = optimize_probe_parameter(sample_input, model, "niox")
    ito_result = optimize_probe_parameter(sample_input, model, "ito")

    scan_grid = np.linspace(0.0, 1.0, 81)
    niox_cost_curve = np.asarray([evaluate_front_probe(sample_input, model, value, "niox")[0] for value in scan_grid], dtype=float)
    ito_cost_curve = np.asarray([evaluate_front_probe(sample_input, model, value, "ito")[0] for value in scan_grid], dtype=float)

    figure_path = FIGURE_DIR / f"phase07_{sample_slug}_sandbox_probe_a.png"
    log_path = LOG_DIR / f"phase07_{sample_slug}_sandbox_probe_a.md"

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.8), dpi=320, constrained_layout=True)
    axes[0].plot(scan_grid, niox_cost_curve, color="#b03a2e", linewidth=1.8, label="NiOx short-k")
    axes[0].plot(scan_grid, ito_cost_curve, color="#005b96", linewidth=1.8, label="ITO short-k")
    axes[0].axhline(0.05, color="#546e7a", linestyle="--", linewidth=1.0, label="Target cost 0.05")
    axes[0].axvline(niox_result["best_extra_k"], color="#b03a2e", linestyle=":", linewidth=1.2)
    axes[0].axvline(ito_result["best_extra_k"], color="#005b96", linestyle=":", linewidth=1.2)
    axes[0].set_xlabel("Extra short-wave k")
    axes[0].set_ylabel("Front-window cost")
    axes[0].set_title("Probe A Cost Scan")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend()

    axes[1].plot(front_sample.wavelength_nm, front_sample.reflectance * 100.0, color="#424242", linewidth=2.3, label="Measured")
    axes[1].plot(front_sample.wavelength_nm, baseline_collected * 100.0, color="#8d6e63", linewidth=1.4, linestyle="--", label="Baseline")
    axes[1].plot(front_sample.wavelength_nm, niox_result["best_collected"] * 100.0, color="#b03a2e", linewidth=1.6, linestyle="--", label="Best NiOx probe")
    axes[1].plot(front_sample.wavelength_nm, ito_result["best_collected"] * 100.0, color="#005b96", linewidth=1.6, linestyle="--", label="Best ITO probe")
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Absolute Reflectance (%)")
    axes[1].set_title("Probe A Front-Window Fits")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend()
    fig.savefig(figure_path, dpi=320, bbox_inches="tight")
    plt.close(fig)

    better_target = "ITO" if ito_result["best_cost"] < niox_result["best_cost"] else "NiOx"
    lines = [
        f"# Phase 07 Sandbox Probe A: {sample_name}",
        "",
        "## Setup",
        "",
        "- Geometry locked: `d_ITO = 100 nm`, `d_NiOx = 45 nm`, `sigma_front_rms_nm = 0`",
        "- Fixed rear parameters: `d_bulk = 700`, `d_rough = 0`, `sigma_thickness = 0`, `ito_alpha = 0`, `pvk_b_scale = 1`, `niox_k = 0`",
        "- Probe compares short-wave extra absorption on `NiOx` and `ITO` separately.",
        "",
        "## Results",
        "",
        f"- baseline_cost: `{baseline_cost:.6f}`",
        f"- niox_best_extra_k: `{niox_result['best_extra_k']:.6f}`",
        f"- niox_best_cost: `{niox_result['best_cost']:.6f}`",
        f"- ito_best_extra_k: `{ito_result['best_extra_k']:.6f}`",
        f"- ito_best_cost: `{ito_result['best_cost']:.6f}`",
        f"- better_target: `{better_target}`",
        "",
        "## Interpretation",
        "",
        "- If `NiOx` probe fails to lower cost while `ITO` helps, the original `NiOx short-wave absorption missing` hypothesis is likely false.",
        "- If neither branch crosses `0.05`, then a single scalar short-wave absorber is insufficient to explain the front-window mismatch.",
        "",
        f"- figure: `{figure_path}`",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"baseline_cost={baseline_cost:.6f}")
    print(f"niox_best_extra_k={niox_result['best_extra_k']:.6f}")
    print(f"niox_best_cost={niox_result['best_cost']:.6f}")
    print(f"ito_best_extra_k={ito_result['best_extra_k']:.6f}")
    print(f"ito_best_cost={ito_result['best_cost']:.6f}")
    print(f"figure_path={figure_path}")
    print(f"log_path={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
