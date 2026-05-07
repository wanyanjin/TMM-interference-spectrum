"""Phase D-1 realistic-background air-gap discrimination database.

This script upgrades the Phase A-C single-mechanism dictionary into a realistic
forward database built on top of local PVK thickness variation plus front/rear
roughness background. The observable is strictly the full-device absolute
reflectance R_total under a thick-glass incoherent cascade.

The PVK optical constants continue to trace back to the stitched surrogate v2
workflow anchored by [LIT-0001] inside the measured band.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import math
import shutil
import sys

import matplotlib
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (str(PROJECT_ROOT / "src"), str(SCRIPT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import stepA1_pristine_baseline as phase_a1  # noqa: E402
from core.full_stack_microcavity import (  # noqa: E402
    AG_BOUNDARY_FINITE_FILM,
    DEFAULT_CONSTANT_GLASS_INDEX,
)


PHASE_NAME = "Phase D-1"
DEFAULT_NK_CSV_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_pvk_v2.csv"
PHASE_A2_REPORT_PATH = PROJECT_ROOT / "results" / "report" / "phaseA2_pvk_thickness_scan" / "PHASE_A2_REPORT.md"
PHASE_A2_1_REPORT_PATH = (
    PROJECT_ROOT / "results" / "report" / "phaseA2_1_pvk_uncertainty_ensemble" / "PHASE_A2_1_REPORT.md"
)
PHASE_B1_REPORT_PATH = PROJECT_ROOT / "results" / "report" / "phaseB1_rear_bema_sandbox" / "PHASE_B1_REPORT.md"
PHASE_B2_REPORT_PATH = PROJECT_ROOT / "results" / "report" / "phaseB2_front_bema_sandbox" / "PHASE_B2_REPORT.md"
PHASE_C1A_REPORT_PATH = PROJECT_ROOT / "results" / "report" / "phaseC1a_rear_air_gap_sandbox" / "PHASE_C1A_REPORT.md"
PHASE_C1B_REPORT_PATH = PROJECT_ROOT / "results" / "report" / "phaseC1b_front_air_gap_sandbox" / "PHASE_C1B_REPORT.md"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phaseD1"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phaseD1"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phaseD1"
REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phaseD1_airgap_discrimination_database"

WINDOW_FRONT = (500.0, 650.0)
WINDOW_TRANSITION = (650.0, 810.0)
WINDOW_REAR = (810.0, 1055.0)
SHIFT_SEARCH_NM = np.arange(-30.0, 31.0, 1.0, dtype=float)

REALISTIC_BASELINE = {
    "d_PVK_nm": 700.0,
    "d_BEMA_front_nm": 10.0,
    "d_BEMA_rear_nm": 20.0,
    "d_gap_front_nm": 0.0,
    "d_gap_rear_nm": 0.0,
}

THICKNESS_GRID_NM = np.arange(675.0, 726.0, 1.0, dtype=float)
FRONT_ROUGHNESS_VALUES_NM = (5.0, 10.0, 15.0)
REAR_ROUGHNESS_VALUES_NM = (10.0, 20.0, 30.0)
GAP_VALUES_NM = (0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0)

ANCHOR_SPECS = (
    ("anchor_01_nominal", 700.0, 10.0, 20.0),
    ("anchor_02_pvk690", 690.0, 10.0, 20.0),
    ("anchor_03_pvk710", 710.0, 10.0, 20.0),
    ("anchor_04_front5", 700.0, 5.0, 20.0),
    ("anchor_05_front15", 700.0, 15.0, 20.0),
    ("anchor_06_rear10", 700.0, 10.0, 10.0),
    ("anchor_07_rear30", 700.0, 10.0, 30.0),
)

SELECTED_THICKNESS_VALUES_NM = (675.0, 690.0, 700.0, 710.0, 725.0)
SELECTED_FRONT_ROUGHNESS_VALUES_NM = FRONT_ROUGHNESS_VALUES_NM
SELECTED_REAR_ROUGHNESS_VALUES_NM = REAR_ROUGHNESS_VALUES_NM
SELECTED_GAP_VALUES_NM = GAP_VALUES_NM
PLOTTING_GAP_ANCHOR_ID = "anchor_01_nominal"

FAMILY_COLORS = {
    "background_anchor": "#9e9e9e",
    "thickness_nuisance": "#1565c0",
    "front_roughness_nuisance": "#ef6c00",
    "rear_roughness_nuisance": "#00897b",
    "front_gap_on_background": "#6a1b9a",
    "rear_gap_on_background": "#c62828",
}
FAMILY_LABELS = {
    "background_anchor": "Background anchor",
    "thickness_nuisance": "Thickness nuisance",
    "front_roughness_nuisance": "Front roughness",
    "rear_roughness_nuisance": "Rear roughness",
    "front_gap_on_background": "Front gap on background",
    "rear_gap_on_background": "Rear gap on background",
}
FAMILY_COMMENTS = {
    "background_anchor": "Reference roughness anchor for gap overlays and nuisance comparisons.",
    "thickness_nuisance": "Rear-window fringe shift remains the dominant signature of local PVK thickness variation.",
    "front_roughness_nuisance": "Front roughness primarily reshapes front and transition-window envelope/background.",
    "rear_roughness_nuisance": "Rear roughness acts more like rear-window envelope/amplitude perturbation than rigid shift.",
    "front_gap_on_background": "Front-gap keeps a front-to-transition dominant signature with secondary rear coupling.",
    "rear_gap_on_background": "Rear-gap keeps a transition-to-rear nonlinear reconstruction signature on roughness background.",
}


@dataclass(frozen=True)
class OutputPaths:
    case_manifest_csv: Path
    rtotal_database_csv: Path
    feature_database_csv: Path
    discrimination_summary_csv: Path
    thickness_heatmap_png: Path
    thickness_selected_curves_png: Path
    front_roughness_curves_png: Path
    rear_roughness_curves_png: Path
    roughness_overview_png: Path
    front_gap_curves_png: Path
    rear_gap_curves_png: Path
    front_gap_heatmap_png: Path
    rear_gap_heatmap_png: Path
    scatter_front_vs_rear_png: Path
    scatter_shift_vs_residual_png: Path
    family_boxplots_png: Path
    atlas_png: Path
    log_md: Path
    report_md: Path
    report_readme: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Phase D-1 realistic-background air-gap discrimination database.")
    parser.add_argument("--nk-csv", type=Path, default=DEFAULT_NK_CSV_PATH)
    return parser.parse_args()


def ensure_output_dirs() -> OutputPaths:
    for path in (PROCESSED_DIR, FIGURE_DIR, LOG_DIR, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    return OutputPaths(
        case_manifest_csv=PROCESSED_DIR / "phaseD1_case_manifest.csv",
        rtotal_database_csv=PROCESSED_DIR / "phaseD1_rtotal_database.csv",
        feature_database_csv=PROCESSED_DIR / "phaseD1_feature_database.csv",
        discrimination_summary_csv=PROCESSED_DIR / "phaseD1_discrimination_summary.csv",
        thickness_heatmap_png=FIGURE_DIR / "phaseD1_thickness_local_deltaRtotal_heatmap.png",
        thickness_selected_curves_png=FIGURE_DIR / "phaseD1_thickness_local_selected_curves.png",
        front_roughness_curves_png=FIGURE_DIR / "phaseD1_front_roughness_selected_curves.png",
        rear_roughness_curves_png=FIGURE_DIR / "phaseD1_rear_roughness_selected_curves.png",
        roughness_overview_png=FIGURE_DIR / "phaseD1_roughness_background_overview.png",
        front_gap_curves_png=FIGURE_DIR / "phaseD1_front_gap_on_background_selected_curves.png",
        rear_gap_curves_png=FIGURE_DIR / "phaseD1_rear_gap_on_background_selected_curves.png",
        front_gap_heatmap_png=FIGURE_DIR / "phaseD1_front_gap_on_background_heatmap.png",
        rear_gap_heatmap_png=FIGURE_DIR / "phaseD1_rear_gap_on_background_heatmap.png",
        scatter_front_vs_rear_png=FIGURE_DIR / "phaseD1_feature_scatter_front_vs_rear.png",
        scatter_shift_vs_residual_png=FIGURE_DIR / "phaseD1_feature_scatter_shift_vs_residual.png",
        family_boxplots_png=FIGURE_DIR / "phaseD1_family_feature_boxplots.png",
        atlas_png=FIGURE_DIR / "phaseD1_discrimination_atlas.png",
        log_md=LOG_DIR / "phaseD1_airgap_discrimination_database.md",
        report_md=REPORT_DIR / "PHASE_D1_REPORT.md",
        report_readme=REPORT_DIR / "README.md",
    )


def load_stack(nk_csv_path: Path):
    stack, _, _ = phase_a1.load_optical_stack_from_aligned_csv(nk_csv_path)
    return stack


def normalize_value(value: float) -> float:
    return float(np.round(float(value), 6))


def case_key(
    d_pvk_nm: float,
    d_bema_front_nm: float,
    d_bema_rear_nm: float,
    d_gap_front_nm: float,
    d_gap_rear_nm: float,
) -> tuple[float, float, float, float, float]:
    return (
        normalize_value(d_pvk_nm),
        normalize_value(d_bema_front_nm),
        normalize_value(d_bema_rear_nm),
        normalize_value(d_gap_front_nm),
        normalize_value(d_gap_rear_nm),
    )


def rms(values: np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    return float(np.sqrt(np.mean(np.square(array))))


def window_mask(wavelength_nm: np.ndarray, window: tuple[float, float]) -> np.ndarray:
    return (wavelength_nm >= window[0]) & (wavelength_nm <= window[1])


def window_mean(values: np.ndarray, mask: np.ndarray) -> float:
    return float(np.mean(values[mask]))


def window_rms(values: np.ndarray, mask: np.ndarray) -> float:
    return rms(values[mask])


def dominant_extrema(signal: np.ndarray, wavelength_nm: np.ndarray) -> tuple[float, float]:
    prominence = max((float(np.max(signal)) - float(np.min(signal))) * 0.08, 1e-6)
    peaks, peak_props = find_peaks(signal, prominence=prominence)
    valleys, valley_props = find_peaks(-signal, prominence=prominence)
    peak_idx = peaks[int(np.argmax(peak_props["prominences"]))] if peaks.size else int(np.argmax(signal))
    valley_idx = valleys[int(np.argmax(valley_props["prominences"]))] if valleys.size else int(np.argmin(signal))
    return float(wavelength_nm[peak_idx]), float(wavelength_nm[valley_idx])


def rear_shift_metrics(
    wavelength_nm: np.ndarray,
    case_signal: np.ndarray,
    reference_signal: np.ndarray,
) -> tuple[float, float, float, float]:
    rear_mask = window_mask(wavelength_nm, WINDOW_REAR)
    rear_wavelength_nm = wavelength_nm[rear_mask]
    case_rear = np.asarray(case_signal[rear_mask], dtype=float)
    reference_rear = np.asarray(reference_signal[rear_mask], dtype=float)
    unaligned = rms(case_rear - reference_rear)
    best_shift_nm = 0.0
    best_residual = unaligned

    for shift_nm in SHIFT_SEARCH_NM:
        shifted_query_nm = rear_wavelength_nm - shift_nm
        valid_mask = (shifted_query_nm >= float(rear_wavelength_nm.min())) & (
            shifted_query_nm <= float(rear_wavelength_nm.max())
        )
        if int(np.count_nonzero(valid_mask)) < 5:
            continue
        shifted_case = np.interp(
            shifted_query_nm[valid_mask],
            rear_wavelength_nm,
            case_rear,
        )
        shifted_reference = reference_rear[valid_mask]
        candidate_residual = rms(shifted_case - shifted_reference)
        if candidate_residual < best_residual:
            best_residual = candidate_residual
            best_shift_nm = float(shift_nm)

    if unaligned <= 1e-12:
        explained_fraction = 1.0
    else:
        explained_fraction = float(np.clip(1.0 - best_residual / unaligned, 0.0, 1.0))
    return best_shift_nm, best_residual, unaligned, explained_fraction


def style_axis(axis: plt.Axes) -> None:
    axis.grid(True, linestyle="--", alpha=0.25)
    axis.set_facecolor("white")


def build_cases() -> tuple[pd.DataFrame, list[dict[str, object]]]:
    physical_registry: dict[tuple[float, float, float, float, float], dict[str, object]] = {}
    logical_rows: list[dict[str, object]] = []
    case_counter = 0

    def register_physical_case(
        *,
        family: str,
        anchor_id: str,
        d_pvk_nm: float,
        d_bema_front_nm: float,
        d_bema_rear_nm: float,
        d_gap_front_nm: float,
        d_gap_rear_nm: float,
        comment: str,
    ) -> str:
        nonlocal case_counter
        key = case_key(d_pvk_nm, d_bema_front_nm, d_bema_rear_nm, d_gap_front_nm, d_gap_rear_nm)
        existing = physical_registry.get(key)
        if existing is not None:
            existing["family_aliases"].add(family)
            if anchor_id:
                existing["anchor_aliases"].add(anchor_id)
            if comment:
                existing["comments"].add(comment)
            return str(existing["case_id"])

        case_counter += 1
        case_id = f"D1_{case_counter:04d}"
        physical_registry[key] = {
            "case_id": case_id,
            "family": family,
            "anchor_id": anchor_id,
            "d_PVK_nm": float(d_pvk_nm),
            "d_BEMA_front_nm": float(d_bema_front_nm),
            "d_BEMA_rear_nm": float(d_bema_rear_nm),
            "d_gap_front_nm": float(d_gap_front_nm),
            "d_gap_rear_nm": float(d_gap_rear_nm),
            "comments": {comment} if comment else set(),
            "family_aliases": {family},
            "anchor_aliases": {anchor_id} if anchor_id else set(),
        }
        return case_id

    anchor_case_ids: dict[str, str] = {}
    for anchor_id, d_pvk_nm, d_front_nm, d_rear_nm in ANCHOR_SPECS:
        case_id = register_physical_case(
            family="background_anchor",
            anchor_id=anchor_id,
            d_pvk_nm=d_pvk_nm,
            d_bema_front_nm=d_front_nm,
            d_bema_rear_nm=d_rear_nm,
            d_gap_front_nm=0.0,
            d_gap_rear_nm=0.0,
            comment="Realistic roughness anchor background.",
        )
        anchor_case_ids[anchor_id] = case_id
        logical_rows.append(
            {
                "case_id": case_id,
                "family": "background_anchor",
                "anchor_id": anchor_id,
                "reference_case_id": case_id,
                "d_PVK_nm": float(d_pvk_nm),
                "d_BEMA_front_nm": float(d_front_nm),
                "d_BEMA_rear_nm": float(d_rear_nm),
                "d_gap_front_nm": 0.0,
                "d_gap_rear_nm": 0.0,
                "comment": "Anchor background self-reference.",
            }
        )

    realistic_reference_case_id = anchor_case_ids["anchor_01_nominal"]

    for d_pvk_nm in THICKNESS_GRID_NM:
        case_id = register_physical_case(
            family="thickness_nuisance",
            anchor_id="anchor_01_nominal",
            d_pvk_nm=float(d_pvk_nm),
            d_bema_front_nm=10.0,
            d_bema_rear_nm=20.0,
            d_gap_front_nm=0.0,
            d_gap_rear_nm=0.0,
            comment="Local PVK thickness nuisance under realistic roughness baseline.",
        )
        logical_rows.append(
            {
                "case_id": case_id,
                "family": "thickness_nuisance",
                "anchor_id": "anchor_01_nominal",
                "reference_case_id": realistic_reference_case_id,
                "d_PVK_nm": float(d_pvk_nm),
                "d_BEMA_front_nm": 10.0,
                "d_BEMA_rear_nm": 20.0,
                "d_gap_front_nm": 0.0,
                "d_gap_rear_nm": 0.0,
                "comment": "Thickness nuisance against realistic baseline 700/10/20.",
            }
        )

    for d_bema_front_nm in FRONT_ROUGHNESS_VALUES_NM:
        case_id = register_physical_case(
            family="front_roughness_nuisance",
            anchor_id="anchor_01_nominal",
            d_pvk_nm=700.0,
            d_bema_front_nm=float(d_bema_front_nm),
            d_bema_rear_nm=20.0,
            d_gap_front_nm=0.0,
            d_gap_rear_nm=0.0,
            comment="Front roughness nuisance with fixed rear background.",
        )
        logical_rows.append(
            {
                "case_id": case_id,
                "family": "front_roughness_nuisance",
                "anchor_id": "anchor_01_nominal",
                "reference_case_id": realistic_reference_case_id,
                "d_PVK_nm": 700.0,
                "d_BEMA_front_nm": float(d_bema_front_nm),
                "d_BEMA_rear_nm": 20.0,
                "d_gap_front_nm": 0.0,
                "d_gap_rear_nm": 0.0,
                "comment": "Front roughness nuisance against realistic baseline 700/10/20.",
            }
        )

    for d_bema_rear_nm in REAR_ROUGHNESS_VALUES_NM:
        case_id = register_physical_case(
            family="rear_roughness_nuisance",
            anchor_id="anchor_01_nominal",
            d_pvk_nm=700.0,
            d_bema_front_nm=10.0,
            d_bema_rear_nm=float(d_bema_rear_nm),
            d_gap_front_nm=0.0,
            d_gap_rear_nm=0.0,
            comment="Rear roughness nuisance with fixed front background.",
        )
        logical_rows.append(
            {
                "case_id": case_id,
                "family": "rear_roughness_nuisance",
                "anchor_id": "anchor_01_nominal",
                "reference_case_id": realistic_reference_case_id,
                "d_PVK_nm": 700.0,
                "d_BEMA_front_nm": 10.0,
                "d_BEMA_rear_nm": float(d_bema_rear_nm),
                "d_gap_front_nm": 0.0,
                "d_gap_rear_nm": 0.0,
                "comment": "Rear roughness nuisance against realistic baseline 700/10/20.",
            }
        )

    for anchor_id, d_pvk_nm, d_front_nm, d_rear_nm in ANCHOR_SPECS:
        reference_case_id = anchor_case_ids[anchor_id]
        for d_gap_front_nm in GAP_VALUES_NM:
            case_id = register_physical_case(
                family="front_gap_on_background",
                anchor_id=anchor_id,
                d_pvk_nm=d_pvk_nm,
                d_bema_front_nm=d_front_nm,
                d_bema_rear_nm=d_rear_nm,
                d_gap_front_nm=float(d_gap_front_nm),
                d_gap_rear_nm=0.0,
                comment="Front-gap overlay on roughness background anchor.",
            )
            logical_rows.append(
                {
                    "case_id": case_id,
                    "family": "front_gap_on_background",
                    "anchor_id": anchor_id,
                    "reference_case_id": reference_case_id,
                    "d_PVK_nm": float(d_pvk_nm),
                    "d_BEMA_front_nm": float(d_front_nm),
                    "d_BEMA_rear_nm": float(d_rear_nm),
                    "d_gap_front_nm": float(d_gap_front_nm),
                    "d_gap_rear_nm": 0.0,
                    "comment": f"Front-gap overlay on {anchor_id}.",
                }
            )

        for d_gap_rear_nm in GAP_VALUES_NM:
            case_id = register_physical_case(
                family="rear_gap_on_background",
                anchor_id=anchor_id,
                d_pvk_nm=d_pvk_nm,
                d_bema_front_nm=d_front_nm,
                d_bema_rear_nm=d_rear_nm,
                d_gap_front_nm=0.0,
                d_gap_rear_nm=float(d_gap_rear_nm),
                comment="Rear-gap overlay on roughness background anchor.",
            )
            logical_rows.append(
                {
                    "case_id": case_id,
                    "family": "rear_gap_on_background",
                    "anchor_id": anchor_id,
                    "reference_case_id": reference_case_id,
                    "d_PVK_nm": float(d_pvk_nm),
                    "d_BEMA_front_nm": float(d_front_nm),
                    "d_BEMA_rear_nm": float(d_rear_nm),
                    "d_gap_front_nm": 0.0,
                    "d_gap_rear_nm": float(d_gap_rear_nm),
                    "comment": f"Rear-gap overlay on {anchor_id}.",
                }
            )

    logical_frame = pd.DataFrame(logical_rows)
    logical_reference_map = (
        logical_frame.groupby("case_id")["reference_case_id"].agg(lambda values: sorted(set(str(v) for v in values))[0]).to_dict()
    )

    manifest_rows: list[dict[str, object]] = []
    for case in sorted(physical_registry.values(), key=lambda item: str(item["case_id"])):
        aliases = ",".join(sorted(str(value) for value in case["family_aliases"]))
        anchor_aliases = ",".join(sorted(str(value) for value in case["anchor_aliases"] if value))
        comments = "; ".join(sorted(str(value) for value in case["comments"]))
        comment = comments
        if aliases and aliases != str(case["family"]):
            comment = f"{comment} Aliases={aliases}.".strip()
        if anchor_aliases and anchor_aliases != str(case["anchor_id"]):
            comment = f"{comment} AnchorAliases={anchor_aliases}.".strip()
        manifest_rows.append(
            {
                "case_id": case["case_id"],
                "family": case["family"],
                "anchor_id": case["anchor_id"],
                "d_PVK_nm": case["d_PVK_nm"],
                "d_BEMA_front_nm": case["d_BEMA_front_nm"],
                "d_BEMA_rear_nm": case["d_BEMA_rear_nm"],
                "d_gap_front_nm": case["d_gap_front_nm"],
                "d_gap_rear_nm": case["d_gap_rear_nm"],
                "reference_case_id": logical_reference_map.get(str(case["case_id"]), str(case["case_id"])),
                "comment": comment.strip(),
            }
        )

    manifest_frame = pd.DataFrame(manifest_rows).sort_values("case_id").reset_index(drop=True)
    logical_rows.sort(key=lambda row: (str(row["family"]), str(row["anchor_id"]), str(row["case_id"])))
    return manifest_frame, logical_rows


def compute_physical_case_spectra(stack, manifest_frame: pd.DataFrame) -> dict[str, dict[str, np.ndarray | float]]:
    spectra_cache: dict[str, dict[str, np.ndarray | float]] = {}
    for row in manifest_frame.itertuples(index=False):
        decomposition = stack.compute_realistic_background_baseline_decomposition(
            d_pvk_nm=float(row.d_PVK_nm),
            d_bema_front_nm=float(row.d_BEMA_front_nm),
            d_bema_rear_nm=float(row.d_BEMA_rear_nm),
            d_gap_front_nm=float(row.d_gap_front_nm),
            d_gap_rear_nm=float(row.d_gap_rear_nm),
            wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
            use_constant_glass=True,
            constant_glass_nk=DEFAULT_CONSTANT_GLASS_INDEX,
            ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
        )
        spectra_cache[str(row.case_id)] = decomposition
    return spectra_cache


def build_databases(
    logical_rows: list[dict[str, object]],
    spectra_cache: dict[str, dict[str, np.ndarray | float]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    spectrum_rows: list[pd.DataFrame] = []
    feature_rows: list[dict[str, object]] = []

    for logical in logical_rows:
        case_id = str(logical["case_id"])
        reference_case_id = str(logical["reference_case_id"])
        case_decomposition = spectra_cache[case_id]
        reference_decomposition = spectra_cache[reference_case_id]
        wavelength_nm = np.asarray(case_decomposition["Wavelength_nm"], dtype=float)
        case_r_total = np.asarray(case_decomposition["R_total"], dtype=float)
        reference_r_total = np.asarray(reference_decomposition["R_total"], dtype=float)
        delta_r_total = case_r_total - reference_r_total

        spectrum_rows.append(
            pd.DataFrame(
                {
                    "case_id": case_id,
                    "family": str(logical["family"]),
                    "anchor_id": str(logical["anchor_id"]),
                    "reference_case_id": reference_case_id,
                    "d_PVK_nm": float(logical["d_PVK_nm"]),
                    "d_BEMA_front_nm": float(logical["d_BEMA_front_nm"]),
                    "d_BEMA_rear_nm": float(logical["d_BEMA_rear_nm"]),
                    "d_gap_front_nm": float(logical["d_gap_front_nm"]),
                    "d_gap_rear_nm": float(logical["d_gap_rear_nm"]),
                    "Wavelength_nm": wavelength_nm,
                    "R_total": case_r_total,
                    "Delta_R_total_vs_reference": delta_r_total,
                }
            )
        )

        front_mask = window_mask(wavelength_nm, WINDOW_FRONT)
        transition_mask = window_mask(wavelength_nm, WINDOW_TRANSITION)
        rear_mask = window_mask(wavelength_nm, WINDOW_REAR)
        rear_best_shift_nm, rear_shift_aligned_rms_residual, rear_unaligned_rms_residual, rear_shift_explained_fraction = (
            rear_shift_metrics(
                wavelength_nm=wavelength_nm,
                case_signal=case_r_total,
                reference_signal=reference_r_total,
            )
        )
        rear_signal = case_r_total[rear_mask]
        rear_wavelength_nm = wavelength_nm[rear_mask]
        rear_peak_nm, rear_valley_nm = dominant_extrema(rear_signal, rear_wavelength_nm)
        front_rms = window_rms(delta_r_total, front_mask)
        transition_rms = window_rms(delta_r_total, transition_mask)
        rear_rms = window_rms(delta_r_total, rear_mask)
        feature_rows.append(
            {
                "case_id": case_id,
                "family": str(logical["family"]),
                "anchor_id": str(logical["anchor_id"]),
                "reference_case_id": reference_case_id,
                "d_PVK_nm": float(logical["d_PVK_nm"]),
                "d_BEMA_front_nm": float(logical["d_BEMA_front_nm"]),
                "d_BEMA_rear_nm": float(logical["d_BEMA_rear_nm"]),
                "d_gap_front_nm": float(logical["d_gap_front_nm"]),
                "d_gap_rear_nm": float(logical["d_gap_rear_nm"]),
                "front_mean_deltaR_500_650": window_mean(delta_r_total, front_mask),
                "front_rms_deltaR_500_650": front_rms,
                "transition_mean_deltaR_650_810": window_mean(delta_r_total, transition_mask),
                "transition_rms_deltaR_650_810": transition_rms,
                "rear_mean_deltaR_810_1055": window_mean(delta_r_total, rear_mask),
                "rear_rms_deltaR_810_1055": rear_rms,
                "front_to_rear_rms_ratio": front_rms / max(rear_rms, 1e-12),
                "transition_to_rear_rms_ratio": transition_rms / max(rear_rms, 1e-12),
                "front_plus_transition_to_rear_ratio": (front_rms + transition_rms) / max(rear_rms, 1e-12),
                "rear_best_shift_nm": rear_best_shift_nm,
                "rear_shift_aligned_rms_residual": rear_shift_aligned_rms_residual,
                "rear_unaligned_rms_residual": rear_unaligned_rms_residual,
                "rear_shift_explained_fraction": rear_shift_explained_fraction,
                "rear_peak_nm": rear_peak_nm,
                "rear_valley_nm": rear_valley_nm,
                "rear_peak_valley_spacing_nm": float(abs(rear_peak_nm - rear_valley_nm)),
                "rear_peak_valley_contrast_percent": float((np.max(rear_signal) - np.min(rear_signal)) * 100.0),
            }
        )

    return pd.concat(spectrum_rows, ignore_index=True), pd.DataFrame(feature_rows)


def build_discrimination_summary(feature_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for family, subset in feature_frame.groupby("family", sort=False):
        rows.append(
            {
                "family": family,
                "n_cases": int(len(subset)),
                "mean_front_rms": float(subset["front_rms_deltaR_500_650"].mean()),
                "std_front_rms": float(subset["front_rms_deltaR_500_650"].std(ddof=0)),
                "mean_transition_rms": float(subset["transition_rms_deltaR_650_810"].mean()),
                "std_transition_rms": float(subset["transition_rms_deltaR_650_810"].std(ddof=0)),
                "mean_rear_rms": float(subset["rear_rms_deltaR_810_1055"].mean()),
                "std_rear_rms": float(subset["rear_rms_deltaR_810_1055"].std(ddof=0)),
                "mean_rear_best_shift_nm": float(subset["rear_best_shift_nm"].mean()),
                "std_rear_best_shift_nm": float(subset["rear_best_shift_nm"].std(ddof=0)),
                "mean_rear_shift_explained_fraction": float(subset["rear_shift_explained_fraction"].mean()),
                "std_rear_shift_explained_fraction": float(subset["rear_shift_explained_fraction"].std(ddof=0)),
                "family_fingerprint_comment": FAMILY_COMMENTS.get(str(family), ""),
            }
        )
    return pd.DataFrame(rows)


def plot_delta_heatmap(
    family_frame: pd.DataFrame,
    parameter_column: str,
    title: str,
    output_path: Path,
) -> None:
    ordered = family_frame.pivot(index=parameter_column, columns="Wavelength_nm", values="Delta_R_total_vs_reference").sort_index()
    wavelengths_nm = ordered.columns.to_numpy(dtype=float)
    parameter_values = ordered.index.to_numpy(dtype=float)
    matrix = ordered.to_numpy(dtype=float) * 100.0
    limit = float(np.max(np.abs(matrix)))
    limit = max(limit, 0.2)
    fig, ax = plt.subplots(figsize=(11.6, 5.8), dpi=320)
    image = ax.imshow(
        matrix,
        origin="lower",
        aspect="auto",
        extent=[float(wavelengths_nm.min()), float(wavelengths_nm.max()), float(parameter_values.min()), float(parameter_values.max())],
        cmap="coolwarm",
        vmin=-limit,
        vmax=limit,
    )
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel(parameter_column.replace("_nm", " (nm)"))
    ax.set_title(title)
    style_axis(ax)
    colorbar = fig.colorbar(image, ax=ax, pad=0.02)
    colorbar.set_label("Delta R_total (%)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_selected_curves(
    family_frame: pd.DataFrame,
    parameter_column: str,
    selected_values: tuple[float, ...],
    title: str,
    output_path: Path,
    *,
    filter_anchor_id: str | None = None,
) -> None:
    subset = family_frame.copy()
    if filter_anchor_id is not None:
        subset = subset[subset["anchor_id"] == filter_anchor_id]

    fig, axes = plt.subplots(2, 1, figsize=(11.6, 7.0), dpi=320, sharex=True)
    colors = plt.cm.plasma(np.linspace(0.08, 0.92, len(selected_values)))
    for color, value in zip(colors, selected_values):
        mask = np.isclose(subset[parameter_column].to_numpy(dtype=float), float(value))
        curve = subset.loc[mask].sort_values("Wavelength_nm")
        if curve.empty:
            continue
        label = f"{value:.1f} nm"
        axes[0].plot(curve["Wavelength_nm"], curve["R_total"] * 100.0, linewidth=2.0, color=color, label=label)
        axes[1].plot(
            curve["Wavelength_nm"],
            curve["Delta_R_total_vs_reference"] * 100.0,
            linewidth=2.0,
            color=color,
            label=label,
        )

    axes[0].set_ylabel("R_total (%)")
    axes[1].set_ylabel("Delta R_total (%)")
    axes[1].set_xlabel("Wavelength (nm)")
    axes[0].set_title(title)
    for axis in axes:
        style_axis(axis)
        axis.legend(loc="best", ncol=3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_roughness_background_overview(
    front_frame: pd.DataFrame,
    rear_frame: pd.DataFrame,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11.6, 7.0), dpi=320, sharex=True)
    front_colors = plt.cm.Oranges(np.linspace(0.35, 0.9, len(SELECTED_FRONT_ROUGHNESS_VALUES_NM)))
    rear_colors = plt.cm.BuGn(np.linspace(0.35, 0.9, len(SELECTED_REAR_ROUGHNESS_VALUES_NM)))
    for color, value in zip(front_colors, SELECTED_FRONT_ROUGHNESS_VALUES_NM):
        curve = front_frame[np.isclose(front_frame["d_BEMA_front_nm"], float(value))].sort_values("Wavelength_nm")
        axes[0].plot(curve["Wavelength_nm"], curve["Delta_R_total_vs_reference"] * 100.0, color=color, linewidth=2.0, label=f"Front {value:.0f} nm")
    for color, value in zip(rear_colors, SELECTED_REAR_ROUGHNESS_VALUES_NM):
        curve = rear_frame[np.isclose(rear_frame["d_BEMA_rear_nm"], float(value))].sort_values("Wavelength_nm")
        axes[1].plot(curve["Wavelength_nm"], curve["Delta_R_total_vs_reference"] * 100.0, color=color, linewidth=2.0, label=f"Rear {value:.0f} nm")

    axes[0].set_title(f"{PHASE_NAME} Roughness Background Overview")
    axes[0].set_ylabel("Delta R_total (%)")
    axes[1].set_ylabel("Delta R_total (%)")
    axes[1].set_xlabel("Wavelength (nm)")
    for axis in axes:
        style_axis(axis)
        axis.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_feature_scatter_front_vs_rear(feature_frame: pd.DataFrame, output_path: Path) -> None:
    plot_frame = feature_frame[feature_frame["family"] != "background_anchor"].copy()
    fig, ax = plt.subplots(figsize=(8.4, 6.4), dpi=320)
    for family, subset in plot_frame.groupby("family", sort=False):
        ax.scatter(
            subset["front_rms_deltaR_500_650"] * 100.0,
            subset["rear_rms_deltaR_810_1055"] * 100.0,
            s=54,
            alpha=0.8,
            label=FAMILY_LABELS.get(str(family), str(family)),
            color=FAMILY_COLORS.get(str(family), "#455a64"),
            edgecolors="white",
            linewidths=0.5,
        )
    ax.set_xlabel("Front RMS Delta R_total (500-650 nm, %)")
    ax.set_ylabel("Rear RMS Delta R_total (810-1055 nm, %)")
    ax.set_title(f"{PHASE_NAME} Front vs Rear Window Response")
    style_axis(ax)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_feature_scatter_shift_vs_residual(feature_frame: pd.DataFrame, output_path: Path) -> None:
    plot_frame = feature_frame[feature_frame["family"] != "background_anchor"].copy()
    fig, ax = plt.subplots(figsize=(8.6, 6.4), dpi=320)
    for family, subset in plot_frame.groupby("family", sort=False):
        ax.scatter(
            subset["rear_best_shift_nm"],
            subset["rear_shift_aligned_rms_residual"] * 100.0,
            s=58,
            alpha=0.82,
            label=FAMILY_LABELS.get(str(family), str(family)),
            color=FAMILY_COLORS.get(str(family), "#455a64"),
            edgecolors="white",
            linewidths=0.5,
        )
    ax.set_xlabel("Rear Best Shift (nm)")
    ax.set_ylabel("Rear Shift-aligned RMS Residual (%)")
    ax.set_title(f"{PHASE_NAME} Rear Shift vs Non-rigid Residual")
    style_axis(ax)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_family_feature_boxplots(feature_frame: pd.DataFrame, output_path: Path) -> None:
    plot_frame = feature_frame[feature_frame["family"] != "background_anchor"].copy()
    family_order = [
        "thickness_nuisance",
        "front_roughness_nuisance",
        "rear_roughness_nuisance",
        "front_gap_on_background",
        "rear_gap_on_background",
    ]
    metric_specs = (
        ("front_plus_transition_to_rear_ratio", "Front+Transition / Rear RMS Ratio"),
        ("rear_best_shift_nm", "Rear Best Shift (nm)"),
        ("rear_shift_explained_fraction", "Rear Shift Explained Fraction"),
    )
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.8), dpi=320)
    for axis, (column, title) in zip(axes, metric_specs):
        data = [
            plot_frame.loc[plot_frame["family"] == family, column].to_numpy(dtype=float)
            for family in family_order
        ]
        box = axis.boxplot(
            data,
            patch_artist=True,
            tick_labels=[FAMILY_LABELS[family] for family in family_order],
            showfliers=False,
        )
        for patch, family in zip(box["boxes"], family_order):
            patch.set_facecolor(FAMILY_COLORS[family])
            patch.set_alpha(0.7)
        axis.set_title(title)
        style_axis(axis)
        axis.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_discrimination_atlas(feature_frame: pd.DataFrame, output_path: Path) -> None:
    plot_frame = feature_frame[feature_frame["family"] != "background_anchor"].copy()
    family_order = [
        "thickness_nuisance",
        "front_roughness_nuisance",
        "rear_roughness_nuisance",
        "front_gap_on_background",
        "rear_gap_on_background",
    ]
    panels = (
        ("rear_best_shift_nm", "front_plus_transition_to_rear_ratio"),
        ("rear_best_shift_nm", "rear_shift_explained_fraction"),
        ("front_plus_transition_to_rear_ratio", "rear_shift_explained_fraction"),
    )
    fig, axes = plt.subplots(1, 3, figsize=(16.0, 4.9), dpi=320)
    label_map = {
        "rear_best_shift_nm": "Rear Best Shift (nm)",
        "front_plus_transition_to_rear_ratio": "Front+Transition / Rear RMS Ratio",
        "rear_shift_explained_fraction": "Rear Shift Explained Fraction",
    }
    for axis, (x_column, y_column) in zip(axes, panels):
        for family in family_order:
            subset = plot_frame[plot_frame["family"] == family]
            axis.scatter(
                subset[x_column],
                subset[y_column],
                s=52,
                alpha=0.8,
                color=FAMILY_COLORS[family],
                label=FAMILY_LABELS[family],
                edgecolors="white",
                linewidths=0.5,
            )
        axis.set_xlabel(label_map[x_column])
        axis.set_ylabel(label_map[y_column])
        style_axis(axis)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
    fig.suptitle(f"{PHASE_NAME} Discrimination Atlas", y=1.02)
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def write_markdown_log(
    output_path: Path,
    manifest_frame: pd.DataFrame,
    feature_frame: pd.DataFrame,
    summary_frame: pd.DataFrame,
) -> None:
    summary_table = summary_frame.to_csv(index=False)
    focus_families = feature_frame[feature_frame["family"] != "background_anchor"].copy()
    top_features = summary_frame.set_index("family")
    log_text = f"""# {PHASE_NAME} air-gap discrimination database

