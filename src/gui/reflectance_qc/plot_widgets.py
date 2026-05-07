from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
from PySide6.QtWidgets import QWidget, QVBoxLayout


@dataclass(frozen=True)
class PlotPayload:
    x: np.ndarray
    y: np.ndarray
    anomaly_mask: np.ndarray
    title: str
    x_label: str = "Wavelength (nm)"
    y_label: str = "Reflectance"


class ReflectancePlotWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._plot = pg.PlotWidget()
        self._plot.showGrid(x=True, y=True, alpha=0.25)
        layout.addWidget(self._plot)
        self._curve = self._plot.plot(pen=pg.mkPen("#2E86DE", width=2))
        self._anomaly = self._plot.plot(
            pen=None,
            symbol="o",
            symbolSize=6,
            symbolBrush=pg.mkBrush("#E74C3C"),
            symbolPen=pg.mkPen("#E74C3C"),
        )

    def render_payload(self, payload: PlotPayload) -> None:
        self._curve.setData(payload.x, payload.y)
        if payload.anomaly_mask.size and np.any(payload.anomaly_mask):
            self._anomaly.setData(payload.x[payload.anomaly_mask], payload.y[payload.anomaly_mask])
        else:
            self._anomaly.setData([], [])
        self._plot.setTitle(payload.title)
        self._plot.setLabel("bottom", payload.x_label)
        self._plot.setLabel("left", payload.y_label)

    def set_x_range(self, x_min: float, x_max: float) -> None:
        self._plot.setXRange(x_min, x_max, padding=0.0)

    def set_y_range(self, y_min: float, y_max: float) -> None:
        self._plot.setYRange(y_min, y_max, padding=0.0)

    def enable_auto_y(self) -> None:
        self._plot.enableAutoRange(axis="y", enable=True)

    def export_png(self, output_path: str) -> None:
        exporter = pg.exporters.ImageExporter(self._plot.plotItem)
        exporter.export(output_path)
