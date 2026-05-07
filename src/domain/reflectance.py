from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from domain.qc import QCSummary


@dataclass(frozen=True)
class ReferenceReflectance:
    wavelength_nm: np.ndarray
    reflectance: np.ndarray
    reference_type: str = "unity"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReflectanceQCConfig:
    wavelength_min_nm: float | None = None
    wavelength_max_nm: float | None = None
    exposure_normalization_enabled: bool = False
    subtract_dark_enabled: bool = False
    reference_low_threshold_counts: float | None = None
    saturation_threshold_counts: float = 60000.0
    reflectance_warn_upper: float = 1.05
    reflectance_fail_upper: float = 1.20
    reflectance_lower_fail: float = -0.02


@dataclass(frozen=True)
class ReflectanceQCResult:
    wavelength_nm: np.ndarray
    reference_intensity_raw: np.ndarray
    sample_intensity_raw: np.ndarray
    reference_intensity_processed: np.ndarray
    sample_intensity_processed: np.ndarray
    reference_reflectance: np.ndarray
    sample_reference_ratio: np.ndarray
    calculated_reflectance: np.ndarray
    valid_mask: np.ndarray
    mask_reason: list[str]
    qc_summary: QCSummary
    metadata: dict[str, Any] = field(default_factory=dict)