## 1. 输入与定位

- 材料主表：`resources/aligned_full_stack_nk_pvk_v2.csv`
- 参考 phase：`A-2 / B-1 / B-2 / C-1a / C-1b`
- 当前定位：不是最终分类器，而是 **realistic thickness + roughness background** 下的 `R_total` 前向判别数据库

## 2. 为什么 thickness scan 收窄到 700 ± 25 nm

宽范围 `500-900 nm` 更适合建立“全局机制字典”，但不适合直接映射真实器件中的局部膜厚起伏。本轮将 thickness nuisance 收窄到 `675-725 nm`，目的是把厚度变化限制在更现实的局部褶皱/起伏尺度上，让后续算法面对的 nuisance 分布更接近实验场景。

## 3. 为什么 BEMA 不再当作单独专题，而视为 roughness background

本轮的目标是区分 thickness / roughness / air-gap，而不是继续扩展单一粗糙机制故事线。因此 front-BEMA 与 rear-BEMA 只保留其“effective roughness proxy”角色，用作 realistic background / nuisance family；真正重点是看 gap 在这种背景上是否仍能保留可判别指纹。

## 4. realistic background 下仍保留的 gap 指纹

- `front-gap`：主要保留 `front + transition` 窗口响应，并伴随次级 rear-window 耦合
- `rear-gap`：主要保留 `transition + rear` 的非均匀重构与更强的 rear shift / 非刚性残差
- 相比之下，thickness 仍更像 rear-window 的“可平移型” fringe 漂移

