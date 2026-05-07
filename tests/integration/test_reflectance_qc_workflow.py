from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from workflows.reflectance_qc_workflow import (
    ReflectanceQCWorkflowConfig,
    run_reflectance_qc_workflow,
)


def test_reflectance_qc_workflow_writes_outputs(tmp_path: Path) -> None:
    sample_path = tmp_path / "sample.csv"
    reference_path = tmp_path / "reference.csv"
    sample_path.write_text("wavelength,counts\n500,10\n600,20\n700,30\n", encoding="utf-8")
    reference_path.write_text("wavelength,counts\n500,20\n600,40\n700,60\n", encoding="utf-8")

    result = run_reflectance_qc_workflow(
        ReflectanceQCWorkflowConfig(
            sample_path=sample_path,
            reference_path=reference_path,
            output_root=tmp_path,
            output_tag="integration",
        )
    )

    assert result["processed_csv"].exists()
    assert result["qc_summary_json"].exists()
    assert result["qc_report_md"].exists()
