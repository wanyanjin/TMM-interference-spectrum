from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from common.exceptions import DataModelError


@dataclass(frozen=True)
class Axis:
    values: np.ndarray
    unit: str
    name: str = "wavelength"


@dataclass(frozen=True)
class SpectrumData:
    wavelength_nm: np.ndarray
    intensity: np.ndarray
    label: str = ""
    exposure_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.wavelength_nm.shape != self.intensity.shape:
            raise DataModelError("wavelength_nm and intensity must have the same shape")
