from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.exceptions import ReaderNotFoundError
from common.registry import SpectrumReaderRegistry
from domain.spectrum import SpectrumData
from storage.readers.base import DataSource


class FakeReader:
    def can_read(self, source: DataSource) -> bool:
        return source.path.suffix == ".fake"

    def read(self, source: DataSource) -> SpectrumData:
        return SpectrumData(
            wavelength_nm=np.array([500.0, 501.0]),
            intensity=np.array([10.0, 12.0]),
            label=source.path.name,
        )


def test_reader_registry_reads_from_registered_reader() -> None:
    registry = SpectrumReaderRegistry()
    registry.register(FakeReader())
    tmp_dir = REPO_ROOT / "tests" / "_tmp_reader_registry"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    source = DataSource(path=tmp_dir / "sample.fake")
    spectrum = registry.read(source)
    assert spectrum.label == "sample.fake"
    assert spectrum.intensity.tolist() == [10.0, 12.0]


def test_reader_registry_raises_when_no_reader_matches() -> None:
    registry = SpectrumReaderRegistry()
    tmp_dir = REPO_ROOT / "tests" / "_tmp_reader_registry"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    source = DataSource(path=tmp_dir / "sample.unknown")
    with pytest.raises(ReaderNotFoundError):
        registry.read(source)
