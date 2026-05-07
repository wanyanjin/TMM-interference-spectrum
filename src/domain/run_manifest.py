from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolRunManifest:
    tool_name: str
    run_id: str
    parameters: dict[str, Any]
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
