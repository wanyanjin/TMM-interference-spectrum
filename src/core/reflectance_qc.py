from __future__ import annotations

from typing import Any

import numpy as np

from domain.qc import QCFlag, QCSummary
from domain.reflectance import (
    ReferenceReflectance,
    ReflectanceQCConfig,
    ReflectanceQCResult,
)
from domain.spectrum import SpectrumData


def align_spectra_to_common_grid(
    sample: SpectrumData,
    reference: SpectrumData,
    wavelength_min_nm: float | None = None,
    wavelength_max_nm: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    sample_order = np.argsort(sample.wavelength_nm)
    reference_order = np.argsort(reference.wavelength_nm)

    sample_wavelength = sample.wavelength_nm[sample_order]
    sample_intensity = sample.intensity[sample_order]
    reference_wavelength = reference.wavelength_nm[reference_order]
    reference_intensity = reference.intensity[reference_order]

    lower_bound = max(sample_wavelength.min(), reference_wavelength.min())
    upper_bound = min(sample_wavelength.max(), reference_wavelength.max())
    if wavelength_min_nm is not None:
        lower_bound = max(lower_bound, wavelength_min_nm)
    if wavelength_max_nm is not None:
        upper_bound = min(upper_bound, wavelength_max_nm)

    if lower_bound > upper_bound:
        raise ValueError("No overlapping wavelength range after applying bounds")

    sample_mask = (sample_wavelength >= lower_bound) & (sample_wavelength <= upper_bound)
    sample_grid = sample_wavelength[sample_mask]
    if sample_grid.size == 0:
        raise ValueError("Sample spectrum has no points inside the common wavelength range")

    reference_aligned = np.interp(sample_grid, reference_wavelength, reference_intensity)
    sample_aligned = sample_intensity[sample_mask]
    interpolation_used = not np.array_equal(sample_grid, reference_wavelength[(reference_wavelength >= lower_bound) & (reference_wavelength <= upper_bound)])

    metadata = {
        "interpolation_used": interpolation_used,
        "alignment_basis": "sample_grid",
        "wavelength_min_nm": float(lower_bound),
        "wavelength_max_nm": float(upper_bound),
        "point_count": int(sample_grid.size),
    }
    return sample_grid, sample_aligned, reference_aligned, metadata


def compute_reflectance_qc(
    sample: SpectrumData,
    reference: SpectrumData,
    config: ReflectanceQCConfig,
    reference_reflectance: ReferenceReflectance | None = None,
) -> ReflectanceQCResult:
    wavelength_nm, sample_raw, reference_raw, alignment_meta = align_spectra_to_common_grid(
        sample=sample,
        reference=reference,
        wavelength_min_nm=config.wavelength_min_nm,
        wavelength_max_nm=config.wavelength_max_nm,
    )

    sample_processed = sample_raw.astype(float, copy=True)
    reference_processed = reference_raw.astype(float, copy=True)

    if config.exposure_normalization_enabled:
        if sample.exposure_ms is None or reference.exposure_ms is None:
            raise ValueError("Exposure normalization requires exposure_ms on both sample and reference spectra")
        sample_processed = sample_processed / sample.exposure_ms
        reference_processed = reference_processed / reference.exposure_ms

    if reference_reflectance is None:
        reference_reflectance_values = np.ones_like(wavelength_nm, dtype=float)
        reference_meta = {"reference_type": "unity"}
    else:
        ref_order = np.argsort(reference_reflectance.wavelength_nm)
        ref_wavelength = reference_reflectance.wavelength_nm[ref_order]
        ref_values = reference_reflectance.reflectance[ref_order]
        reference_reflectance_values = np.interp(wavelength_nm, ref_wavelength, ref_values)
        reference_meta = {
            "reference_type": reference_reflectance.reference_type,
            "reference_metadata": reference_reflectance.metadata,
        }

    ratio = np.full_like(sample_processed, np.nan, dtype=float)
    valid_reference = reference_processed > 0
    ratio[valid_reference] = sample_processed[valid_reference] / reference_processed[valid_reference]
    calculated_reflectance = ratio * reference_reflectance_values

    reference_low_mask = np.zeros_like(reference_processed, dtype=bool)
    if config.reference_low_threshold_counts is not None:
        reference_low_mask = reference_processed < config.reference_low_threshold_counts

    valid_mask = np.ones_like(sample_processed, dtype=bool)
    mask_reason: list[str] = []
    for index in range(sample_processed.size):
        reason = "ok"
        if not np.isfinite(sample_processed[index]) or not np.isfinite(reference_processed[index]):
            reason = "non_finite"
        elif reference_processed[index] <= 0:
            reason = "reference_nonpositive"
        elif sample_processed[index] <= 0:
            reason = "sample_nonpositive"
        elif reference_low_mask[index]:
            reason = "reference_below_threshold"
        elif not np.isfinite(calculated_reflectance[index]):
            reason = "reflectance_non_finite"

        mask_reason.append(reason)
        valid_mask[index] = reason == "ok"

    total_points = int(wavelength_nm.size)
    valid_point_count = int(np.count_nonzero(valid_mask))

    reference_saturation_mask = reference_processed >= config.saturation_threshold_counts
    sample_saturation_mask = sample_processed >= config.saturation_threshold_counts
    reflectance_lt_fail = np.isfinite(calculated_reflectance) & (
        calculated_reflectance < config.reflectance_lower_fail
    )
    reflectance_gt_warn = np.isfinite(calculated_reflectance) & (
        calculated_reflectance > config.reflectance_warn_upper
    )
    reflectance_gt_fail = np.isfinite(calculated_reflectance) & (
        calculated_reflectance > config.reflectance_fail_upper
    )

    band_mask = (
        valid_mask
        & (wavelength_nm >= 500.0)
        & (wavelength_nm <= 750.0)
        & np.isfinite(calculated_reflectance)
    )
    median_reflectance_500_750 = float(np.nanmedian(calculated_reflectance[band_mask])) if np.any(band_mask) else float("nan")
    reflectance_600nm = float(np.interp(600.0, wavelength_nm, calculated_reflectance)) if total_points > 0 else float("nan")

    metrics = {
        "point_count": float(total_points),
        "valid_point_count": float(valid_point_count),
        "invalid_fraction": float(1.0 - (valid_point_count / total_points if total_points else 0.0)),
        "reference_low_fraction": float(np.count_nonzero(reference_low_mask) / total_points if total_points else 0.0),
        "reference_near_saturation_fraction": float(np.count_nonzero(reference_saturation_mask) / total_points if total_points else 0.0),
        "sample_near_saturation_fraction": float(np.count_nonzero(sample_saturation_mask) / total_points if total_points else 0.0),
        "reflectance_lt_minus_0p02_fraction": float(np.count_nonzero(reflectance_lt_fail) / total_points if total_points else 0.0),
        "reflectance_gt_1p05_fraction": float(np.count_nonzero(reflectance_gt_warn) / total_points if total_points else 0.0),
        "reflectance_gt_1p2_fraction": float(np.count_nonzero(reflectance_gt_fail) / total_points if total_points else 0.0),
        "median_reflectance_500_750": median_reflectance_500_750,
        "reflectance_600nm": reflectance_600nm,
    }

    flags: list[QCFlag] = []
    if metrics["reflectance_gt_1p2_fraction"] > 0.01:
        flags.append(QCFlag(name="reflectance_gt_1p2", severity="fail", message="More than 1% of points exceed reflectance 1.20"))
    if metrics["reflectance_lt_minus_0p02_fraction"] > 0.01:
        flags.append(QCFlag(name="reflectance_lt_minus_0p02", severity="fail", message="More than 1% of points fall below reflectance -0.02"))
    if valid_point_count < 10:
        flags.append(QCFlag(name="too_few_valid_points", severity="fail", message="Valid point count is below 10"))
    if metrics["reflectance_gt_1p05_fraction"] > 0.01:
        flags.append(QCFlag(name="reflectance_gt_1p05", severity="warn", message="More than 1% of points exceed reflectance 1.05"))
    if metrics["reference_low_fraction"] > 0.05:
        flags.append(QCFlag(name="reference_low_fraction", severity="warn", message="Reference low-count fraction exceeds 5%"))
    if metrics["reference_near_saturation_fraction"] > 0.01:
        flags.append(QCFlag(name="reference_near_saturation", severity="warn", message="Reference spectrum approaches saturation"))
    if metrics["sample_near_saturation_fraction"] > 0.01:
        flags.append(QCFlag(name="sample_near_saturation", severity="warn", message="Sample spectrum approaches saturation"))

    if (
        metrics["reflectance_gt_1p2_fraction"] > 0.01
        or metrics["reflectance_lt_minus_0p02_fraction"] > 0.01
        or valid_point_count < 10
    ):
        overall_status = "FAIL"
    elif (
        metrics["reflectance_gt_1p05_fraction"] > 0.01
        or metrics["reference_low_fraction"] > 0.05
        or metrics["reference_near_saturation_fraction"] > 0.01
        or metrics["sample_near_saturation_fraction"] > 0.01
    ):
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    qc_summary = QCSummary(
        overall_status=overall_status,
        metrics=metrics,
        flags=flags,
        metadata={
            **alignment_meta,
            **reference_meta,
            "exposure_normalization_enabled": config.exposure_normalization_enabled,
        },
    )

    return ReflectanceQCResult(
        wavelength_nm=wavelength_nm,
        reference_intensity_raw=reference_raw,
        sample_intensity_raw=sample_raw,
        reference_intensity_processed=reference_processed,
        sample_intensity_processed=sample_processed,
        reference_reflectance=reference_reflectance_values,
        sample_reference_ratio=ratio,
        calculated_reflectance=calculated_reflectance,
        valid_mask=valid_mask,
        mask_reason=mask_reason,
        qc_summary=qc_summary,
        metadata={
            "sample_label": sample.label,
            "reference_label": reference.label,
        },
    )
