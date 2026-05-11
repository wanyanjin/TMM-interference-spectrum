from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SiReferenceCurveResult:
    wavelength_nm: np.ndarray
    n_si: np.ndarray
    k_si: np.ndarray
    r_air_si: np.ndarray
    oxide_curves: dict[str, np.ndarray]
    metadata: dict[str, object]
