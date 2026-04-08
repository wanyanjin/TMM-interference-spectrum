"""Phase 05 parser for structured ellipsometry Markdown reports.

This script scans ``resources/n-kdata/*/full.md`` and extracts the fitted
optical parameters needed to build a material master database. HTML tables are
parsed with BeautifulSoup, while plain-text fallbacks are used for overview
fields such as ``Thickness = ... nm``.

Dependency note:
- ``beautifulsoup4`` is required for table parsing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_ROOT = PROJECT_ROOT / "resources" / "n-kdata"
OUTPUT_PATH = PROJECT_ROOT / "resources" / "materials_master_db.json"

MODEL_PARAMETER_ORDER = {
    "Tauc-Lorentz": ["A", "E0", "C", "Eg"],
    "Lorentz": ["f", "E0", "Γ"],
    "Cauchy": ["B", "C", "D", "E", "F"],
    "Gauss": ["Amp", "E0", "Br"],
}
GLOBAL_PARAMETER_KEYS = {"Eps_inf", "N_inf"}


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compact_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def parse_float(text: str) -> float | None:
    match = re.search(r"[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?", text)
    return float(match.group(0)) if match else None


def canonical_parameter_name(label: str) -> str:
    label = normalize_text(label)
    label = label.replace("Gamma", "Γ")
    label = re.sub(r"\([^)]*\)", "", label)
    label = label.strip(" :-")
    return label


def warning(material: str, field: str, source_md: Path, parse_warnings: list[str], reason: str) -> None:
    entry = f"{reason}:{field}"
    if entry not in parse_warnings:
        parse_warnings.append(entry)
    print(f"WARNING [{material}] missing `{field}` in {source_md} ({reason})")


def extract_sample_id(markdown_text: str) -> str | None:
    lines = markdown_text.splitlines()
    for index, line in enumerate(lines):
        if compact_key(line) == "sampleid":
            for follow in lines[index + 1 :]:
                value = normalize_text(follow)
                if value:
                    return value
    return None


def extract_overview_thickness(markdown_text: str) -> float | None:
    match = re.search(r"Thickness\s*=\s*([-+]?\d+(?:\.\d+)?)\s*nm", markdown_text, flags=re.IGNORECASE)
    return float(match.group(1)) if match else None


def extract_section(markdown_text: str, start_marker: str, end_marker: str | None) -> str:
    start_index = markdown_text.find(start_marker)
    if start_index == -1:
        return ""
    end_index = markdown_text.find(end_marker, start_index) if end_marker else -1
    if end_index == -1:
        end_index = len(markdown_text)
    return markdown_text[start_index:end_index]


def table_to_rows(table: Any) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.find_all("tr"):
        cells = [normalize_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["td", "th"])]
        if cells:
            rows.append(cells)
    return rows


def parse_wavelength_range(value: str) -> dict[str, float] | None:
    match = re.search(
        r"([-+]?\d+(?:\.\d+)?)\s*-\s*([-+]?\d+(?:\.\d+)?)\s*nm",
        value,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return {"min": float(match.group(1)), "max": float(match.group(2))}


def build_model_entries(dispersion_models: list[str]) -> list[dict[str, Any]]:
    entries = []
    for index, model_name in enumerate(dispersion_models, start=1):
        entries.append(
            {
                "model_index": index,
                "model_name": model_name,
                "parameters": {},
            }
        )
    return entries


def expected_keys(model_name: str) -> list[str]:
    return MODEL_PARAMETER_ORDER.get(model_name, [])


def assign_parameter(
    label: str,
    value: float | None,
    fit_parameters: list[dict[str, Any]],
    cursor: dict[str, int],
    global_parameters: dict[str, float | None],
) -> None:
    if value is None:
        return

    key = canonical_parameter_name(label)
    if key in GLOBAL_PARAMETER_KEYS:
        global_parameters[key] = value
        return

    if not fit_parameters:
        global_parameters[key] = value
        return

    current_index = cursor["index"]
    current_entry = fit_parameters[current_index]
    current_expected = expected_keys(current_entry["model_name"])

    if current_expected:
        next_expected_pos = cursor["positions"].get(current_index, 0)
        if next_expected_pos < len(current_expected) and key == current_expected[next_expected_pos]:
            current_entry["parameters"][key] = value
            cursor["positions"][current_index] = next_expected_pos + 1
            if cursor["positions"][current_index] >= len(current_expected) and current_index < len(fit_parameters) - 1:
                cursor["index"] += 1
            return

        if key in current_entry["parameters"]:
            current_entry["parameters"][f"{key}_{len(current_entry['parameters']) + 1}"] = value
            return

        if key in current_expected:
            for future_index in range(current_index + 1, len(fit_parameters)):
                future_expected = expected_keys(fit_parameters[future_index]["model_name"])
                future_pos = cursor["positions"].get(future_index, 0)
                if future_pos < len(future_expected) and key == future_expected[future_pos]:
                    cursor["index"] = future_index
                    assign_parameter(label, value, fit_parameters, cursor, global_parameters)
                    return

    current_entry["parameters"][key] = value


def parse_optical_model_rows(rows: list[list[str]]) -> list[str]:
    models: list[str] = []
    for row in rows:
        if len(row) >= 2:
            if compact_key(row[0]) == "dispersionlaw":
                models.append(row[1])
            elif not row[0] and row[1]:
                models.append(row[1])
    return models


def parse_results_table(rows: list[list[str]], dispersion_models: list[str]) -> tuple[float | None, float | None, dict[str, float] | None, list[dict[str, Any]], dict[str, float | None]]:
    thickness_nm: float | None = None
    rmse: float | None = None
    wavelength_range_nm: dict[str, float] | None = None
    fit_parameters = build_model_entries(dispersion_models)
    derived_parameters: dict[str, float | None] = {
        "n_at_632_8_nm": None,
        "k_at_632_8_nm": None,
    }
    global_parameters: dict[str, float | None] = {}

    phase_active = False
    derived_active = False
    derived_phase_active = False
    cursor = {"index": 0, "positions": {}}

    for row in rows:
        first_cell = row[0]
        compact_first = compact_key(first_cell)

        if compact_first == "wavelengthrange" and len(row) >= 2:
            wavelength_range_nm = parse_wavelength_range(row[1])
            continue

        if compact_first == "rmse" and len(row) >= 2:
            rmse = parse_float(row[1])
            continue

        if compact_first == "derivedparameters":
            derived_active = True
            derived_phase_active = False
            phase_active = False
            continue

        if compact_first == "fitquality":
            derived_active = False
            derived_phase_active = False
            phase_active = False
            continue

        if re.match(r"^Phase\s+\d+\s*\(.+\)$", first_cell):
            if derived_active:
                derived_phase_active = True
                continue
            phase_active = True
            continue

        if derived_active and compact_first.startswith("substrate"):
            derived_phase_active = False
            continue

        if phase_active and len(row) >= 2 and compact_first not in {"model", "aoishift", "angularaperture", "parameters"}:
            if canonical_parameter_name(first_cell) == "Thickness":
                thickness_nm = parse_float(row[1])
                continue
            assign_parameter(first_cell, parse_float(row[1]), fit_parameters, cursor, global_parameters)
            continue

        if derived_active and derived_phase_active and len(row) >= 2:
            if compact_first == "n6328nm":
                derived_parameters["n_at_632_8_nm"] = parse_float(row[1])
            elif compact_first == "k6328nm":
                derived_parameters["k_at_632_8_nm"] = parse_float(row[1])

    if global_parameters:
        fit_parameters.append(
            {
                "model_index": None,
                "model_name": "Global",
                "parameters": global_parameters,
            }
        )

    return thickness_nm, rmse, wavelength_range_nm, fit_parameters, derived_parameters


def parse_material_report(material_dir: Path) -> dict[str, Any]:
    source_md = material_dir / "full.md"
    markdown_text = source_md.read_text(encoding="utf-8")
    soup = BeautifulSoup(markdown_text, "html.parser")
    tables = [table_to_rows(table) for table in soup.find_all("table")]

    sample_id = extract_sample_id(markdown_text)
    overview_thickness_nm = extract_overview_thickness(markdown_text)

    dispersion_models: list[str] = []
    thickness_nm: float | None = None
    rmse: float | None = None
    wavelength_range_nm: dict[str, float] | None = None
    fit_parameters: list[dict[str, Any]] = []
    derived_parameters: dict[str, float | None] = {
        "n_at_632_8_nm": None,
        "k_at_632_8_nm": None,
    }

    for rows in tables:
        flat_cells = [compact_key(cell) for row in rows for cell in row]
        if "dispersionlaw" in flat_cells:
            dispersion_models = parse_optical_model_rows(rows)
        if "measurementinformation" in flat_cells and "fitquality" in flat_cells:
            (
                thickness_nm,
                rmse,
                wavelength_range_nm,
                fit_parameters,
                derived_parameters,
            ) = parse_results_table(rows, dispersion_models)

    if thickness_nm is None:
        thickness_nm = overview_thickness_nm

    requires_extrapolation = None
    if wavelength_range_nm is not None:
        requires_extrapolation = wavelength_range_nm["max"] < 1100.0

    parse_warnings: list[str] = []
    overview_section = extract_section(markdown_text, "Overview", "Optical model")
    results_section = extract_section(markdown_text, "# Reg ress ion resu lts", None)
    has_overview_image = "![](images/" in overview_section
    has_results_image = "![](images/" in results_section

    if thickness_nm is None:
        reason = "IMAGE_ONLY_ERROR" if has_overview_image or has_results_image else "MISSING"
        warning(material_dir.name, "thickness_nm", source_md, parse_warnings, reason)

    if rmse is None:
        reason = "IMAGE_ONLY_ERROR" if has_results_image else "MISSING"
        warning(material_dir.name, "rmse", source_md, parse_warnings, reason)

    if wavelength_range_nm is None:
        reason = "IMAGE_ONLY_ERROR" if has_results_image else "MISSING"
        warning(material_dir.name, "wavelength_range_nm", source_md, parse_warnings, reason)

    if not dispersion_models:
        reason = "IMAGE_ONLY_ERROR" if has_overview_image else "MISSING"
        warning(material_dir.name, "dispersion_models", source_md, parse_warnings, reason)

    if not fit_parameters:
        reason = "IMAGE_ONLY_ERROR" if has_results_image else "MISSING"
        warning(material_dir.name, "fit_parameters", source_md, parse_warnings, reason)
    else:
        for entry in fit_parameters:
            if entry["model_name"] == "Global":
                continue
            if not entry["parameters"]:
                reason = "IMAGE_ONLY_ERROR" if has_results_image else "MISSING"
                warning(
                    material_dir.name,
                    f"fit_parameters.{entry['model_name']}[{entry['model_index']}]",
                    source_md,
                    parse_warnings,
                    reason,
                )

    return {
        "material_name": material_dir.name,
        "source_md": str(source_md.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "sample_id": sample_id,
        "thickness_nm": thickness_nm,
        "rmse": rmse,
        "wavelength_range_nm": wavelength_range_nm,
        "requires_extrapolation": requires_extrapolation,
        "dispersion_models": dispersion_models,
        "fit_parameters": fit_parameters,
        "derived_parameters": derived_parameters,
        "parse_warnings": parse_warnings,
    }


def validate_database(database: dict[str, Any]) -> None:
    required_fields = {
        "thickness_nm",
        "rmse",
        "wavelength_range_nm",
        "requires_extrapolation",
        "dispersion_models",
        "fit_parameters",
        "parse_warnings",
    }
    for material_name, payload in database.items():
        missing = sorted(required_fields - payload.keys())
        if missing:
            raise ValueError(f"{material_name} missing required fields: {missing}")


def main() -> None:
    material_dirs = sorted(path for path in INPUT_ROOT.iterdir() if path.is_dir() and (path / "full.md").exists())
    database: dict[str, Any] = {}
    warning_count = 0
    failed_fields: list[str] = []

    for material_dir in material_dirs:
        payload = parse_material_report(material_dir)
        database[material_dir.name] = payload
        if payload["parse_warnings"]:
            warning_count += 1
            failed_fields.extend(f"{material_dir.name}:{item}" for item in payload["parse_warnings"])

    validate_database(database)
    OUTPUT_PATH.write_text(json.dumps(database, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Parsed {len(database)} materials into {OUTPUT_PATH}")
    print(f"Materials with warnings: {warning_count}")
    if failed_fields:
        print("Failed or image-only fields:")
        for entry in failed_fields:
            print(f"- {entry}")


if __name__ == "__main__":
    main()
