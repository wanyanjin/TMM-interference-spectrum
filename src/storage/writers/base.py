from __future__ import annotations

from typing import Protocol


class ResultWriter(Protocol):
    def write(self, result: object) -> None:
        ...
