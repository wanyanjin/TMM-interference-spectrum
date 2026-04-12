"""Phase 07 two-step decoupled inversion core.

The PVK optical constants consumed here come from the Phase 05c aligned stack,
which ultimately traces back to [LIT-0001] within its measured window and uses
documented engineering extrapolation outside that window.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math

import matplotlib
import numpy as np
import pandas as pd
from lmfit import Parameters, minimize
from scipy.interpolate import PchipInterpolator
from scipy.optimize import differential_evolution
from scipy.signal import find_peaks, savgol_filter
from tmm import coh_tmm

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NK_CSV_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk.csv"

FRONT_WINDOW_NM = (500.0, 650.0)
MASKED_WINDOW_NM = (650.0, 860.0)
REAR_WINDOW_NM = (860.0, 1055.0)

WINDOW_FRONT = "front"
WINDOW_MASKED = "masked"
WINDOW_REAR = "rear"

SAM_THICKNESS_NM = 5.0
SAM_NK = 1.5 + 0.0j
ITO_THICKNESS_NM = 100.0
NIOX_THICKNESS_NM = 45.0
TOTAL_C60_THICKNESS_NM = 15.0
AG_THICKNESS_NM = 100.0
GLASS_FRONT_AIR_N = 1.0 + 0.0j

THICKNESS_AVERAGE_POINT_COUNT = 5
THICKNESS_AVERAGE_MIN_SIGMA_NM = 0.1
PARAMETER_BOUND_TOLERANCE_RATIO = 0.05
RESIDUAL_SCALE_FLOOR = 0.005
REAR_D_BULK_SCAN_STEP_NM = 1.0
REAR_BASIN_HALF_WIDTH_NM = 15.0
MAX_COARSE_BASIN_COUNT = 2
MIN_BASIN_SEPARATION_NM = 8.0
DE_SEED = 7
DE_MAXITER = 6
DE_POPSIZE = 5
DE_TOL = 1e-3
TIE_BREAK_COST_REL_TOL = 0.02
TIE_BREAK_COST_ABS_TOL = 1e-5
OPTIMIZATION_WINDOW_STRIDE = 8
SCATTER_FLOOR = 1e-6


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    initial: float
    minimum: float
    maximum: float


@dataclass(frozen=True)
class WindowScale:
    label: str
    start_nm: float
    end_nm: float
    point_count: int
    median_reflectance: float
    mad_reflectance: float
    scale_value: float


@dataclass(frozen=True)
class MaskedResidualStats:
    mean: float
    std: float
    max_abs: float


@dataclass(frozen=True)
class RearWindowSanityCheck:
    sample_name: str
    smoothing_window_length: int
    smoothing_polyorder: int
    lambda_peak_nm: float
    lambda_valley_nm: float
    n_avg_pvk: float
    d_estimate_nm: float
    rear_z_measured: np.ndarray
    rear_z_fitted: np.ndarray | None = None


@dataclass(frozen=True)
class Phase07Config:
    stage1_specs: tuple[ParameterSpec, ...]
    stage2_specs: tuple[ParameterSpec, ...]

    @classmethod
    def default(cls) -> "Phase07Config":
        return cls(
            stage1_specs=(
                ParameterSpec("d_ITO", 100.0, 90.0, 110.0),
                ParameterSpec("d_NiOx", 45.0, 35.0, 55.0),
                ParameterSpec("sigma_front_rms_nm", 25.0, 0.0, 60.0),
            ),
            stage2_specs=(
                ParameterSpec("d_bulk", 700.0, 580.0, 900.0),
                ParameterSpec("d_rough", 12.0, 0.0, 30.0),
                ParameterSpec("sigma_thickness", 12.0, 0.0, 80.0),
                ParameterSpec("ito_alpha", 1.0, 0.0, 5.0),
                ParameterSpec("pvk_b_scale", 1.0, 0.80, 1.25),
                ParameterSpec("niox_k", 0.0, 0.0, 0.12),
            ),
        )

    @property
    def all_specs(self) -> tuple[ParameterSpec, ...]:
        return self.stage1_specs + self.stage2_specs


@dataclass(frozen=True)
class Phase07SampleInput:
    sample_name: str
    with_ag: bool
    source_mode: str
    source_path: Path
    fit_input_path: Path
    wavelength_nm: np.ndarray
    reflectance: np.ndarray
    window_label: np.ndarray

    @property
    def front_mask(self) -> np.ndarray:
        return self.window_label == WINDOW_FRONT

    @property
    def masked_mask(self) -> np.ndarray:
        return self.window_label == WINDOW_MASKED

    @property
    def rear_mask(self) -> np.ndarray:
        return self.window_label == WINDOW_REAR


@dataclass(frozen=True)
class Phase07OpticalModel:
    wavelength_nm: np.ndarray
    n_glass: np.ndarray
    n_ito: np.ndarray
    n_niox: np.ndarray
    n_pvk: np.ndarray
    n_c60: np.ndarray
    n_ag: np.ndarray


@dataclass(frozen=True)
class Phase07FrontStageResult:
    best_params: dict[str, float]
    fitted_reflectance: np.ndarray
    physical_reflectance: np.ndarray
    scatter_curve: np.ndarray
    normalized_residual: np.ndarray
    cost: float
    optimizer_summary: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class Phase07RearStageResult:
    best_params: dict[str, float]
    fitted_reflectance: np.ndarray
    physical_reflectance: np.ndarray
    normalized_residual: np.ndarray
    total_cost: float
    rear_cost: float
    front_cost: float
    rear_derivative_correlation: float
    coarse_scan_thickness_nm: np.ndarray
    coarse_scan_cost: np.ndarray
    coarse_scan_basins_nm: np.ndarray
    optimizer_summary: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class Phase07FitResult:
    sample_input: Phase07SampleInput
    fitted_reflectance: np.ndarray
    physical_reflectance: np.ndarray
    residual: np.ndarray
    normalized_residual: np.ndarray
    best_params: dict[str, float]
    d_c60_bulk_best: float
    window_scales: tuple[WindowScale, ...]
    window_cost_front: float
    window_cost_rear: float
    total_cost: float
    masked_band_residual_stats: MaskedResidualStats
    rear_derivative_correlation: float
    coarse_scan_thickness_nm: np.ndarray
    coarse_scan_cost: np.ndarray
    coarse_scan_basins_nm: np.ndarray
    optimizer_stage_summary: tuple[dict[str, object], ...]
    bound_hit_flags: dict[str, bool]
    warnings: tuple[str, ...]
    rear_z_measured: np.ndarray
    rear_z_fitted: np.ndarray
    stage1_result: Phase07FrontStageResult
    stage2_result: Phase07RearStageResult


def classify_window_label(wavelength_nm: float) -> str:
    if FRONT_WINDOW_NM[0] <= wavelength_nm <= FRONT_WINDOW_NM[1]:
        return WINDOW_FRONT
    if MASKED_WINDOW_NM[0] < wavelength_nm < MASKED_WINDOW_NM[1]:
        return WINDOW_MASKED
    if REAR_WINDOW_NM[0] <= wavelength_nm <= REAR_WINDOW_NM[1]:
        return WINDOW_REAR
    raise ValueError(
        "Phase 07 仅支持 500-1055 nm 实测窗口；"
        f"当前波长 {wavelength_nm:.3f} nm 超出定义范围。"
    )


def build_window_labels(wavelength_nm: np.ndarray) -> np.ndarray:
    return np.asarray([classify_window_label(value) for value in wavelength_nm], dtype=object)


def load_phase07_sample_input(
    fit_input_path: Path,
    sample_name: str | None = None,
    source_mode: str | None = None,
    source_path: Path | None = None,
    with_ag: bool | None = None,
) -> Phase07SampleInput:
    frame = pd.read_csv(fit_input_path)
    required_columns = {"Wavelength_nm", "Absolute_Reflectance", "window_label", "with_ag"}
    missing_columns = sorted(required_columns - set(frame.columns))
    if missing_columns:
        raise ValueError(f"{fit_input_path} 缺少必要列: {missing_columns}")

    wavelength_nm = pd.to_numeric(frame["Wavelength_nm"], errors="coerce").to_numpy(dtype=float)
    reflectance = pd.to_numeric(frame["Absolute_Reflectance"], errors="coerce").to_numpy(dtype=float)
    labels = frame["window_label"].astype(str).to_numpy(dtype=object)
    with_ag_series = frame["with_ag"].astype(str).str.lower()

    valid_mask = np.isfinite(wavelength_nm) & np.isfinite(reflectance)
    wavelength_nm = wavelength_nm[valid_mask]
    reflectance = reflectance[valid_mask]
    labels = labels[valid_mask]
    with_ag_series = with_ag_series[valid_mask]

    sort_index = np.argsort(wavelength_nm)
    wavelength_nm = wavelength_nm[sort_index]
    reflectance = reflectance[sort_index]
    labels = labels[sort_index]
    with_ag_series = with_ag_series.iloc[sort_index].reset_index(drop=True)

    inferred_with_ag = bool(with_ag_series.map({"true": True, "false": False}).iloc[0])
    if not with_ag_series.isin(["true", "false"]).all():
        raise ValueError(f"{fit_input_path} 的 with_ag 列必须是 true/false。")
    if np.any((reflectance < 0.0) | (reflectance > 1.0)):
        raise ValueError(f"{fit_input_path} 的 Absolute_Reflectance 超出 0-1 范围。")

    expected_labels = build_window_labels(wavelength_nm)
    if not np.array_equal(labels, expected_labels):
        raise ValueError(f"{fit_input_path} 的 window_label 与波长段定义不一致。")

    return Phase07SampleInput(
        sample_name=sample_name or fit_input_path.stem.replace("_fit_input", ""),
        with_ag=inferred_with_ag if with_ag is None else with_ag,
        source_mode=source_mode or "fit_input",
        source_path=source_path or fit_input_path,
        fit_input_path=fit_input_path,
        wavelength_nm=wavelength_nm,
        reflectance=reflectance,
        window_label=labels,
    )


def write_phase07_fit_input(
    source_table_path: Path,
    output_path: Path,
    sample_name: str,
    with_ag: bool,
) -> Phase07SampleInput:
    frame = pd.read_csv(source_table_path)
    required_columns = {"Wavelength_nm", "Absolute_Reflectance"}
    missing_columns = sorted(required_columns - set(frame.columns))
    if missing_columns:
        raise ValueError(f"{source_table_path} 缺少必要列: {missing_columns}")

    wavelength_nm = pd.to_numeric(frame["Wavelength_nm"], errors="coerce").to_numpy(dtype=float)
    reflectance = pd.to_numeric(frame["Absolute_Reflectance"], errors="coerce").to_numpy(dtype=float)
    valid_mask = np.isfinite(wavelength_nm) & np.isfinite(reflectance)
    wavelength_nm = wavelength_nm[valid_mask]
    reflectance = reflectance[valid_mask]

    sort_index = np.argsort(wavelength_nm)
    wavelength_nm = wavelength_nm[sort_index]
    reflectance = reflectance[sort_index]

    range_mask = (wavelength_nm >= FRONT_WINDOW_NM[0]) & (wavelength_nm <= REAR_WINDOW_NM[1])
    wavelength_nm = wavelength_nm[range_mask]
    reflectance = reflectance[range_mask]

    if wavelength_nm.size == 0:
        raise ValueError(f"{source_table_path} 在 500-1055 nm 内没有有效数据。")

    labels = build_window_labels(wavelength_nm)
    output_frame = pd.DataFrame(
        {
            "Wavelength_nm": wavelength_nm,
            "Absolute_Reflectance": reflectance,
            "window_label": labels,
            "with_ag": np.full(wavelength_nm.size, bool(with_ag), dtype=bool),
        }
    )
    output_frame.to_csv(output_path, index=False, encoding="utf-8-sig")
    return load_phase07_sample_input(
        fit_input_path=output_path,
        sample_name=sample_name,
        source_mode="hdr_csv",
        source_path=source_table_path,
        with_ag=with_ag,
    )


def build_phase07_stack_model(
    nk_csv_path: Path = DEFAULT_NK_CSV_PATH,
) -> Phase07OpticalModel:
    frame = pd.read_csv(nk_csv_path)
    required_columns = (
        "Wavelength_nm",
        "n_Glass",
        "k_Glass",
        "n_ITO",
        "k_ITO",
        "n_NiOx",
        "k_NiOx",
        "n_PVK",
        "k_PVK",
        "n_C60",
        "k_C60",
        "n_Ag",
        "k_Ag",
    )
    missing_columns = [column for column in required_columns if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"{nk_csv_path} 缺少必要列: {missing_columns}")

    wavelength_nm = frame["Wavelength_nm"].to_numpy(dtype=float)
    return Phase07OpticalModel(
        wavelength_nm=wavelength_nm,
        n_glass=frame["n_Glass"].to_numpy(dtype=float) + 1j * frame["k_Glass"].to_numpy(dtype=float),
        n_ito=frame["n_ITO"].to_numpy(dtype=float) + 1j * frame["k_ITO"].to_numpy(dtype=float),
        n_niox=frame["n_NiOx"].to_numpy(dtype=float) + 1j * frame["k_NiOx"].to_numpy(dtype=float),
        n_pvk=frame["n_PVK"].to_numpy(dtype=float) + 1j * frame["k_PVK"].to_numpy(dtype=float),
        n_c60=frame["n_C60"].to_numpy(dtype=float) + 1j * frame["k_C60"].to_numpy(dtype=float),
        n_ag=frame["n_Ag"].to_numpy(dtype=float) + 1j * frame["k_Ag"].to_numpy(dtype=float),
    )


def interpolate_complex(base_wavelength_nm: np.ndarray, base_values: np.ndarray, query_wavelength_nm: np.ndarray) -> np.ndarray:
    query = np.asarray(query_wavelength_nm, dtype=float)
    if query.min() < base_wavelength_nm.min() or query.max() > base_wavelength_nm.max():
        raise ValueError(
            "目标波长超出 aligned_full_stack_nk.csv 支持范围: "
            f"query=({query.min():.3f}, {query.max():.3f}) nm"
        )
    real_part = np.interp(query, base_wavelength_nm, np.real(base_values))
    imag_part = np.interp(query, base_wavelength_nm, np.imag(base_values))
    return real_part + 1j * imag_part


def calc_bruggeman_ema_50_50(nk_a: np.ndarray, nk_b: np.ndarray) -> np.ndarray:
    eps_a = np.asarray(nk_a, dtype=np.complex128) ** 2
    eps_b = np.asarray(nk_b, dtype=np.complex128) ** 2
    b_term = 0.5 * (eps_a + eps_b)
    eps_eff = 0.5 * (b_term + np.sqrt(b_term**2 + 2.0 * eps_a * eps_b))
    return np.sqrt(eps_eff)


def apply_ito_alpha(base_nk: np.ndarray, wavelength_nm: np.ndarray, ito_alpha: float) -> np.ndarray:
    x_norm = (np.asarray(wavelength_nm, dtype=float) - REAR_WINDOW_NM[0]) / (REAR_WINDOW_NM[1] - REAR_WINDOW_NM[0])
    x_norm = np.clip(x_norm, 0.0, 1.0)
    k_new = np.imag(base_nk) * (1.0 + ito_alpha * (x_norm**2))
    return np.real(base_nk) + 1j * k_new


def apply_pvk_b_scale(base_nk: np.ndarray, wavelength_nm: np.ndarray, pvk_b_scale: float) -> np.ndarray:
    wavelength = np.asarray(wavelength_nm, dtype=float)
    anchor_index = int(np.argmin(np.abs(wavelength - 1000.0)))
    n_anchor = float(np.real(base_nk[anchor_index]))
    n_scaled = n_anchor + pvk_b_scale * (np.real(base_nk) - n_anchor)
    return n_scaled + 1j * np.imag(base_nk)


def apply_rear_weighted_niox_k(base_nk: np.ndarray, wavelength_nm: np.ndarray, extra_k: float) -> np.ndarray:
    wavelength = np.asarray(wavelength_nm, dtype=float)
    weight = ((wavelength - REAR_WINDOW_NM[0]) / (REAR_WINDOW_NM[1] - REAR_WINDOW_NM[0])) ** 2
    weight = np.clip(weight, 0.0, 1.0)
    return np.real(base_nk) + 1j * (np.imag(base_nk) + extra_k * weight)


def compute_remaining_c60_bulk_thickness_nm(d_rough_nm: float) -> float:
    return max(0.0, TOTAL_C60_THICKNESS_NM - 0.5 * d_rough_nm)


def build_coherent_stack(
    with_ag: bool,
    glass_nk: complex,
    ito_nk: complex,
    niox_nk: complex,
    pvk_nk: complex,
    rough_nk: complex,
    c60_nk: complex,
    ag_nk: complex,
    d_ito_nm: float,
    d_niox_nm: float,
    d_bulk_nm: float,
    d_rough_nm: float,
    d_c60_bulk_nm: float,
) -> tuple[list[complex], list[float]]:
    n_list = [glass_nk, ito_nk, niox_nk, SAM_NK, pvk_nk]
    d_list = [np.inf, d_ito_nm, d_niox_nm, SAM_THICKNESS_NM, d_bulk_nm]
    if d_rough_nm > 0.0:
        n_list.append(rough_nk)
        d_list.append(d_rough_nm)
    if d_c60_bulk_nm > 0.0:
        n_list.append(c60_nk)
        d_list.append(d_c60_bulk_nm)
    if with_ag:
        n_list.extend([ag_nk, GLASS_FRONT_AIR_N])
        d_list.extend([AG_THICKNESS_NM, np.inf])
    else:
        n_list.append(GLASS_FRONT_AIR_N)
        d_list.append(np.inf)
    return n_list, d_list


def calc_front_surface_reflectance(glass_nk: np.ndarray) -> np.ndarray:
    reflection = (GLASS_FRONT_AIR_N - glass_nk) / (GLASS_FRONT_AIR_N + glass_nk)
    return np.abs(reflection) ** 2


def calc_macro_reflectance(
    model: Phase07OpticalModel,
    wavelengths_nm: np.ndarray,
    with_ag: bool,
    d_ITO_nm: float,
    d_NiOx_nm: float,
    d_bulk_nm: float,
    d_rough_nm: float,
    sigma_thickness_nm: float,
    ito_alpha: float,
    pvk_b_scale: float,
    niox_k: float,
) -> np.ndarray:
    wavelengths = np.asarray(wavelengths_nm, dtype=float)
    base_glass = interpolate_complex(model.wavelength_nm, model.n_glass, wavelengths)
    base_ito = interpolate_complex(model.wavelength_nm, model.n_ito, wavelengths)
    base_niox = interpolate_complex(model.wavelength_nm, model.n_niox, wavelengths)
    base_pvk = interpolate_complex(model.wavelength_nm, model.n_pvk, wavelengths)
    base_c60 = interpolate_complex(model.wavelength_nm, model.n_c60, wavelengths)
    base_ag = interpolate_complex(model.wavelength_nm, model.n_ag, wavelengths)

    ito_nk = apply_ito_alpha(base_ito, wavelengths, ito_alpha)
    niox_nk = apply_rear_weighted_niox_k(base_niox, wavelengths, niox_k)
    pvk_nk = apply_pvk_b_scale(base_pvk, wavelengths, pvk_b_scale)
    rough_nk = calc_bruggeman_ema_50_50(pvk_nk, base_c60)
    d_c60_bulk_nm = compute_remaining_c60_bulk_thickness_nm(d_rough_nm)

    def calc_single_reflectance(single_d_bulk_nm: float) -> np.ndarray:
        r_stack = np.empty(wavelengths.size, dtype=float)
        for index, wavelength_nm in enumerate(wavelengths):
            n_list, d_list = build_coherent_stack(
                with_ag=with_ag,
                glass_nk=complex(base_glass[index]),
                ito_nk=complex(ito_nk[index]),
                niox_nk=complex(niox_nk[index]),
                pvk_nk=complex(pvk_nk[index]),
                rough_nk=complex(rough_nk[index]),
                c60_nk=complex(base_c60[index]),
                ag_nk=complex(base_ag[index]),
                d_ito_nm=d_ITO_nm,
                d_niox_nm=d_NiOx_nm,
                d_bulk_nm=single_d_bulk_nm,
                d_rough_nm=d_rough_nm,
                d_c60_bulk_nm=d_c60_bulk_nm,
            )
            r_stack[index] = float(coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(wavelength_nm))["R"])
        return r_stack

    if sigma_thickness_nm < THICKNESS_AVERAGE_MIN_SIGMA_NM:
        return calc_single_reflectance(d_bulk_nm)

    offsets_nm = np.linspace(-3.0 * sigma_thickness_nm, 3.0 * sigma_thickness_nm, THICKNESS_AVERAGE_POINT_COUNT, dtype=float)
    weights = np.exp(-(offsets_nm**2) / (2.0 * sigma_thickness_nm**2))
    weights /= np.sum(weights)

    averaged = np.zeros(wavelengths.size, dtype=float)
    for offset_nm, weight in zip(offsets_nm, weights):
        averaged += float(weight) * calc_single_reflectance(d_bulk_nm + float(offset_nm))
    return averaged


def compute_debye_waller_scatter(
    glass_nk: np.ndarray,
    wavelength_nm: np.ndarray,
    sigma_front_rms_nm: float,
) -> np.ndarray:
    wavelength = np.asarray(wavelength_nm, dtype=float)
    n_real = np.real(glass_nk)
    x_front = (4.0 * np.pi * float(sigma_front_rms_nm) * n_real / wavelength) ** 2
    return np.clip(np.exp(-x_front), SCATTER_FLOOR, 1.0)


def apply_front_scattering_observation_model(
    glass_nk: np.ndarray,
    wavelength_nm: np.ndarray,
    sigma_front_rms_nm: float,
    stack_reflectance: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    r_front = calc_front_surface_reflectance(glass_nk)
    t_front = 1.0 - r_front
    s_front = compute_debye_waller_scatter(glass_nk, wavelength_nm, sigma_front_rms_nm)
    denominator = 1.0 - r_front * stack_reflectance
    if np.any(np.isclose(denominator, 0.0)):
        raise ValueError("厚玻璃非相干级联分母接近 0。")
    collected = s_front * r_front + (s_front**2) * (t_front**2) * stack_reflectance / denominator
    return collected, s_front


def compute_window_scales(sample_input: Phase07SampleInput) -> tuple[WindowScale, ...]:
    outputs: list[WindowScale] = []
    for label, bounds in ((WINDOW_FRONT, FRONT_WINDOW_NM), (WINDOW_REAR, REAR_WINDOW_NM)):
        mask = sample_input.window_label == label
        reflectance = sample_input.reflectance[mask]
        if reflectance.size == 0:
            median_reflectance = RESIDUAL_SCALE_FLOOR
            mad_reflectance = 0.0
            scale_value = RESIDUAL_SCALE_FLOOR
        else:
            median_reflectance = float(np.median(reflectance))
            mad_reflectance = float(np.median(np.abs(reflectance - median_reflectance)))
            scale_value = max(median_reflectance, 1.4826 * mad_reflectance, RESIDUAL_SCALE_FLOOR)
        outputs.append(
            WindowScale(
                label=label,
                start_nm=float(bounds[0]),
                end_nm=float(bounds[1]),
                point_count=int(np.count_nonzero(mask)),
                median_reflectance=median_reflectance,
                mad_reflectance=mad_reflectance,
                scale_value=scale_value,
            )
        )
    return tuple(outputs)


def build_optimization_sample_input(sample_input: Phase07SampleInput, stride: int = OPTIMIZATION_WINDOW_STRIDE) -> Phase07SampleInput:
    if stride <= 1:
        return sample_input
    selected_indices: list[int] = []
    for label in (WINDOW_FRONT, WINDOW_REAR):
        label_indices = np.flatnonzero(sample_input.window_label == label)
        selected_indices.extend(label_indices[::stride].tolist())
        if label_indices.size > 0 and label_indices[-1] not in selected_indices:
            selected_indices.append(int(label_indices[-1]))
    selected_indices = sorted(set(selected_indices))
    return Phase07SampleInput(
        sample_name=sample_input.sample_name,
        with_ag=sample_input.with_ag,
        source_mode=sample_input.source_mode,
        source_path=sample_input.source_path,
        fit_input_path=sample_input.fit_input_path,
        wavelength_nm=sample_input.wavelength_nm[selected_indices],
        reflectance=sample_input.reflectance[selected_indices],
        window_label=sample_input.window_label[selected_indices],
    )


def compute_rear_derivative_correlation(sample_input: Phase07SampleInput, modeled_reflectance: np.ndarray) -> float:
    rear_mask = sample_input.rear_mask
    measured = sample_input.reflectance[rear_mask]
    modeled = modeled_reflectance[rear_mask]
    measured_gradient = np.gradient(measured, sample_input.wavelength_nm[rear_mask])
    modeled_gradient = np.gradient(modeled, sample_input.wavelength_nm[rear_mask])
    measured_std = float(np.std(measured_gradient))
    modeled_std = float(np.std(modeled_gradient))
    if measured_std < 1e-12 or modeled_std < 1e-12:
        return 0.0
    return float(np.corrcoef(measured_gradient, modeled_gradient)[0, 1])


def compute_zscore(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return (array - float(np.mean(array))) / (float(np.std(array)) + 1e-9)


def build_front_residual(sample_input: Phase07SampleInput, modeled_reflectance: np.ndarray, window_scales: tuple[WindowScale, ...]) -> np.ndarray:
    residual = modeled_reflectance - sample_input.reflectance
    normalized = np.full(residual.shape, np.nan, dtype=float)
    scale_map = {item.label: item.scale_value for item in window_scales}
    point_map = {item.label: item.point_count for item in window_scales}
    front_mask = sample_input.front_mask
    if point_map[WINDOW_FRONT] > 0:
        normalized[front_mask] = math.sqrt(1.0 / point_map[WINDOW_FRONT]) * residual[front_mask] / scale_map[WINDOW_FRONT]
    return normalized


def build_rear_residual(sample_input: Phase07SampleInput, modeled_reflectance: np.ndarray, window_scales: tuple[WindowScale, ...]) -> np.ndarray:
    normalized = np.full(sample_input.reflectance.shape, np.nan, dtype=float)
    point_map = {item.label: item.point_count for item in window_scales}
    rear_mask = sample_input.rear_mask
    if point_map[WINDOW_REAR] > 0:
        z_model = compute_zscore(modeled_reflectance[rear_mask])
        z_meas = compute_zscore(sample_input.reflectance[rear_mask])
        normalized[rear_mask] = math.sqrt(1.0 / point_map[WINDOW_REAR]) * (z_model - z_meas)
    return normalized


def compute_cost_from_normalized_residual(normalized_residual: np.ndarray) -> float:
    finite = normalized_residual[np.isfinite(normalized_residual)]
    if finite.size == 0:
        raise ValueError("归一化残差为空，无法计算 cost。")
    return float(np.sum(finite**2))


def params_to_lmfit_parameters(specs: tuple[ParameterSpec, ...], initial_values: dict[str, float]) -> Parameters:
    params = Parameters()
    for spec in specs:
        params.add(spec.name, value=float(initial_values[spec.name]), min=float(spec.minimum), max=float(spec.maximum))
    return params


def estimate_rear_window_thickness(
    sample_input: Phase07SampleInput,
    model: Phase07OpticalModel,
    smoothing_fraction: float = 0.45,
    polyorder: int = 3,
) -> RearWindowSanityCheck:
    rear_mask = sample_input.rear_mask
    wavelength_nm = sample_input.wavelength_nm[rear_mask]
    reflectance = sample_input.reflectance[rear_mask]
    if wavelength_nm.size < 9:
        raise ValueError("后窗点数不足，无法进行峰谷自证验算。")
    window_length = max(11, int(wavelength_nm.size * smoothing_fraction))
    if window_length % 2 == 0:
        window_length += 1
    if window_length >= wavelength_nm.size:
        window_length = wavelength_nm.size - 1
        if window_length % 2 == 0:
            window_length -= 1
    smoothed = savgol_filter(reflectance, window_length=window_length, polyorder=polyorder)
    prominence = max((float(np.max(smoothed)) - float(np.min(smoothed))) * 0.015, 1e-6)
    distance = max(30, wavelength_nm.size // 8)
    peaks, _ = find_peaks(smoothed, prominence=prominence, distance=distance)
    valleys, _ = find_peaks(-smoothed, prominence=prominence, distance=distance)
    extrema = sorted([(int(index), "peak") for index in peaks] + [(int(index), "valley") for index in valleys], key=lambda item: item[0])
    selected_pair: tuple[int, int] | None = None
    selected_types: tuple[str, str] | None = None
    for left, right in zip(extrema, extrema[1:]):
        if left[1] != right[1]:
            selected_pair = (left[0], right[0])
            selected_types = (left[1], right[1])
            break
    if selected_pair is None or selected_types is None:
        peak_index = int(np.argmax(smoothed))
        valley_index = int(np.argmin(smoothed))
        selected_pair = tuple(sorted((peak_index, valley_index)))
        selected_types = ("peak", "valley") if peak_index < valley_index else ("valley", "peak")
    left_index, right_index = selected_pair
    lambda_left = float(wavelength_nm[left_index])
    lambda_right = float(wavelength_nm[right_index])
    left_type, right_type = selected_types
    if left_type == "peak":
        lambda_peak_nm = lambda_left
        lambda_valley_nm = lambda_right
    else:
        lambda_peak_nm = lambda_right
        lambda_valley_nm = lambda_left
    lambda_mean = 0.5 * (lambda_peak_nm + lambda_valley_nm)
    n_avg_pvk = float(np.interp(lambda_mean, model.wavelength_nm, np.real(model.n_pvk)))
    d_estimate_nm = (lambda_peak_nm * lambda_valley_nm) / (4.0 * n_avg_pvk * abs(lambda_peak_nm - lambda_valley_nm))
    return RearWindowSanityCheck(
        sample_name=sample_input.sample_name,
        smoothing_window_length=window_length,
        smoothing_polyorder=polyorder,
        lambda_peak_nm=lambda_peak_nm,
        lambda_valley_nm=lambda_valley_nm,
        n_avg_pvk=n_avg_pvk,
        d_estimate_nm=float(d_estimate_nm),
        rear_z_measured=compute_zscore(reflectance),
    )


def _stage1_defaults() -> dict[str, float]:
    return {
        "d_ITO": ITO_THICKNESS_NM,
        "d_NiOx": NIOX_THICKNESS_NM,
        "sigma_front_rms_nm": 25.0,
        "d_bulk": 700.0,
        "d_rough": 0.0,
        "sigma_thickness": 0.0,
        "ito_alpha": 0.0,
        "pvk_b_scale": 1.0,
        "niox_k": 0.0,
    }


def evaluate_stage1_model(
    sample_input: Phase07SampleInput,
    model: Phase07OpticalModel,
    params: dict[str, float],
    window_scales: tuple[WindowScale, ...],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    wavelengths = sample_input.wavelength_nm
    base_glass = interpolate_complex(model.wavelength_nm, model.n_glass, wavelengths)
    physical = calc_macro_reflectance(
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
    collected, scatter_curve = apply_front_scattering_observation_model(
        glass_nk=base_glass,
        wavelength_nm=wavelengths,
        sigma_front_rms_nm=params["sigma_front_rms_nm"],
        stack_reflectance=physical,
    )
    normalized = build_front_residual(sample_input, collected, window_scales)
    cost = compute_cost_from_normalized_residual(np.where(sample_input.front_mask, normalized, np.nan))
    return physical, collected, normalized, cost


def fit_stage1_front_window(
    sample_input: Phase07SampleInput,
    model: Phase07OpticalModel,
    config: Phase07Config,
) -> Phase07FrontStageResult:
    front_sample = Phase07SampleInput(
        sample_name=sample_input.sample_name,
        with_ag=sample_input.with_ag,
        source_mode=sample_input.source_mode,
        source_path=sample_input.source_path,
        fit_input_path=sample_input.fit_input_path,
        wavelength_nm=sample_input.wavelength_nm[sample_input.front_mask],
        reflectance=sample_input.reflectance[sample_input.front_mask],
        window_label=sample_input.window_label[sample_input.front_mask],
    )
    window_scales = compute_window_scales(front_sample)
    optimization_sample = build_optimization_sample_input(front_sample)
    optimization_scales = compute_window_scales(optimization_sample)
    specs = config.stage1_specs
    defaults = _stage1_defaults()

    def vector_to_dict(vector: np.ndarray) -> dict[str, float]:
        output = dict(defaults)
        for index, spec in enumerate(specs):
            output[spec.name] = float(vector[index])
        return output

    def scalar_cost(vector: np.ndarray) -> float:
        params = vector_to_dict(np.asarray(vector, dtype=float))
        _, _, _, cost = evaluate_stage1_model(optimization_sample, model, params, optimization_scales)
        return cost

    bounds = [(spec.minimum, spec.maximum) for spec in specs]
    de_result = differential_evolution(
        scalar_cost,
        bounds=bounds,
        seed=DE_SEED,
        maxiter=DE_MAXITER,
        popsize=DE_POPSIZE,
        tol=DE_TOL,
        polish=False,
        updating="deferred",
        workers=1,
    )
    de_params = vector_to_dict(np.asarray(de_result.x, dtype=float))
    lmfit_params = params_to_lmfit_parameters(specs, de_params)

    def residual_for_lmfit(params_obj: Parameters) -> np.ndarray:
        params = dict(defaults)
        for spec in specs:
            params[spec.name] = float(params_obj[spec.name].value)
        _, _, normalized, _ = evaluate_stage1_model(optimization_sample, model, params, optimization_scales)
        return normalized[np.isfinite(normalized)]

    lmfit_result = minimize(residual_for_lmfit, lmfit_params, method="least_squares", max_nfev=80)
    best_params = dict(defaults)
    for spec in specs:
        best_params[spec.name] = float(lmfit_result.params[spec.name].value)
    physical, collected, normalized, cost = evaluate_stage1_model(sample_input, model, best_params, window_scales)
    _, scatter_curve = apply_front_scattering_observation_model(
        glass_nk=interpolate_complex(model.wavelength_nm, model.n_glass, sample_input.wavelength_nm),
        wavelength_nm=sample_input.wavelength_nm,
        sigma_front_rms_nm=best_params["sigma_front_rms_nm"],
        stack_reflectance=physical,
    )
    return Phase07FrontStageResult(
        best_params={key: float(best_params[key]) for key in ("d_ITO", "d_NiOx", "sigma_front_rms_nm")},
        fitted_reflectance=collected,
        physical_reflectance=physical,
        scatter_curve=scatter_curve,
        normalized_residual=normalized,
        cost=cost,
        optimizer_summary=(
            {
                "stage": "stage1_front",
                "de_fun": float(de_result.fun),
                "de_nit": int(de_result.nit),
                "de_nfev": int(de_result.nfev),
                "lmfit_nfev": int(lmfit_result.nfev),
                "lmfit_success": bool(lmfit_result.success),
                "params": {key: float(best_params[key]) for key in ("d_ITO", "d_NiOx", "sigma_front_rms_nm")},
                "front_cost": float(cost),
            },
        ),
    )


def evaluate_stage2_model(
    sample_input: Phase07SampleInput,
    model: Phase07OpticalModel,
    stage1_params: dict[str, float],
    stage2_params: dict[str, float],
    window_scales: tuple[WindowScale, ...],
    use_rear_only: bool = False,
) -> tuple[np.ndarray, np.ndarray, float, float, np.ndarray]:
    wavelengths = sample_input.wavelength_nm
    base_glass = interpolate_complex(model.wavelength_nm, model.n_glass, wavelengths)
    physical = calc_macro_reflectance(
        model=model,
        wavelengths_nm=wavelengths,
        with_ag=sample_input.with_ag,
        d_ITO_nm=stage1_params["d_ITO"],
        d_NiOx_nm=stage1_params["d_NiOx"],
        d_bulk_nm=stage2_params["d_bulk"],
        d_rough_nm=stage2_params["d_rough"],
        sigma_thickness_nm=stage2_params["sigma_thickness"],
        ito_alpha=stage2_params["ito_alpha"],
        pvk_b_scale=stage2_params["pvk_b_scale"],
        niox_k=stage2_params["niox_k"],
    )
    collected, _ = apply_front_scattering_observation_model(
        glass_nk=base_glass,
        wavelength_nm=wavelengths,
        sigma_front_rms_nm=stage1_params["sigma_front_rms_nm"],
        stack_reflectance=physical,
    )
    front_norm = build_front_residual(sample_input, collected, window_scales)
    rear_norm = build_rear_residual(sample_input, collected, window_scales)
    normalized = np.where(np.isfinite(front_norm), front_norm, rear_norm)
    cost_target = np.where(sample_input.rear_mask, rear_norm, np.nan) if use_rear_only else normalized
    cost = compute_cost_from_normalized_residual(cost_target)
    derivative_correlation = compute_rear_derivative_correlation(sample_input, collected)
    rear_z_model = compute_zscore(collected[sample_input.rear_mask])
    return physical, collected, cost, derivative_correlation, normalized


def identify_coarse_scan_basins(thickness_nm: np.ndarray, cost_values: np.ndarray) -> np.ndarray:
    candidate_indices: list[int] = []
    for index in range(1, len(cost_values) - 1):
        if cost_values[index] <= cost_values[index - 1] and cost_values[index] <= cost_values[index + 1]:
            candidate_indices.append(index)
    if not candidate_indices:
        candidate_indices = [int(np.argmin(cost_values))]
    ordered = sorted(candidate_indices, key=lambda item: float(cost_values[item]))
    selected_nm: list[float] = []
    for index in ordered:
        value_nm = float(thickness_nm[index])
        if all(abs(value_nm - existing) >= MIN_BASIN_SEPARATION_NM for existing in selected_nm):
            selected_nm.append(value_nm)
        if len(selected_nm) >= MAX_COARSE_BASIN_COUNT:
            break
    return np.asarray(selected_nm, dtype=float)


def fit_stage2_rear_window(
    sample_input: Phase07SampleInput,
    model: Phase07OpticalModel,
    config: Phase07Config,
    stage1_result: Phase07FrontStageResult,
) -> Phase07RearStageResult:
    window_scales = compute_window_scales(sample_input)
    optimization_sample = build_optimization_sample_input(sample_input)
    optimization_scales = compute_window_scales(optimization_sample)
    specs = config.stage2_specs
    defaults = {spec.name: spec.initial for spec in specs}
    stage1_params = dict(stage1_result.best_params)

    scan_spec = next(spec for spec in specs if spec.name == "d_bulk")
    coarse_scan_thickness_nm = np.arange(scan_spec.minimum, scan_spec.maximum + REAR_D_BULK_SCAN_STEP_NM, REAR_D_BULK_SCAN_STEP_NM, dtype=float)
    coarse_scan_cost = np.empty_like(coarse_scan_thickness_nm)
    for index, d_bulk_nm in enumerate(coarse_scan_thickness_nm):
        defaults["d_bulk"] = float(d_bulk_nm)
        _, _, cost, _, _ = evaluate_stage2_model(
            optimization_sample,
            model,
            stage1_params,
            defaults,
            optimization_scales,
            use_rear_only=True,
        )
        coarse_scan_cost[index] = cost
    coarse_scan_basins_nm = identify_coarse_scan_basins(coarse_scan_thickness_nm, coarse_scan_cost)

    def vector_to_dict(vector: np.ndarray) -> dict[str, float]:
        return {spec.name: float(vector[index]) for index, spec in enumerate(specs)}

    candidate_summaries: list[dict[str, object]] = []
    for basin_center_nm in coarse_scan_basins_nm:
        bounds: list[tuple[float, float]] = []
        for spec in specs:
            if spec.name == "d_bulk":
                bounds.append((max(spec.minimum, basin_center_nm - REAR_BASIN_HALF_WIDTH_NM), min(spec.maximum, basin_center_nm + REAR_BASIN_HALF_WIDTH_NM)))
            else:
                bounds.append((spec.minimum, spec.maximum))

        def scalar_cost(vector: np.ndarray) -> float:
            stage2_params = vector_to_dict(np.asarray(vector, dtype=float))
            _, _, cost, _, _ = evaluate_stage2_model(
                optimization_sample,
                model,
                stage1_params,
                stage2_params,
                optimization_scales,
                use_rear_only=False,
            )
            return cost

        de_result = differential_evolution(
            scalar_cost,
            bounds=bounds,
            seed=DE_SEED,
            maxiter=DE_MAXITER,
            popsize=DE_POPSIZE,
            tol=DE_TOL,
            polish=False,
            updating="deferred",
            workers=1,
        )
        de_params = vector_to_dict(np.asarray(de_result.x, dtype=float))
        lmfit_params = params_to_lmfit_parameters(specs, de_params)

        def residual_for_lmfit(params_obj: Parameters) -> np.ndarray:
            stage2_params = {spec.name: float(params_obj[spec.name].value) for spec in specs}
            _, _, _, _, normalized = evaluate_stage2_model(
                optimization_sample,
                model,
                stage1_params,
                stage2_params,
                optimization_scales,
                use_rear_only=False,
            )
            return normalized[np.isfinite(normalized)]

        lmfit_result = minimize(residual_for_lmfit, lmfit_params, method="least_squares", max_nfev=80)
        stage2_params = {spec.name: float(lmfit_result.params[spec.name].value) for spec in specs}
        physical, collected, total_cost, derivative_correlation, normalized = evaluate_stage2_model(
            sample_input,
            model,
            stage1_params,
            stage2_params,
            window_scales,
            use_rear_only=False,
        )
        front_cost = compute_cost_from_normalized_residual(np.where(sample_input.front_mask, normalized, np.nan))
        rear_cost = compute_cost_from_normalized_residual(np.where(sample_input.rear_mask, normalized, np.nan))
        candidate_summaries.append(
            {
                "basin_center_nm": float(basin_center_nm),
                "de_fun": float(de_result.fun),
                "de_nit": int(de_result.nit),
                "de_nfev": int(de_result.nfev),
                "lmfit_nfev": int(lmfit_result.nfev),
                "lmfit_success": bool(lmfit_result.success),
                "params": stage2_params,
                "physical_reflectance": physical,
                "fitted_reflectance": collected,
                "normalized_residual": normalized,
                "total_cost": total_cost,
                "front_cost": front_cost,
                "rear_cost": rear_cost,
                "rear_derivative_correlation": derivative_correlation,
            }
        )

    best_cost = min(float(item["total_cost"]) for item in candidate_summaries)
    tied = [item for item in candidate_summaries if float(item["total_cost"]) <= max(best_cost * (1.0 + TIE_BREAK_COST_REL_TOL), best_cost + TIE_BREAK_COST_ABS_TOL)]
    chosen = max(tied, key=lambda item: (float(item["rear_derivative_correlation"]), -float(item["total_cost"])))
    return Phase07RearStageResult(
        best_params={key: float(chosen["params"][key]) for key in chosen["params"]},
        fitted_reflectance=np.asarray(chosen["fitted_reflectance"], dtype=float),
        physical_reflectance=np.asarray(chosen["physical_reflectance"], dtype=float),
        normalized_residual=np.asarray(chosen["normalized_residual"], dtype=float),
        total_cost=float(chosen["total_cost"]),
        rear_cost=float(chosen["rear_cost"]),
        front_cost=float(chosen["front_cost"]),
        rear_derivative_correlation=float(chosen["rear_derivative_correlation"]),
        coarse_scan_thickness_nm=coarse_scan_thickness_nm,
        coarse_scan_cost=coarse_scan_cost,
        coarse_scan_basins_nm=coarse_scan_basins_nm,
        optimizer_summary=tuple(
            {
                "stage": "stage2_rear",
                "basin_center_nm": float(item["basin_center_nm"]),
                "de_fun": float(item["de_fun"]),
                "de_nit": int(item["de_nit"]),
                "de_nfev": int(item["de_nfev"]),
                "lmfit_nfev": int(item["lmfit_nfev"]),
                "lmfit_success": bool(item["lmfit_success"]),
                "total_cost": float(item["total_cost"]),
                "front_cost": float(item["front_cost"]),
                "rear_cost": float(item["rear_cost"]),
                "rear_derivative_correlation": float(item["rear_derivative_correlation"]),
                "params": {key: float(value) for key, value in dict(item["params"]).items()},
            }
            for item in candidate_summaries
        ),
    )


def fit_phase07_two_step_sample(
    sample_input: Phase07SampleInput,
    model: Phase07OpticalModel,
    config: Phase07Config | None = None,
) -> Phase07FitResult:
    config = config or Phase07Config.default()
    window_scales = compute_window_scales(sample_input)
    stage1_result = fit_stage1_front_window(sample_input, model, config)
    stage2_result = fit_stage2_rear_window(sample_input, model, config, stage1_result)

    best_params = dict(stage1_result.best_params)
    best_params.update(stage2_result.best_params)
    residual = stage2_result.fitted_reflectance - sample_input.reflectance
    masked_residual = residual[sample_input.masked_mask]
    masked_stats = MaskedResidualStats(
        mean=float(np.mean(masked_residual)),
        std=float(np.std(masked_residual)),
        max_abs=float(np.max(np.abs(masked_residual))),
    )
    d_c60_bulk_best = compute_remaining_c60_bulk_thickness_nm(best_params["d_rough"])

    bound_hit_flags: dict[str, bool] = {}
    warnings: list[str] = []
    for spec in config.all_specs:
        span = spec.maximum - spec.minimum
        tolerance = PARAMETER_BOUND_TOLERANCE_RATIO * span
        value = best_params[spec.name]
        hit = (value - spec.minimum) <= tolerance or (spec.maximum - value) <= tolerance
        bound_hit_flags[spec.name] = bool(hit)
        if hit:
            warnings.append(f"{spec.name} 接近边界")
    if np.isclose(d_c60_bulk_best, 0.0):
        warnings.append("d_C60_bulk 退化到 0 nm，粗糙层已耗尽致密 C60")

    optimizer_summary = stage1_result.optimizer_summary + stage2_result.optimizer_summary
    return Phase07FitResult(
        sample_input=sample_input,
        fitted_reflectance=stage2_result.fitted_reflectance,
        physical_reflectance=stage2_result.physical_reflectance,
        residual=residual,
        normalized_residual=stage2_result.normalized_residual,
        best_params=best_params,
        d_c60_bulk_best=d_c60_bulk_best,
        window_scales=window_scales,
        window_cost_front=float(stage1_result.cost),
        window_cost_rear=float(stage2_result.rear_cost),
        total_cost=float(stage2_result.total_cost),
        masked_band_residual_stats=masked_stats,
        rear_derivative_correlation=float(stage2_result.rear_derivative_correlation),
        coarse_scan_thickness_nm=stage2_result.coarse_scan_thickness_nm,
        coarse_scan_cost=stage2_result.coarse_scan_cost,
        coarse_scan_basins_nm=stage2_result.coarse_scan_basins_nm,
        optimizer_stage_summary=optimizer_summary,
        bound_hit_flags=bound_hit_flags,
        warnings=tuple(warnings),
        rear_z_measured=compute_zscore(sample_input.reflectance[sample_input.rear_mask]),
        rear_z_fitted=compute_zscore(stage2_result.fitted_reflectance[sample_input.rear_mask]),
        stage1_result=stage1_result,
        stage2_result=stage2_result,
    )


def fit_dual_window_sample(
    sample_input: Phase07SampleInput,
    model: Phase07OpticalModel,
    config: Phase07Config | None = None,
) -> Phase07FitResult:
    return fit_phase07_two_step_sample(sample_input=sample_input, model=model, config=config)


def export_fit_curve_table(result: Phase07FitResult, output_path: Path) -> None:
    rear_z_measured = np.full(result.sample_input.wavelength_nm.shape, np.nan, dtype=float)
    rear_z_fitted = np.full(result.sample_input.wavelength_nm.shape, np.nan, dtype=float)
    scatter_curve = np.full(result.sample_input.wavelength_nm.shape, np.nan, dtype=float)
    physical_stage1 = np.full(result.sample_input.wavelength_nm.shape, np.nan, dtype=float)
    rear_z_measured[result.sample_input.rear_mask] = result.rear_z_measured
    rear_z_fitted[result.sample_input.rear_mask] = result.rear_z_fitted
    scatter_curve[result.sample_input.front_mask] = result.stage1_result.scatter_curve[result.sample_input.front_mask]
    physical_stage1[result.sample_input.front_mask] = result.stage1_result.physical_reflectance[result.sample_input.front_mask]
    frame = pd.DataFrame(
        {
            "Wavelength_nm": result.sample_input.wavelength_nm,
            "Absolute_Reflectance_Measured": result.sample_input.reflectance,
            "Absolute_Reflectance_Fitted": result.fitted_reflectance,
            "Absolute_Reflectance_Physical": result.physical_reflectance,
            "Residual": result.residual,
            "Normalized_Residual": result.normalized_residual,
            "Front_Scatter_Curve": scatter_curve,
            "Front_Physical_Reflectance": physical_stage1,
            "Rear_ZScore_Measured": rear_z_measured,
            "Rear_ZScore_Fitted": rear_z_fitted,
            "window_label": result.sample_input.window_label,
        }
    )
    frame.to_csv(output_path, index=False, encoding="utf-8-sig")


def export_fit_summary_table(result: Phase07FitResult, output_path: Path) -> None:
    payload = {
        "sample_name": result.sample_input.sample_name,
        "with_ag": result.sample_input.with_ag,
        "source_mode": result.sample_input.source_mode,
        "stage1_locked": True,
        "d_C60_bulk_best": result.d_c60_bulk_best,
        "stage1_front_cost": result.stage1_result.cost,
        "stage2_rear_cost": result.stage2_result.rear_cost,
        "window_cost_front": result.window_cost_front,
        "window_cost_rear": result.window_cost_rear,
        "total_cost": result.total_cost,
        "rear_derivative_correlation": result.rear_derivative_correlation,
        "masked_residual_mean": result.masked_band_residual_stats.mean,
        "masked_residual_std": result.masked_band_residual_stats.std,
        "masked_residual_max_abs": result.masked_band_residual_stats.max_abs,
        "bound_hit_flags": json.dumps(result.bound_hit_flags, ensure_ascii=False, sort_keys=True),
        "warnings": json.dumps(list(result.warnings), ensure_ascii=False),
        "optimizer_stage_summary": json.dumps(result.optimizer_stage_summary, ensure_ascii=False),
    }
    for key, value in result.best_params.items():
        payload[key] = value
    for scale in result.window_scales:
        payload[f"window_{scale.label}_scale"] = scale.scale_value
        payload[f"window_{scale.label}_point_count"] = scale.point_count
    pd.DataFrame([payload]).to_csv(output_path, index=False, encoding="utf-8-sig")


def write_optimizer_log(result: Phase07FitResult, output_path: Path) -> None:
    lines = [
        f"# Phase 07 Two-Step Inversion Log: {result.sample_input.sample_name}",
        "",
        "## Sample",
        "",
        f"- source_mode: `{result.sample_input.source_mode}`",
        f"- source_path: `{result.sample_input.source_path}`",
        f"- with_ag: `{result.sample_input.with_ag}`",
        "",
        "## Stage 1 Front Lock",
        "",
        f"- d_ITO: `{result.stage1_result.best_params['d_ITO']:.6f}` nm",
        f"- d_NiOx: `{result.stage1_result.best_params['d_NiOx']:.6f}` nm",
        f"- sigma_front_rms_nm: `{result.stage1_result.best_params['sigma_front_rms_nm']:.6f}` nm",
        f"- stage1_front_cost: `{result.stage1_result.cost:.6f}`",
        "",
        "## Stage 2 Rear Fit",
        "",
    ]
    for key in ("d_bulk", "d_rough", "sigma_thickness", "ito_alpha", "pvk_b_scale", "niox_k"):
        lines.append(f"- {key}: `{result.best_params[key]:.6f}`")
    lines.extend(
        [
            f"- d_C60_bulk_best: `{result.d_c60_bulk_best:.6f}` nm",
            f"- window_cost_front: `{result.window_cost_front:.6f}`",
            f"- window_cost_rear: `{result.window_cost_rear:.6f}`",
            f"- total_cost: `{result.total_cost:.6f}`",
            f"- rear_derivative_correlation: `{result.rear_derivative_correlation:.6f}`",
            "",
            "## Boundary Checks",
            "",
            f"- bound_hit_flags: `{json.dumps(result.bound_hit_flags, ensure_ascii=False, sort_keys=True)}`",
            f"- warnings: `{json.dumps(list(result.warnings), ensure_ascii=False)}`",
            "",
            "## Optimizer Stages",
            "",
            f"```json\n{json.dumps(result.optimizer_stage_summary, ensure_ascii=False, indent=2)}\n```",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _apply_window_background(axis: plt.Axes) -> None:
    axis.axvspan(FRONT_WINDOW_NM[0], FRONT_WINDOW_NM[1], color="#e8f3ec", alpha=0.85)
    axis.axvspan(MASKED_WINDOW_NM[0], MASKED_WINDOW_NM[1], color="#fff2cc", alpha=0.9)
    axis.axvspan(REAR_WINDOW_NM[0], REAR_WINDOW_NM[1], color="#e7f0fa", alpha=0.9)


def _build_masked_visual_guide(result: Phase07FitResult) -> np.ndarray:
    fitted_visual = result.fitted_reflectance.copy()
    front_indices = np.flatnonzero(result.sample_input.front_mask)
    rear_indices = np.flatnonzero(result.sample_input.rear_mask)
    masked_indices = np.flatnonzero(result.sample_input.masked_mask)
    if front_indices.size > 0 and rear_indices.size > 0 and masked_indices.size > 1:
        anchor_x = np.array(
            [
                result.sample_input.wavelength_nm[front_indices[-1]],
                result.sample_input.wavelength_nm[rear_indices[0]],
            ],
            dtype=float,
        )
        anchor_y = np.array(
            [
                result.fitted_reflectance[front_indices[-1]],
                result.fitted_reflectance[rear_indices[0]],
            ],
            dtype=float,
        )
        control_x = np.array(
            [
                max(FRONT_WINDOW_NM[0], anchor_x[0] - 40.0),
                anchor_x[0],
                anchor_x[1],
                min(REAR_WINDOW_NM[1], anchor_x[1] + 40.0),
            ],
            dtype=float,
        )
        control_y = np.array([anchor_y[0], anchor_y[0], anchor_y[1], anchor_y[1]], dtype=float)
        fitted_visual[masked_indices] = PchipInterpolator(control_x, control_y)(
            result.sample_input.wavelength_nm[masked_indices]
        )
    return fitted_visual


def plot_measured_vs_fitted_full_spectrum(result: Phase07FitResult, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.0, 5.6), dpi=320)
    _apply_window_background(ax)
    fitted_visual = _build_masked_visual_guide(result)
    masked_indices = np.flatnonzero(result.sample_input.masked_mask)
    ax.plot(result.sample_input.wavelength_nm, result.sample_input.reflectance * 100.0, color="#424242", linewidth=2.4, label="Measured")
    ax.plot(result.sample_input.wavelength_nm, fitted_visual * 100.0, color="#005b96", linewidth=1.8, linestyle="--", label="Fitted")
    if masked_indices.size > 1:
        ax.plot(
            result.sample_input.wavelength_nm[masked_indices],
            fitted_visual[masked_indices] * 100.0,
            color="#5dade2",
            linewidth=2.1,
            linestyle=":",
            alpha=0.95,
            label="Masked visual guide only",
        )
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Absolute Reflectance (%)")
    ax.set_title(f"Phase 07 Two-Step Fit: {result.sample_input.sample_name}")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_dual_window_zoom(result: Phase07FitResult, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), dpi=320, constrained_layout=True)
    front_mask = result.sample_input.front_mask
    wavelength_front = result.sample_input.wavelength_nm[front_mask]
    axes[0].plot(wavelength_front, result.sample_input.reflectance[front_mask] * 100.0, color="#424242", linewidth=2.3, label="Measured")
    axes[0].plot(wavelength_front, result.fitted_reflectance[front_mask] * 100.0, color="#b03a2e", linewidth=1.8, linestyle="--", label="Collected fit")
    axes[0].plot(wavelength_front, result.stage1_result.physical_reflectance[front_mask] * 100.0, color="#1f77b4", linewidth=1.5, linestyle=":", label="Unattenuated physical")
    ax2 = axes[0].twinx()
    ax2.plot(wavelength_front, result.stage1_result.scatter_curve[front_mask], color="#2e7d32", linewidth=1.4, alpha=0.8, label="S_front")
    axes[0].set_xlim(FRONT_WINDOW_NM[0], FRONT_WINDOW_NM[1])
    axes[0].set_xlabel("Wavelength (nm)")
    axes[0].set_ylabel("Absolute Reflectance (%)")
    ax2.set_ylabel("Front Scatter Factor")
    axes[0].set_title("Stage 1 Front Window")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    h1, l1 = axes[0].get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    axes[0].legend(h1 + h2, l1 + l2, loc="upper right")

    rear_mask = result.sample_input.rear_mask
    rear_wavelength_nm = result.sample_input.wavelength_nm[rear_mask]
    axes[1].plot(rear_wavelength_nm, result.rear_z_measured, color="#424242", linewidth=2.3, label="z_meas")
    axes[1].plot(rear_wavelength_nm, result.rear_z_fitted, color="#005b96", linewidth=1.8, linestyle="--", label="z_model")
    axes[1].set_xlim(REAR_WINDOW_NM[0], REAR_WINDOW_NM[1])
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Z-Score Normalized Reflectance")
    axes[1].set_title("Stage 2 Rear Window")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_stage1_front_fit(result: Phase07FitResult, output_path: Path) -> None:
    front_mask = result.sample_input.front_mask
    wavelength_front = result.sample_input.wavelength_nm[front_mask]
    fig, ax = plt.subplots(figsize=(10.5, 4.8), dpi=320)
    ax.plot(wavelength_front, result.sample_input.reflectance[front_mask] * 100.0, color="#424242", linewidth=2.3, label="Measured")
    ax.plot(wavelength_front, result.fitted_reflectance[front_mask] * 100.0, color="#b03a2e", linewidth=1.8, linestyle="--", label="Collected fit")
    ax.plot(wavelength_front, result.stage1_result.physical_reflectance[front_mask] * 100.0, color="#1f77b4", linewidth=1.5, linestyle=":", label="Unattenuated physical")
    ax2 = ax.twinx()
    ax2.plot(wavelength_front, result.stage1_result.scatter_curve[front_mask], color="#2e7d32", linewidth=1.4, alpha=0.8, label="S_front")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Absolute Reflectance (%)")
    ax2.set_ylabel("Front Scatter Factor")
    ax.set_title(f"Phase 07 Stage 1 Front Fit: {result.sample_input.sample_name}")
    ax.grid(True, linestyle="--", alpha=0.25)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_rear_window_sanity_check(sample_input: Phase07SampleInput, sanity_check: RearWindowSanityCheck, output_path: Path) -> None:
    rear_mask = sample_input.rear_mask
    wavelength_nm = sample_input.wavelength_nm[rear_mask]
    reflectance = sample_input.reflectance[rear_mask]
    smoothed = savgol_filter(reflectance, window_length=sanity_check.smoothing_window_length, polyorder=sanity_check.smoothing_polyorder)
    fig, axes = plt.subplots(2, 1, figsize=(11.0, 7.0), dpi=320, constrained_layout=True, sharex=True)
    axes[0].plot(wavelength_nm, reflectance * 100.0, color="#9e9e9e", linewidth=1.1, label="Measured")
    axes[0].plot(wavelength_nm, smoothed * 100.0, color="#005b96", linewidth=2.0, label="Smoothed")
    axes[0].axvline(sanity_check.lambda_peak_nm, color="#2e7d32", linestyle="--", linewidth=1.3, label="Peak")
    axes[0].axvline(sanity_check.lambda_valley_nm, color="#c62828", linestyle="--", linewidth=1.3, label="Valley")
    axes[0].set_ylabel("Absolute Reflectance (%)")
    axes[0].set_title(f"Rear-Window Sanity Check: {sample_input.sample_name} | d_estimate={sanity_check.d_estimate_nm:.1f} nm")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend()
    axes[1].plot(wavelength_nm, sanity_check.rear_z_measured, color="#5d4037", linewidth=1.6)
    axes[1].axvline(sanity_check.lambda_peak_nm, color="#2e7d32", linestyle="--", linewidth=1.2)
    axes[1].axvline(sanity_check.lambda_valley_nm, color="#c62828", linestyle="--", linewidth=1.2)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Z-Score Normalized Reflectance")
    axes[1].set_title("Rear Window Z-Score Shape")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_residual_diagnostics(result: Phase07FitResult, output_path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11.0, 7.2), dpi=320, constrained_layout=True, sharex=True)
    for axis in axes:
        _apply_window_background(axis)
    axes[0].plot(result.sample_input.wavelength_nm, result.residual * 100.0, color="#5d4037", linewidth=1.6)
    axes[0].axhline(0.0, color="#546e7a", linewidth=1.0, linestyle="--")
    axes[0].set_ylabel("Residual (%)")
    axes[0].set_title("Raw Residual")
    axes[0].grid(True, linestyle="--", alpha=0.25)

    finite_mask = np.isfinite(result.normalized_residual)
    axes[1].plot(result.sample_input.wavelength_nm[finite_mask], result.normalized_residual[finite_mask], color="#1565c0", linewidth=1.4, label="Normalized residual")
    masked_band = result.sample_input.masked_mask
    axes[1].plot(
        result.sample_input.wavelength_nm[masked_band],
        result.residual[masked_band] * 100.0,
        color="#ef6c00",
        linewidth=1.1,
        alpha=0.9,
        label="Masked visual-only gap",
    )
    axes[1].axhline(0.0, color="#546e7a", linewidth=1.0, linestyle="--")
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Normalized Residual")
    axes[1].set_title("Residual Diagnostics")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_rear_basin_scan(result: Phase07FitResult, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.8, 4.8), dpi=320)
    ax.plot(result.coarse_scan_thickness_nm, result.coarse_scan_cost, color="#1e8449", linewidth=1.8)
    basin_cost = np.interp(result.coarse_scan_basins_nm, result.coarse_scan_thickness_nm, result.coarse_scan_cost)
    ax.scatter(result.coarse_scan_basins_nm, basin_cost, color="#b03a2e", s=40, zorder=3, label="Candidate basins")
    ax.axvline(result.best_params["d_bulk"], color="#283593", linestyle="--", linewidth=1.4, label="Final d_bulk")
    ax.set_xlabel("d_bulk (nm)")
    ax.set_ylabel("Rear-window cost")
    ax.set_title(f"Phase 07 Rear-Window Basin Scan: {result.sample_input.sample_name}")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)
