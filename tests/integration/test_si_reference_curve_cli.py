from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_si_reference_curve_cli_generates_outputs(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    cli_path = repo_root / "src" / "cli" / "si_reference_curve.py"
    cmd = [sys.executable, str(cli_path), "--output-root", str(tmp_path)]
    completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    assert "si_reference_curve completed" in completed.stdout
    assert (tmp_path / "si_air_reflectance_green_2008_400_1000nm.csv").exists()
    assert (tmp_path / "metadata.json").exists()
