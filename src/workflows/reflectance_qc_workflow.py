from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.reflectance_qc import compute_reflectance_qc
from domain.reflectance import ReflectanceQCConfig
from domain.run_manifest import ToolRunManifest
from domain.spectrum import SpectrumData
from storage.readers.base import DataSource
from storage.readers.csv_spectrum_reader import CSVSpectrumReader
from storage.writers.reflectance_qc_writer import (
    write_processed_reflectance_csv,
    write_qc_report_md,
    write_qc_summary_json,
)


@dataclass(frozen=True)
class ReflectanceQCWorkflowConfig:
    sample_path: Path
    reference_path: Path
    output_root: Path
    output_tag: str | None = None
    sample_exposure_ms: float | None = None
    reference_exposure_ms: float | None = None
    exposure_normalization_enabled: bool = False
    wavelength_min_nm: float | None = None
    wavelength_max_nm: float | None = None


def run_reflectance_qc_workflow(config: ReflectanceQCWorkflowConfig) -> dict[str, Any]:
    reader = CSVSpectrumReader()
    sample = _with_exposure(reader.read(DataSource(config.sample_path)), config.sample_exposure_ms)
    reference = _with_exposure(reader.read(DataSource(config.reference_path)), config.reference_exposure_ms)

    qc_config = ReflectanceQCConfig(
        wavelength_min_nm=config.wavelength_min_nm,
        wavelength_max_nm=config.wavelength_max_nm,
        exposure_normalization_enabled=config.exposure_normalization_enabled,
    )
    result = compute_reflectance_qc(sample=sample, reference=reference, config=qc_config)

    run_id = _build_run_id("reflectance_qc", config.output_tag)
    processed_dir = config.output_root / "data" / "processed" / "phase09" / "reflectance_qc" / run_id
    report_dir = config.output_root / "results" / "report" / "phase09_reflectance_qc" / run_id
    processed_csv = processed_dir / "processed_reflectance.csv"
    qc_summary_json = processed_dir / "qc_summary.json"
    qc_report_md = report_dir / "qc_report.md"

    manifest = ToolRunManifest(
        tool_name="reflectance_qc",
        run_id=run_id,
        parameters={
            "sample_exposure_ms": config.sample_exposure_ms,
            "reference_exposure_ms": config.reference_exposure_ms,
            "exposure_normalization_enabled": config.exposure_normalization_enabled,
            "wavelength_min_nm": config.wavelength_min_nm,
            "wavelength_max_nm": config.wavelength_max_nm,
        },
        inputs={
            "sample_path": str(config.sample_path),
            "reference_path": str(config.reference_path),
        },
        outputs={
            "processed_csv": str(processed_csv),
            "qc_summary_json": str(qc_summary_json),
            "qc_report_md": str(qc_report_md),
        },
        warnings=[],
    )

    write_processed_reflectance_csv(result, processed_csv)
    write_qc_summary_json(result, qc_summary_json, manifest=manifest)
    write_qc_report_md(result, qc_report_md, manifest=manifest)

    return {
        "run_id": run_id,
        "processed_csv": processed_csv,
        "qc_summary_json": qc_summary_json,
        "qc_report_md": qc_report_md,
        "qc_summary": result.qc_summary,
        "manifest": manifest,
    }


def _with_exposure(spectrum: SpectrumData, exposure_ms: float | None) -> SpectrumData:
    if exposure_ms is None:
        return spectrum
    return SpectrumData(
        wavelength_nm=spectrum.wavelength_nm,
        intensity=spectrum.intensity,
        label=spectrum.label,
        exposure_ms=exposure_ms,
        metadata=spectrum.metadata,
    )


def _build_run_id(tool_name: str, output_tag: str | None) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{output_tag}" if output_tag else ""
    return f"{timestamp}_{tool_name}{suffix}"
