from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from gui.reflectance_qc.view_models import (
    ReflectanceQCLoadedData,
    ReflectanceQCWindowMetrics,
    ReflectanceQCViewSettings,
    validate_processed_reflectance_schema,
)
from workflows.reflectance_qc_workflow import ReflectanceQCWorkflowConfig


def load_processed_reflectance_csv(path: Path) -> ReflectanceQCLoadedData:
    dataframe = pd.read_csv(path)
    schema = validate_processed_reflectance_schema(list(dataframe.columns))
    warnings: list[str] = []
    missing_recommended = schema["missing_recommended_columns"]
    if missing_recommended:
        warnings.append(
            "Missing recommended columns: " + ", ".join(missing_recommended)
        )
    return ReflectanceQCLoadedData(
        dataframe=dataframe,
        required_columns=schema["required_columns"],
        missing_recommended_columns=missing_recommended,
        missing_optional_columns=schema["missing_optional_columns"],
        warnings=warnings,
    )


def load_qc_summary_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise FileNotFoundError(f"qc_summary.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def infer_run_id(processed_csv_path: Path, qc_summary: dict[str, Any] | None) -> str:
    if qc_summary:
        manifest = qc_summary.get("manifest", {})
        run_id = manifest.get("run_id")
        if isinstance(run_id, str) and run_id.strip():
            return run_id
    parent = processed_csv_path.parent.name
    if parent:
        return parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_reflectance_qc_gui"


def build_gui_export_metadata(
    *,
    processed_csv_path: Path,
    qc_summary_path: Path | None,
    run_id: str,
    settings: ReflectanceQCViewSettings,
    current_y_range: tuple[float, float] | None,
    window_metrics: ReflectanceQCWindowMetrics,
    highlighted_flags: list[str],
) -> dict[str, Any]:
    return {
        "input_processed_reflectance_csv": str(processed_csv_path),
        "input_qc_summary_json": str(qc_summary_path) if qc_summary_path else None,
        "x_range": [settings.x_min, settings.x_max],
        "y_range": list(current_y_range) if current_y_range else None,
        "autoscale_mode": settings.y_mode,
        "visible_point_count": window_metrics.point_count,
        "valid_point_count": window_metrics.valid_point_count,
        "invalid_fraction": window_metrics.invalid_fraction,
        "highlighted_flags": highlighted_flags,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "run_id": run_id,
        "application_version_or_phase": "Phase 09C-1",
    }


def export_view_settings_json(export_dir: Path, payload: dict[str, Any]) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    output = export_dir / "view_settings.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def export_gui_qc_summary_json(export_dir: Path, payload: dict[str, Any]) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    output = export_dir / "gui_qc_summary.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def build_workflow_config_from_gui(
    *,
    sample_path: Path,
    reference_path: Path,
    output_root: Path,
    output_tag: str | None,
    sample_exposure_text: str,
    reference_exposure_text: str,
    exposure_normalization_enabled: bool,
    wavelength_preset: str,
    wavelength_min_text: str,
    wavelength_max_text: str,
    output_dir: Path | None = None,
    output_basename: str | None = None,
) -> ReflectanceQCWorkflowConfig:
    if not sample_path.exists():
        raise FileNotFoundError(f"Sample CSV not found: {sample_path}")
    if not reference_path.exists():
        raise FileNotFoundError(f"Reference CSV not found: {reference_path}")
    sample_exposure_ms = float(sample_exposure_text) if sample_exposure_text else None
    reference_exposure_ms = float(reference_exposure_text) if reference_exposure_text else None

    preset = wavelength_preset.replace(" nm", "")
    if preset == "Full range":
        wavelength_min_nm, wavelength_max_nm = None, None
    elif preset == "400-750":
        wavelength_min_nm, wavelength_max_nm = 400.0, 750.0
    elif preset == "500-700":
        wavelength_min_nm, wavelength_max_nm = 500.0, 700.0
    else:
        wavelength_min_nm = float(wavelength_min_text)
        wavelength_max_nm = float(wavelength_max_text)
        if wavelength_min_nm >= wavelength_max_nm:
            raise ValueError("Custom wavelength range requires min < max.")

    return ReflectanceQCWorkflowConfig(
        sample_path=sample_path,
        reference_path=reference_path,
        output_root=output_root,
        output_tag=output_tag,
        sample_exposure_ms=sample_exposure_ms,
        reference_exposure_ms=reference_exposure_ms,
        exposure_normalization_enabled=exposure_normalization_enabled,
        wavelength_min_nm=wavelength_min_nm,
        wavelength_max_nm=wavelength_max_nm,
        output_dir=output_dir,
        output_basename=output_basename,
    )
