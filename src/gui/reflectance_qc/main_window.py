from __future__ import annotations

import os
import traceback
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.reflectance_qc.io import (
    build_gui_export_metadata,
    build_workflow_config_from_gui,
    export_gui_qc_summary_json,
    export_view_settings_json,
    infer_run_id,
    load_processed_reflectance_csv,
    load_qc_summary_json,
)
from gui.reflectance_qc.plot_widgets import PlotPayload, ReflectancePlotWidget
from gui.reflectance_qc.view_models import (
    ReflectanceQCLoadedData,
    ReflectanceQCViewSettings,
    classify_anomaly_points,
    compute_current_window_qc,
    compute_full_auto_y_limits,
    compute_robust_y_limits,
    filter_visible_rows,
    resolve_x_range,
)
from workflows.reflectance_qc_workflow import run_reflectance_qc_workflow


class ReflectanceQCMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Reflectance QC GUI (Phase 09C-2)")
        self.resize(1360, 820)
        self._loaded_data: ReflectanceQCLoadedData | None = None
        self._qc_summary: dict | None = None
        self._processed_csv_path: Path | None = None
        self._qc_json_path: Path | None = None
        self._last_output_dir: Path | None = None
        self._repo_root = Path(__file__).resolve().parents[3]
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)
        layout = QGridLayout(root)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)

        layout.addWidget(self._build_controls(), 0, 0, 2, 1)
        self.plot_widget = ReflectancePlotWidget(self)
        layout.addWidget(self.plot_widget, 0, 1)

        metrics = QGroupBox("QC Metrics", self)
        metrics_layout = QVBoxLayout(metrics)
        self.full_metrics = QLabel("Full-range QC: N/A", self)
        self.window_metrics = QLabel("Current-window QC: N/A", self)
        self.full_metrics.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.window_metrics.setTextInteractionFlags(Qt.TextSelectableByMouse)
        metrics_layout.addWidget(self.full_metrics)
        metrics_layout.addWidget(self.window_metrics)
        layout.addWidget(metrics, 1, 1)
        self.statusBar().showMessage("Load sample and reference CSV, then click Run QC.")

    def _build_controls(self) -> QWidget:
        box = QGroupBox("Controls", self)
        v = QVBoxLayout(box)
        self.input_mode = QComboBox()
        self.input_mode.addItems(["Raw spectra QC", "Processed result viewer"])
        self.input_mode.currentTextChanged.connect(self._on_mode_changed)
        v.addWidget(self.input_mode)

        self.raw_group = self._build_raw_group()
        self.viewer_group = self._build_viewer_group()
        v.addWidget(self.raw_group)
        v.addWidget(self.viewer_group)

        form = QFormLayout()
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Calculated reflectance", "Sample/reference ratio", "Sample intensity processed", "Reference intensity processed"])
        self.view_combo.currentTextChanged.connect(lambda _: self._refresh_plot())
        form.addRow("View", self.view_combo)

        self.x_preset = QComboBox()
        self.x_preset.addItems(["500-700 nm", "Full range", "400-750 nm", "500-750 nm", "Custom"])
        self.x_preset.currentTextChanged.connect(lambda _: self._refresh_plot())
        form.addRow("X preset", self.x_preset)
        self.x_min = QLineEdit("500")
        self.x_max = QLineEdit("700")
        self.x_min.editingFinished.connect(self._refresh_plot)
        self.x_max.editingFinished.connect(self._refresh_plot)
        form.addRow("X min/max", self._row(self.x_min, self.x_max))

        self.y_mode = QComboBox()
        self.y_mode.addItems(["Robust auto", "Full auto", "Physical reflectance range", "Manual"])
        self.y_mode.currentTextChanged.connect(lambda _: self._refresh_plot())
        form.addRow("Y mode", self.y_mode)
        self.y_min = QLineEdit("-0.05")
        self.y_max = QLineEdit("1.2")
        self.y_min.editingFinished.connect(self._refresh_plot)
        self.y_max.editingFinished.connect(self._refresh_plot)
        form.addRow("Y min/max", self._row(self.y_min, self.y_max))
        v.addLayout(form)

        self.btn_export = QPushButton("Export Current View")
        self.btn_export.clicked.connect(self._on_export)
        self.btn_open_output = QPushButton("Open Output Folder")
        self.btn_open_output.clicked.connect(self._on_open_output)
        v.addWidget(self.btn_export)
        v.addWidget(self.btn_open_output)
        v.addStretch(1)
        self._on_mode_changed(self.input_mode.currentText())
        return box

    def _build_raw_group(self) -> QWidget:
        group = QGroupBox("Raw spectra QC", self)
        form = QFormLayout(group)
        self.sample_path_edit = QLineEdit()
        self.reference_path_edit = QLineEdit()
        self.btn_sample = QPushButton("Load Sample CSV")
        self.btn_reference = QPushButton("Load Reference CSV")
        self.btn_sample.clicked.connect(lambda: self._pick_csv(self.sample_path_edit))
        self.btn_reference.clicked.connect(lambda: self._pick_csv(self.reference_path_edit))
        form.addRow(self.btn_sample, self.sample_path_edit)
        form.addRow(self.btn_reference, self.reference_path_edit)
        self.sample_exposure_edit = QLineEdit("20")
        self.reference_exposure_edit = QLineEdit("20")
        form.addRow("Sample exposure ms", self.sample_exposure_edit)
        form.addRow("Reference exposure ms", self.reference_exposure_edit)
        self.exposure_norm_check = QCheckBox("Exposure normalize")
        self.exposure_norm_check.setChecked(True)
        form.addRow(self.exposure_norm_check)
        self.raw_range_preset = QComboBox()
        self.raw_range_preset.addItems(["500-700 nm", "Full range", "400-750 nm", "Custom"])
        form.addRow("Wavelength preset", self.raw_range_preset)
        self.raw_x_min = QLineEdit("500")
        self.raw_x_max = QLineEdit("700")
        form.addRow("Wavelength min/max", self._row(self.raw_x_min, self.raw_x_max))
        self.output_tag_edit = QLineEdit("phase09c2_gui")
        form.addRow("Output tag", self.output_tag_edit)
        self.btn_run_qc = QPushButton("Run QC")
        self.btn_run_qc.clicked.connect(self._on_run_qc)
        form.addRow(self.btn_run_qc)
        return group

    def _build_viewer_group(self) -> QWidget:
        group = QGroupBox("Processed result viewer", self)
        h = QHBoxLayout(group)
        self.btn_load_csv = QPushButton("Load Processed CSV")
        self.btn_load_json = QPushButton("Load QC JSON (Optional)")
        self.btn_load_csv.clicked.connect(self._on_load_processed_csv)
        self.btn_load_json.clicked.connect(self._on_load_qc_json)
        h.addWidget(self.btn_load_csv)
        h.addWidget(self.btn_load_json)
        return group

    @staticmethod
    def _row(left: QWidget, right: QWidget) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(left)
        h.addWidget(right)
        return w

    def _on_mode_changed(self, mode: str) -> None:
        is_raw = mode == "Raw spectra QC"
        self.raw_group.setEnabled(is_raw)
        self.viewer_group.setEnabled(not is_raw)

    def _pick_csv(self, target: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV/TXT", "", "Data Files (*.csv *.txt)")
        if path:
            target.setText(path)

    def _parse_range(self, preset_text: str, x_min_text: str, x_max_text: str) -> tuple[float | None, float | None]:
        preset = preset_text.replace(" nm", "")
        if preset == "Full range":
            return None, None
        if preset == "400-750":
            return 400.0, 750.0
        if preset == "500-700":
            return 500.0, 700.0
        return float(x_min_text), float(x_max_text)

    def _on_run_qc(self) -> None:
        try:
            config = build_workflow_config_from_gui(
                sample_path=Path(self.sample_path_edit.text().strip()),
                reference_path=Path(self.reference_path_edit.text().strip()),
                output_root=self._repo_root,
                output_tag=self.output_tag_edit.text().strip() or None,
                sample_exposure_text=self.sample_exposure_edit.text().strip(),
                reference_exposure_text=self.reference_exposure_edit.text().strip(),
                exposure_normalization_enabled=self.exposure_norm_check.isChecked(),
                wavelength_preset=self.raw_range_preset.currentText(),
                wavelength_min_text=self.raw_x_min.text().strip(),
                wavelength_max_text=self.raw_x_max.text().strip(),
            )
            self.btn_run_qc.setEnabled(False)
            self.statusBar().showMessage("Running reflectance QC...")
            result = run_reflectance_qc_workflow(config)
            self._processed_csv_path = Path(result["processed_csv"])
            self._qc_json_path = Path(result["qc_summary_json"])
            self._last_output_dir = self._processed_csv_path.parent
            self._loaded_data = load_processed_reflectance_csv(self._processed_csv_path)
            self._qc_summary = load_qc_summary_json(self._qc_json_path)
            self._refresh_plot()
            self.statusBar().showMessage(f"Done. Output: {self._processed_csv_path.parent}")
        except Exception as exc:
            summary = traceback.format_exc(limit=4)
            QMessageBox.critical(self, "Run QC Failed", f"{exc}\n\n{summary}")
        finally:
            self.btn_run_qc.setEnabled(True)

    def _on_load_processed_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select processed_reflectance.csv", "", "CSV Files (*.csv)")
        if not path:
            return
        self._loaded_data = load_processed_reflectance_csv(Path(path))
        self._processed_csv_path = Path(path)
        self._refresh_plot()

    def _on_load_qc_json(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select qc_summary.json", "", "JSON Files (*.json)")
        if not path:
            return
        self._qc_summary = load_qc_summary_json(Path(path))
        self._qc_json_path = Path(path)
        self._refresh_plot()

    def _current_x_range(self) -> tuple[float, float]:
        if self._loaded_data is None:
            raise ValueError("No loaded data.")
        preset = self.x_preset.currentText().replace(" nm", "")
        values = self._loaded_data.dataframe["wavelength_nm"].to_numpy(dtype=float)
        if preset == "Custom":
            return float(self.x_min.text()), float(self.x_max.text())
        mapped = {"Full range": "full", "400-750": "400-750", "500-700": "500-700", "500-750": "500-750"}
        key = mapped.get(preset, "500-700")
        return resolve_x_range(key, None, None, values)

    def _refresh_plot(self) -> None:
        if self._loaded_data is None:
            return
        frame = self._loaded_data.dataframe
        x_min, x_max = self._current_x_range()
        visible = filter_visible_rows(frame, (x_min, x_max))
        anomaly = classify_anomaly_points(visible)
        x = visible["wavelength_nm"].to_numpy(dtype=float)
        view_name = self.view_combo.currentText()

        if view_name == "Calculated reflectance":
            y = visible["calculated_reflectance"].to_numpy(dtype=float)
            robust_valid = ~(anomaly["non_finite_reflectance"] | anomaly["invalid_mask"] | anomaly["reflectance_lt_0"] | anomaly["reflectance_gt_1p2"])
            y_label = "Reflectance"
        elif view_name == "Sample/reference ratio":
            y = visible["sample_reference_ratio"].to_numpy(dtype=float)
            robust_valid = ~(anomaly["invalid_mask"])
            y_label = "Ratio"
        elif view_name == "Sample intensity processed":
            y = visible["sample_intensity_processed"].to_numpy(dtype=float)
            robust_valid = np.isfinite(y) & (y >= 0)
            y_label = "Counts"
        else:
            y = visible["reference_intensity_processed"].to_numpy(dtype=float)
            robust_valid = np.isfinite(y) & (y > 0)
            y_label = "Counts"

        self.plot_widget.render_payload(PlotPayload(x=x, y=y, anomaly_mask=~robust_valid, title=view_name, y_label=y_label))
        self.plot_widget.set_x_range(x_min, x_max)
        self._apply_y_mode(y, robust_valid.to_numpy() if hasattr(robust_valid, "to_numpy") else robust_valid)
        full_metrics = compute_current_window_qc(frame, (float(frame["wavelength_nm"].min()), float(frame["wavelength_nm"].max())))
        window_metrics = compute_current_window_qc(frame, (x_min, x_max))
        self.full_metrics.setText(f"Full-range QC: invalid_fraction={full_metrics.invalid_fraction:.4f}, points={full_metrics.point_count}")
        self.window_metrics.setText(f"Current-window QC: invalid_fraction={window_metrics.invalid_fraction:.4f}, points={window_metrics.point_count}")

    def _apply_y_mode(self, y: np.ndarray, robust_valid: np.ndarray) -> None:
        mode = self.y_mode.currentText()
        if mode == "Physical reflectance range":
            self.plot_widget.set_y_range(-0.05, 1.2)
            return
        if mode == "Manual":
            y_min, y_max = float(self.y_min.text()), float(self.y_max.text())
            if y_min >= y_max:
                raise ValueError("y_min must be smaller than y_max.")
            self.plot_widget.set_y_range(y_min, y_max)
            return
        if mode == "Robust auto":
            result = compute_robust_y_limits(y, robust_valid)
            if result[0] is None:
                full = compute_full_auto_y_limits(y)
                if full is not None:
                    self.plot_widget.set_y_range(full[0], full[1])
                return
            self.plot_widget.set_y_range(result[0][0], result[0][1])
            return
        full = compute_full_auto_y_limits(y)
        if full is not None:
            self.plot_widget.set_y_range(full[0], full[1])

    def _on_export(self) -> None:
        if self._loaded_data is None or self._processed_csv_path is None:
            QMessageBox.warning(self, "Export skipped", "Load or run QC first.")
            return
        x_min, x_max = self._current_x_range()
        run_id = infer_run_id(self._processed_csv_path, self._qc_summary)
        export_dir = self._repo_root / "results" / "gui_exports" / "reflectance_qc" / run_id
        metrics = compute_current_window_qc(self._loaded_data.dataframe, (x_min, x_max))
        settings = ReflectanceQCViewSettings(
            x_preset="custom",
            x_min=x_min,
            x_max=x_max,
            y_mode="robust_auto",
            active_view="reflectance",
            highlighted_flags=[],
        )
        payload = build_gui_export_metadata(
            processed_csv_path=self._processed_csv_path,
            qc_summary_path=self._qc_json_path,
            run_id=run_id,
            settings=settings,
            current_y_range=(self.plot_widget._plot.viewRange()[1][0], self.plot_widget._plot.viewRange()[1][1]),
            window_metrics=metrics,
            highlighted_flags=[],
        )
        export_view_settings_json(export_dir, payload)
        export_gui_qc_summary_json(export_dir, {"current_window_qc": asdict(metrics), "full_range_qc": self._qc_summary or {}})
        try:
            self.plot_widget.export_png(str(export_dir / "current_view.png"))
        except Exception:
            pass
        self.statusBar().showMessage(f"Exported to {export_dir}")

    def _on_open_output(self) -> None:
        path = self._last_output_dir or (self._processed_csv_path.parent if self._processed_csv_path else None)
        if path is None:
            QMessageBox.information(self, "No output", "No output folder available yet.")
            return
        if os.name == "nt":
            os.startfile(str(path))
            return
        QMessageBox.information(self, "Platform note", f"Open manually: {path}")
