"""Compute normal-incidence Fresnel reflectance for the Si/Air interface."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


PHASE_NAME = "Phase 09F"
INPUT_CSV = PROJECT_ROOT / "resources" / "refractiveindex_info" / "normalized" / "si_schinke_2015_nk.csv"
OUTPUT_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "phase09" / "si_air_interface"
OUTPUT_FIG_DIR = PROJECT_ROOT / "results" / "figures" / "phase09" / "si_air_interface"
OUTPUT_REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phase09_si_air_interface"

WAVELENGTH_MIN_NM = 400.0
WAVELENGTH_MAX_NM = 1100.0
N_AIR = 1.0 + 0.0j


def ensure_dirs() -> None:
    for path in (OUTPUT_DATA_DIR, OUTPUT_FIG_DIR, OUTPUT_REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_si_nk(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"Wavelength_nm", "n", "k"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{path} 缺少必要列: {missing}")
    subset = frame[(frame["Wavelength_nm"] >= WAVELENGTH_MIN_NM) & (frame["Wavelength_nm"] <= WAVELENGTH_MAX_NM)].copy()
    if subset.empty:
        raise ValueError("Si nk 数据未覆盖 400-1100 nm。")
    if float(subset["Wavelength_nm"].min()) > WAVELENGTH_MIN_NM or float(subset["Wavelength_nm"].max()) < WAVELENGTH_MAX_NM:
        raise ValueError("Si nk 数据在 400-1100 nm 范围内覆盖不完整。")
    return subset.reset_index(drop=True)


def fresnel_reflectance_air_to_material(material_nk: np.ndarray) -> np.ndarray:
    reflection = (N_AIR - material_nk) / (N_AIR + material_nk)
    return np.abs(reflection) ** 2


def build_output_frame(si_frame: pd.DataFrame) -> pd.DataFrame:
    material_nk = si_frame["n"].to_numpy(dtype=float) + 1j * si_frame["k"].to_numpy(dtype=float)
    reflectance = fresnel_reflectance_air_to_material(material_nk)
    return pd.DataFrame(
        {
            "Wavelength_nm": si_frame["Wavelength_nm"].to_numpy(dtype=float),
            "n_Si": si_frame["n"].to_numpy(dtype=float),
            "k_Si": si_frame["k"].to_numpy(dtype=float),
            "R_Si_Air": reflectance,
        }
    )


def plot_reflectance(output_frame: pd.DataFrame, png_path: Path, pdf_path: Path) -> None:
    wavelengths = output_frame["Wavelength_nm"].to_numpy(dtype=float)
    reflectance = output_frame["R_Si_Air"].to_numpy(dtype=float)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "legend.fontsize": 9.5,
        }
    )

    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=300, constrained_layout=True)
    ax.plot(wavelengths, reflectance, color="#005f73", linewidth=2.0, label="Si / Air")
    ax.set_xlim(WAVELENGTH_MIN_NM, WAVELENGTH_MAX_NM)
    ax.set_ylim(0.0, 0.65)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Reflectance (0-1)")
    ax.set_title("Si / Air Interface Reflectance")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")

    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path, dpi=300)
    plt.close(fig)


def build_manifest(output_frame: pd.DataFrame, csv_path: Path, png_path: Path, pdf_path: Path, report_path: Path) -> dict[str, object]:
    wavelength_nm = output_frame["Wavelength_nm"].to_numpy(dtype=float)
    reflectance = output_frame["R_Si_Air"].to_numpy(dtype=float)
    return {
        "phase": PHASE_NAME,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "input_csv": INPUT_CSV.relative_to(PROJECT_ROOT).as_posix(),
        "interface": "Air / Si",
        "incidence": {
            "angle_deg": 0.0,
            "polarization": "unpolarized_equivalent_at_normal_incidence",
        },
        "formula": "R = |(n_air - n_si)/(n_air + n_si)|^2",
        "outputs": {
            "csv": csv_path.relative_to(PROJECT_ROOT).as_posix(),
            "figure_png": png_path.relative_to(PROJECT_ROOT).as_posix(),
            "figure_pdf": pdf_path.relative_to(PROJECT_ROOT).as_posix(),
            "report_md": report_path.relative_to(PROJECT_ROOT).as_posix(),
        },
        "summary": {
            "wavelength_min_nm": float(wavelength_nm.min()),
            "wavelength_max_nm": float(wavelength_nm.max()),
            "point_count": int(output_frame.shape[0]),
            "reflectance_min": float(reflectance.min()),
            "reflectance_max": float(reflectance.max()),
            "reflectance_400nm": float(output_frame.loc[output_frame["Wavelength_nm"] == 400.0, "R_Si_Air"].iloc[0]),
            "reflectance_600nm": float(output_frame.loc[output_frame["Wavelength_nm"] == 600.0, "R_Si_Air"].iloc[0]),
            "reflectance_1100nm": float(output_frame.loc[output_frame["Wavelength_nm"] == 1100.0, "R_Si_Air"].iloc[0]),
        },
    }


def render_report(manifest: dict[str, object], report_path: Path) -> None:
    summary = manifest["summary"]
    lines = [
        "# Phase 09F Si/Air Interface Reflectance",
        "",
        "## 1. 执行摘要",
        "",
        "- 使用 `refractiveindex.info` 的 `Si / Schinke 2015` 标准化 `n/k` 数据，计算了 `Si/Air` 在 `400-1100 nm` 的法向入射反射率。",
        "- 模型为单界面 Fresnel 反射，不含薄膜干涉、粗糙层、角度平均或表面氧化层。",
        "",
        "## 2. 输入与公式",
        "",
        f"- 输入 `n/k`：`{manifest['input_csv']}`",
        "- 界面：`Air / Si`",
        "- 入射条件：法向入射",
        "",
        "$$",
        "R(\\lambda)=\\left|\\frac{n_{\\mathrm{air}}-\\tilde{n}_{\\mathrm{Si}}(\\lambda)}{n_{\\mathrm{air}}+\\tilde{n}_{\\mathrm{Si}}(\\lambda)}\\right|^2",
        "$$",
        "",
        "## 3. 关键结果",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| wavelength range (nm) | {summary['wavelength_min_nm']:.0f}-{summary['wavelength_max_nm']:.0f} |",
        f"| point count | {summary['point_count']} |",
        f"| reflectance min | {summary['reflectance_min']:.6f} |",
        f"| reflectance max | {summary['reflectance_max']:.6f} |",
        f"| reflectance 400 nm | {summary['reflectance_400nm']:.6f} |",
        f"| reflectance 600 nm | {summary['reflectance_600nm']:.6f} |",
        f"| reflectance 1100 nm | {summary['reflectance_1100nm']:.6f} |",
        "",
        "## 4. 输出文件",
        "",
        f"- CSV: `{manifest['outputs']['csv']}`",
        f"- Figure PNG: `{manifest['outputs']['figure_png']}`",
        f"- Figure PDF: `{manifest['outputs']['figure_pdf']}`",
        "",
        "## 5. 风险与假设",
        "",
        "- 这里是理想平整 `Si/Air` 单界面模型，不代表含原生氧化层、粗糙度或多层结构的真实样品表面。",
        "- `Si` 的 `n/k` 来自 `Schinke 2015`，波段覆盖 `250-1450 nm`；本次仅截取 `400-1100 nm`。",
        "- 结果为能量反射率 `0-1`，不是百分比。",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    si_frame = load_si_nk(INPUT_CSV)
    output_frame = build_output_frame(si_frame)

    csv_path = OUTPUT_DATA_DIR / "phase09f_si_air_reflectance.csv"
    manifest_path = OUTPUT_DATA_DIR / "phase09f_si_air_reflectance_manifest.json"
    png_path = OUTPUT_FIG_DIR / "phase09f_si_air_reflectance.png"
    pdf_path = OUTPUT_FIG_DIR / "phase09f_si_air_reflectance.pdf"
    report_path = OUTPUT_REPORT_DIR / "phase09f_si_air_reflectance_report.md"

    output_frame.to_csv(csv_path, index=False)
    plot_reflectance(output_frame, png_path, pdf_path)
    manifest = build_manifest(output_frame, csv_path, png_path, pdf_path, report_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_report(manifest, report_path)


if __name__ == "__main__":
    main()
