from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.exceptions import DataModelError
from domain.spectrum import SpectrumData


def test_spectrum_data_accepts_matching_shapes() -> None:
    spectrum = SpectrumData(
        wavelength_nm=np.array([500.0, 501.0]),
        intensity=np.array([1.0, 2.0]),
        exposure_ms=20.0,
    )
    assert spectrum.exposure_ms == 20.0


def test_spectrum_data_rejects_shape_mismatch() -> None:
    with pytest.raises(DataModelError):
        SpectrumData(
            wavelength_nm=np.array([500.0, 501.0]),
            intensity=np.array([1.0]),
        )