## 5. 哪些特征更像 thickness

- `rear_best_shift_nm` 较大
- `rear_shift_explained_fraction` 较高
- `front_plus_transition_to_rear_ratio` 较低

这说明 local thickness nuisance 仍然更接近“rear-window rigid shift”而非强局部重构。

## 6. 哪些特征更像 roughness

- `front_roughness_nuisance`：前窗与过渡区 RMS 响应较强，`front_plus_transition_to_rear_ratio` 偏高
- `rear_roughness_nuisance`：rear-window 幅度微扰明显，但 `rear_shift_explained_fraction` 低于 thickness

也就是说，roughness 更像 envelope / amplitude perturbation，而不是 rigid phase shift。

## 7. 哪些特征最有希望区分 front-gap vs rear-gap

- `front_plus_transition_to_rear_ratio`
- `rear_best_shift_nm`
- `rear_shift_explained_fraction`
- `front_rms_deltaR_500_650`
- `rear_rms_deltaR_810_1055`

其中：
- `front-gap` 更偏前窗/过渡区占优，且存在次级 rear 耦合
- `rear-gap` 更偏 transition/rear 主导，并保留更强的非刚性 rear-window 重构

## 8. 当前还不能回答什么

- 尚未纳入 composition variation / 成分工程
- 尚未进行实验拟合或真实噪声建模
- 仍是 specular TMM，不含散射
- 当前 roughness 仍是 BEMA proxy，不等于真实 AFM RMS 真值

