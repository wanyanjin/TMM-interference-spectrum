from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.reflectance_qc import compute_reflectance_qc
from domain.reflectance import ReflectanceQCConfig
from domain.spectrum import SpectrumData


def test_compute_reflectance_qc_basic_ratio() -> None:
    sample = SpectrumData(
        wavelength_nm=np.linspace(500.0, 720.0, 12),
        intensity=np.full(12, 10.0),
        exposure_ms=10.0,
    )
    reference = SpectrumData(
        wavelength_nm=np.linspace(500.0, 720.0, 12),
        intensity=np.full(12, 20.0),
        exposure_ms=20.0,
    )
    result = compute_reflectance_qc(
        sample,
        reference,
        ReflectanceQCConfig(exposure_normalization_enabled=True),
    )
    assert np.allclose(result.calculated_reflectance, np.ones(12))
    assert result.qc_summary.overall_status == "PASS"


def test_compute_reflectance_qc_interpolates_reference() -> None:
    sample = SpectrumData(
        wavelength_nm=np.array([500.0, 550.0, 600.0]),
        intensity=np.array([10.0, 12.0, 14.0]),
    )
    reference = SpectrumData(
        wavelength_nm=np.array([500.0, 600.0]),
        intensity=np.array([20.0, 28.0]),
    )
    result = compute_reflectance_qc(sample, reference, ReflectanceQCConfig())
    assert np.allclose(result.reference_intensity_raw, [20.0, 24.0, 28.0])


def test_compute_reflectance_qc_masks_nonpositive_reference() -> None:
    sample = SpectrumData(
        wavelength_nm=np.array([500.0, 600.0, 700.0]),
        intensity=np.array([10.0, 20.0, 30.0]),
    )
    reference = SpectrumData(
        wavelength_nm=np.array([500.0, 600.0, 700.0]),
        intensity=np.array([20.0, 0.0, -1.0]),
    )
    result = compute_reflectance_qc(sample, reference, ReflectanceQCConfig())
    assert result.mask_reason == ["ok", "reference_nonpositive", "reference_nonpositive"]
    assert result.valid_mask.tolist() == [True, False, False]


def test_compute_reflectance_qc_fail_when_reflectance_too_high() -> None:
    sample = SpectrumData(
        wavelength_nm=np.linspace(500.0, 620.0, 20),
        intensity=np.full(20, 130.0),
    )
    reference = SpectrumData(
        wavelength_nm=np.linspace(500.0, 620.0, 20),
        intensity=np.full(20, 100.0),
    )
    result = compute_reflectance_qc(sample, reference, ReflectanceQCConfig())
    assert result.qc_summary.overall_status == "FAIL"
    assert result.qc_summary.metrics["reflectance_gt_1p2_fraction"] == 1.0


def test_compute_reflectance_qc_band_metrics() -> None:
    wavelength = np.array([500.0, 600.0, 700.0, 760.0])
    sample = SpectrumData(wavelength_nm=wavelength, intensity=np.array([10.0, 20.0, 30.0, 40.0]))
    reference = SpectrumData(wavelength_nm=wavelength, intensity=np.array([20.0, 40.0, 60.0, 20.0]))
    result = compute_reflectance_qc(sample, reference, ReflectanceQCConfig())
    assert result.qc_summary.metrics["median_reflectance_500_750"] == 0.5
    assert result.qc_summary.metrics["reflectance_600nm"] == 0.5
