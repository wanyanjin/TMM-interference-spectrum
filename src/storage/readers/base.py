from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from domain.spectrum import SpectrumData


@dataclass(frozen=True)
class DataSource:
    path: Path
    format_hint: str | None = None


class SpectrumReader(Protocol):
    def can_read(self, source: DataSource) -> bool:
        ...

    def read(self, source: DataSource) -> SpectrumData:
        ...