## 9. 数据库规模摘要

- physical cases（manifest 唯一物理 case）：`{len(manifest_frame)}`
- logical family cases（feature DB 行数）：`{len(feature_frame)}`
- 关键 family 统计：
```csv
{summary_table.strip()}
```

## 10. 初步判别结论

- `thickness_nuisance` 的 family 平均 `rear_shift_explained_fraction` 为 `{float(top_features.loc["thickness_nuisance", "mean_rear_shift_explained_fraction"]):.3f}`
- `rear_gap_on_background` 的 family 平均 `rear_best_shift_nm` 为 `{float(top_features.loc["rear_gap_on_background", "mean_rear_best_shift_nm"]):.3f} nm`
- `front_gap_on_background` 的 family 平均前窗 RMS 为 `{float(top_features.loc["front_gap_on_background", "mean_front_rms"])*100.0:.3f}%`

这些结果支持：在 realistic thickness + roughness background 下，gap 指纹没有消失，只是必须依赖窗口分布 + rear shift/nonrigid residual 的联合特征去区分。
"""
    output_path.write_text(log_text, encoding="utf-8")


def write_report(
    output_path: Path,
    manifest_frame: pd.DataFrame,
    feature_frame: pd.DataFrame,
    summary_frame: pd.DataFrame,
) -> None:
    report_text = f"""# {PHASE_NAME} REPORT

