"""Phase 07 dual-window inversion core.

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
from scipy.optimize import differential_evolution
from tmm import coh_tmm

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, savgol_filter


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
    parameter_specs: tuple[ParameterSpec, ...]

    @classmethod
    def default(cls) -> "Phase07Config":
        return cls(
            parameter_specs=(
                ParameterSpec("d_bulk", 700.0, 580.0, 900.0),
                ParameterSpec("d_rough", 12.0, 0.0, 30.0),
                ParameterSpec("sigma_thickness", 12.0, 0.0, 80.0),
                ParameterSpec("ito_alpha", 1.0, 0.0, 5.0),
                ParameterSpec("pvk_b_scale", 1.0, 0.80, 1.25),
                ParameterSpec("niox_k", 0.0, 0.0, 0.12),
            )
        )

    def get_spec(self, name: str) -> ParameterSpec:
        for spec in self.parameter_specs:
            if spec.name == name:
                return spec
        raise KeyError(f"未知参数: {name}")


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
class Phase07FitResult:
    sample_input: Phase07SampleInput
    fitted_reflectance: np.ndarray
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


def interpolate_complex(
    base_wavelength_nm: np.ndarray,
    base_values: np.ndarray,
    query_wavelength_nm: np.ndarray,
) -> np.ndarray:
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


def apply_niox_k(base_nk: np.ndarray, extra_k: float) -> np.ndarray:
    return np.real(base_nk) + 1j * (np.imag(base_nk) + extra_k)


def compute_remaining_c60_bulk_thickness_nm(d_rough_nm: float) -> float:
    # Roughness is a 50/50 PVK/C60 mixture, so half of its thickness consumes C60 mass.
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
    d_bulk_nm: float,
    d_rough_nm: float,
    d_c60_bulk_nm: float,
) -> tuple[list[complex], list[float]]:
    n_list = [glass_nk, ito_nk, niox_nk, SAM_NK, pvk_nk]
    d_list = [np.inf, ITO_THICKNESS_NM, NIOX_THICKNESS_NM, SAM_THICKNESS_NM, d_bulk_nm]

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
    niox_nk = apply_niox_k(base_niox, niox_k)
    pvk_nk = apply_pvk_b_scale(base_pvk, wavelengths, pvk_b_scale)
    rough_nk = calc_bruggeman_ema_50_50(pvk_nk, base_c60)
    d_c60_bulk_nm = compute_remaining_c60_bulk_thickness_nm(d_rough_nm)
    r_front = calc_front_surface_reflectance(base_glass)
    t_front = 1.0 - r_front

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
                d_bulk_nm=single_d_bulk_nm,
                d_rough_nm=d_rough_nm,
                d_c60_bulk_nm=d_c60_bulk_nm,
            )
            r_stack[index] = float(coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(wavelength_nm))["R"])
        denominator = 1.0 - r_front * r_stack
        if np.any(np.isclose(denominator, 0.0)):
            raise ValueError("厚玻璃非相干级联分母接近 0。")
        return r_front + (t_front**2) * r_stack / denominator

    if sigma_thickness_nm < THICKNESS_AVERAGE_MIN_SIGMA_NM:
        return calc_single_reflectance(d_bulk_nm)

    offsets_nm = np.linspace(
        -3.0 * sigma_thickness_nm,
        3.0 * sigma_thickness_nm,
        THICKNESS_AVERAGE_POINT_COUNT,
        dtype=float,
    )
    weights = np.exp(-(offsets_nm**2) / (2.0 * sigma_thickness_nm**2))
    weights /= np.sum(weights)

    averaged = np.zeros(wavelengths.size, dtype=float)
    for offset_nm, weight in zip(offsets_nm, weights):
        averaged += float(weight) * calc_single_reflectance(d_bulk_nm + float(offset_nm))
    return averaged


def compute_window_scales(sample_input: Phase07SampleInput) -> tuple[WindowScale, ...]:
    outputs: list[WindowScale] = []
    for label, bounds in ((WINDOW_FRONT, FRONT_WINDOW_NM), (WINDOW_REAR, REAR_WINDOW_NM)):
        mask = sample_input.window_label == label
        reflectance = sample_input.reflectance[mask]
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


def build_optimization_sample_input(
    sample_input: Phase07SampleInput,
    stride: int = OPTIMIZATION_WINDOW_STRIDE,
) -> Phase07SampleInput:
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


def compute_rear_derivative_correlation(
    sample_input: Phase07SampleInput,
    modeled_reflectance: np.ndarray,
) -> float:
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


def build_normalized_residual(
    sample_input: Phase07SampleInput,
    modeled_reflectance: np.ndarray,
    window_scales: tuple[WindowScale, ...],
) -> np.ndarray:
    residual = modeled_reflectance - sample_input.reflectance
    normalized = np.full(residual.shape, np.nan, dtype=float)
    scale_map = {item.label: item.scale_value for item in window_scales}
    point_map = {item.label: item.point_count for item in window_scales}
    front_mask = sample_input.window_label == WINDOW_FRONT
    normalized[front_mask] = (
        math.sqrt(0.5 / point_map[WINDOW_FRONT]) * residual[front_mask] / scale_map[WINDOW_FRONT]
    )

    rear_mask = sample_input.window_label == WINDOW_REAR
    rear_z_modeled = compute_zscore(modeled_reflectance[rear_mask])
    rear_z_measured = compute_zscore(sample_input.reflectance[rear_mask])
    normalized[rear_mask] = math.sqrt(0.5 / point_map[WINDOW_REAR]) * (rear_z_modeled - rear_z_measured)
    return normalized


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

    extrema = sorted(
        [(int(index), "peak") for index in peaks] + [(int(index), "valley") for index in valleys],
        key=lambda item: item[0],
    )
    selected_pair: tuple[int, int] | None = None
    selected_types: tuple[str, str] | None = None
    for left, right in zip(extrema, extrema[1:]):
        if left[1] == right[1]:
            continue
        selected_pair = (left[0], right[0])
        selected_types = (left[1], right[1])
        break

    if selected_pair is None or selected_types is None:
        peak_index = int(np.argmax(smoothed))
        valley_index = int(np.argmin(smoothed))
        if peak_index == valley_index:
            raise ValueError("后窗平滑曲线未能识别有效峰谷。")
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
    d_estimate_nm = (lambda_peak_nm * lambda_valley_nm) / (
        4.0 * n_avg_pvk * abs(lambda_peak_nm - lambda_valley_nm)
    )

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


def compute_cost_from_normalized_residual(normalized_residual: np.ndarray) -> float:
    finite = normalized_residual[np.isfinite(normalized_residual)]
    if finite.size == 0:
        raise ValueError("归一化残差为空，无法计算 cost。")
    return float(np.sum(finite**2))


def parameter_vector_to_dict(config: Phase07Config, vector: np.ndarray) -> dict[str, float]:
    return {
        spec.name: float(vector[index])
        for index, spec in enumerate(config.parameter_specs)
    }


def params_to_lmfit_parameters(config: Phase07Config, initial_values: dict[str, float]) -> Parameters:
    params = Parameters()
    for spec in config.parameter_specs:
        params.add(
            spec.name,
            value=float(initial_values[spec.name]),
            min=float(spec.minimum),
            max=float(spec.maximum),
        )
    return params


def evaluate_model_and_cost(
    sample_input: Phase07SampleInput,
    model: Phase07OpticalModel,
    params_dict: dict[str, float],
    window_scales: tuple[WindowScale, ...],
    use_rear_only: bool = False,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    modeled_reflectance = calc_macro_reflectance(
        model=model,
        wavelengths_nm=sample_input.wavelength_nm,
        with_ag=sample_input.with_ag,
        d_bulk_nm=params_dict["d_bulk"],
        d_rough_nm=params_dict["d_rough"],
        sigma_thickness_nm=params_dict["sigma_thickness"],
        ito_alpha=params_dict["ito_alpha"],
        pvk_b_scale=params_dict["pvk_b_scale"],
        niox_k=params_dict["niox_k"],
    )
    normalized_residual = build_normalized_residual(sample_input, modeled_reflectance, window_scales)
    if use_rear_only:
        rear_only = np.full_like(normalized_residual, np.nan)
        rear_only[sample_input.rear_mask] = normalized_residual[sample_input.rear_mask]
        cost = compute_cost_from_normalized_residual(rear_only)
    else:
        cost = compute_cost_from_normalized_residual(normalized_residual)
    derivative_correlation = compute_rear_derivative_correlation(sample_input, modeled_reflectance)
    return modeled_reflectance, normalized_residual, cost, derivative_correlation


def identify_coarse_scan_basins(
    thickness_nm: np.ndarray,
    cost_values: np.ndarray,
) -> np.ndarray:
    candidate_indices: list[int] = []
    for index in range(1, len(cost_values) - 1):
        if cost_values[index] <= cost_values[index - 1] and cost_values[index] <= cost_values[index + 1]:
            candidate_indices.append(index)
    if not candidate_indices:
        candidate_indices = [int(np.argmin(cost_values))]

    ordered_indices = sorted(candidate_indices, key=lambda item: float(cost_values[item]))
    selected_nm: list[float] = []
    for index in ordered_indices:
        value_nm = float(thickness_nm[index])
        if all(abs(value_nm - existing) >= MIN_BASIN_SEPARATION_NM for existing in selected_nm):
            selected_nm.append(value_nm)
        if len(selected_nm) >= MAX_COARSE_BASIN_COUNT:
            break
    return np.asarray(selected_nm, dtype=float)


def residual_for_lmfit(
    params: Parameters,
    sample_input: Phase07SampleInput,
    model: Phase07OpticalModel,
    window_scales: tuple[WindowScale, ...],
) -> np.ndarray:
    param_dict = {name: float(params[name].value) for name in params}
    _, normalized_residual, _, _ = evaluate_model_and_cost(
        sample_input=sample_input,
        model=model,
        params_dict=param_dict,
        window_scales=window_scales,
        use_rear_only=False,
    )
    return normalized_residual[np.isfinite(normalized_residual)]


def fit_dual_window_sample(
    sample_input: Phase07SampleInput,
    model: Phase07OpticalModel,
    config: Phase07Config | None = None,
) -> Phase07FitResult:
    config = config or Phase07Config.default()
    window_scales = compute_window_scales(sample_input)
    optimization_sample_input = build_optimization_sample_input(sample_input)
    optimization_window_scales = compute_window_scales(optimization_sample_input)

    scan_spec = config.get_spec("d_bulk")
    coarse_scan_thickness_nm = np.arange(
        scan_spec.minimum,
        scan_spec.maximum + REAR_D_BULK_SCAN_STEP_NM,
        REAR_D_BULK_SCAN_STEP_NM,
        dtype=float,
    )
    coarse_scan_cost = np.empty_like(coarse_scan_thickness_nm)
    defaults = {spec.name: spec.initial for spec in config.parameter_specs}
    for index, d_bulk_nm in enumerate(coarse_scan_thickness_nm):
        defaults["d_bulk"] = float(d_bulk_nm)
        _, _, cost, _ = evaluate_model_and_cost(
            sample_input=optimization_sample_input,
            model=model,
            params_dict=defaults,
            window_scales=optimization_window_scales,
            use_rear_only=True,
        )
        coarse_scan_cost[index] = cost

    coarse_scan_basins_nm = identify_coarse_scan_basins(coarse_scan_thickness_nm, coarse_scan_cost)
    candidate_summaries: list[dict[str, object]] = []

    for basin_center_nm in coarse_scan_basins_nm:
        basin_bounds: list[tuple[float, float]] = []
        for spec in config.parameter_specs:
            if spec.name == "d_bulk":
                basin_bounds.append(
                    (
                        max(spec.minimum, float(basin_center_nm - REAR_BASIN_HALF_WIDTH_NM)),
                        min(spec.maximum, float(basin_center_nm + REAR_BASIN_HALF_WIDTH_NM)),
                    )
                )
            else:
                basin_bounds.append((spec.minimum, spec.maximum))

        def scalar_cost(vector: np.ndarray) -> float:
            params_dict = parameter_vector_to_dict(config, vector)
            _, _, cost, _ = evaluate_model_and_cost(
                sample_input=optimization_sample_input,
                model=model,
                params_dict=params_dict,
                window_scales=optimization_window_scales,
                use_rear_only=False,
            )
            return cost

        de_result = differential_evolution(
            scalar_cost,
            bounds=basin_bounds,
            seed=DE_SEED,
            maxiter=DE_MAXITER,
            popsize=DE_POPSIZE,
            tol=DE_TOL,
            polish=False,
            updating="deferred",
            workers=1,
        )
        de_params = parameter_vector_to_dict(config, np.asarray(de_result.x, dtype=float))
        lmfit_params = params_to_lmfit_parameters(config, de_params)
        lmfit_result = minimize(
            residual_for_lmfit,
            lmfit_params,
            args=(optimization_sample_input, model, optimization_window_scales),
            method="least_squares",
            max_nfev=80,
        )
        local_params = {
            spec.name: float(lmfit_result.params[spec.name].value)
            for spec in config.parameter_specs
        }
        modeled_reflectance, normalized_residual, total_cost, derivative_correlation = evaluate_model_and_cost(
            sample_input=sample_input,
            model=model,
            params_dict=local_params,
            window_scales=window_scales,
            use_rear_only=False,
        )
        candidate_summaries.append(
            {
                "basin_center_nm": float(basin_center_nm),
                "de_fun": float(de_result.fun),
                "de_nit": int(de_result.nit),
                "de_nfev": int(de_result.nfev),
                "lmfit_nfev": int(lmfit_result.nfev),
                "lmfit_success": bool(lmfit_result.success),
                "total_cost": total_cost,
                "rear_derivative_correlation": derivative_correlation,
                "params": local_params,
                "modeled_reflectance": modeled_reflectance,
                "normalized_residual": normalized_residual,
            }
        )

    best_cost = min(float(item["total_cost"]) for item in candidate_summaries)
    tied_candidates = [
        item
        for item in candidate_summaries
        if float(item["total_cost"]) <= max(best_cost * (1.0 + TIE_BREAK_COST_REL_TOL), best_cost + TIE_BREAK_COST_ABS_TOL)
    ]
    chosen_candidate = max(
        tied_candidates,
        key=lambda item: (float(item["rear_derivative_correlation"]), -float(item["total_cost"])),
    )

    best_params = dict(chosen_candidate["params"])
    fitted_reflectance = np.asarray(chosen_candidate["modeled_reflectance"], dtype=float)
    normalized_residual = np.asarray(chosen_candidate["normalized_residual"], dtype=float)
    residual = fitted_reflectance - sample_input.reflectance
    masked_residual = residual[sample_input.masked_mask]
    masked_stats = MaskedResidualStats(
        mean=float(np.mean(masked_residual)),
        std=float(np.std(masked_residual)),
        max_abs=float(np.max(np.abs(masked_residual))),
    )

    front_cost = compute_cost_from_normalized_residual(
        np.where(sample_input.front_mask, normalized_residual, np.nan)
    )
    rear_cost = compute_cost_from_normalized_residual(
        np.where(sample_input.rear_mask, normalized_residual, np.nan)
    )
    d_c60_bulk_best = compute_remaining_c60_bulk_thickness_nm(best_params["d_rough"])

    bound_hit_flags: dict[str, bool] = {}
    warnings: list[str] = []
    for spec in config.parameter_specs:
        span = spec.maximum - spec.minimum
        tolerance = PARAMETER_BOUND_TOLERANCE_RATIO * span
        value = best_params[spec.name]
        hit = (value - spec.minimum) <= tolerance or (spec.maximum - value) <= tolerance
        bound_hit_flags[spec.name] = bool(hit)
        if hit:
            warnings.append(f"{spec.name} 接近边界")
    if np.isclose(d_c60_bulk_best, 0.0):
        warnings.append("d_C60_bulk 退化到 0 nm，粗糙层已耗尽致密 C60")
    if d_c60_bulk_best == 0.0 and rear_cost > 0.02:
        warnings.append("C60 退化后后窗残差仍偏大，可能存在结构未充分约束")

    optimizer_stage_summary = tuple(
        {
            "basin_center_nm": float(item["basin_center_nm"]),
            "de_fun": float(item["de_fun"]),
            "de_nit": int(item["de_nit"]),
            "de_nfev": int(item["de_nfev"]),
            "lmfit_nfev": int(item["lmfit_nfev"]),
            "lmfit_success": bool(item["lmfit_success"]),
            "total_cost": float(item["total_cost"]),
            "rear_derivative_correlation": float(item["rear_derivative_correlation"]),
            "params": {
                key: float(value)
                for key, value in dict(item["params"]).items()
            },
        }
        for item in candidate_summaries
    )

    return Phase07FitResult(
        sample_input=sample_input,
        fitted_reflectance=fitted_reflectance,
        residual=residual,
        normalized_residual=normalized_residual,
        best_params=best_params,
        d_c60_bulk_best=d_c60_bulk_best,
        window_scales=window_scales,
        window_cost_front=front_cost,
        window_cost_rear=rear_cost,
        total_cost=float(chosen_candidate["total_cost"]),
        masked_band_residual_stats=masked_stats,
        rear_derivative_correlation=float(chosen_candidate["rear_derivative_correlation"]),
        coarse_scan_thickness_nm=coarse_scan_thickness_nm,
        coarse_scan_cost=coarse_scan_cost,
        coarse_scan_basins_nm=coarse_scan_basins_nm,
        optimizer_stage_summary=optimizer_stage_summary,
        bound_hit_flags=bound_hit_flags,
        warnings=tuple(warnings),
        rear_z_measured=compute_zscore(sample_input.reflectance[sample_input.rear_mask]),
        rear_z_fitted=compute_zscore(fitted_reflectance[sample_input.rear_mask]),
    )


def export_fit_curve_table(result: Phase07FitResult, output_path: Path) -> None:
    rear_z_measured = np.full(result.sample_input.wavelength_nm.shape, np.nan, dtype=float)
    rear_z_fitted = np.full(result.sample_input.wavelength_nm.shape, np.nan, dtype=float)
    rear_z_measured[result.sample_input.rear_mask] = result.rear_z_measured
    rear_z_fitted[result.sample_input.rear_mask] = result.rear_z_fitted
    frame = pd.DataFrame(
        {
            "Wavelength_nm": result.sample_input.wavelength_nm,
            "Absolute_Reflectance_Measured": result.sample_input.reflectance,
            "Absolute_Reflectance_Fitted": result.fitted_reflectance,
            "Residual": result.residual,
            "Normalized_Residual": result.normalized_residual,
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
        "d_C60_bulk_best": result.d_c60_bulk_best,
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
        payload[f"{scale.label}_scale"] = scale.scale_value
        payload[f"{scale.label}_point_count"] = scale.point_count
    pd.DataFrame([payload]).to_csv(output_path, index=False, encoding="utf-8-sig")


def write_optimizer_log(result: Phase07FitResult, output_path: Path) -> None:
    lines = [
        f"# Phase 07 Dual-Window Inversion Log: {result.sample_input.sample_name}",
        "",
        "## Sample",
        "",
        f"- source_mode: `{result.sample_input.source_mode}`",
        f"- source_path: `{result.sample_input.source_path}`",
        f"- with_ag: `{result.sample_input.with_ag}`",
        "",
        "## Window Scales",
        "",
    ]
    for scale in result.window_scales:
        lines.extend(
            [
                f"- {scale.label}: n=`{scale.point_count}`, median=`{scale.median_reflectance:.6f}`, "
                f"MAD=`{scale.mad_reflectance:.6f}`, scale=`{scale.scale_value:.6f}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Best Parameters",
            "",
        ]
    )
    for key, value in result.best_params.items():
        lines.append(f"- {key}: `{value:.6f}`")
    lines.extend(
        [
            f"- d_C60_bulk_best: `{result.d_c60_bulk_best:.6f}` nm",
            f"- window_cost_front: `{result.window_cost_front:.6f}`",
            f"- window_cost_rear: `{result.window_cost_rear:.6f}`",
            f"- total_cost: `{result.total_cost:.6f}`",
            f"- rear_derivative_correlation: `{result.rear_derivative_correlation:.6f}`",
            "",
            "## Masked Band Residual",
            "",
            f"- mean: `{result.masked_band_residual_stats.mean:.6e}`",
            f"- std: `{result.masked_band_residual_stats.std:.6e}`",
            f"- max_abs: `{result.masked_band_residual_stats.max_abs:.6e}`",
            "",
            "## Coarse Basin Candidates",
            "",
            f"- basins_nm: `{[float(value) for value in result.coarse_scan_basins_nm]}`",
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


def plot_measured_vs_fitted_full_spectrum(result: Phase07FitResult, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.0, 5.6), dpi=320)
    _apply_window_background(ax)
    ax.plot(
        result.sample_input.wavelength_nm,
        result.sample_input.reflectance * 100.0,
        color="#424242",
        linewidth=2.4,
        label="Measured",
    )
    ax.plot(
        result.sample_input.wavelength_nm,
        result.fitted_reflectance * 100.0,
        color="#005b96",
        linewidth=1.8,
        linestyle="--",
        label="Fitted",
    )
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Absolute Reflectance (%)")
    ax.set_title(f"Phase 07 Dual-Window Fit: {result.sample_input.sample_name}")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_dual_window_zoom(result: Phase07FitResult, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), dpi=320, constrained_layout=True)
    front_mask = result.sample_input.front_mask
    axes[0].plot(
        result.sample_input.wavelength_nm[front_mask],
        result.sample_input.reflectance[front_mask] * 100.0,
        color="#424242",
        linewidth=2.3,
        label="Measured",
    )
    axes[0].plot(
        result.sample_input.wavelength_nm[front_mask],
        result.fitted_reflectance[front_mask] * 100.0,
        color="#b03a2e",
        linewidth=1.8,
        linestyle="--",
        label="Fitted",
    )
    axes[0].set_xlim(FRONT_WINDOW_NM[0], FRONT_WINDOW_NM[1])
    axes[0].set_xlabel("Wavelength (nm)")
    axes[0].set_ylabel("Absolute Reflectance (%)")
    axes[0].set_title("Front Window")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend()

    rear_mask = result.sample_input.rear_mask
    rear_wavelength_nm = result.sample_input.wavelength_nm[rear_mask]
    axes[1].plot(
        rear_wavelength_nm,
        result.rear_z_measured,
        color="#424242",
        linewidth=2.3,
        label="z_meas",
    )
    axes[1].plot(
        rear_wavelength_nm,
        result.rear_z_fitted,
        color="#005b96",
        linewidth=1.8,
        linestyle="--",
        label="z_model",
    )
    axes[1].set_xlim(REAR_WINDOW_NM[0], REAR_WINDOW_NM[1])
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Z-Score Normalized Reflectance")
    axes[1].set_title("Rear Window")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_rear_window_sanity_check(
    sample_input: Phase07SampleInput,
    sanity_check: RearWindowSanityCheck,
    output_path: Path,
) -> None:
    rear_mask = sample_input.rear_mask
    wavelength_nm = sample_input.wavelength_nm[rear_mask]
    reflectance = sample_input.reflectance[rear_mask]
    smoothed = savgol_filter(
        reflectance,
        window_length=sanity_check.smoothing_window_length,
        polyorder=sanity_check.smoothing_polyorder,
    )

    fig, axes = plt.subplots(2, 1, figsize=(11.0, 7.0), dpi=320, constrained_layout=True, sharex=True)
    axes[0].plot(wavelength_nm, reflectance * 100.0, color="#9e9e9e", linewidth=1.1, label="Measured")
    axes[0].plot(wavelength_nm, smoothed * 100.0, color="#005b96", linewidth=2.0, label="Smoothed")
    axes[0].axvline(sanity_check.lambda_peak_nm, color="#2e7d32", linestyle="--", linewidth=1.3, label="Peak")
    axes[0].axvline(sanity_check.lambda_valley_nm, color="#c62828", linestyle="--", linewidth=1.3, label="Valley")
    axes[0].set_ylabel("Absolute Reflectance (%)")
    axes[0].set_title(
        f"Rear-Window Sanity Check: {sample_input.sample_name} | "
        f"d_estimate={sanity_check.d_estimate_nm:.1f} nm"
    )
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
    axes[1].plot(
        result.sample_input.wavelength_nm[finite_mask],
        result.normalized_residual[finite_mask],
        color="#1565c0",
        linewidth=1.4,
        label="Normalized residual",
    )
    masked_band = result.sample_input.masked_mask
    axes[1].plot(
        result.sample_input.wavelength_nm[masked_band],
        result.residual[masked_band] * 100.0,
        color="#ef6c00",
        linewidth=1.1,
        alpha=0.9,
        label="Masked PL residual (%)",
    )
    axes[1].axhline(0.0, color="#546e7a", linewidth=1.0, linestyle="--")
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Normalized Residual")
    axes[1].set_title("Normalized Residual + Masked PL Band")
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
