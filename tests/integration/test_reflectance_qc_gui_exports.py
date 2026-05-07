from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from gui.reflectance_qc.io import load_processed_reflectance_csv
from gui.reflectance_qc.main_window import ReflectanceQCMainWindow


def test_gui_export_json_artifacts(monkeypatch, tmp_path: Path) -> None:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    csv_path = tmp_path / "processed_reflectance.csv"
    pd.DataFrame(
        {
            "wavelength_nm": [500.0, 550.0, 600.0, 650.0, 700.0],
            "calculated_reflectance": [0.2, 0.25, 0.3, 0.35, 0.4],
            "valid_mask": [True, True, True, True, True],
            "mask_reason": ["ok", "ok", "ok", "ok", "ok"],
            "reference_intensity_processed": [100, 100, 100, 100, 100],
            "sample_intensity_processed": [20, 25, 30, 35, 40],
        }
    ).to_csv(csv_path, index=False)
    app = QApplication.instance() or QApplication([])
    window = ReflectanceQCMainWindow()
    window._loaded_data = load_processed_reflectance_csv(csv_path)
    window._processed_csv_path = csv_path
    window._refresh_plot()
    monkeypatch.chdir(tmp_path)
    window._on_export()
    out_root = tmp_path / "results" / "gui_exports" / "reflectance_qc"
    run_dirs = [p for p in out_root.iterdir() if p.is_dir()]
    assert run_dirs
    export_dir = run_dirs[0]
    assert (export_dir / "view_settings.json").exists()
    assert (export_dir / "gui_qc_summary.json").exists()
    window.close()
    app.quit()