## 1. 阶段目标

本阶段从 A-C 的“单机制字典”推进到 **realistic background 下的 air-gap 判别数据库**。目标不是训练分类器，而是先建立一套统一的前向判别输入，回答在局部 thickness 起伏与前后 roughness 背景存在时，front-gap / rear-gap 是否仍保留可识别的 `R_total` 指纹。

## 2. 为什么本轮不引入成分模型

本轮先冻结 composition engineering，不再继续扩展成分扰动或 surrogate uncertainty。这样可以把问题收敛为 thickness / roughness / gap 三类结构机制之间的判别问题，避免在算法路线选择前引入额外高维不确定性。

## 3. 模型定义

### realistic baseline

- `d_PVK = 700 nm`
- `d_BEMA_front = 10 nm`
- `d_BEMA_rear = 20 nm`
- `d_gap_front = 0`
- `d_gap_rear = 0`

### thickness nuisance family

- `d_PVK = 675-725 nm`
- `d_BEMA_front = 10 nm`
- `d_BEMA_rear = 20 nm`
- no gap

### roughness nuisance family

- front roughness: `d_BEMA_front = 5, 10, 15 nm`
- rear roughness: `d_BEMA_rear = 10, 20, 30 nm`

### gap overlays on realistic anchors

- 7 个 anchor backgrounds
- front-gap overlay: `d_gap_front = 0, 0.5, 1, 2, 3, 5, 10, 15 nm`
- rear-gap overlay: `d_gap_rear = 0, 0.5, 1, 2, 3, 5, 10, 15 nm`

