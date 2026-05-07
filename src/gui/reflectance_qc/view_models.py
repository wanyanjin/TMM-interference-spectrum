from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd

XRangePreset = Literal["full", "400-750", "500-700", "500-750", "custom"]
YMode = Literal["full_auto", "robust_auto", "physical_range", "manual"]
ViewName = Literal["reflectance", "ratio", "intensity"]

REQUIRED_COLUMNS = ("wavelength_nm", "calculated_reflectance")
RECOMMENDED_COLUMNS = (
    "sample_reference_ratio",
    "reference_intensity_processed",
    "sample_intensity_processed",
    "valid_mask",
    "mask_reason",
)
OPTIONAL_COLUMNS = (
    "reference_intensity_raw",
    "sample_intensity_raw",
    "reference_reflectance",
)


@dataclass(frozen=True)
class ReflectanceQCViewSettings:
    x_preset: XRangePreset = "500-700"
    x_min: float | None = 500.0
    x_max: float | None = 700.0
    y_mode: YMode = "robust_auto"
    y_min: float | None = None
    y_max: float | None = None
    active_view: ViewName = "reflectance"
    highlighted_flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReflectanceQCWindowMetrics:
    wavelength_min: float
    wavelength_max: float
    point_count: int
    valid_point_count: int
    invalid_fraction: float
    median_reflectance: float | None
    mean_reflectance: float | None
    reflectance_600nm: float | None
    reflectance_600nm_note: str | None
    reflectance_gt_1p2_fraction: float
    reflectance_lt_0_fraction: float
    non_finite_count: int
    reference_low_fraction: float


@dataclass(frozen=True)
class ReflectanceQCLoadedData:
    dataframe: pd.DataFrame
    required_columns: tuple[str, ...]
    missing_recommended_columns: tuple[str, ...]
    missing_optional_columns: tuple[str, ...]
    warnings: list[str] = field(default_factory=list)


def validate_processed_reflectance_schema(columns: list[str]) -> dict[str, Any]:
    missing_required = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing_required:
        raise ValueError(
            "Missing required columns in processed_reflectance.csv: "
            + ", ".join(missing_required)
        )
    missing_recommended = [column for column in RECOMMENDED_COLUMNS if column not in columns]
    missing_optional = [column for column in OPTIONAL_COLUMNS if column not in columns]
    return {
        "required_columns": REQUIRED_COLUMNS,
        "missing_recommended_columns": tuple(missing_recommended),
        "missing_optional_columns": tuple(missing_optional),
    }


def resolve_x_range(
    preset: XRangePreset,
    custom_min: float | None,
    custom_max: float | None,
    wavelength_values: np.ndarray,
) -> tuple[float, float]:
    wavelength_values = np.asarray(wavelength_values, dtype=float)
    finite = wavelength_values[np.isfinite(wavelength_values)]
    if finite.size == 0:
        raise ValueError("No finite wavelength points available.")
    minimum = float(finite.min())
    maximum = float(finite.max())

    if preset == "full":
        return minimum, maximum
    if preset == "400-750":
        return 400.0, 750.0
    if preset == "500-700":
        return 500.0, 700.0
    if preset == "500-750":
        return 500.0, 750.0
    if preset == "custom":
        if custom_min is None or custom_max is None:
            raise ValueError("Custom x-range requires both min and max.")
        if not np.isfinite(custom_min) or not np.isfinite(custom_max):
            raise ValueError("Custom x-range must be finite numbers.")
        if custom_min >= custom_max:
            raise ValueError("Custom x-range requires min < max.")
        return float(custom_min), float(custom_max)
    raise ValueError(f"Unsupported x-range preset: {preset}")


def filter_visible_rows(data: pd.DataFrame, x_range: tuple[float, float]) -> pd.DataFrame:
    x_min, x_max = x_range
    mask = (
        pd.to_numeric(data["wavelength_nm"], errors="coerce").notna()
        & (data["wavelength_nm"] >= x_min)
        & (data["wavelength_nm"] <= x_max)
    )
    return data.loc[mask].copy()


def classify_anomaly_points(data: pd.DataFrame) -> dict[str, pd.Series]:
    reflectance = pd.to_numeric(data.get("calculated_reflectance"), errors="coerce")
    finite_reflectance = np.isfinite(reflectance)
    valid_mask = _as_bool_series(data.get("valid_mask"), len(data), default=True)
    mask_reason = data.get("mask_reason", pd.Series(["ok"] * len(data))).astype(str).str.lower()
    reference_processed = pd.to_numeric(
        data.get("reference_intensity_processed"), errors="coerce"
    )
    reference_finite = np.isfinite(reference_processed)

    return {
        "non_finite_reflectance": pd.Series(~finite_reflectance, index=data.index),
        "reflectance_lt_0": pd.Series(finite_reflectance & (reflectance < 0.0), index=data.index),
        "reflectance_gt_1p2": pd.Series(
            finite_reflectance & (reflectance > 1.2), index=data.index
        ),
        "invalid_mask": pd.Series(~valid_mask, index=data.index),
        "mask_reason_not_ok": pd.Series(mask_reason != "ok", index=data.index),
        "reference_non_finite": pd.Series(~reference_finite, index=data.index),
        "reference_nonpositive": pd.Series(
            reference_finite & (reference_processed <= 0.0), index=data.index
        ),
    }


def compute_robust_y_limits(
    values: np.ndarray,
    valid_mask: np.ndarray,
) -> tuple[tuple[float, float] | None, str | None]:
    values = np.asarray(values, dtype=float)
    valid_mask = np.asarray(valid_mask, dtype=bool)
    usable = values[np.isfinite(values) & valid_mask]
    if usable.size < 10:
        return None, "too_few_valid_points"

    lower = float(np.percentile(usable, 1))
    upper = float(np.percentile(usable, 99))
    if not np.isfinite(lower) or not np.isfinite(upper):
        return None, "non_finite_percentile"
    if upper <= lower:
        return None, "flat_or_invalid_range"

    margin = 0.05 * (upper - lower)
    return (lower - margin, upper + margin), None


