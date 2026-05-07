"""Utilities for extracting FA0.9Cs0.1PbI3 optical constants from Table S3. [LIT-0002]"""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd


EV_TO_NM = 1239.841984
DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
X01_HEADER = "ε for FA0.9Cs0.1PbI3 vs photon energy (eV)"
X02_HEADER = "ε for FA0.8Cs0.2PbI3 vs photon energy (eV)"


def _read_docx_paragraphs(docx_path: Path) -> list[str]:
    with ZipFile(docx_path) as archive:
        xml_bytes = archive.read("word/document.xml")
    root = ET.fromstring(xml_bytes)
    paragraphs: list[str] = []
    for para in root.findall(".//w:p", DOCX_NS):
        text = "".join(node.text or "" for node in para.findall(".//w:t", DOCX_NS)).strip()
        paragraphs.append(text)
    return paragraphs


def _find_index(paragraphs: list[str], marker: str) -> int:
    for idx, text in enumerate(paragraphs):
        if text == marker:
            return idx
    raise ValueError(f"在 docx 中未找到段落标记: {marker}")


def _parse_fixed_width_epsilon_row(row_text: str) -> tuple[float, float, float]:
    stripped = row_text.strip()
    if len(stripped) < 24:
        raise ValueError(f"Table S3 数据行长度不足: {row_text!r}")
    photon_energy_ev = float(stripped[:8])
    epsilon_1 = float(stripped[8:16])
    epsilon_2 = float(stripped[16:])
    return photon_energy_ev, epsilon_1, epsilon_2


def extract_x01_epsilon_from_docx(docx_path: Path) -> pd.DataFrame:
    """Extract Table S3 x=0.1 epsilon rows from the supplementary docx. [LIT-0002]"""
    paragraphs = _read_docx_paragraphs(docx_path)
    start_idx = _find_index(paragraphs, X01_HEADER)
    end_idx = _find_index(paragraphs, X02_HEADER)
    if end_idx <= start_idx:
        raise ValueError("docx 中 x=0.1 / x=0.2 章节顺序异常。")

    rows: list[tuple[float, float, float]] = []
    for text in paragraphs[start_idx + 1 : end_idx]:
        if not text or text.startswith("Photon Energy"):
            continue
        if not text[0].isdigit():
            continue
        rows.append(_parse_fixed_width_epsilon_row(text))

    if len(rows) == 0:
        raise ValueError("未从 Table S3 x=0.1 区块提取到任何 epsilon 数据行。")

    frame = pd.DataFrame(rows, columns=["Photon_Energy_eV", "Epsilon1", "Epsilon2"])
    return frame


def epsilon_to_nk_table(epsilon_df: pd.DataFrame) -> pd.DataFrame:
    """Convert epsilon1/epsilon2 to wavelength/n/k. [LIT-0002]"""
    required = ["Photon_Energy_eV", "Epsilon1", "Epsilon2"]
    missing = [column for column in required if column not in epsilon_df.columns]
    if missing:
        raise ValueError(f"epsilon_df 缺少必要列: {missing}")

    photon_energy_ev = epsilon_df["Photon_Energy_eV"].to_numpy(dtype=float)
    epsilon_1 = epsilon_df["Epsilon1"].to_numpy(dtype=float)
    epsilon_2 = epsilon_df["Epsilon2"].to_numpy(dtype=float)
    epsilon_abs = np.sqrt(epsilon_1**2 + epsilon_2**2)
    n_values = np.sqrt((epsilon_abs + epsilon_1) / 2.0)
    k_values = np.sqrt(np.maximum((epsilon_abs - epsilon_1) / 2.0, 0.0))
    wavelength_nm = EV_TO_NM / photon_energy_ev

    frame = pd.DataFrame(
        {
            "Photon_Energy_eV": photon_energy_ev,
            "Wavelength_nm": wavelength_nm,
            "Epsilon1": epsilon_1,
            "Epsilon2": epsilon_2,
            "n": n_values,
            "k": k_values,
        }
    ).sort_values("Wavelength_nm", ascending=True, ignore_index=True)
    return frame


def build_phase08_x01_aligned_nk(base_nk_csv: Path, x01_nk_csv: Path) -> pd.DataFrame:
    """Replace only PVK n/k in the aligned stack using x=0.1 literature data. [LIT-0002]"""
    base_df = pd.read_csv(base_nk_csv)
    x01_df = pd.read_csv(x01_nk_csv)

    required_base = {"Wavelength_nm", "n_PVK", "k_PVK"}
    required_x01 = {"Wavelength_nm", "n", "k"}
    if not required_base.issubset(base_df.columns):
        raise ValueError(f"{base_nk_csv} 缺少必要列: {sorted(required_base - set(base_df.columns))}")
    if not required_x01.issubset(x01_df.columns):
        raise ValueError(f"{x01_nk_csv} 缺少必要列: {sorted(required_x01 - set(x01_df.columns))}")

    x01_sorted = x01_df.sort_values("Wavelength_nm", ascending=True, ignore_index=True)
    base_wavelength_nm = base_df["Wavelength_nm"].to_numpy(dtype=float)
    x01_wavelength_nm = x01_sorted["Wavelength_nm"].to_numpy(dtype=float)
    if base_wavelength_nm.min() < x01_wavelength_nm.min() or base_wavelength_nm.max() > x01_wavelength_nm.max():
        raise ValueError("x=0.1 文献 nk 波长覆盖不足，无法无外推替换当前 aligned_full_stack_nk 网格。")

    output_df = base_df.copy()
    output_df["n_PVK"] = np.interp(
        base_wavelength_nm,
        x01_wavelength_nm,
        x01_sorted["n"].to_numpy(dtype=float),
    )
    output_df["k_PVK"] = np.interp(
        base_wavelength_nm,
        x01_wavelength_nm,
        x01_sorted["k"].to_numpy(dtype=float),
    )
    return output_df
