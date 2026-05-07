from __future__ import annotations

from common.exceptions import ReaderNotFoundError
from domain.spectrum import SpectrumData
from storage.readers.base import DataSource, SpectrumReader


class SpectrumReaderRegistry:
    def __init__(self) -> None:
        self._readers: list[SpectrumReader] = []

    def register(self, reader: SpectrumReader) -> None:
        self._readers.append(reader)

    def read(self, source: DataSource) -> SpectrumData:
        for reader in self._readers:
            if reader.can_read(source):
                return reader.read(source)
        raise ReaderNotFoundError(f"No SpectrumReader can read source: {source.path}")
