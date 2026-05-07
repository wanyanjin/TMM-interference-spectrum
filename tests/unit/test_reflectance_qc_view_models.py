from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from gui.reflectance_qc.view_models import (
    classify_anomaly_points,
    compute_current_window_qc,
    compute_full_auto_y_limits,
    compute_robust_y_limits,
    resolve_x_range,
    validate_processed_reflectance_schema,
)


def test_validate_schema_success() -> None:
    result = validate_processed_reflectance_schema(
        ["wavelength_nm", "calculated_reflectance", "valid_mask"]
    )
    assert result["required_columns"] == ("wavelength_nm", "calculated_reflectance")


def test_validate_schema_missing_required() -> None:
    with pytest.raises(ValueError):
        validate_processed_reflectance_schema(["wavelength_nm"])


def test_resolve_x_range_presets_and_custom() -> None:
    wavelengths = np.array([400.0, 500.0, 600.0, 750.0])
    assert resolve_x_range("full", None, None, wavelengths) == (400.0, 750.0)
    assert resolve_x_range("500-700", None, None, wavelengths) == (500.0, 700.0)
    assert resolve_x_range("custom", 510.0, 690.0, wavelengths) == (510.0, 690.0)


def test_resolve_x_range_custom_invalid() -> None:
    wavelengths = np.array([400.0, 500.0])
    with pytest.raises(ValueError):
        resolve_x_range("custom", 700.0, 500.0, wavelengths)


def test_compute_robust_y_limits_filters_outlier() -> None:
    values = np.array([0.30] * 98 + [0.31, 8.0], dtype=float)
    valid_mask = np.ones_like(values, dtype=bool)
    limits, reason = compute_robust_y_limits(values, valid_mask)
    assert reason is None
    assert limits is not None
    assert limits[1] < 1.0


def test_compute_robust_y_limits_fallback_reason() -> None:
    values = np.array([0.3, 0.31, np.nan], dtype=float)
    valid_mask = np.array([True, True, True], dtype=bool)
    limits, reason = compute_robust_y_limits(values, valid_mask)
    assert limits is None
    assert reason == "too_few_valid_points"


def test_compute_full_auto_y_limits() -> None:
    values = np.array([0.25, 0.35, np.nan])
    limits = compute_full_auto_y_limits(values)
    assert limits is not None
    assert limits[0] < 0.25
    assert limits[1] > 0.35


def test_classify_anomaly_points() -> None:
    data = pd.DataFrame(
        {
            "calculated_reflectance": [0.2, -0.1, 1.3, np.nan],
            "valid_mask": [True, True, False, True],
            "mask_reason": ["ok", "ok", "reference_nonpositive", "ok"],
            "reference_intensity_processed": [1.0, 1.0, 0.0, np.nan],
        }
    )
    anomaly = classify_anomaly_points(data)
    assert anomaly["reflectance_lt_0"].sum() == 1
    assert anomaly["reflectance_gt_1p2"].sum() == 1
    assert anomaly["invalid_mask"].sum() == 1
    assert anomaly["non_finite_reflectance"].sum() == 1
    assert anomaly["reference_nonpositive"].sum() == 1


def test_compute_current_window_qc_inside_600nm() -> None:
    data = pd.DataFrame(
        {
            "wavelength_nm": [500.0, 600.0, 700.0],
            "calculated_reflectance": [0.3, 0.32, 0.34],
            "valid_mask": [True, True, True],
            "mask_reason": ["ok", "ok", "ok"],
            "reference_intensity_processed": [1.0, 1.0, 1.0],
        }
    )
    metrics = compute_current_window_qc(data, (500.0, 700.0))
    assert metrics.point_count == 3
    assert metrics.valid_point_count == 3
    assert metrics.reflectance_600nm == 0.32
    assert metrics.reflectance_600nm_note is None


def test_compute_current_window_qc_outside_600nm() -> None:
    data = pd.DataFrame(
        {
            "wavelength_nm": [650.0, 700.0],
            "calculated_reflectance": [0.3, 0.32],
            "valid_mask": [True, True],
            "mask_reason": ["ok", "ok"],
            "reference_intensity_processed": [1.0, 1.0],
        }
    )
    metrics = compute_current_window_qc(data, (650.0, 700.0))
    assert metrics.reflectance_600nm is None
    assert metrics.reflectance_600nm_note == "N/A, 600 nm outside current window"

