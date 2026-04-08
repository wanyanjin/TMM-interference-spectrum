"""Phase 05b cross-validation for materials_master_db.json against source PDFs.

This script verifies the Phase 05 Markdown-derived material database using the
original ellipsometry PDFs under ``resources/n-kdata``. PDF text is extracted
with PyMuPDF and used to:

- validate macro anchors (thickness, RMSE, wavelength range)
- validate optical-model completeness
- backfill missing parameters only when JSON data is absent

The script preserves the existing JSON schema and only appends a
``pdf_validation`` block per material.
"""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import fitz


PROJECT_ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = PROJECT_ROOT / "resources" / "materials_master_db.json"
PDF_ROOT = PROJECT_ROOT / "resources" / "n-kdata"

MODEL_PARAMETER_ORDER = {
    "Tauc-Lorentz": ["A", "E0", "C", "Eg"],
    "Lorentz": ["f", "E0", "Γ"],
    "Cauchy": ["B", "C", "D", "E", "F"],
    "Gauss": ["Amp", "E0", "Br"],
    "Drude": [],
}
GLOBAL_PARAMETER_KEYS = {"Eps_inf", "N_inf"}
GAMMA_ALIASES = ("Γ", "Gamma", "ŚŁ", "螕")
EXPLICIT_PDF_MAP = {"sno": "sno拟合曲线.pdf"}
MODEL_PATTERN = re.compile(r"(Tauc-Lorentz|Cauchy|Drude|Lorentz|Gauss)")


def normalize_pdf_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def load_pdf_text(pdf_path: Path) -> tuple[str, str]:
    with fitz.open(pdf_path) as document:
        page_texts = [page.get_text() for page in document]
    raw_text = "\n".join(page_texts)
    compact_text = normalize_whitespace(raw_text)
    return raw_text, compact_text


def find_pdf_for_material(material_name: str) -> Path | None:
    explicit_name = EXPLICIT_PDF_MAP.get(material_name)
    if explicit_name:
        candidate = PDF_ROOT / explicit_name
        if candidate.exists():
            return candidate

    target = normalize_pdf_key(material_name)
    candidates: list[Path] = []
    for pdf_path in PDF_ROOT.glob("*.pdf"):
        stem_key = normalize_pdf_key(pdf_path.stem)
        if stem_key == target or target in stem_key or stem_key in target:
            candidates.append(pdf_path)

    if len(candidates) == 1:
        return candidates[0]
    return None


def parse_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if not match:
        return None
    return float(match.group(1))


