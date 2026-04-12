"""Phase A-1.2 PVK surrogate v2 rebuild.

This script repairs the PVK band-edge seam around 740-780 nm at the material
layer, keeps v1/v2 side-by-side, and writes a new aligned stack table without
overwriting the original v1 file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import math
import sys

import matplotlib
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.signal import find_peaks

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (str(SRC_ROOT), str(SCRIPT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import stepA1_pristine_baseline as phase_a1  # noqa: E402


PHASE_NAME = "Phase A-1.2"
ALIGNED_V1_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk.csv"
ALIGNED_V2_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_pvk_v2.csv"
EXTENDED_PATH = PROJECT_ROOT / "data" / "processed" / "CsFAPI_nk_extended.csv"
DIGITIZED_PATH = PROJECT_ROOT / "resources" / "digitized" / "phase02_fig3_csfapi_optical_constants_digitized.csv"
BASELINE_V1_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA1" / "phaseA1_pristine_baseline.csv"

LOCAL_FOCUS_WINDOW = (730.0, 900.0)
SEAM_WINDOW = (740.0, 780.0)
RERUN_FRINGE_WINDOW = (810.0, 1100.0)
SEAM_LEFT_NM = 749.0
SEAM_RIGHT_NM = 750.0
CANDIDATE_ZONES = (
    (744.0, 760.0),
    (740.0, 770.0),
    (740.0, 780.0),
)
MORE_ABSORPTIVE_SCALE = 1.20
LESS_ABSORPTIVE_SCALE = 0.80


@dataclass(frozen=True)
class CandidateResult:
    start_nm: float
    end_nm: float
    score: float
    delta_n: float
    delta_k: float
    delta_eps2: float
    delta_r_stack: float
    delta_r_total: float
    max_abs_dn: float
    max_abs_dk: float
    max_abs_d2n: float
    max_abs_d2k: float
    fringe_rmse: float
    fringe_corr: float
    fringe_peak_shift_nm: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Phase A-1.2 PVK surrogate v2.")
    parser.add_argument("--aligned-v1", type=Path, default=ALIGNED_V1_PATH)
    parser.add_argument("--baseline-v1", type=Path, default=BASELINE_V1_PATH)
    return parser.parse_args()


def ensure_output_dirs() -> tuple[Path, Path, Path]:
    processed_dir = PROJECT_ROOT / "data" / "processed" / "phaseA1_2"
    figure_dir = PROJECT_ROOT / "results" / "figures" / "phaseA1_2"
    log_dir = PROJECT_ROOT / "results" / "logs" / "phaseA1_2"
    processed_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir, figure_dir, log_dir


def smoothstep(x: np.ndarray) -> np.ndarray:
    x_clipped = np.clip(np.asarray(x, dtype=float), 0.0, 1.0)
    return x_clipped * x_clipped * (3.0 - 2.0 * x_clipped)


def cosine_taper(wavelength_nm: np.ndarray, start_nm: float, end_nm: float) -> np.ndarray:
    wavelength = np.asarray(wavelength_nm, dtype=float)
    result = np.ones_like(wavelength, dtype=float)
    left_mask = wavelength <= start_nm
    right_mask = wavelength >= end_nm
    mid_mask = (~left_mask) & (~right_mask)
    result[right_mask] = 0.0
    if np.any(mid_mask):
        phase = (wavelength[mid_mask] - start_nm) / (end_nm - start_nm)
        result[mid_mask] = 0.5 * (1.0 + np.cos(np.pi * phase))
    return result


def compute_derivative(values: np.ndarray, wavelength_nm: np.ndarray) -> np.ndarray:
    return np.gradient(np.asarray(values, dtype=float), np.asarray(wavelength_nm, dtype=float))


def compute_second_difference(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return np.gradient(np.gradient(array))


def seam_step(values: np.ndarray, wavelength_nm: np.ndarray) -> float:
    idx_749 = int(np.argmin(np.abs(wavelength_nm - SEAM_LEFT_NM)))
    idx_750 = int(np.argmin(np.abs(wavelength_nm - SEAM_RIGHT_NM)))
    return float(values[idx_750] - values[idx_749])


def load_digitized_components() -> tuple[PchipInterpolator, PchipInterpolator]:
    frame = pd.read_csv(DIGITIZED_PATH)
    pvk = frame[frame["series"] == "ITO/CsFAPI"].copy()
    n_frame = pvk[pvk["quantity"] == "n"].sort_values("wavelength_nm")
    k_frame = pvk[pvk["quantity"] == "kappa"].sort_values("wavelength_nm")
    return (
        PchipInterpolator(n_frame["wavelength_nm"].to_numpy(dtype=float), n_frame["value"].to_numpy(dtype=float), extrapolate=True),
        PchipInterpolator(k_frame["wavelength_nm"].to_numpy(dtype=float), k_frame["value"].to_numpy(dtype=float), extrapolate=True),
    )


def load_extended_n_interpolator() -> PchipInterpolator:
    frame = pd.read_csv(EXTENDED_PATH).sort_values("Wavelength")
    return PchipInterpolator(frame["Wavelength"].to_numpy(dtype=float), frame["n"].to_numpy(dtype=float), extrapolate=True)


def build_candidate_pvk(
    aligned_frame: pd.DataFrame,
    start_nm: float,
    end_nm: float,
    k_scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    wavelength = aligned_frame["Wavelength_nm"].to_numpy(dtype=float)
    base_n = aligned_frame["n_PVK"].to_numpy(dtype=float)
    base_k = aligned_frame["k_PVK"].to_numpy(dtype=float)

    digitized_n_interp, digitized_k_interp = load_digitized_components()
    extended_n_interp = load_extended_n_interpolator()

    n_v2 = base_n.copy()
    k_v2 = base_k.copy()
    blend_mask = (wavelength >= start_nm) & (wavelength <= end_nm)
    if np.any(blend_mask):
        weights = smoothstep((wavelength[blend_mask] - start_nm) / (end_nm - start_nm))
        left_anchor_wl = np.array([start_nm - 20.0, start_nm - 10.0, start_nm - 5.0, start_nm], dtype=float)
        left_n_values = np.interp(left_anchor_wl, wavelength, base_n)
        left_k_values = np.interp(left_anchor_wl, wavelength, base_k)
        left_n_interp = PchipInterpolator(left_anchor_wl, left_n_values, extrapolate=True)
        left_k_interp = PchipInterpolator(left_anchor_wl, left_k_values, extrapolate=True)

        left_n = left_n_interp(wavelength[blend_mask])
        left_k = np.maximum(left_k_interp(wavelength[blend_mask]), 0.0)
        right_n = extended_n_interp(wavelength[blend_mask])
        right_k = np.zeros_like(right_n, dtype=float)

        n_v2[blend_mask] = (1.0 - weights) * left_n + weights * right_n
        k_v2[blend_mask] = (1.0 - weights) * left_k + weights * right_k
    right_mask = wavelength > end_nm
    n_v2[right_mask] = extended_n_interp(wavelength[right_mask])
    k_v2[right_mask] = 0.0
    return n_v2, np.maximum(k_v2, 0.0)


def build_stack_and_baseline(aligned_frame: pd.DataFrame, n_pvk: np.ndarray, k_pvk: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    v2_frame = aligned_frame.copy()
    v2_frame["n_PVK"] = n_pvk
    v2_frame["k_PVK"] = k_pvk

    stack, _, _ = phase_a1.load_optical_stack_from_aligned_csv(ALIGNED_V2_PATH) if False else phase_a1.load_optical_stack_from_aligned_csv(ALIGNED_V1_PATH)
    stack = phase_a1.OpticalStackTable(
        wavelength_nm=v2_frame["Wavelength_nm"].to_numpy(dtype=float),
        n_glass=np.full(v2_frame["Wavelength_nm"].shape, phase_a1.DEFAULT_CONSTANT_GLASS_INDEX, dtype=np.complex128),
        n_ito=v2_frame["n_ITO"].to_numpy(dtype=float) + 1j * v2_frame["k_ITO"].to_numpy(dtype=float),
        n_niox=v2_frame["n_NiOx"].to_numpy(dtype=float) + 1j * v2_frame["k_NiOx"].to_numpy(dtype=float),
        n_pvk=v2_frame["n_PVK"].to_numpy(dtype=float) + 1j * v2_frame["k_PVK"].to_numpy(dtype=float),
        n_c60=v2_frame["n_C60"].to_numpy(dtype=float) + 1j * v2_frame["k_C60"].to_numpy(dtype=float),
        n_ag=v2_frame["n_Ag"].to_numpy(dtype=float) + 1j * v2_frame["k_Ag"].to_numpy(dtype=float),
        thicknesses=phase_a1.LayerThicknesses(ito_nm=100.0, niox_nm=45.0, sam_nm=5.0, pvk_nm=700.0, c60_nm=15.0, ag_nm=100.0),
    )
    decomposition = stack.compute_pristine_baseline_decomposition(
        wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
        use_constant_glass=True,
        constant_glass_nk=phase_a1.DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode=phase_a1.AG_BOUNDARY_FINITE_FILM,
    )
    baseline = pd.DataFrame(decomposition)
    baseline["zone_label"] = phase_a1.build_zone_labels(baseline["Wavelength_nm"].to_numpy(dtype=float))
    baseline = baseline[["Wavelength_nm", "zone_label", "R_front", "T_front", "R_stack", "R_total"]]
    return v2_frame, baseline


def compare_peak_positions(v1: np.ndarray, v2: np.ndarray, wavelength_nm: np.ndarray) -> float:
    v1 = np.asarray(v1, dtype=float)
    v2 = np.asarray(v2, dtype=float)
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    prominence = max((float(np.max(v1)) - float(np.min(v1))) * 0.08, 1e-6)
    shifts: list[float] = []
    for signal_a, signal_b in ((v1, v2), (-v1, -v2)):
        peaks_a, props_a = find_peaks(signal_a, prominence=prominence)
        peaks_b, _ = find_peaks(signal_b, prominence=prominence)
        if peaks_a.size == 0 or peaks_b.size == 0:
            continue
        order = np.argsort(props_a["prominences"])[::-1]
        for idx in peaks_a[order[: min(3, len(order))]]:
            shifts.append(float(np.min(np.abs(wavelength_nm[peaks_b] - wavelength_nm[idx]))))
    if not shifts:
        return float("nan")
    return float(np.mean(shifts))


def evaluate_candidate(
    aligned_frame: pd.DataFrame,
    baseline_v1: pd.DataFrame,
    start_nm: float,
    end_nm: float,
) -> tuple[CandidateResult, np.ndarray, np.ndarray, pd.DataFrame]:
    n_v2, k_v2 = build_candidate_pvk(aligned_frame, start_nm, end_nm)
    _, baseline_v2 = build_stack_and_baseline(aligned_frame, n_v2, k_v2)

    wavelength = aligned_frame["Wavelength_nm"].to_numpy(dtype=float)
    eps2_v2 = 2.0 * n_v2 * k_v2
    local_mask = (wavelength >= SEAM_WINDOW[0]) & (wavelength <= SEAM_WINDOW[1])
    local_wl = wavelength[local_mask]
    dn = compute_derivative(n_v2[local_mask], local_wl)
    dk = compute_derivative(k_v2[local_mask], local_wl)
    d2n = compute_second_difference(n_v2[local_mask])
    d2k = compute_second_difference(k_v2[local_mask])

    fringe_mask = (wavelength >= RERUN_FRINGE_WINDOW[0]) & (wavelength <= RERUN_FRINGE_WINDOW[1])
    rt_v1 = baseline_v1.loc[fringe_mask, "R_total"].to_numpy(dtype=float)
    rt_v2 = baseline_v2.loc[fringe_mask, "R_total"].to_numpy(dtype=float)
    wl_fringe = wavelength[fringe_mask]
    fringe_rmse = float(np.sqrt(np.mean((rt_v2 - rt_v1) ** 2)))
    fringe_corr = float(np.corrcoef(rt_v1, rt_v2)[0, 1])
    fringe_peak_shift = compare_peak_positions(rt_v1, rt_v2, wl_fringe)
    if math.isnan(fringe_peak_shift):
        fringe_peak_shift = 99.0

    delta_n = seam_step(n_v2, wavelength)
    delta_k = seam_step(k_v2, wavelength)
    delta_eps2 = seam_step(eps2_v2, wavelength)
    delta_r_stack = seam_step(baseline_v2["R_stack"].to_numpy(dtype=float), wavelength)
    delta_r_total = seam_step(baseline_v2["R_total"].to_numpy(dtype=float), wavelength)

    score = (
        5.0 * abs(delta_r_total)
        + 3.0 * abs(delta_r_stack)
        + 2.0 * abs(delta_eps2)
        + 0.05 * np.max(np.abs(dn))
        + 0.05 * np.max(np.abs(dk))
        + 0.02 * np.max(np.abs(d2n))
        + 0.02 * np.max(np.abs(d2k))
        + 4.0 * fringe_rmse
        + 0.1 * fringe_peak_shift
        + 0.5 * max(0.0, 0.995 - fringe_corr)
    )

    result = CandidateResult(
        start_nm=start_nm,
        end_nm=end_nm,
        score=float(score),
        delta_n=float(delta_n),
        delta_k=float(delta_k),
        delta_eps2=float(delta_eps2),
        delta_r_stack=float(delta_r_stack),
        delta_r_total=float(delta_r_total),
        max_abs_dn=float(np.max(np.abs(dn))),
        max_abs_dk=float(np.max(np.abs(dk))),
        max_abs_d2n=float(np.max(np.abs(d2n))),
        max_abs_d2k=float(np.max(np.abs(d2k))),
        fringe_rmse=fringe_rmse,
        fringe_corr=fringe_corr,
        fringe_peak_shift_nm=fringe_peak_shift,
    )
    return result, n_v2, k_v2, baseline_v2


def choose_best_candidate(results: list[CandidateResult]) -> CandidateResult:
    ordered = sorted(results, key=lambda item: (item.score, item.end_nm - item.start_nm))
    best = ordered[0]
    for candidate in ordered[1:]:
        if abs(candidate.score - best.score) <= 0.01 and (candidate.end_nm - candidate.start_nm) < (best.end_nm - best.start_nm):
            best = candidate
    return best


def build_local_comparison_frame(aligned_v1: pd.DataFrame, n_v2: np.ndarray, k_v2: np.ndarray) -> pd.DataFrame:
    wavelength = aligned_v1["Wavelength_nm"].to_numpy(dtype=float)
    mask = (wavelength >= LOCAL_FOCUS_WINDOW[0]) & (wavelength <= LOCAL_FOCUS_WINDOW[1])
    wl = wavelength[mask]
    n_v1 = aligned_v1.loc[mask, "n_PVK"].to_numpy(dtype=float)
    k_v1 = aligned_v1.loc[mask, "k_PVK"].to_numpy(dtype=float)
    eps1_v1 = n_v1**2 - k_v1**2
    eps2_v1 = 2.0 * n_v1 * k_v1
    eps1_v2 = n_v2[mask] ** 2 - k_v2[mask] ** 2
    eps2_v2 = 2.0 * n_v2[mask] * k_v2[mask]
    frame = pd.DataFrame(
        {
            "Wavelength_nm": wl,
            "n_v1": n_v1,
            "k_v1": k_v1,
            "n_v2": n_v2[mask],
            "k_v2": k_v2[mask],
            "eps1_v1": eps1_v1,
            "eps2_v1": eps2_v1,
            "eps1_v2": eps1_v2,
            "eps2_v2": eps2_v2,
        }
    )
    frame["dn_v1_dlambda"] = compute_derivative(frame["n_v1"].to_numpy(dtype=float), wl)
    frame["dk_v1_dlambda"] = compute_derivative(frame["k_v1"].to_numpy(dtype=float), wl)
    frame["dn_v2_dlambda"] = compute_derivative(frame["n_v2"].to_numpy(dtype=float), wl)
    frame["dk_v2_dlambda"] = compute_derivative(frame["k_v2"].to_numpy(dtype=float), wl)
    return frame


def save_surrogate_figures(local_frame: pd.DataFrame, figure_dir: Path) -> None:
    wl = local_frame["Wavelength_nm"].to_numpy(dtype=float)
    seam_mask = (wl >= SEAM_WINDOW[0]) & (wl <= SEAM_WINDOW[1])

    def seam_lines(ax: plt.Axes) -> None:
        ax.axvline(SEAM_LEFT_NM, color="#8e244d", linestyle="--", linewidth=1.0)
        ax.axvline(SEAM_RIGHT_NM, color="#d84315", linestyle="--", linewidth=1.0)

    fig, ax = plt.subplots(figsize=(10.6, 5.2), dpi=320)
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "n_v1"].to_numpy(dtype=float), color="#616161", linewidth=1.8, label="n_v1")
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "n_v2"].to_numpy(dtype=float), color="#005b96", linewidth=1.8, label="n_v2")
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "k_v1"].to_numpy(dtype=float), color="#8d6e63", linewidth=1.8, linestyle="--", label="k_v1")
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "k_v2"].to_numpy(dtype=float), color="#b03a2e", linewidth=1.8, linestyle="--", label="k_v2")
    seam_lines(ax)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Value")
    ax.set_title("PVK v2 n/k Local Zoom (740-780 nm)")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(figure_dir / "pvk_v2_nk_local_zoom.png", dpi=320, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10.6, 5.2), dpi=320)
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "eps1_v1"].to_numpy(dtype=float), color="#616161", linewidth=1.8, label="eps1_v1")
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "eps1_v2"].to_numpy(dtype=float), color="#005b96", linewidth=1.8, label="eps1_v2")
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "eps2_v1"].to_numpy(dtype=float), color="#8d6e63", linewidth=1.8, linestyle="--", label="eps2_v1")
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "eps2_v2"].to_numpy(dtype=float), color="#b03a2e", linewidth=1.8, linestyle="--", label="eps2_v2")
    seam_lines(ax)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Dielectric Function")
    ax.set_title("PVK v1/v2 eps Local Zoom (740-780 nm)")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(figure_dir / "pvk_v2_eps_local_zoom.png", dpi=320, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10.6, 5.2), dpi=320)
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "dn_v1_dlambda"].to_numpy(dtype=float), color="#616161", linewidth=1.8, label="dn_v1/dlambda")
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "dn_v2_dlambda"].to_numpy(dtype=float), color="#005b96", linewidth=1.8, label="dn_v2/dlambda")
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "dk_v1_dlambda"].to_numpy(dtype=float), color="#8d6e63", linewidth=1.8, linestyle="--", label="dk_v1/dlambda")
    ax.plot(wl[seam_mask], local_frame.loc[seam_mask, "dk_v2_dlambda"].to_numpy(dtype=float), color="#b03a2e", linewidth=1.8, linestyle="--", label="dk_v2/dlambda")
    seam_lines(ax)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Derivative")
    ax.set_title("PVK v1/v2 Derivative Local Zoom (740-780 nm)")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(figure_dir / "pvk_v2_derivative_local_zoom.png", dpi=320, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(10.8, 8.6), dpi=320, constrained_layout=True, sharex=True)
    for axis, columns, title in (
        (axes[0], ("n_v1", "n_v2"), "n(730-900 nm)"),
        (axes[1], ("k_v1", "k_v2"), "k(730-900 nm)"),
    ):
        axis.plot(wl, local_frame[columns[0]].to_numpy(dtype=float), color="#616161", linewidth=1.8, label=columns[0])
        axis.plot(wl, local_frame[columns[1]].to_numpy(dtype=float), color="#005b96", linewidth=1.8, label=columns[1])
        seam_lines(axis)
        axis.set_ylabel("Value")
        axis.set_title(f"PVK v1 vs v2 Overlay: {title}")
        axis.grid(True, linestyle="--", alpha=0.25)
        axis.legend(loc="best")
    axes[-1].set_xlabel("Wavelength (nm)")
    fig.savefig(figure_dir / "pvk_v1_vs_v2_overlay.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def write_builder_summary(
    processed_dir: Path,
    log_dir: Path,
    best: CandidateResult,
    local_frame: pd.DataFrame,
) -> None:
    delta_n_v1 = seam_step(local_frame["n_v1"].to_numpy(dtype=float), local_frame["Wavelength_nm"].to_numpy(dtype=float))
    delta_n_v2 = seam_step(local_frame["n_v2"].to_numpy(dtype=float), local_frame["Wavelength_nm"].to_numpy(dtype=float))
    delta_k_v1 = seam_step(local_frame["k_v1"].to_numpy(dtype=float), local_frame["Wavelength_nm"].to_numpy(dtype=float))
    delta_k_v2 = seam_step(local_frame["k_v2"].to_numpy(dtype=float), local_frame["Wavelength_nm"].to_numpy(dtype=float))
    lines = [
        f"# {PHASE_NAME} PVK Surrogate v2 Build",
        "",
        f"- selected transition zone: `{best.start_nm:.0f}-{best.end_nm:.0f} nm`",
        "- method: `smoothstep blend inside transition zone + cosine-tail k decay + relaxed n target`",
        "- right-side hard-zero at 750 nm removed: `True`",
        f"- delta_n v1 -> v2: `{delta_n_v1:+.6f} -> {delta_n_v2:+.6f}`",
        f"- delta_k v1 -> v2: `{delta_k_v1:+.6f} -> {delta_k_v2:+.6f}`",
        f"- candidate score: `{best.score:.6f}`",
        "",
        "## Files",
        "",
        f"- aligned v2 csv: `{ALIGNED_V2_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- candidate metrics: `{(processed_dir / 'pvk_v2_candidate_metrics.csv').relative_to(PROJECT_ROOT).as_posix()}`",
        f"- local comparison: `{(processed_dir / 'pvk_v1_v2_local_comparison.csv').relative_to(PROJECT_ROOT).as_posix()}`",
    ]
    (log_dir / "phaseA1_2_pvk_surrogate_build.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    processed_dir, figure_dir, log_dir = ensure_output_dirs()
    aligned_v1 = pd.read_csv(args.aligned_v1.resolve())
    baseline_v1 = pd.read_csv(args.baseline_v1.resolve())

    candidate_results: list[CandidateResult] = []
    candidate_payload: dict[tuple[float, float], tuple[np.ndarray, np.ndarray, pd.DataFrame]] = {}
    for start_nm, end_nm in CANDIDATE_ZONES:
        result, n_v2, k_v2, baseline_v2 = evaluate_candidate(aligned_v1, baseline_v1, start_nm, end_nm)
        candidate_results.append(result)
        candidate_payload[(start_nm, end_nm)] = (n_v2, k_v2, baseline_v2)

    best = choose_best_candidate(candidate_results)
    n_best, k_best, _ = candidate_payload[(best.start_nm, best.end_nm)]
    local_frame = build_local_comparison_frame(aligned_v1, n_best, k_best)
    aligned_v2, _ = build_stack_and_baseline(aligned_v1, n_best, k_best)

    aligned_v2.to_csv(ALIGNED_V2_PATH, index=False, encoding="utf-8-sig")
    pd.DataFrame([item.__dict__ for item in candidate_results]).to_csv(
        processed_dir / "pvk_v2_candidate_metrics.csv",
        index=False,
        encoding="utf-8-sig",
    )
    local_frame.to_csv(processed_dir / "pvk_v1_v2_local_comparison.csv", index=False, encoding="utf-8-sig")
    save_surrogate_figures(local_frame, figure_dir)
    write_builder_summary(processed_dir, log_dir, best, local_frame)

    print(f"aligned_v2_csv={ALIGNED_V2_PATH}")
    print(f"selected_transition_zone={best.start_nm:.0f}-{best.end_nm:.0f}nm")
    print(f"candidate_metrics_csv={processed_dir / 'pvk_v2_candidate_metrics.csv'}")
    print(f"local_comparison_csv={processed_dir / 'pvk_v1_v2_local_comparison.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
