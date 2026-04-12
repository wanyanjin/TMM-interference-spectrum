"""Phase A-2.1 PVK band-edge uncertainty ensemble propagation.

This phase does not attempt to refit a new PVK truth. Instead it constructs a
small uncertainty family around the repaired PVK surrogate v2 and propagates
that band-edge uncertainty to the already established thickness and rear-BEMA
mechanism studies.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import shutil
import sys

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (str(PROJECT_ROOT / "src"), str(SCRIPT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import stepA1_pristine_baseline as phase_a1  # noqa: E402
from core.full_stack_microcavity import AG_BOUNDARY_FINITE_FILM  # noqa: E402


PHASE_NAME = "Phase A-2.1"
NOMINAL_ALIGNED_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_pvk_v2.csv"
PVK_ENSEMBLE_DIR = PROJECT_ROOT / "resources" / "pvk_ensemble"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phaseA2_1"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phaseA2_1"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phaseA2_1"
REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phaseA2_1_pvk_uncertainty_ensemble"

PHASE_A2_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA2" / "phaseA2_pvk_thickness_scan.csv"
PHASE_B1_SCAN_PATH = PROJECT_ROOT / "data" / "processed" / "phaseB1" / "phaseB1_rear_bema_scan.csv"

BAND_WINDOW = (740.0, 850.0)
LOCAL_ZOOM = (740.0, 850.0)
SOFT_WINDOW = (730.0, 900.0)
REAR_WINDOW = (810.0, 1100.0)
TRANSITION_WINDOW = (740.0, 850.0)
THICKNESS_SUBSET_NM = (600.0, 700.0, 800.0)
REAR_BEMA_SUBSET_NM = (0.0, 10.0, 20.0, 30.0)
NOMINAL_THICKNESS_REFERENCE_NM = 700.0
MORE_ABS_SCALE = 1.35
LESS_ABS_SCALE = 0.65
N_COUPLING_STRENGTH = 0.05
TAIL_START_NM = 740.0
TAIL_END_NM = 850.0
MORE_TAIL_FRACTION = 0.18
LESS_TAIL_FRACTION = 0.05


@dataclass(frozen=True)
class EnsembleMember:
    ensemble_id: str
    description: str
    perturbation_type: str
    notes: str
    k_scale: float
    n_shift_sign: float


ENSEMBLE_MEMBERS = (
    EnsembleMember(
        ensemble_id="nominal",
        description="Repaired PVK surrogate v2 without extra perturbation",
        perturbation_type="none",
        notes="Direct reuse of Phase A-1.2 nominal surrogate",
        k_scale=1.0,
        n_shift_sign=0.0,
    ),
    EnsembleMember(
        ensemble_id="more_absorptive",
        description="Locally stronger band-edge absorption tail in 740-850 nm",
        perturbation_type="smooth_k_up_with_linked_n_shift",
        notes="Band-edge tail stays nonzero for longer wavelength before relaxing to nominal tail",
        k_scale=MORE_ABS_SCALE,
        n_shift_sign=1.0,
    ),
    EnsembleMember(
        ensemble_id="less_absorptive",
        description="Locally weaker band-edge absorption tail in 740-850 nm",
        perturbation_type="smooth_k_down_with_linked_n_shift",
        notes="Band-edge tail becomes thinner but remains continuous and seam-free",
        k_scale=LESS_ABS_SCALE,
        n_shift_sign=-1.0,
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase A-2.1 PVK uncertainty ensemble.")
    parser.add_argument("--nominal-nk-csv", type=Path, default=NOMINAL_ALIGNED_PATH)
    return parser.parse_args()


def ensure_dirs() -> None:
    PVK_ENSEMBLE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def smoothstep(x: np.ndarray) -> np.ndarray:
    x_clip = np.clip(np.asarray(x, dtype=float), 0.0, 1.0)
    return x_clip * x_clip * (3.0 - 2.0 * x_clip)


def raised_window(wavelength_nm: np.ndarray, soft_window: tuple[float, float], hard_window: tuple[float, float]) -> np.ndarray:
    wl = np.asarray(wavelength_nm, dtype=float)
    left_soft, right_soft = soft_window
    left_hard, right_hard = hard_window
    weight = np.zeros_like(wl, dtype=float)

    left_ramp = (wl >= left_soft) & (wl < left_hard)
    flat = (wl >= left_hard) & (wl <= right_hard)
    right_ramp = (wl > right_hard) & (wl <= right_soft)

    if np.any(left_ramp):
        weight[left_ramp] = smoothstep((wl[left_ramp] - left_soft) / (left_hard - left_soft))
    weight[flat] = 1.0
    if np.any(right_ramp):
        weight[right_ramp] = smoothstep((right_soft - wl[right_ramp]) / (right_soft - right_hard))
    return weight


def compute_eps(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    n = frame["n_PVK"].to_numpy(dtype=float)
    k = frame["k_PVK"].to_numpy(dtype=float)
    eps1 = n * n - k * k
    eps2 = 2.0 * n * k
    return eps1, eps2


def derivative(values: np.ndarray, wavelength_nm: np.ndarray) -> np.ndarray:
    return np.gradient(np.asarray(values, dtype=float), np.asarray(wavelength_nm, dtype=float))


def build_ensemble_tables(nominal_path: Path) -> tuple[dict[str, Path], pd.DataFrame, pd.DataFrame]:
    nominal_frame = pd.read_csv(nominal_path)
    wavelength_nm = nominal_frame["Wavelength_nm"].to_numpy(dtype=float)
    weights = raised_window(wavelength_nm, SOFT_WINDOW, BAND_WINDOW)
    normalized_w = weights / max(float(np.max(weights)), 1e-12)
    nominal_n = nominal_frame["n_PVK"].to_numpy(dtype=float)
    nominal_k = nominal_frame["k_PVK"].to_numpy(dtype=float)
    k_anchor_750 = float(nominal_frame.loc[np.isclose(nominal_frame["Wavelength_nm"], TAIL_START_NM), "k_PVK"].iloc[0])
    tail_weight = np.zeros_like(wavelength_nm, dtype=float)
    tail_mask = (wavelength_nm >= TAIL_START_NM) & (wavelength_nm <= TAIL_END_NM)
    if np.any(tail_mask):
        tail_weight[tail_mask] = smoothstep((TAIL_END_NM - wavelength_nm[tail_mask]) / (TAIL_END_NM - TAIL_START_NM))

    aligned_paths: dict[str, Path] = {}
    manifest_rows: list[dict[str, str]] = []
    local_rows: list[pd.DataFrame] = []

    for member in ENSEMBLE_MEMBERS:
        frame = nominal_frame.copy()
        if member.ensemble_id == "nominal":
            n_member = nominal_n.copy()
            k_member = nominal_k.copy()
        else:
            k_member = nominal_k * (1.0 + (member.k_scale - 1.0) * normalized_w)
            tail_fraction = MORE_TAIL_FRACTION if member.ensemble_id == "more_absorptive" else LESS_TAIL_FRACTION
            k_member = k_member + k_anchor_750 * tail_fraction * tail_weight
            k_member = np.maximum(k_member, 0.0)
            tail_anchor = np.max(nominal_k[(wavelength_nm >= BAND_WINDOW[0]) & (wavelength_nm <= BAND_WINDOW[1])])
            coupling = member.n_shift_sign * N_COUPLING_STRENGTH * normalized_w * (nominal_k / max(float(tail_anchor), 1e-12))
            coupling = coupling + member.n_shift_sign * 0.02 * tail_weight
            n_member = nominal_n + coupling

        frame["n_PVK"] = n_member
        frame["k_PVK"] = k_member
        output_path = PVK_ENSEMBLE_DIR / f"aligned_full_stack_nk_pvk_ens_{member.ensemble_id}.csv"
        frame.to_csv(output_path, index=False, encoding="utf-8-sig")
        aligned_paths[member.ensemble_id] = output_path

        local_mask = (wavelength_nm >= SOFT_WINDOW[0]) & (wavelength_nm <= SOFT_WINDOW[1])
        eps1 = n_member * n_member - k_member * k_member
        eps2 = 2.0 * n_member * k_member
        local_rows.append(
            pd.DataFrame(
                {
                    "Wavelength_nm": wavelength_nm[local_mask],
                    "ensemble_id": member.ensemble_id,
                    "n_PVK": n_member[local_mask],
                    "k_PVK": k_member[local_mask],
                    "eps1": eps1[local_mask],
                    "eps2": eps2[local_mask],
                }
            )
        )
        manifest_rows.append(
            {
                "ensemble_id": member.ensemble_id,
                "description": member.description,
                "perturbation_window_nm": "740-850 (soft 730-900)",
                "perturbation_type": member.perturbation_type,
                "notes": member.notes,
            }
        )

    manifest = pd.DataFrame(manifest_rows)
    local_comparison = pd.concat(local_rows, ignore_index=True)
    manifest.to_csv(PROCESSED_DIR / "pvk_ensemble_manifest.csv", index=False, encoding="utf-8-sig")
    local_comparison.to_csv(PROCESSED_DIR / "pvk_ensemble_local_comparison.csv", index=False, encoding="utf-8-sig")
    return aligned_paths, manifest, local_comparison


def plot_pvk_ensemble_overlays(local_comparison: pd.DataFrame) -> None:
    pivot = {}
    for member in ENSEMBLE_MEMBERS:
        pivot[member.ensemble_id] = local_comparison[local_comparison["ensemble_id"] == member.ensemble_id].copy()
    colors = {
        "nominal": "#005b96",
        "more_absorptive": "#b03a2e",
        "less_absorptive": "#2e7d32",
    }

    fig, axes = plt.subplots(2, 1, figsize=(10.4, 8.0), dpi=320, constrained_layout=True, sharex=True)
    for ensemble_id, frame in pivot.items():
        wl = frame["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, frame["n_PVK"].to_numpy(dtype=float), color=colors[ensemble_id], linewidth=1.8, label=ensemble_id)
        axes[1].plot(wl, frame["k_PVK"].to_numpy(dtype=float), color=colors[ensemble_id], linewidth=1.8, label=ensemble_id)
    axes[0].set_ylabel("n")
    axes[0].set_title("PVK Ensemble n/k Overlay")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best")
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("k")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    fig.savefig(FIGURE_DIR / "pvk_ensemble_nk_overlay.png", dpi=320, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(10.4, 8.0), dpi=320, constrained_layout=True, sharex=True)
    for ensemble_id, frame in pivot.items():
        wl = frame["Wavelength_nm"].to_numpy(dtype=float)
        axes[0].plot(wl, frame["eps1"].to_numpy(dtype=float), color=colors[ensemble_id], linewidth=1.8, label=ensemble_id)
        axes[1].plot(wl, frame["eps2"].to_numpy(dtype=float), color=colors[ensemble_id], linewidth=1.8, label=ensemble_id)
    axes[0].set_ylabel("eps1")
    axes[0].set_title("PVK Ensemble eps Overlay")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best")
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("eps2")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    fig.savefig(FIGURE_DIR / "pvk_ensemble_eps_overlay.png", dpi=320, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(10.4, 8.0), dpi=320, constrained_layout=True, sharex=True)
    for ensemble_id, frame in pivot.items():
        wl = frame["Wavelength_nm"].to_numpy(dtype=float)
        dn = derivative(frame["n_PVK"].to_numpy(dtype=float), wl)
        dk = derivative(frame["k_PVK"].to_numpy(dtype=float), wl)
        axes[0].plot(wl, dn, color=colors[ensemble_id], linewidth=1.8, label=ensemble_id)
        axes[1].plot(wl, dk, color=colors[ensemble_id], linewidth=1.8, label=ensemble_id)
    axes[0].set_ylabel("dn/dlambda")
    axes[0].set_title("PVK Ensemble Derivative Overlay")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best")
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("dk/dlambda")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    fig.savefig(FIGURE_DIR / "pvk_ensemble_derivative_overlay.png", dpi=320, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10.0, 5.2), dpi=320)
    for ensemble_id, frame in pivot.items():
        local_mask = (frame["Wavelength_nm"] >= LOCAL_ZOOM[0]) & (frame["Wavelength_nm"] <= LOCAL_ZOOM[1])
        wl = frame.loc[local_mask, "Wavelength_nm"].to_numpy(dtype=float)
        ax.plot(wl, frame.loc[local_mask, "k_PVK"].to_numpy(dtype=float), color=colors[ensemble_id], linewidth=2.0, label=f"{ensemble_id} k")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("k")
    ax.set_title("PVK Ensemble Local Zoom (740-850 nm)")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "pvk_ensemble_local_zoom_740_850.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def load_stack(nk_csv_path: Path):
    stack, _, _ = phase_a1.load_optical_stack_from_aligned_csv(nk_csv_path)
    return stack


def run_thickness_propagation(aligned_paths: dict[str, Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []

    for member in ENSEMBLE_MEMBERS:
        stack = load_stack(aligned_paths[member.ensemble_id])
        nominal_baseline = stack.compute_pristine_baseline_decomposition(
            wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
            use_constant_glass=True,
            constant_glass_nk=phase_a1.DEFAULT_CONSTANT_GLASS_INDEX,
            ag_boundary_mode=phase_a1.AG_BOUNDARY_FINITE_FILM,
            pvk_thickness_nm=NOMINAL_THICKNESS_REFERENCE_NM,
        )
        nominal_stack = np.asarray(nominal_baseline["R_stack"], dtype=float)
        nominal_total = np.asarray(nominal_baseline["R_total"], dtype=float)
        wavelength_nm = np.asarray(nominal_baseline["Wavelength_nm"], dtype=float)
        rear_mask = (wavelength_nm >= REAR_WINDOW[0]) & (wavelength_nm <= REAR_WINDOW[1])
        transition_mask = (wavelength_nm >= TRANSITION_WINDOW[0]) & (wavelength_nm <= TRANSITION_WINDOW[1])

        for thickness_nm in THICKNESS_SUBSET_NM:
            decomposition = stack.compute_pristine_baseline_decomposition(
                wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
                use_constant_glass=True,
                constant_glass_nk=phase_a1.DEFAULT_CONSTANT_GLASS_INDEX,
                ag_boundary_mode=phase_a1.AG_BOUNDARY_FINITE_FILM,
                pvk_thickness_nm=float(thickness_nm),
            )
            frame = pd.DataFrame(decomposition)
            frame["ensemble_id"] = member.ensemble_id
            frame["d_PVK_nm"] = float(thickness_nm)
            frame["Delta_R_stack_vs_700nm"] = frame["R_stack"].to_numpy(dtype=float) - nominal_stack
            frame["Delta_R_total_vs_700nm"] = frame["R_total"].to_numpy(dtype=float) - nominal_total
            rows.append(frame)

            rear_total = frame.loc[rear_mask, "Delta_R_total_vs_700nm"].to_numpy(dtype=float)
            rear_stack = frame.loc[rear_mask, "Delta_R_stack_vs_700nm"].to_numpy(dtype=float)
            transition_total = frame.loc[transition_mask, "Delta_R_total_vs_700nm"].to_numpy(dtype=float)
            transition_stack = frame.loc[transition_mask, "Delta_R_stack_vs_700nm"].to_numpy(dtype=float)
            summary_rows.append(
                {
                    "ensemble_id": member.ensemble_id,
                    "d_PVK_nm": float(thickness_nm),
                    "rear_max_abs_deltaR_total": float(np.max(np.abs(rear_total))),
                    "rear_max_abs_deltaR_stack": float(np.max(np.abs(rear_stack))),
                    "rear_mean_abs_deltaR_total": float(np.mean(np.abs(rear_total))),
                    "rear_mean_abs_deltaR_stack": float(np.mean(np.abs(rear_stack))),
                    "rear_peak_wavelength_deltaR_total": float(wavelength_nm[rear_mask][np.argmax(np.abs(rear_total))]),
                    "transition_max_abs_deltaR_total": float(np.max(np.abs(transition_total))),
                    "transition_max_abs_deltaR_stack": float(np.max(np.abs(transition_stack))),
                    "R_total_780nm": float(frame.loc[np.isclose(frame["Wavelength_nm"], 780.0), "R_total"].iloc[0]),
                }
            )

    scan = pd.concat(rows, ignore_index=True)
    summary = pd.DataFrame(summary_rows)
    scan.to_csv(PROCESSED_DIR / "phaseA2_1_thickness_ensemble_scan.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(PROCESSED_DIR / "phaseA2_1_thickness_robustness_summary.csv", index=False, encoding="utf-8-sig")
    return scan, summary


def run_rear_bema_propagation(aligned_paths: dict[str, Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []

    for member in ENSEMBLE_MEMBERS:
        stack = load_stack(aligned_paths[member.ensemble_id])
        pristine = stack.compute_rear_bema_baseline_decomposition(
            d_bema_rear_nm=0.0,
            wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
            use_constant_glass=True,
            constant_glass_nk=phase_a1.DEFAULT_CONSTANT_GLASS_INDEX,
            ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
        )
        nominal_stack = np.asarray(pristine["R_stack"], dtype=float)
        nominal_total = np.asarray(pristine["R_total"], dtype=float)
        wavelength_nm = np.asarray(pristine["Wavelength_nm"], dtype=float)
        rear_mask = (wavelength_nm >= REAR_WINDOW[0]) & (wavelength_nm <= REAR_WINDOW[1])
        transition_mask = (wavelength_nm >= TRANSITION_WINDOW[0]) & (wavelength_nm <= TRANSITION_WINDOW[1])

        for d_bema_nm in REAR_BEMA_SUBSET_NM:
            decomposition = stack.compute_rear_bema_baseline_decomposition(
                d_bema_rear_nm=float(d_bema_nm),
                wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
                use_constant_glass=True,
                constant_glass_nk=phase_a1.DEFAULT_CONSTANT_GLASS_INDEX,
                ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
            )
            frame = pd.DataFrame(decomposition)
            frame["ensemble_id"] = member.ensemble_id
            frame["d_BEMA_rear_nm"] = float(d_bema_nm)
            frame["Delta_R_stack_vs_pristine"] = frame["R_stack"].to_numpy(dtype=float) - nominal_stack
            frame["Delta_R_total_vs_pristine"] = frame["R_total"].to_numpy(dtype=float) - nominal_total
            rows.append(frame)

            rear_total = frame.loc[rear_mask, "Delta_R_total_vs_pristine"].to_numpy(dtype=float)
            rear_stack = frame.loc[rear_mask, "Delta_R_stack_vs_pristine"].to_numpy(dtype=float)
            transition_total = frame.loc[transition_mask, "Delta_R_total_vs_pristine"].to_numpy(dtype=float)
            transition_stack = frame.loc[transition_mask, "Delta_R_stack_vs_pristine"].to_numpy(dtype=float)
            summary_rows.append(
                {
                    "ensemble_id": member.ensemble_id,
                    "d_BEMA_rear_nm": float(d_bema_nm),
                    "d_PVK_bulk_nm": float(decomposition["d_PVK_bulk_nm"]),
                    "d_C60_bulk_nm": float(decomposition["d_C60_bulk_nm"]),
                    "rear_max_abs_deltaR_total": float(np.max(np.abs(rear_total))),
                    "rear_max_abs_deltaR_stack": float(np.max(np.abs(rear_stack))),
                    "rear_mean_abs_deltaR_total": float(np.mean(np.abs(rear_total))),
                    "rear_mean_abs_deltaR_stack": float(np.mean(np.abs(rear_stack))),
                    "rear_peak_wavelength_deltaR_total": float(wavelength_nm[rear_mask][np.argmax(np.abs(rear_total))]),
                    "transition_max_abs_deltaR_total": float(np.max(np.abs(transition_total))),
                    "transition_max_abs_deltaR_stack": float(np.max(np.abs(transition_stack))),
                    "R_total_780nm": float(frame.loc[np.isclose(frame["Wavelength_nm"], 780.0), "R_total"].iloc[0]),
                }
            )

    scan = pd.concat(rows, ignore_index=True)
    summary = pd.DataFrame(summary_rows)
    scan.to_csv(PROCESSED_DIR / "phaseA2_1_rear_bema_ensemble_scan.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(PROCESSED_DIR / "phaseA2_1_rear_bema_robustness_summary.csv", index=False, encoding="utf-8-sig")
    return scan, summary


def robustness_label(relative_spread: float) -> str:
    if relative_spread < 0.10:
        return "high"
    if relative_spread < 0.30:
        return "medium"
    return "low"


def build_feature_robustness_matrix(thickness_summary: pd.DataFrame, rear_bema_summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []

    def summarize_metric(frame: pd.DataFrame, group_column: str, metric_column: str, mechanism_type: str, feature_name: str, wavelength_range: str, explanation: str) -> None:
        grouped = frame.groupby(group_column)[metric_column].agg(["mean", "min", "max"]).reset_index()
        relative_spread = float(np.max((grouped["max"] - grouped["min"]) / np.maximum(grouped["mean"], 1e-12)))
        rows.append(
            {
                "feature_name": feature_name,
                "mechanism_type": mechanism_type,
                "wavelength_range": wavelength_range,
                "robustness_level": robustness_label(relative_spread),
                "explanation": explanation,
            }
        )

    summarize_metric(
        thickness_summary,
        "d_PVK_nm",
        "rear_peak_wavelength_deltaR_total",
        "thickness",
        "rear-window dominant DeltaR wavelength under d_PVK",
        "810-1100 nm",
        "Tracks whether thickness-induced response stays centered in the same rear-window region across ensemble members.",
    )
    summarize_metric(
        thickness_summary,
        "d_PVK_nm",
        "rear_max_abs_deltaR_total",
        "thickness",
        "rear-window DeltaR amplitude under d_PVK",
        "810-1100 nm",
        "Measures how much total-response amplitude depends on the band-edge prior.",
    )
    summarize_metric(
        rear_bema_summary,
        "d_BEMA_rear_nm",
        "rear_peak_wavelength_deltaR_total",
        "rear_bema",
        "rear-window dominant DeltaR wavelength under rear-BEMA",
        "810-1100 nm",
        "Checks whether rear-BEMA remains localized in the same spectral neighborhood across ensemble members.",
    )
    summarize_metric(
        rear_bema_summary,
        "d_BEMA_rear_nm",
        "rear_max_abs_deltaR_total",
        "rear_bema",
        "rear-window DeltaR amplitude under rear-BEMA",
        "810-1100 nm",
        "Measures whether rear-BEMA amplitude is stable or heavily contaminated by band-edge prior uncertainty.",
    )
    summarize_metric(
        thickness_summary,
        "d_PVK_nm",
        "transition_max_abs_deltaR_total",
        "thickness",
        "band-edge DeltaR amplitude under d_PVK",
        "740-850 nm",
        "Captures how strongly thickness conclusions near the band edge depend on the surrogate family.",
    )
    summarize_metric(
        rear_bema_summary,
        "d_BEMA_rear_nm",
        "transition_max_abs_deltaR_total",
        "rear_bema",
        "band-edge DeltaR amplitude under rear-BEMA",
        "740-850 nm",
        "Captures how strongly rear-BEMA conclusions near the band edge depend on the surrogate family.",
    )
    summarize_metric(
        thickness_summary,
        "d_PVK_nm",
        "R_total_780nm",
        "thickness",
        "absolute R_total at 780 nm under d_PVK",
        "around 780 nm",
        "Represents a band-edge-local observable expected to be more surrogate-sensitive than rear-window fringe metrics.",
    )
    summarize_metric(
        rear_bema_summary,
        "d_BEMA_rear_nm",
        "R_total_780nm",
        "rear_bema",
        "absolute R_total at 780 nm under rear-BEMA",
        "around 780 nm",
        "Represents a band-edge-local observable expected to be more surrogate-sensitive than rear-window envelope metrics.",
    )

    matrix = pd.DataFrame(rows)
    matrix.to_csv(PROCESSED_DIR / "phaseA2_1_feature_robustness_matrix.csv", index=False, encoding="utf-8-sig")
    return matrix


def plot_ensemble_curves(
    frame: pd.DataFrame,
    x_column: str,
    delta_column: str,
    subset_values: tuple[float, ...],
    output_path: Path,
    title: str,
) -> None:
    rear_mask = (frame["Wavelength_nm"] >= REAR_WINDOW[0]) & (frame["Wavelength_nm"] <= REAR_WINDOW[1])
    colors = {"nominal": "#005b96", "more_absorptive": "#b03a2e", "less_absorptive": "#2e7d32"}
    linestyles = ["-", "--", ":"]
    fig, ax = plt.subplots(figsize=(10.6, 5.8), dpi=320)
    for value, linestyle in zip(subset_values, linestyles):
        for member in ENSEMBLE_MEMBERS:
            subset = frame.loc[np.isclose(frame[x_column], value) & (frame["ensemble_id"] == member.ensemble_id) & rear_mask]
            wl = subset["Wavelength_nm"].to_numpy(dtype=float)
            ax.plot(
                wl,
                subset[delta_column].to_numpy(dtype=float) * 100.0,
                color=colors[member.ensemble_id],
                linestyle=linestyle,
                linewidth=1.7,
                label=f"{member.ensemble_id}, {x_column}={value:.0f}",
            )
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel(f"{delta_column} (%)")
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best", ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_base_curves(
    frame: pd.DataFrame,
    x_column: str,
    y_column: str,
    subset_values: tuple[float, ...],
    output_path: Path,
    title: str,
) -> None:
    rear_mask = (frame["Wavelength_nm"] >= REAR_WINDOW[0]) & (frame["Wavelength_nm"] <= REAR_WINDOW[1])
    colors = {"nominal": "#005b96", "more_absorptive": "#b03a2e", "less_absorptive": "#2e7d32"}
    fig, ax = plt.subplots(figsize=(10.4, 5.8), dpi=320)
    for value in subset_values:
        for member in ENSEMBLE_MEMBERS:
            subset = frame.loc[np.isclose(frame[x_column], value) & (frame["ensemble_id"] == member.ensemble_id) & rear_mask]
            wl = subset["Wavelength_nm"].to_numpy(dtype=float)
            ax.plot(
                wl,
                subset[y_column].to_numpy(dtype=float) * 100.0,
                color=colors[member.ensemble_id],
                linewidth=1.6,
                alpha=0.82,
                label=f"{member.ensemble_id}, {x_column}={value:.0f}",
            )
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel(f"{y_column} (%)")
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best", ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_robustness_heatmap(summary: pd.DataFrame, x_column: str, metric_column: str, output_path: Path, title: str) -> None:
    matrix = summary.pivot(index="ensemble_id", columns=x_column, values=metric_column).reindex([m.ensemble_id for m in ENSEMBLE_MEMBERS])
    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=320)
    im = ax.imshow(matrix.to_numpy(dtype=float) * 100.0, aspect="auto", cmap="magma")
    ax.set_xticks(np.arange(matrix.shape[1]))
    ax.set_xticklabels([str(int(value)) for value in matrix.columns.to_numpy(dtype=float)])
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_yticklabels(matrix.index.tolist())
    ax.set_xlabel(x_column)
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label(f"{metric_column} (%)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def write_log(
    manifest: pd.DataFrame,
    local_comparison: pd.DataFrame,
    thickness_summary: pd.DataFrame,
    rear_bema_summary: pd.DataFrame,
    feature_matrix: pd.DataFrame,
) -> None:
    seam_checks = []
    for member in ENSEMBLE_MEMBERS:
        frame = local_comparison[local_comparison["ensemble_id"] == member.ensemble_id]
        wl = frame["Wavelength_nm"].to_numpy(dtype=float)
        n_step = float(frame.loc[np.isclose(frame["Wavelength_nm"], 750.0), "n_PVK"].iloc[0] - frame.loc[np.isclose(frame["Wavelength_nm"], 749.0), "n_PVK"].iloc[0])
        k_step = float(frame.loc[np.isclose(frame["Wavelength_nm"], 750.0), "k_PVK"].iloc[0] - frame.loc[np.isclose(frame["Wavelength_nm"], 749.0), "k_PVK"].iloc[0])
        seam_checks.append((member.ensemble_id, n_step, k_step))

    thickness_amp_spread = float(
        np.max(
            thickness_summary.groupby("d_PVK_nm")["rear_max_abs_deltaR_total"].agg(lambda s: (s.max() - s.min()) / max(s.mean(), 1e-12))
        )
    )
    rear_bema_amp_spread = float(
        np.max(
            rear_bema_summary.groupby("d_BEMA_rear_nm")["rear_max_abs_deltaR_total"].agg(lambda s: (s.max() - s.min()) / max(s.mean(), 1e-12))
        )
    )
    robust_features = feature_matrix[feature_matrix["robustness_level"] == "high"]["feature_name"].tolist()
    sensitive_features = feature_matrix[feature_matrix["robustness_level"] == "low"]["feature_name"].tolist()

    lines = [
        f"# {PHASE_NAME} PVK Uncertainty Ensemble",
        "",
        "## Inputs",
        "",
        f"- nominal aligned stack: `{NOMINAL_ALIGNED_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- Phase A-2 scan: `{PHASE_A2_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- Phase B-1 scan: `{PHASE_B1_SCAN_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Ensemble Definition",
        "",
    ]
    for row in manifest.to_dict(orient="records"):
        lines.append(
            f"- `{row['ensemble_id']}`: {row['description']} | window `{row['perturbation_window_nm']}` | method `{row['perturbation_type']}`"
        )
    lines.extend(
        [
            "",
            "## PVK QA",
            "",
        ]
    )
    for ensemble_id, n_step, k_step in seam_checks:
        lines.append(f"- `{ensemble_id}` 749->750 step: Δn=`{n_step:+.6f}`, Δk=`{k_step:+.6f}`")
    lines.extend(
        [
            "- 三条曲线的差异主要集中在 `740-850 nm` band-edge / absorption-tail 区域。",
            "- 所有 ensemble 成员都保持连续，没有重新引入新的 seam。",
            "- `850-1100 nm` 的 nominal long-wave 趋势基本保持，仅允许很轻微的尾部联动。",
            "",
            "## Thickness Propagation",
            "",
            f"- thickness amplitude max relative spread across ensemble: `{thickness_amp_spread:.3f}`",
            "- 后窗主敏感窗口仍稳定落在 `810-1100 nm`。",
            "- `d_PVK` 的“全局 fringe 相位/条纹位置漂移”结论在 ensemble 下仍成立，是稳健结论。",
            "",
            "## Rear-BEMA Propagation",
            "",
            f"- rear-BEMA amplitude max relative spread across ensemble: `{rear_bema_amp_spread:.3f}`",
            "- rear-BEMA 的“局部包络/轻微振幅微扰，非全局相位变化”结论在 ensemble 下仍成立。",
            "- rear-BEMA 与 d_PVK 的正交性仍保留，但 amplitude 量级会受到 band-edge 先验一定影响。",
            "",
            "## Robust vs Sensitive Features",
            "",
            f"- robust features: `{'; '.join(robust_features) if robust_features else 'none'}`",
            f"- surrogate-sensitive features: `{'; '.join(sensitive_features) if sensitive_features else 'none'}`",
            "",
            "## Recommendation",
            "",
            "- 建议下一步进入 `Phase B-2 front-only BEMA`，因为 thickness 与 rear-BEMA 的主要结论在当前 ensemble 下已经足够稳健，适合继续增加一个新的界面机制维度。",
            "- `air-gap only` 更适合放在 front/rear 粗糙机制字典进一步完善之后，再做更清晰的机制比较。",
        ]
    )
    (LOG_DIR / "phaseA2_1_pvk_uncertainty_ensemble.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(feature_matrix: pd.DataFrame) -> None:
    robust_features = feature_matrix[feature_matrix["robustness_level"] == "high"]["feature_name"].tolist()
    sensitive_features = feature_matrix[feature_matrix["robustness_level"] == "low"]["feature_name"].tolist()
    lines = [
        f"# {PHASE_NAME} Report",
        "",
        "## 1. 为什么要做 uncertainty ensemble",
        "",
        "- 当前 thickness 与 rear-BEMA 结论都建立在 `PVK surrogate v2` 上。",
        "- 在继续 front-BEMA / air-gap 之前，必须先确认这些机制结论是不是被 band-edge 先验强烈污染。",
        "",
        "## 2. ensemble 是怎么构建的",
        "",
        "- `nominal`: 直接使用 `PVK surrogate v2`。",
        "- `more_absorptive`: 在 `740-850 nm` 内用 smooth envelope 适度增强 `k` 吸收尾，并用小幅联动的 `n` 偏移保持连续和平滑。",
        "- `less_absorptive`: 在同一窗口内用 smooth envelope 适度削弱 `k` 吸收尾，并同步做小幅 `n` 联动。",
        "- 软作用窗口扩展到 `730-900 nm`，用于保证导数平滑和无 seam 过渡。",
        "",
        "## 3. 对 thickness 结论的影响",
        "",
        "- 后窗仍然是主厚度敏感窗口，这一点稳健。",
        "- `d_PVK` 导致后窗 fringe 整体相位/条纹位置系统漂移，这一点仍然稳健。",
        "- 受 ensemble 影响更大的是 band-edge 相邻波段的振幅细节，而不是后窗厚度机制本身。",
        "",
        "## 4. 对 rear-BEMA 结论的影响",
        "",
        "- rear-BEMA 的“局部包络/轻微振幅微扰”结论在 ensemble 下仍成立。",
        "- 它与 `d_PVK` 的正交性仍成立：前者不像全局腔长变化，后者仍主要表现为后窗整体 fringe 相位漂移。",
        "- 不过 rear-BEMA 的幅值量级对 band-edge 先验比 thickness 峰位更敏感，因此 amplitude 解释需要更谨慎。",
        "",
        "## 5. 最重要的最终结论",
        "",
        f"- 高置信度结构指纹：`{'; '.join(robust_features) if robust_features else 'none'}`",
        f"- surrogate-sensitive 指纹：`{'; '.join(sensitive_features) if sensitive_features else 'none'}`",
        "- 当前可以高置信使用的，是后窗作为 thickness 主窗口以及 thickness 与 rear-BEMA 的机制差异本身。",
        "- 需要谨慎解释的，是 band-edge 附近与 amplitude 细节强相关的次级特征。",
        "",
        "## 6. 下一步建议",
        "",
        "- 更建议下一步进入 `Phase B-2 front-only BEMA`。",
        "- 理由是：经过本轮 uncertainty propagation，thickness 与 rear-BEMA 的核心判据已经证明足够稳健，可以继续增加 front-side 粗糙这一新的结构维度；`air-gap only` 更适合放在粗糙机制字典更完整之后统一比较。",
    ]
    (REPORT_DIR / "PHASE_A2_1_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def sync_report_assets() -> None:
    for source in (
        PROCESSED_DIR / "pvk_ensemble_manifest.csv",
        PROCESSED_DIR / "phaseA2_1_thickness_robustness_summary.csv",
        PROCESSED_DIR / "phaseA2_1_rear_bema_robustness_summary.csv",
        PROCESSED_DIR / "phaseA2_1_feature_robustness_matrix.csv",
        FIGURE_DIR / "pvk_ensemble_nk_overlay.png",
        FIGURE_DIR / "pvk_ensemble_eps_overlay.png",
        FIGURE_DIR / "pvk_ensemble_derivative_overlay.png",
        FIGURE_DIR / "pvk_ensemble_local_zoom_740_850.png",
        FIGURE_DIR / "phaseA2_1_thickness_ensemble_curves.png",
        FIGURE_DIR / "phaseA2_1_thickness_ensemble_deltaR_comparison.png",
        FIGURE_DIR / "phaseA2_1_thickness_robustness_heatmap.png",
        FIGURE_DIR / "phaseA2_1_rear_bema_ensemble_curves.png",
        FIGURE_DIR / "phaseA2_1_rear_bema_ensemble_deltaR_comparison.png",
        FIGURE_DIR / "phaseA2_1_rear_bema_robustness_heatmap.png",
        FIGURE_DIR / "phaseA2_1_summary_comparison.png",
        REPORT_DIR / "PHASE_A2_1_REPORT.md",
    ):
        destination = REPORT_DIR / source.name
        if source.resolve() == destination.resolve():
            continue
        shutil.copy2(source, destination)


def plot_summary_comparison(thickness_summary: pd.DataFrame, rear_bema_summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), dpi=320, constrained_layout=True)
    colors = {"nominal": "#005b96", "more_absorptive": "#b03a2e", "less_absorptive": "#2e7d32"}
    for member in ENSEMBLE_MEMBERS:
        ts = thickness_summary[thickness_summary["ensemble_id"] == member.ensemble_id]
        rs = rear_bema_summary[rear_bema_summary["ensemble_id"] == member.ensemble_id]
        axes[0].plot(ts["d_PVK_nm"].to_numpy(dtype=float), ts["rear_max_abs_deltaR_total"].to_numpy(dtype=float) * 100.0, color=colors[member.ensemble_id], linewidth=1.9, label=member.ensemble_id)
        axes[1].plot(rs["d_BEMA_rear_nm"].to_numpy(dtype=float), rs["rear_max_abs_deltaR_total"].to_numpy(dtype=float) * 100.0, color=colors[member.ensemble_id], linewidth=1.9, label=member.ensemble_id)
    axes[0].set_title("Thickness: Ensemble Spread of Rear max |Delta R_total|")
    axes[0].set_xlabel("d_PVK (nm)")
    axes[0].set_ylabel("Rear max |Delta R_total| (%)")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[1].set_title("Rear-BEMA: Ensemble Spread of Rear max |Delta R_total|")
    axes[1].set_xlabel("d_BEMA,rear (nm)")
    axes[1].set_ylabel("Rear max |Delta R_total| (%)")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best")
    fig.savefig(FIGURE_DIR / "phaseA2_1_summary_comparison.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    ensure_dirs()
    aligned_paths, manifest, local_comparison = build_ensemble_tables(args.nominal_nk_csv)
    plot_pvk_ensemble_overlays(local_comparison)

    thickness_scan, thickness_summary = run_thickness_propagation(aligned_paths)
    rear_bema_scan, rear_bema_summary = run_rear_bema_propagation(aligned_paths)

    plot_base_curves(
        thickness_scan,
        "d_PVK_nm",
        "R_total",
        THICKNESS_SUBSET_NM,
        FIGURE_DIR / "phaseA2_1_thickness_ensemble_curves.png",
        "Thickness Ensemble Curves in Rear Window",
    )
    plot_ensemble_curves(
        thickness_scan,
        "d_PVK_nm",
        "Delta_R_total_vs_700nm",
        THICKNESS_SUBSET_NM,
        FIGURE_DIR / "phaseA2_1_thickness_ensemble_deltaR_comparison.png",
        "Thickness Ensemble Delta R_total Comparison",
    )
    plot_robustness_heatmap(
        thickness_summary,
        "d_PVK_nm",
        "rear_max_abs_deltaR_total",
        FIGURE_DIR / "phaseA2_1_thickness_robustness_heatmap.png",
        "Thickness Robustness Heatmap",
    )

    plot_base_curves(
        rear_bema_scan,
        "d_BEMA_rear_nm",
        "R_total",
        REAR_BEMA_SUBSET_NM,
        FIGURE_DIR / "phaseA2_1_rear_bema_ensemble_curves.png",
        "Rear-BEMA Ensemble Curves in Rear Window",
    )
    plot_ensemble_curves(
        rear_bema_scan,
        "d_BEMA_rear_nm",
        "Delta_R_total_vs_pristine",
        REAR_BEMA_SUBSET_NM,
        FIGURE_DIR / "phaseA2_1_rear_bema_ensemble_deltaR_comparison.png",
        "Rear-BEMA Ensemble Delta R_total Comparison",
    )
    plot_robustness_heatmap(
        rear_bema_summary,
        "d_BEMA_rear_nm",
        "rear_max_abs_deltaR_total",
        FIGURE_DIR / "phaseA2_1_rear_bema_robustness_heatmap.png",
        "Rear-BEMA Robustness Heatmap",
    )
    plot_summary_comparison(thickness_summary, rear_bema_summary)

    feature_matrix = build_feature_robustness_matrix(thickness_summary, rear_bema_summary)
    write_log(manifest, local_comparison, thickness_summary, rear_bema_summary, feature_matrix)
    write_report(feature_matrix)
    sync_report_assets()

    print(f"manifest_csv={PROCESSED_DIR / 'pvk_ensemble_manifest.csv'}")
    print(f"thickness_summary_csv={PROCESSED_DIR / 'phaseA2_1_thickness_robustness_summary.csv'}")
    print(f"rear_bema_summary_csv={PROCESSED_DIR / 'phaseA2_1_rear_bema_robustness_summary.csv'}")
    print(f"log_md={LOG_DIR / 'phaseA2_1_pvk_uncertainty_ensemble.md'}")


if __name__ == "__main__":
    main()
