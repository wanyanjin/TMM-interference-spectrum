from __future__ import annotations

from pathlib import Path

import pandas as pd

from common.exceptions import DataModelError
from domain.spectrum import SpectrumData
from storage.readers.base import DataSource, SpectrumReader

WAVELENGTH_CANDIDATES = {
    "wavelength",
    "wavelength_nm",
    "lambda",
    "lambda_nm",
    "nm",
}
INTENSITY_CANDIDATES = {
    "intensity",
    "counts",
    "count",
    "signal",
}


class CSVSpectrumReader(SpectrumReader):
    def can_read(self, source: DataSource) -> bool:
        return source.path.suffix.lower() in {".csv", ".txt"}

    def read(self, source: DataSource) -> SpectrumData:
        if not self.can_read(source):
            raise DataModelError(f"Unsupported spectrum file suffix: {source.path.suffix}")

        frame = self._read_table(source.path)
        wavelength_column, intensity_column = self._detect_columns(frame, source.path)
        numeric_frame = frame[[wavelength_column, intensity_column]].apply(pd.to_numeric, errors="coerce").dropna()
        if numeric_frame.empty:
            raise DataModelError(f"No numeric spectrum rows found in {source.path}")

        numeric_frame = numeric_frame.sort_values(by=wavelength_column, kind="mergesort")
        return SpectrumData(
            wavelength_nm=numeric_frame[wavelength_column].to_numpy(dtype=float),
            intensity=numeric_frame[intensity_column].to_numpy(dtype=float),
            label=source.path.name,
            metadata={
                "source_path": str(source.path),
                "reader": self.__class__.__name__,
                "wavelength_column": wavelength_column,
                "intensity_column": intensity_column,
            },
        )

    def _read_table(self, path: Path) -> pd.DataFrame:
        if path.suffix.lower() == ".csv":
            frame = pd.read_csv(path)
            if frame.shape[1] > 1:
                if self._columns_look_numeric(frame):
                    return pd.read_csv(path, header=None)
                return frame

        for separator in [r"\s+", ","]:
            frame = pd.read_csv(path, sep=separator, engine="python", header=None)
            if frame.shape[1] >= 2:
                return frame

        raise DataModelError(f"Unable to parse spectrum table from {path}")

    def _columns_look_numeric(self, frame: pd.DataFrame) -> bool:
        for column in frame.columns:
            try:
                float(str(column).strip())
            except ValueError:
                return False
        return True

    def _detect_columns(self, frame: pd.DataFrame, path: Path) -> tuple[object, object]:
        if all(isinstance(column, str) for column in frame.columns):
            normalized = {column: str(column).strip().lower() for column in frame.columns}
            wavelength_column = next(
                (column for column, value in normalized.items() if value in WAVELENGTH_CANDIDATES),
                None,
            )
            intensity_column = next(
                (column for column, value in normalized.items() if value in INTENSITY_CANDIDATES),
                None,
            )
            if wavelength_column is not None and intensity_column is not None:
                return wavelength_column, intensity_column

        numeric_columns = []
        for column in frame.columns:
            series = pd.to_numeric(frame[column], errors="coerce")
            if series.notna().sum() > 0:
                numeric_columns.append(column)
        if len(numeric_columns) == 2:
            return numeric_columns[0], numeric_columns[1]

        raise DataModelError(
            f"Unable to identify wavelength and intensity columns in {path}. "
            "Expected known column names or exactly two numeric columns."
        )