def parse_anchor_values(raw_text: str) -> dict[str, Any]:
    thickness_nm = parse_float(r"Thickness\s+([0-9]+(?:\.[0-9]+)?)\s+X?\s*[0-9.]*\s*nm", raw_text)
    if thickness_nm is None:
        thickness_nm = parse_float(r"Thickness\s*[=:]?\s*([0-9]+(?:\.[0-9]+)?)\s*nm", raw_text)

    rmse = parse_float(r"RMSE\s+([0-9]+(?:\.[0-9]+)?)", raw_text)

    wavelength_match = re.search(
        r"Wavelength range\s+([0-9]+(?:\.[0-9]+)?)\s*-\s*([0-9]+(?:\.[0-9]+)?)\s*nm",
        raw_text,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    wavelength_range_nm = None
    if wavelength_match:
        wavelength_range_nm = {
            "min": float(wavelength_match.group(1)),
            "max": float(wavelength_match.group(2)),
        }

    return {
        "thickness_nm": thickness_nm,
        "rmse": rmse,
        "wavelength_range_nm": wavelength_range_nm,
    }


def extract_optical_model_block(raw_text: str) -> str:
    match = re.search(
        r"Optical model(?P<body>.*?)(Regression results|Page 1|Results)",
        raw_text,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return match.group("body") if match else raw_text[:2000]


def extract_results_block(raw_text: str) -> str:
    match = re.search(
        r"Results(?P<body>.*?)(Derived parameters|Fit quality)",
        raw_text,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return match.group("body") if match else raw_text


def extract_global_block(raw_text: str) -> str:
    match = re.search(
        r"Results(?P<body>.*?)(Derived parameters)",
        raw_text,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return match.group("body") if match else raw_text


def parse_models_from_pdf(raw_text: str) -> list[str]:
    block = extract_optical_model_block(raw_text)
    return MODEL_PATTERN.findall(block)


def parameter_key_in_entry(parameters: dict[str, Any], canonical_key: str) -> str:
    if canonical_key == "Γ":
        for alias in GAMMA_ALIASES:
            if alias in parameters:
                return alias
    return canonical_key


def choose_parameter_key(parameters: dict[str, Any], canonical_key: str) -> str:
    if canonical_key == "Γ":
        for alias in GAMMA_ALIASES:
            if alias in parameters:
                return alias
    return canonical_key


def extract_model_parameters_from_pdf(raw_text: str, model_name: str, model_occurrence: int) -> dict[str, float]:
    results_block = extract_results_block(raw_text)
    section_pattern = re.compile(
        r"Phase\s+\d+\s*\([^)]+\)\s*(?P<body>.*?)(?:Derived parameters|Fit quality)",
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = section_pattern.search(results_block)
    block = match.group("body") if match else results_block

    model_order = parse_models_from_pdf(raw_text)
    keys = MODEL_PARAMETER_ORDER.get(model_name, [])
    extracted: dict[str, float] = {}
    if not keys:
        return extracted

    if model_name not in model_order:
        return extracted

    current_occurrence = -1
    last_end = 0

    for key in keys:
        label_pattern = re.escape(key)
        if key == "Γ":
            label_pattern = r"(?:Γ|Gamma)"
        regex = re.compile(
            rf"{label_pattern}\s*(?:\([^)]+\))?\s+([-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?)",
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )

        matches = list(regex.finditer(block, last_end))
        if not matches:
            continue

        if key == keys[0]:
            if model_occurrence >= len(matches):
                break
            selected = matches[model_occurrence]
            current_occurrence = model_occurrence
        else:
            if current_occurrence == -1 or current_occurrence >= len(matches):
                break
            selected = matches[current_occurrence]

        extracted[key] = float(selected.group(1))
        last_end = selected.end()

    return extracted


def extract_global_parameters_from_pdf(raw_text: str) -> dict[str, float]:
    block = extract_global_block(raw_text)
    extracted: dict[str, float] = {}
    for key in GLOBAL_PARAMETER_KEYS:
        match = re.search(
            rf"{re.escape(key)}\s+([-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?)",
            block,
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
        if match:
            extracted[key] = float(match.group(1))
    return extracted


def values_close(lhs: float | None, rhs: float | None, tolerance: float) -> bool:
    if lhs is None or rhs is None:
        return False
    return abs(lhs - rhs) <= tolerance


def maybe_update_anchor(payload: dict[str, Any], anchor_name: str, pdf_value: Any, tolerance: float, repaired_fields: list[str], checks_passed: list[str]) -> None:
    if pdf_value is None:
        return

    current_value = payload.get(anchor_name)
    if isinstance(pdf_value, dict):
        current_range = current_value or {}
        min_match = values_close(current_range.get("min"), pdf_value["min"], tolerance)
        max_match = values_close(current_range.get("max"), pdf_value["max"], tolerance)
        if min_match and max_match:
            checks_passed.append(anchor_name)
            return
        payload[anchor_name] = pdf_value
        repaired_fields.append(anchor_name)
        payload["requires_extrapolation"] = pdf_value["max"] < 1100.0
        return

    if current_value is None:
        payload[anchor_name] = pdf_value
        repaired_fields.append(anchor_name)
        return

    if values_close(current_value, pdf_value, tolerance):
        checks_passed.append(anchor_name)
    else:
        payload[anchor_name] = pdf_value
        repaired_fields.append(anchor_name)


def validate_models(payload: dict[str, Any], pdf_models: list[str], checks_passed: list[str], manual_review_fields: list[str]) -> None:
    json_models = payload.get("dispersion_models", [])
    if json_models == pdf_models:
        checks_passed.append("dispersion_models")
        return

    manual_review_fields.append(
        f"MODEL_MISMATCH:json={json_models};pdf={pdf_models}"
    )


def backfill_missing_parameters(payload: dict[str, Any], raw_text: str, repaired_fields: list[str], manual_review_fields: list[str]) -> None:
    fit_parameters = payload.get("fit_parameters", [])
    model_occurrences: dict[str, int] = {}
    for entry in fit_parameters:
        model_name = entry.get("model_name")
        parameters = entry.get("parameters", {})
        if model_name == "Global":
            extracted = extract_global_parameters_from_pdf(raw_text)
            for key in GLOBAL_PARAMETER_KEYS:
                if parameters.get(key) is None and key in extracted:
                    parameters[key] = extracted[key]
                    repaired_fields.append(f"fit_parameters.Global.{key}")
            continue

        occurrence = model_occurrences.get(model_name, 0)
        model_occurrences[model_name] = occurrence + 1

        if parameters:
            continue

        model_index = entry.get("model_index") or 1
        extracted = extract_model_parameters_from_pdf(raw_text, model_name, occurrence)
        expected_keys = MODEL_PARAMETER_ORDER.get(model_name, [])
        if not extracted:
            manual_review_fields.append(f"MANUAL_REVIEW_REQUIRED:fit_parameters.{model_name}[{model_index}]")
            continue

        for canonical_key in expected_keys:
            if canonical_key in extracted:
                entry["parameters"][choose_parameter_key(entry["parameters"], canonical_key)] = extracted[canonical_key]

        missing_after_fill = [key for key in expected_keys if parameter_key_in_entry(entry["parameters"], key) not in entry["parameters"]]
        if missing_after_fill:
            manual_review_fields.append(
                f"MANUAL_REVIEW_REQUIRED:fit_parameters.{model_name}[{model_index}] missing={missing_after_fill}"
            )
        else:
            repaired_fields.append(f"fit_parameters.{model_name}[{model_index}]")


def build_validation_block(pdf_path: Path | None, checks_passed: list[str], repaired_fields: list[str], manual_review_fields: list[str]) -> dict[str, Any]:
    return {
        "pdf_source": str(pdf_path.relative_to(PROJECT_ROOT)).replace("\\", "/") if pdf_path else None,
        "checks_passed": checks_passed,
        "repaired_fields": repaired_fields,
        "manual_review_fields": manual_review_fields,
    }


def validate_material(material_name: str, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    updated_payload = deepcopy(payload)
    checks_passed: list[str] = []
    repaired_fields: list[str] = []
    manual_review_fields: list[str] = []

    pdf_path = find_pdf_for_material(material_name)
    if pdf_path is None:
        manual_review_fields.append("MANUAL_REVIEW_REQUIRED:pdf_not_found")
        updated_payload["pdf_validation"] = build_validation_block(None, checks_passed, repaired_fields, manual_review_fields)
        summary = (
            f"[{material_name}] PDF=missing | repaired=none | manual_review={manual_review_fields}"
        )
        return updated_payload, summary

    raw_text, _ = load_pdf_text(pdf_path)
    anchors = parse_anchor_values(raw_text)
    pdf_models = parse_models_from_pdf(raw_text)

    maybe_update_anchor(updated_payload, "thickness_nm", anchors["thickness_nm"], 0.01, repaired_fields, checks_passed)
    maybe_update_anchor(updated_payload, "rmse", anchors["rmse"], 1e-6, repaired_fields, checks_passed)
    maybe_update_anchor(updated_payload, "wavelength_range_nm", anchors["wavelength_range_nm"], 0.01, repaired_fields, checks_passed)

    if updated_payload.get("wavelength_range_nm"):
        updated_payload["requires_extrapolation"] = updated_payload["wavelength_range_nm"]["max"] < 1100.0

    validate_models(updated_payload, pdf_models, checks_passed, manual_review_fields)
    backfill_missing_parameters(updated_payload, raw_text, repaired_fields, manual_review_fields)

    updated_payload["pdf_validation"] = build_validation_block(pdf_path, checks_passed, repaired_fields, manual_review_fields)

    summary = (
        f"[{material_name}] PDF=ok | checks={checks_passed or ['none']} | "
        f"repaired={repaired_fields or ['none']} | manual_review={manual_review_fields or ['none']}"
    )
    return updated_payload, summary


def print_summary(material_summaries: list[str], database: dict[str, Any]) -> None:
    print("Validation Summary")
    print("=" * 72)
    for line in material_summaries:
        print(line)

    total = len(database)
    all_passed = 0
    auto_repaired = 0
    manual_review = 0
    for payload in database.values():
        validation = payload.get("pdf_validation", {})
        if validation.get("repaired_fields"):
            auto_repaired += 1
        if validation.get("manual_review_fields"):
            manual_review += 1
        if not validation.get("repaired_fields") and not validation.get("manual_review_fields"):
            all_passed += 1

    print("-" * 72)
    print(f"Materials total: {total}")
    print(f"All checks passed without repair: {all_passed}")
    print(f"Materials auto-repaired: {auto_repaired}")
    print(f"Materials requiring manual review: {manual_review}")


def validate_database_shape(database: dict[str, Any]) -> None:
    required = {
        "thickness_nm",
        "rmse",
        "wavelength_range_nm",
        "requires_extrapolation",
        "dispersion_models",
        "fit_parameters",
        "parse_warnings",
    }
    for material_name, payload in database.items():
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"{material_name} missing required fields after validation: {missing}")


def run_validation(database_path: Path, write: bool) -> dict[str, Any]:
    database = json.loads(database_path.read_text(encoding="utf-8"))
    updated_database: dict[str, Any] = {}
    material_summaries: list[str] = []

    for material_name in sorted(database):
        updated_payload, summary = validate_material(material_name, database[material_name])
        updated_database[material_name] = updated_payload
        material_summaries.append(summary)

    validate_database_shape(updated_database)
    print_summary(material_summaries, updated_database)

    if write:
        database_path.write_text(json.dumps(updated_database, indent=2, ensure_ascii=False), encoding="utf-8")

    return updated_database


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-validate materials_master_db.json against source PDFs.")
    parser.add_argument("--json", default=str(JSON_PATH), help="Path to materials_master_db.json")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing changes back")
    args = parser.parse_args()

    run_validation(Path(args.json), write=not args.dry_run)


if __name__ == "__main__":
    main()
