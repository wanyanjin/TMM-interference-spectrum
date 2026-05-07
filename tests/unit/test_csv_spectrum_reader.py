from __future__ import annotations

from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.exceptions import DataModelError
from storage.readers.base import DataSource
from storage.readers.csv_spectrum_reader import CSVSpectrumReader


def test_csv_reader_reads_named_columns(tmp_path: Path) -> None:
    reader = CSVSpectrumReader()
    source_path = tmp_path / "phase09_named.csv"
    source_path.write_text("wavelength,counts\n500,10\n501,12\n", encoding="utf-8")
    spectrum = reader.read(DataSource(source_path))
    assert spectrum.wavelength_nm.tolist() == [500.0, 501.0]
    assert spectrum.intensity.tolist() == [10.0, 12.0]


def test_csv_reader_reads_two_column_headerless_file(tmp_path: Path) -> None:
    source_path = tmp_path / "headerless.csv"
    source_path.write_text("501,12\n500,10\n", encoding="utf-8")
    spectrum = CSVSpectrumReader().read(DataSource(source_path))
    assert spectrum.wavelength_nm.tolist() == [500.0, 501.0]
    assert spectrum.intensity.tolist() == [10.0, 12.0]


def test_csv_reader_sorts_wavelengths(tmp_path: Path) -> None:
    source_path = tmp_path / "unordered.txt"
    source_path.write_text("Wavelength Intensity\n510 5\n500 3\n", encoding="utf-8")
    spectrum = CSVSpectrumReader().read(DataSource(source_path))
    assert spectrum.wavelength_nm.tolist() == [500.0, 510.0]


def test_csv_reader_raises_for_unrecognized_columns(tmp_path: Path) -> None:
    source_path = tmp_path / "bad.csv"
    source_path.write_text("a,b,c\n1,2,3\n4,5,6\n", encoding="utf-8")
    with pytest.raises(DataModelError):
        CSVSpectrumReader().read(DataSource(source_path))