def compute_full_auto_y_limits(values: np.ndarray) -> tuple[float, float] | None:
    values = np.asarray(values, dtype=float)
    usable = values[np.isfinite(values)]
    if usable.size == 0:
        return None
    minimum = float(usable.min())
    maximum = float(usable.max())
    if maximum <= minimum:
        margin = 0.05 * (abs(minimum) if minimum != 0 else 1.0)
        return minimum - margin, maximum + margin
    margin = 0.05 * (maximum - minimum)
    return minimum - margin, maximum + margin


def compute_current_window_qc(
    data: pd.DataFrame,
    x_range: tuple[float, float],
) -> ReflectanceQCWindowMetrics:
    visible = filter_visible_rows(data, x_range)
    point_count = int(len(visible))
    if point_count == 0:
        return ReflectanceQCWindowMetrics(
            wavelength_min=x_range[0],
            wavelength_max=x_range[1],
            point_count=0,
            valid_point_count=0,
            invalid_fraction=1.0,
            median_reflectance=None,
            mean_reflectance=None,
            reflectance_600nm=None,
            reflectance_600nm_note="N/A, no points in current window",
            reflectance_gt_1p2_fraction=0.0,
            reflectance_lt_0_fraction=0.0,
            non_finite_count=0,
            reference_low_fraction=0.0,
        )

    reflectance = pd.to_numeric(visible["calculated_reflectance"], errors="coerce")
    finite_reflectance = np.isfinite(reflectance.to_numpy(dtype=float))
    valid_mask = _as_bool_series(visible.get("valid_mask"), point_count, default=True)
    valid_reflectance = finite_reflectance & valid_mask
    valid_point_count = int(np.count_nonzero(valid_reflectance))
    invalid_fraction = float(1.0 - (valid_point_count / point_count))

    median_reflectance = (
        float(np.median(reflectance[valid_reflectance])) if valid_point_count else None
    )
    mean_reflectance = (
        float(np.mean(reflectance[valid_reflectance])) if valid_point_count else None
    )

    reflectance_600nm, reflectance_600nm_note = _reflectance_near_600nm(
        visible, reflectance.to_numpy(dtype=float), finite_reflectance
    )
    gt_1p2_fraction = float(
        np.count_nonzero(finite_reflectance & (reflectance.to_numpy(dtype=float) > 1.2))
        / point_count
    )
    lt_0_fraction = float(
        np.count_nonzero(finite_reflectance & (reflectance.to_numpy(dtype=float) < 0.0))
        / point_count
    )
    non_finite_count = int(np.count_nonzero(~finite_reflectance))

    reference_low_mask = _reference_low_mask(visible)
    reference_low_fraction = float(np.count_nonzero(reference_low_mask) / point_count)

    return ReflectanceQCWindowMetrics(
        wavelength_min=float(x_range[0]),
        wavelength_max=float(x_range[1]),
        point_count=point_count,
        valid_point_count=valid_point_count,
        invalid_fraction=invalid_fraction,
        median_reflectance=median_reflectance,
        mean_reflectance=mean_reflectance,
        reflectance_600nm=reflectance_600nm,
        reflectance_600nm_note=reflectance_600nm_note,
        reflectance_gt_1p2_fraction=gt_1p2_fraction,
        reflectance_lt_0_fraction=lt_0_fraction,
        non_finite_count=non_finite_count,
        reference_low_fraction=reference_low_fraction,
    )


def _as_bool_series(series: Any, length: int, default: bool) -> np.ndarray:
    if series is None:
        return np.full(length, default, dtype=bool)
    if isinstance(series, pd.Series):
        lowered = series.astype(str).str.strip().str.lower()
    else:
        lowered = pd.Series(series).astype(str).str.strip().str.lower()
    true_values = {"true", "1", "yes", "y"}
    false_values = {"false", "0", "no", "n"}
    result = np.full(len(lowered), default, dtype=bool)
    for idx, value in enumerate(lowered):
        if value in true_values:
            result[idx] = True
        elif value in false_values:
            result[idx] = False
        else:
            result[idx] = default
    return result


def _reflectance_near_600nm(
    visible: pd.DataFrame,
    reflectance: np.ndarray,
    finite_reflectance: np.ndarray,
) -> tuple[float | None, str | None]:
    wavelengths = pd.to_numeric(visible["wavelength_nm"], errors="coerce").to_numpy(dtype=float)
    finite_wavelengths = np.isfinite(wavelengths)
    if not (wavelengths.min() <= 600.0 <= wavelengths.max()):
        return None, "N/A, 600 nm outside current window"
    candidate_mask = finite_wavelengths & finite_reflectance
    if not np.any(candidate_mask):
        return None, "N/A, no finite point near 600 nm"
    candidate_indices = np.where(candidate_mask)[0]
    nearest = candidate_indices[np.argmin(np.abs(wavelengths[candidate_indices] - 600.0))]
    return float(reflectance[nearest]), None


def _reference_low_mask(data: pd.DataFrame) -> np.ndarray:
    if "mask_reason" in data.columns:
        reason = data["mask_reason"].astype(str).str.lower().to_numpy()
        return reason == "reference_below_threshold"
    reference = pd.to_numeric(data.get("reference_intensity_processed"), errors="coerce")
    finite = np.isfinite(reference.to_numpy(dtype=float))
    values = reference.to_numpy(dtype=float)
    return (~finite) | (values <= 0.0)