## 4. 关键结果

### 局部 thickness 变化主要保留什么指纹

- rear-window `810-1055 nm` 仍是主敏感窗口
- `rear_best_shift_nm` 与 `rear_shift_explained_fraction` 仍然较高
- 在 realistic roughness background 上，thickness 仍然更像可平移型 fringe 漂移

### roughness 变化主要保留什么指纹

- front roughness 更偏前窗背景与 transition 包络变化
- rear roughness 更偏 rear-window 的 envelope / amplitude perturbation
- 两者都不像纯 thickness 那样能被单一 shift 高比例解释

### gap 叠加 roughness 后仍可用的窗口特征

- front-gap：`front + transition` 的 RMS 分布和次级 rear coupling 仍可用
- rear-gap：`transition + rear` 的非刚性重构、较强 rear shift / residual 组合仍可用
- 因此 gap 在 realistic background 上没有“消失”，只是需要用联合特征识别

## 5. 对后续算法的启发

最值得优先尝试的 robust features：

- `rear_best_shift_nm`
- `rear_shift_explained_fraction`
- `front_plus_transition_to_rear_ratio`
- `front_rms_deltaR_500_650`
- `rear_rms_deltaR_810_1055`

这些特征分别刻画：

- rear-window 是否更像 rigid shift
- rear-window 是否存在非刚性 residual
- 响应是否偏前侧还是偏后侧

