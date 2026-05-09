"""Fetch Si / SiO2 optical constants from refractiveindex.info.

This script preserves two raw artifacts for each selected material page:
1. CSV export from the website UI
2. Full database record (YAML)

It then standardizes the data into project-friendly `Wavelength_nm / n / k`
CSV files plus a small JSON index for later reuse.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import math
import re
import sys
from typing import Any
from urllib.request import urlopen

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "resources" / "refractiveindex_info"
DATABASE_CITATION = (
    "M. N. Polyanskiy. Refractiveindex.info database of optical constants. "
    "Sci. Data 11, 94 (2024). https://doi.org/10.1038/s41597-023-02898-2"
)


@dataclass(frozen=True)
class MaterialSpec:
    material: str
    page_label: str
    page_url: str
    csv_url: str
    full_record_url: str
    normalized_filename: str
    normalized_kind: str
    notes: str


MATERIAL_SPECS: dict[str, MaterialSpec] = {
    "Si": MaterialSpec(
        material="Si",
        page_label="Schinke et al. 2015: n,k 0.25-1.45 um",
        page_url="https://refractiveindex.info/?shelf=main&book=Si&page=Schinke",
        csv_url="https://refractiveindex.info/data_csv.php?datafile=database/data/main/Si/nk/Schinke.yml",
        full_record_url="https://refractiveindex.info/database/data/main/Si/nk/Schinke.yml",
        normalized_filename="si_schinke_2015_nk.csv",
        normalized_kind="tabulated_nk",
        notes="Normalized CSV preserves the full tabulated Schinke 2015 wavelength coverage.",
    ),
    "SiO2": MaterialSpec(
        material="SiO2",
        page_label="Malitson 1965: n 0.21-6.7 um",
        page_url="https://refractiveindex.info/?shelf=main&book=SiO2&page=Malitson",
        csv_url="https://refractiveindex.info/data_csv.php?datafile=database/data/main/SiO2/nk/Malitson.yml",
        full_record_url="https://refractiveindex.info/database/data/main/SiO2/nk/Malitson.yml",
        normalized_filename="sio2_malitson_1965_nk_400_1100nm.csv",
        normalized_kind="formula_1_with_zero_k",
        notes="Bulk fused silica baseline; n is evaluated on 400-1100 nm / 1 nm grid and k is set to 0 in this band.",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and normalize refractiveindex.info material sources.")
    parser.add_argument(
        "--materials",
        nargs="+",
        choices=sorted(MATERIAL_SPECS.keys()),
        default=sorted(MATERIAL_SPECS.keys()),
        help="Material pages to fetch. Default: Si SiO2",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Output root for raw and normalized refractiveindex.info assets.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="Network timeout for each download request.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and print the planned downloads without writing files.",
    )
    return parser.parse_args()


def fetch_text(url: str, timeout_seconds: float) -> str:
    with urlopen(url, timeout=timeout_seconds) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset)


def extract_literal_block(yaml_text: str, key: str, next_keys: tuple[str, ...]) -> str:
    pattern = rf"^{re.escape(key)}:\s*\|\s*\n(?P<body>(?:^[ ]{{4}}.*\n?)*)"
    match = re.search(pattern, yaml_text, flags=re.MULTILINE)
    if not match:
        return ""
    body = match.group("body")
    lines = [line[4:] if line.startswith("    ") else line for line in body.splitlines()]
    text = "\n".join(lines).strip()
    for next_key in next_keys:
        if text.endswith(next_key + ":"):
            text = text[: -(len(next_key) + 1)].rstrip()
    return text


def parse_tabulated_nk_yaml(yaml_text: str) -> pd.DataFrame:
    data_match = re.search(r"^\s*data:\s*\|\s*\n(?P<body>(?:^[ ]{8}.*\n?)*)", yaml_text, flags=re.MULTILINE)
    if not data_match:
        raise ValueError("YAML 中未找到 tabulated nk data block。")
    rows: list[tuple[float, float, float]] = []
    for raw_line in data_match.group("body").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 3:
            raise ValueError(f"tabulated nk 数据行格式错误: {line!r}")
        wavelength_um, n_value, k_value = (float(item) for item in parts)
        rows.append((wavelength_um, n_value, k_value))
    if not rows:
        raise ValueError("tabulated nk data block 为空。")
    frame = pd.DataFrame(rows, columns=["Wavelength_um", "n", "k"])
    frame["Wavelength_nm"] = frame["Wavelength_um"] * 1000.0
    return frame[["Wavelength_nm", "n", "k"]]


def parse_formula_1_coefficients(yaml_text: str) -> tuple[tuple[float, float], list[float]]:
    range_match = re.search(r"wavelength_range:\s*([0-9Ee+\-.]+)\s+([0-9Ee+\-.]+)", yaml_text)
    coeff_match = re.search(r"coefficients:\s*(.+)", yaml_text)
    if not range_match or not coeff_match:
        raise ValueError("formula 1 YAML 缺少 wavelength_range 或 coefficients。")
    wavelength_range_um = (float(range_match.group(1)), float(range_match.group(2)))
    coefficients = [float(item) for item in coeff_match.group(1).split()]
    if len(coefficients) < 3 or (len(coefficients) - 1) % 2 != 0:
        raise ValueError("formula 1 coefficients 格式错误。")
    return wavelength_range_um, coefficients


def evaluate_formula_1_n(wavelength_um: np.ndarray, coefficients: list[float]) -> np.ndarray:
    lambda_sq = np.asarray(wavelength_um, dtype=float) ** 2
    epsilon = np.full_like(lambda_sq, coefficients[0], dtype=float)
    for index in range(1, len(coefficients), 2):
        b_value = coefficients[index]
        c_value = coefficients[index + 1]
        epsilon += b_value * lambda_sq / (lambda_sq - c_value**2)
    n_sq = 1.0 + epsilon
    if np.any(n_sq <= 0.0):
        raise ValueError("formula 1 计算得到非正 n^2。")
    return np.sqrt(n_sq)


def build_sio2_formula_csv(yaml_text: str) -> pd.DataFrame:
    wavelength_range_um, coefficients = parse_formula_1_coefficients(yaml_text)
    wavelength_nm = np.arange(400.0, 1101.0, 1.0, dtype=float)
    wavelength_um = wavelength_nm / 1000.0
    if wavelength_um.min() < wavelength_range_um[0] or wavelength_um.max() > wavelength_range_um[1]:
        raise ValueError(
            f"SiO2 formula 覆盖不足，范围为 {wavelength_range_um[0]}-{wavelength_range_um[1]} um，"
            "无法生成 400-1100 nm 标准化 CSV。"
        )
    n_values = evaluate_formula_1_n(wavelength_um=wavelength_um, coefficients=coefficients)
    k_values = np.zeros_like(n_values, dtype=float)
    return pd.DataFrame({"Wavelength_nm": wavelength_nm, "n": n_values, "k": k_values})


def ensure_dirs(output_root: Path, materials: list[str]) -> dict[str, Path]:
    raw_root = output_root / "raw"
    normalized_root = output_root / "normalized"
    raw_root.mkdir(parents=True, exist_ok=True)
    normalized_root.mkdir(parents=True, exist_ok=True)
    for material in materials:
        (raw_root / material).mkdir(parents=True, exist_ok=True)
    return {
        "raw_root": raw_root,
        "normalized_root": normalized_root,
    }


def relative_posix(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def build_material_entry(
    spec: MaterialSpec,
    raw_csv_path: Path,
    raw_yaml_path: Path,
    normalized_csv_path: Path,
    references: str,
    comments: str,
    normalized_df: pd.DataFrame,
) -> dict[str, Any]:
    return {
        "material": spec.material,
        "page_label": spec.page_label,
        "page_url": spec.page_url,
        "csv_url": spec.csv_url,
        "full_record_url": spec.full_record_url,
        "raw_files": {
            "csv_export": relative_posix(raw_csv_path),
            "full_database_record": relative_posix(raw_yaml_path),
        },
        "normalized_csv": relative_posix(normalized_csv_path),
        "normalized_kind": spec.normalized_kind,
        "wavelength_range_nm": {
            "min": float(normalized_df["Wavelength_nm"].min()),
            "max": float(normalized_df["Wavelength_nm"].max()),
            "count": int(normalized_df.shape[0]),
        },
        "references": references,
        "comments": comments,
        "notes": spec.notes,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    selected = sorted(dict.fromkeys(args.materials))
    dirs = ensure_dirs(output_root=args.output_root, materials=selected)
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    if args.dry_run:
        return {
            "fetched_at_utc": fetched_at,
            "output_root": str(args.output_root),
            "materials": [
                {
                    "material": MATERIAL_SPECS[name].material,
                    "page_url": MATERIAL_SPECS[name].page_url,
                    "csv_url": MATERIAL_SPECS[name].csv_url,
                    "full_record_url": MATERIAL_SPECS[name].full_record_url,
                }
                for name in selected
            ],
        }

    entries: list[dict[str, Any]] = []
    for material_name in selected:
        spec = MATERIAL_SPECS[material_name]
        raw_dir = dirs["raw_root"] / spec.material
        raw_csv_text = fetch_text(spec.csv_url, timeout_seconds=args.timeout_seconds)
        raw_yaml_text = fetch_text(spec.full_record_url, timeout_seconds=args.timeout_seconds)

        raw_csv_path = raw_dir / f"{spec.material}_{spec.page_label.split(':', 1)[0].replace(' ', '_').replace('.', '')}.csv"
        raw_yaml_path = raw_dir / f"{spec.material}_{spec.page_label.split(':', 1)[0].replace(' ', '_').replace('.', '')}.yml"
        normalized_csv_path = dirs["normalized_root"] / spec.normalized_filename

        write_text(raw_csv_path, raw_csv_text)
        write_text(raw_yaml_path, raw_yaml_text)

        references = extract_literal_block(raw_yaml_text, "REFERENCES", ("COMMENTS", "DATA", "CONDITIONS"))
        comments = extract_literal_block(raw_yaml_text, "COMMENTS", ("DATA", "CONDITIONS"))

        if spec.material == "Si":
            normalized_df = parse_tabulated_nk_yaml(raw_yaml_text)
        elif spec.material == "SiO2":
            normalized_df = build_sio2_formula_csv(raw_yaml_text)
        else:
            raise ValueError(f"未实现的材料: {spec.material}")

        if not np.isfinite(normalized_df[["Wavelength_nm", "n", "k"]].to_numpy(dtype=float)).all():
            raise ValueError(f"{spec.material} 标准化 CSV 含 NaN/Inf。")
        if (normalized_df["k"].to_numpy(dtype=float) < 0.0).any():
            raise ValueError(f"{spec.material} 标准化 CSV 含负 k。")
        if not np.all(np.diff(normalized_df["Wavelength_nm"].to_numpy(dtype=float)) > 0.0):
            raise ValueError(f"{spec.material} 标准化 CSV 波长未严格递增。")

        normalized_df.to_csv(normalized_csv_path, index=False, encoding="utf-8")
        entries.append(
            build_material_entry(
                spec=spec,
                raw_csv_path=raw_csv_path,
                raw_yaml_path=raw_yaml_path,
                normalized_csv_path=normalized_csv_path,
                references=references,
                comments=comments,
                normalized_df=normalized_df,
            )
        )

    manifest = {
        "fetched_at_utc": fetched_at,
        "source_site": "https://refractiveindex.info",
        "database_citation": DATABASE_CITATION,
        "entries": entries,
    }
    manifest_path = args.output_root / "refractiveindex_info_index.json"
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


def main() -> None:
    args = parse_args()
    payload = run(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
