from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from gui.reflectance_qc.io import (
    build_gui_export_metadata,
    build_workflow_config_from_gui,
    export_gui_qc_summary_json,
    export_view_settings_json,
    infer_run_id,
    load_processed_reflectance_csv,
)
from gui.reflectance_qc.view_models import ReflectanceQCViewSettings, compute_current_window_qc


def test_load_processed_reflectance_csv_success(tmp_path: Path) -> None:
    csv_path = tmp_path / "processed_reflectance.csv"
    pd.DataFrame(
        {
            "wavelength_nm": [500.0, 600.0],
            "calculated_reflectance": [0.3, 0.4],
            "valid_mask": [True, True],
        }
    ).to_csv(csv_path, index=False)
    loaded = load_processed_reflectance_csv(csv_path)
    assert loaded.dataframe.shape[0] == 2


def test_load_processed_reflectance_csv_missing_required(tmp_path: Path) -> None:
    csv_path = tmp_path / "processed_reflectance.csv"
    pd.DataFrame({"wavelength_nm": [500.0]}).to_csv(csv_path, index=False)
    with pytest.raises(ValueError):
        load_processed_reflectance_csv(csv_path)


def test_infer_run_id_from_manifest() -> None:
    run_id = infer_run_id(Path("a/b/processed_reflectance.csv"), {"manifest": {"run_id": "abc"}})
    assert run_id == "abc"


def test_export_json_files(tmp_path: Path) -> None:
    data = pd.DataFrame(
        {
            "wavelength_nm": [500.0, 600.0, 700.0],
            "calculated_reflectance": [0.3, 0.31, 0.32],
            "valid_mask": [True, True, True],
            "mask_reason": ["ok", "ok", "ok"],
            "reference_intensity_processed": [1.0, 1.0, 1.0],
        }
    )
    metrics = compute_current_window_qc(data, (500.0, 700.0))
    settings = ReflectanceQCViewSettings()
    payload = build_gui_export_metadata(
        processed_csv_path=tmp_path / "processed_reflectance.csv",
        qc_summary_path=None,
        run_id="run123",
        settings=settings,
        current_y_range=(0.2, 0.4),
        window_metrics=metrics,
        highlighted_flags=["reflectance_gt_1p2"],
    )
    export_dir = tmp_path / "results" / "gui_exports" / "reflectance_qc" / "run123"
    settings_path = export_view_settings_json(export_dir, payload)
    summary_path = export_gui_qc_summary_json(export_dir, payload)
    assert settings_path.exists()
    assert summary_path.exists()


def test_build_workflow_config_from_gui(tmp_path: Path) -> None:
    sample_path = tmp_path / "sample.csv"
    reference_path = tmp_path / "reference.csv"
    sample_path.write_text("wavelength_nm,intensity\n500,1\n", encoding="utf-8")
    reference_path.write_text("wavelength_nm,intensity\n500,1\n", encoding="utf-8")
    config = build_workflow_config_from_gui(
        sample_path=sample_path,
        reference_path=reference_path,
        output_root=tmp_path,
        output_tag="x",
        sample_exposure_text="20",
        reference_exposure_text="21",
        exposure_normalization_enabled=True,
        wavelength_preset="500-700 nm",
        wavelength_min_text="",
        wavelength_max_text="",
    )
    assert config.sample_path == sample_path
    assert config.reference_path == reference_path
    assert config.sample_exposure_ms == 20.0
    assert config.reference_exposure_ms == 21.0
    assert config.wavelength_min_nm == 500.0
    assert config.wavelength_max_nm == 700.0
