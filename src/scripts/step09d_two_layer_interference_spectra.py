"""Generate two-layer TMM interference spectra for glass/PVK and PVK/glass.

This script reuses the aligned optical-constant table already tracked in the
repository. The PVK columns in that table trace back to the documented project
literature sources in `docs/LITERATURE_MAP.md`, primarily [LIT-0001] with
Phase 08 comparison support from [LIT-0002].
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math
import sys

import matplotlib
import numpy as np
import pandas as pd
from tmm import inc_tmm

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


PHASE_NAME = "Phase 09D"
NK_CSV = PROJECT_ROOT / "resources" / "aligned_full_stack_nk.csv"
OUTPUT_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "phase09" / "two_layer_interference"
OUTPUT_FIG_DIR = PROJECT_ROOT / "results" / "figures" / "phase09" / "two_layer_interference"
OUTPUT_REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phase09_two_layer_interference"

WAVELENGTH_MIN_NM = 400.0
WAVELENGTH_MAX_NM = 1100.0
GLASS_THICKNESS_NM = 1_000_000.0
PVK_THICKNESS_NM = 700.0
AIR = 1.0 + 0.0j


@dataclass(frozen=True)
class StackDefinition:
    label: str
    structure: str
    n_columns: tuple[str, ...]
    k_columns: tuple[str, ...]
    d_list_nm: tuple[float, ...]
    c_list: tuple[str, ...]


STACKS = (
    StackDefinition(
        label="glass_1mm_pvk_700nm",
        structure="Air / Glass(1 mm, incoherent) / PVK(700 nm, coherent) / Air",
        n_columns=("n_Glass", "n_PVK"),
        k_columns=("k_Glass", "k_PVK"),
        d_list_nm=(np.inf, GLASS_THICKNESS_NM, PVK_THICKNESS_NM, np.inf),
        c_list=("i", "i", "c", "i"),
    ),
    StackDefinition(
        label="pvk_700nm_glass_1mm",
        structure="Air / PVK(700 nm, coherent) / Glass(1 mm, incoherent) / Air",
        n_columns=("n_PVK", "n_Glass"),
        k_columns=("k_PVK", "k_Glass"),
        d_list_nm=(np.inf, PVK_THICKNESS_NM, GLASS_THICKNESS_NM, np.inf),
        c_list=("i", "c", "i", "i"),
    ),
)


def ensure_output_dirs() -> None:
    for path in (OUTPUT_DATA_DIR, OUTPUT_FIG_DIR, OUTPUT_REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_nk_table(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"Wavelength_nm", "n_Glass", "k_Glass", "n_PVK", "k_PVK"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{path} 缺少必要列: {missing}")
    subset = frame[(frame["Wavelength_nm"] >= WAVELENGTH_MIN_NM) & (frame["Wavelength_nm"] <= WAVELENGTH_MAX_NM)].copy()
    if subset.empty:
        raise ValueError("给定波段内没有可用 nk 数据。")
    if float(subset["Wavelength_nm"].min()) > WAVELENGTH_MIN_NM or float(subset["Wavelength_nm"].max()) < WAVELENGTH_MAX_NM:
        raise ValueError(
            f"nk 数据未完整覆盖 {WAVELENGTH_MIN_NM:.0f}-{WAVELENGTH_MAX_NM:.0f} nm，"
            f"实际为 {subset['Wavelength_nm'].min():.3f}-{subset['Wavelength_nm'].max():.3f} nm。"
        )
    return subset.reset_index(drop=True)


def build_refractive_index_series(frame: pd.DataFrame, n_col: str, k_col: str) -> np.ndarray:
    return frame[n_col].to_numpy(dtype=float) + 1j * frame[k_col].to_numpy(dtype=float)


def compute_stack_spectrum(wavelength_nm: np.ndarray, stack: StackDefinition, nk_frame: pd.DataFrame) -> pd.DataFrame:
    media = [AIR]
    for n_col, k_col in zip(stack.n_columns, stack.k_columns, strict=True):
        media.append(build_refractive_index_series(nk_frame, n_col, k_col))
    media.append(AIR)

    reflectance = np.zeros_like(wavelength_nm, dtype=float)
    transmittance = np.zeros_like(wavelength_nm, dtype=float)

    for idx, lam_nm in enumerate(wavelength_nm):
        n_list = [complex(m[idx]) if isinstance(m, np.ndarray) else complex(m) for m in media]
        result = inc_tmm(
            pol="s",
            n_list=n_list,
            d_list=list(stack.d_list_nm),
            c_list=list(stack.c_list),
            th_0=0.0,
            lam_vac=float(lam_nm),
        )
        reflectance[idx] = float(result["R"])
        transmittance[idx] = float(result["T"])

    absorptance = 1.0 - reflectance - transmittance
    absorptance[np.isclose(absorptance, 0.0, atol=1e-12, rtol=0.0)] = 0.0
    return pd.DataFrame(
        {
            "Wavelength_nm": wavelength_nm,
            f"R_{stack.label}": reflectance,
            f"T_{stack.label}": transmittance,
            f"A_{stack.label}": absorptance,
        }
    )


def build_output_frame(nk_frame: pd.DataFrame) -> pd.DataFrame:
    wavelength_nm = nk_frame["Wavelength_nm"].to_numpy(dtype=float)
    output = pd.DataFrame({"Wavelength_nm": wavelength_nm})
    for stack in STACKS:
        spectrum = compute_stack_spectrum(wavelength_nm=wavelength_nm, stack=stack, nk_frame=nk_frame)
        output = output.merge(spectrum, on="Wavelength_nm", how="inner")
    return output


def plot_spectra(output_frame: pd.DataFrame, png_path: Path, pdf_path: Path) -> None:
    wavelengths = output_frame["Wavelength_nm"].to_numpy(dtype=float)

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
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.8), dpi=300, sharex=True, constrained_layout=True)

    palette = {
        "glass_1mm_pvk_700nm": "#0b6e4f",
        "pvk_700nm_glass_1mm": "#c84c09",
    }
    labels = {
        "glass_1mm_pvk_700nm": "Glass(1 mm) / PVK(700 nm)",
        "pvk_700nm_glass_1mm": "PVK(700 nm) / Glass(1 mm)",
    }
    for stack in STACKS:
        axes[0].plot(
            wavelengths,
            output_frame[f"R_{stack.label}"].to_numpy(dtype=float),
            linewidth=2.0,
            color=palette[stack.label],
            label=labels[stack.label],
        )
        axes[1].plot(
            wavelengths,
            output_frame[f"T_{stack.label}"].to_numpy(dtype=float),
            linewidth=2.0,
            color=palette[stack.label],
            label=labels[stack.label],
        )

    axes[0].set_xlim(WAVELENGTH_MIN_NM, WAVELENGTH_MAX_NM)
    axes[0].set_ylim(0.0, 1.0)
    axes[1].set_ylim(0.0, 1.0)
    axes[0].set_ylabel("Reflectance (0-1)")
    axes[1].set_ylabel("Transmittance (0-1)")
    axes[1].set_xlabel("Wavelength (nm)")
    axes[0].set_title("Two-Layer TMM Interference Spectra")
    for axis in axes:
        axis.grid(True, linestyle="--", alpha=0.25)
        axis.legend(loc="best")

    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path, dpi=300)
    plt.close(fig)


def build_manifest(output_frame: pd.DataFrame, csv_path: Path, png_path: Path, pdf_path: Path, report_path: Path) -> dict[str, object]:
    def serialize_thicknesses(values: tuple[float, ...]) -> list[float | str]:
        serialized: list[float | str] = []
        for value in values:
            if math.isinf(value):
                serialized.append("inf")
            else:
                serialized.append(float(value))
        return serialized

    wavelength_nm = output_frame["Wavelength_nm"].to_numpy(dtype=float)
    payload: dict[str, object] = {
        "phase": PHASE_NAME,
        "inputs": {
            "nk_csv": str(NK_CSV.relative_to(PROJECT_ROOT).as_posix()),
            "wavelength_range_nm": [WAVELENGTH_MIN_NM, WAVELENGTH_MAX_NM],
            "glass_thickness_nm": GLASS_THICKNESS_NM,
            "pvk_thickness_nm": PVK_THICKNESS_NM,
            "incident_angle_deg": 0.0,
            "polarization": "s",
        },
        "structures": [
            {
                "label": stack.label,
                "structure": stack.structure,
                "d_list_nm": serialize_thicknesses(stack.d_list_nm),
                "c_list": list(stack.c_list),
            }
            for stack in STACKS
        ],
        "outputs": {
            "csv": str(csv_path.relative_to(PROJECT_ROOT).as_posix()),
            "figure_png": str(png_path.relative_to(PROJECT_ROOT).as_posix()),
            "figure_pdf": str(pdf_path.relative_to(PROJECT_ROOT).as_posix()),
            "report_md": str(report_path.relative_to(PROJECT_ROOT).as_posix()),
        },
        "summary": {
            "point_count": int(output_frame.shape[0]),
            "wavelength_min_nm": float(wavelength_nm.min()),
            "wavelength_max_nm": float(wavelength_nm.max()),
        },
    }
    for stack in STACKS:
        payload["summary"][f"reflectance_min_{stack.label}"] = float(output_frame[f"R_{stack.label}"].min())
        payload["summary"][f"reflectance_max_{stack.label}"] = float(output_frame[f"R_{stack.label}"].max())
        payload["summary"][f"transmittance_min_{stack.label}"] = float(output_frame[f"T_{stack.label}"].min())
        payload["summary"][f"transmittance_max_{stack.label}"] = float(output_frame[f"T_{stack.label}"].max())
        payload["summary"][f"absorptance_min_{stack.label}"] = float(output_frame[f"A_{stack.label}"].min())
        payload["summary"][f"absorptance_max_{stack.label}"] = float(output_frame[f"A_{stack.label}"].max())
    return payload


def render_report(output_frame: pd.DataFrame, manifest: dict[str, object], path: Path) -> None:
    def fmt(value: float) -> str:
        return f"{value:.6f}"

    summary = manifest["summary"]
    lines = [
        "# Phase 09D Two-Layer Interference Spectra",
        "",
        "## 1. 执行摘要",
        "",
        f"- 使用现有 `{manifest['inputs']['nk_csv']}` 在 `400-1100 nm` 计算了两种层序的 TMM 干涉谱。",
        "- 结构一：`Air / Glass(1 mm, incoherent) / PVK(700 nm, coherent) / Air`。",
        "- 结构二：`Air / PVK(700 nm, coherent) / Glass(1 mm, incoherent) / Air`。",
        "- 玻璃按厚基底非相干处理，PVK 按相干单层处理，与仓库现有厚玻璃建模口径一致。",
        "",
        "## 2. 输入与模型",
        "",
        "- `n/k` 来源：`resources/aligned_full_stack_nk.csv`。",
        "- PVK 列沿用仓库已对齐的光学常数表；该表的文献脉络见 `docs/LITERATURE_MAP.md` 中 `[LIT-0001]` 与 `[LIT-0002]`。",
        "- 入射条件：法向入射，`s` 偏振。",
        "- 厚度：`d_glass = 1 mm`，`d_PVK = 700 nm`。",
        "",
        "采用的强度量为：",
        "",
        "$$",
        "R(\\lambda) = \\text{inc\\_tmm}\\left(\\lambda\\right), \\qquad",
        "A(\\lambda) = 1 - R(\\lambda) - T(\\lambda)",
        "$$",
        "",
        "其中玻璃层在 coherency list 中标记为 `i`，PVK 标记为 `c`。",
        "",
        "## 3. 关键结果",
        "",
        "| Structure | R_min | R_max | T_min | T_max | A_min | A_max |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for stack in STACKS:
        lines.append(
            "| "
            + " | ".join(
                [
                    stack.label,
                    fmt(summary[f"reflectance_min_{stack.label}"]),
                    fmt(summary[f"reflectance_max_{stack.label}"]),
                    fmt(summary[f"transmittance_min_{stack.label}"]),
                    fmt(summary[f"transmittance_max_{stack.label}"]),
                    fmt(summary[f"absorptance_min_{stack.label}"]),
                    fmt(summary[f"absorptance_max_{stack.label}"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 4. 输出文件",
            "",
            f"- CSV: `{manifest['outputs']['csv']}`",
            f"- Figure PNG: `{manifest['outputs']['figure_png']}`",
            f"- Figure PDF: `{manifest['outputs']['figure_pdf']}`",
            "",
            "## 5. 风险与假设",
            "",
            "- 本结果是理想法向 specular TMM，不含角度平均、表面粗糙、仪器带宽和散射。",
            "- 1 mm 玻璃被视为非相干厚基底，因此这里输出的是包络意义上的基底级联结果，而不是保留玻璃全相干超密条纹。",
            "- `aligned_full_stack_nk.csv` 的 PVK 列代表当前仓库采用的 surrogate / 对齐版本，不等同于对真实样品来源的最终证明。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_output_dirs()
    nk_frame = load_nk_table(NK_CSV)
    output_frame = build_output_frame(nk_frame)

    csv_path = OUTPUT_DATA_DIR / "phase09d_two_layer_interference_spectra.csv"
    manifest_path = OUTPUT_DATA_DIR / "phase09d_two_layer_interference_manifest.json"
    png_path = OUTPUT_FIG_DIR / "phase09d_two_layer_interference_spectra.png"
    pdf_path = OUTPUT_FIG_DIR / "phase09d_two_layer_interference_spectra.pdf"
    report_path = OUTPUT_REPORT_DIR / "phase09d_two_layer_interference_report.md"

    output_frame.to_csv(csv_path, index=False)
    plot_spectra(output_frame=output_frame, png_path=png_path, pdf_path=pdf_path)
    manifest = build_manifest(output_frame=output_frame, csv_path=csv_path, png_path=png_path, pdf_path=pdf_path, report_path=report_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_report(output_frame=output_frame, manifest=manifest, path=report_path)


if __name__ == "__main__":
    main()
