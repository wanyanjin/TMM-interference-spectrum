from __future__ import annotations

from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_reflectance_qc_cli_runs(tmp_path: Path) -> None:
    sample_path = tmp_path / "sample.csv"
    reference_path = tmp_path / "reference.csv"
    sample_path.write_text("wavelength,counts\n500,10\n600,20\n700,30\n", encoding="utf-8")
    reference_path.write_text("wavelength,counts\n500,20\n600,40\n700,60\n", encoding="utf-8")

    command = [
        sys.executable,
        str(REPO_ROOT / "src" / "cli" / "reflectance_qc.py"),
        "--sample-csv",
        str(sample_path),
        "--reference-csv",
        str(reference_path),
        "--output-root",
        str(tmp_path),
        "--output-tag",
        "cli",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr
    assert "Reflectance QC completed." in completed.stdout