## 6. 限制

- 未引入 composition variation
- 未做实验拟合
- 仍为 specular TMM
- BEMA 仍是 proxy，而不是真实 AFM 粗糙度真值
- gap 仍为理想平面 separation

## 7. 数据规模

- manifest 物理 case 数：`{len(manifest_frame)}`
- feature DB 逻辑 family case 数：`{len(feature_frame)}`

## 8. 下一步算法建议

当前数据库更适合作为后续算法比较的输入，而不是直接当作最终分类器。下一步可优先比较：

1. 基于 hand-crafted features 的线性 / 树模型基线
2. 基于 rear shift + nonrigid residual 的两阶段判别
3. 基于窗口化 `Delta R_total` 的低维嵌入 + family classification
"""
    output_path.write_text(report_text, encoding="utf-8")


def write_report_readme(output_path: Path) -> None:
    readme_text = """# Phase D-1 Air-gap Discrimination Database

这里存放的是用于后续算法讨论的 **前向判别数据库**，不是最终分类器。

本目录聚焦：

- realistic thickness nuisance
- realistic roughness background family
- front-gap / rear-gap on roughness background
- 面向 `R_total` 的窗口特征与 rear shift / nonrigid residual 摘要
"""
    output_path.write_text(readme_text, encoding="utf-8")


def sync_report_assets(paths: OutputPaths) -> None:
    assets_to_copy = [
        paths.case_manifest_csv,
        paths.feature_database_csv,
        paths.discrimination_summary_csv,
        paths.thickness_heatmap_png,
        paths.roughness_overview_png,
        paths.front_gap_heatmap_png,
        paths.rear_gap_heatmap_png,
        paths.scatter_front_vs_rear_png,
        paths.scatter_shift_vs_residual_png,
        paths.family_boxplots_png,
        paths.atlas_png,
    ]
    for asset in assets_to_copy:
        shutil.copy2(asset, REPORT_DIR / asset.name)


def plot_all_figures(paths: OutputPaths, spectra_frame: pd.DataFrame, feature_frame: pd.DataFrame) -> None:
    thickness_frame = spectra_frame[spectra_frame["family"] == "thickness_nuisance"].copy()
    front_roughness_frame = spectra_frame[spectra_frame["family"] == "front_roughness_nuisance"].copy()
    rear_roughness_frame = spectra_frame[spectra_frame["family"] == "rear_roughness_nuisance"].copy()
    front_gap_frame = spectra_frame[
        (spectra_frame["family"] == "front_gap_on_background") & (spectra_frame["anchor_id"] == PLOTTING_GAP_ANCHOR_ID)
    ].copy()
    rear_gap_frame = spectra_frame[
        (spectra_frame["family"] == "rear_gap_on_background") & (spectra_frame["anchor_id"] == PLOTTING_GAP_ANCHOR_ID)
    ].copy()

    plot_delta_heatmap(
        thickness_frame,
        parameter_column="d_PVK_nm",
        title=f"{PHASE_NAME} Local Thickness Delta R_total vs 700 nm",
        output_path=paths.thickness_heatmap_png,
    )
    plot_selected_curves(
        thickness_frame,
        parameter_column="d_PVK_nm",
        selected_values=SELECTED_THICKNESS_VALUES_NM,
        title=f"{PHASE_NAME} Local Thickness Selected R_total Curves",
        output_path=paths.thickness_selected_curves_png,
    )
    plot_selected_curves(
        front_roughness_frame,
        parameter_column="d_BEMA_front_nm",
        selected_values=SELECTED_FRONT_ROUGHNESS_VALUES_NM,
        title=f"{PHASE_NAME} Front Roughness Background Curves",
        output_path=paths.front_roughness_curves_png,
    )
    plot_selected_curves(
        rear_roughness_frame,
        parameter_column="d_BEMA_rear_nm",
        selected_values=SELECTED_REAR_ROUGHNESS_VALUES_NM,
        title=f"{PHASE_NAME} Rear Roughness Background Curves",
        output_path=paths.rear_roughness_curves_png,
    )
    plot_roughness_background_overview(front_roughness_frame, rear_roughness_frame, paths.roughness_overview_png)

    plot_selected_curves(
        front_gap_frame,
        parameter_column="d_gap_front_nm",
        selected_values=SELECTED_GAP_VALUES_NM,
        title=f"{PHASE_NAME} Front-gap on Realistic Background",
        output_path=paths.front_gap_curves_png,
    )
    plot_selected_curves(
        rear_gap_frame,
        parameter_column="d_gap_rear_nm",
        selected_values=SELECTED_GAP_VALUES_NM,
        title=f"{PHASE_NAME} Rear-gap on Realistic Background",
        output_path=paths.rear_gap_curves_png,
    )
    plot_delta_heatmap(
        front_gap_frame,
        parameter_column="d_gap_front_nm",
        title=f"{PHASE_NAME} Front-gap Delta R_total on Realistic Background",
        output_path=paths.front_gap_heatmap_png,
    )
    plot_delta_heatmap(
        rear_gap_frame,
        parameter_column="d_gap_rear_nm",
        title=f"{PHASE_NAME} Rear-gap Delta R_total on Realistic Background",
        output_path=paths.rear_gap_heatmap_png,
    )
    plot_feature_scatter_front_vs_rear(feature_frame, paths.scatter_front_vs_rear_png)
    plot_feature_scatter_shift_vs_residual(feature_frame, paths.scatter_shift_vs_residual_png)
    plot_family_feature_boxplots(feature_frame, paths.family_boxplots_png)
    plot_discrimination_atlas(feature_frame, paths.atlas_png)


def validate_outputs(
    manifest_frame: pd.DataFrame,
    spectra_frame: pd.DataFrame,
    feature_frame: pd.DataFrame,
) -> None:
    if manifest_frame["case_id"].duplicated().any():
        raise ValueError("phaseD1_case_manifest.csv 中存在重复 case_id。")
    expected_rows = len(feature_frame) * len(phase_a1.EXPECTED_WAVELENGTHS_NM)
    if len(spectra_frame) != expected_rows:
        raise ValueError(f"phaseD1_rtotal_database.csv 行数不符，预期 {expected_rows}，实际 {len(spectra_frame)}。")
    if not np.isfinite(spectra_frame["R_total"].to_numpy(dtype=float)).all():
        raise ValueError("R_total 数据含有 NaN/Inf。")
    if not np.isfinite(spectra_frame["Delta_R_total_vs_reference"].to_numpy(dtype=float)).all():
        raise ValueError("Delta_R_total_vs_reference 含有 NaN/Inf。")
    if np.any((spectra_frame["R_total"].to_numpy(dtype=float) < -1e-9) | (spectra_frame["R_total"].to_numpy(dtype=float) > 1.0 + 1e-9)):
        raise ValueError("R_total 超出 [0,1] 物理边界。")
    if feature_frame["reference_case_id"].isna().any():
        raise ValueError("feature database 中存在缺失的 reference_case_id。")
    if not np.isfinite(feature_frame.select_dtypes(include=[np.number]).to_numpy(dtype=float)).all():
        raise ValueError("feature database 含有 NaN/Inf。")
    explained = feature_frame["rear_shift_explained_fraction"].to_numpy(dtype=float)
    if np.any((explained < -1e-9) | (explained > 1.0 + 1e-9)):
        raise ValueError("rear_shift_explained_fraction 超出 [0,1]。")


def main() -> None:
    args = parse_args()
    output_paths = ensure_output_dirs()
    stack = load_stack(args.nk_csv)

    manifest_frame, logical_rows = build_cases()
    spectra_cache = compute_physical_case_spectra(stack, manifest_frame)
    spectra_frame, feature_frame = build_databases(logical_rows, spectra_cache)
    discrimination_summary = build_discrimination_summary(feature_frame)

    validate_outputs(manifest_frame, spectra_frame, feature_frame)

    manifest_frame.to_csv(output_paths.case_manifest_csv, index=False)
    spectra_frame.to_csv(output_paths.rtotal_database_csv, index=False)
    feature_frame.to_csv(output_paths.feature_database_csv, index=False)
    discrimination_summary.to_csv(output_paths.discrimination_summary_csv, index=False)

    plot_all_figures(output_paths, spectra_frame, feature_frame)
    write_markdown_log(output_paths.log_md, manifest_frame, feature_frame, discrimination_summary)
    write_report(output_paths.report_md, manifest_frame, feature_frame, discrimination_summary)
    write_report_readme(output_paths.report_readme)
    sync_report_assets(output_paths)


if __name__ == "__main__":
    main()
