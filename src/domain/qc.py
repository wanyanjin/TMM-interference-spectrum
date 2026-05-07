from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class QCFlag:
    name: str
    severity: str
    message: str


@dataclass(frozen=True)
class QCSummary:
    overall_status: str
    metrics: dict[str, float]
    flags: list[QCFlag] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
