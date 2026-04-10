"""Phase 06c hybrid reference stitching rescue test."""

from __future__ import annotations

from pathlib import Path
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

from core import hdr_absolute_calibration as hdr  # noqa: E402


PHASE_NAME = "Phase 06c"
SAMPLE_HDR_PATH = PROJECT_ROOT / "test_data" / "phase7_data" / "DEVICE-1-withAg-P1_hdr_curves.csv"
HYBRID_NIR_PATH = Path(
    "/Users/luxin/Library/CloudStorage/OneDrive-共享的库-onedrive/Data/PL/2026/0403/cor/"
    "Ag-mirro-700-1250nm-25ms-850lp-1 2026 四月 03 15_43_47-cor.csv"
)
HYBRID_NIR_EXPOSURE_MS = 25.0
HYBRID_SWITCH_NM = 850.0
FIGURE_PATH = PROJECT_ROOT / "results" / "figures" / "phase06c_hybrid_calibration_test.png"
LOG_PATH = PROJECT_ROOT / "results" / "logs" / "phase06c_hybrid_calibration_test.md"


def ensure_output_dirs() -> None:
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_sample_hdr_table() -> pd.DataFrame:
    frame = pd.read_csv(SAMPLE_HDR_PATH)
    required_columns = {
        "Wavelength_nm",
        "Sample_HDR_CountsPerMs",
        "Ag_N_Long",
        "Ag_Theory_Reflectance",
        "Absolute_Reflectance",
    }
    missing_columns = sorted(required_columns - set(frame.columns))
    if missing_columns:
        raise ValueError(f"{SAMPLE_HDR_PATH} 缺少必要列: {missing_columns}")
    return frame


def load_hybrid_nir_counts_per_ms(target_wavelength_nm: np.ndarray) -> np.ndarray:
    wavelength_nm, counts = hdr.load_csv_spectrum(HYBRID_NIR_PATH)
    counts_per_ms = counts / HYBRID_NIR_EXPOSURE_MS
    target_nir = np.asarray(target_wavelength_nm, dtype=float)
    target_nir = target_nir[target_nir >= HYBRID_SWITCH_NM]
    if target_nir.size == 0:
        raise ValueError("目标网格中没有 >= 850 nm 的点。")
    if target_nir.min() < wavelength_nm.min() or target_nir.max() > wavelength_nm.max():
        raise ValueError(
            "850LP 银镜文件的波长范围不足以覆盖目标网格: "
            f"target=({target_nir.min():.3f}, {target_nir.max():.3f}) nm, "
            f"source=({wavelength_nm.min():.3f}, {wavelength_nm.max():.3f}) nm"
        )
    return np.interp(target_wavelength_nm, wavelength_nm, counts_per_ms)


def build_hybrid_reference(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    wavelength_nm = pd.to_numeric(frame["Wavelength_nm"], errors="coerce").to_numpy(dtype=float)
    ag_visible_counts_ms = pd.to_numeric(frame["Ag_N_Long"], errors="coerce").to_numpy(dtype=float)
    ag_nir_counts_ms = load_hybrid_nir_counts_per_ms(wavelength_nm)

    hybrid_counts_ms = np.where(wavelength_nm < HYBRID_SWITCH_NM, ag_visible_counts_ms, ag_nir_counts_ms)
    return ag_nir_counts_ms, hybrid_counts_ms


def plot_comparison(
    wavelength_nm: np.ndarray,
    old_abs_reflectance: np.ndarray,
    hybrid_abs_reflectance: np.ndarray,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(12.0, 8.6), dpi=320, constrained_layout=True)

    for axis in axes:
        axis.axvline(HYBRID_SWITCH_NM, color="#616161", linestyle=":", linewidth=1.2)
        axis.plot(
            wavelength_nm,
            old_abs_reflectance * 100.0,
            color="#c62828",
            linewidth=1.8,
            linestyle="--",
            label="Legacy R_abs (old reference)",
        )
        axis.plot(
            wavelength_nm,
            hybrid_abs_reflectance * 100.0,
            color="#1565c0",
            linewidth=2.0,
            linestyle="-",
            label="Hybrid R_abs (visible+850LP)",
        )
        axis.grid(True, linestyle="--", alpha=0.25)
        axis.legend()

    axes[0].set_xlim(500.0, 1055.0)
    axes[0].set_ylabel("Absolute Reflectance (%)")
    axes[0].set_title(f"{PHASE_NAME} Hybrid Calibration Rescue Test: Full Window")

    axes[1].set_xlim(850.0, 1055.0)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Absolute Reflectance (%)")
    axes[1].set_title(f"{PHASE_NAME} Hybrid Calibration Rescue Test: 850-1055 nm")

    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def write_log(
    wavelength_nm: np.ndarray,
    sample_hdr_counts_ms: np.ndarray,
    ag_visible_counts_ms: np.ndarray,
    ag_nir_counts_ms: np.ndarray,
    hybrid_counts_ms: np.ndarray,
    legacy_abs_reflectance: np.ndarray,
    hybrid_abs_reflectance: np.ndarray,
    output_path: Path,
) -> None:
    nir_mask = (wavelength_nm >= HYBRID_SWITCH_NM) & (wavelength_nm <= 1055.4603242295705)
    lines = [
        f"# {PHASE_NAME} Hybrid Calibration Test",
        "",
        f"- sample_hdr_path: `{SAMPLE_HDR_PATH}`",
        f"- hybrid_nir_path: `{HYBRID_NIR_PATH}`",
        f"- hybrid_switch_nm: `{HYBRID_SWITCH_NM}`",
        f"- figure: `{FIGURE_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## 850-1055 nm Summary",
        "",
        f"- Sample_HDR_CountsPerMs median: `{float(np.median(sample_hdr_counts_ms[nir_mask])):.6f}`",
        f"- Ag_Visible_CountsPerMs median: `{float(np.median(ag_visible_counts_ms[nir_mask])):.6f}`",
        f"- Ag_850LP_CountsPerMs median: `{float(np.median(ag_nir_counts_ms[nir_mask])):.6f}`",
        f"- Hybrid_CountsPerMs median: `{float(np.median(hybrid_counts_ms[nir_mask])):.6f}`",
        f"- Legacy R_abs median: `{float(np.median(legacy_abs_reflectance[nir_mask]) * 100.0):.3f}%`",
        f"- Hybrid R_abs median: `{float(np.median(hybrid_abs_reflectance[nir_mask]) * 100.0):.3f}%`",
    ]

    for target_nm in (850.0, 900.0, 950.0, 1000.0, 1050.0):
        index = int(np.argmin(np.abs(wavelength_nm - target_nm)))
        lines.extend(
            [
                "",
                f"## Probe {wavelength_nm[index]:.3f} nm",
                "",
                f"- Sample_HDR_CountsPerMs: `{sample_hdr_counts_ms[index]:.6f}`",
                f"- Ag_Visible_CountsPerMs: `{ag_visible_counts_ms[index]:.6f}`",
                f"- Ag_850LP_CountsPerMs: `{ag_nir_counts_ms[index]:.6f}`",
                f"- Hybrid_CountsPerMs: `{hybrid_counts_ms[index]:.6f}`",
                f"- Legacy R_abs: `{legacy_abs_reflectance[index] * 100.0:.3f}%`",
                f"- Hybrid R_abs: `{hybrid_abs_reflectance[index] * 100.0:.3f}%`",
            ]
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_output_dirs()
    frame = load_sample_hdr_table()
    wavelength_nm = pd.to_numeric(frame["Wavelength_nm"], errors="coerce").to_numpy(dtype=float)
    sample_hdr_counts_ms = pd.to_numeric(frame["Sample_HDR_CountsPerMs"], errors="coerce").to_numpy(dtype=float)
    ag_visible_counts_ms = pd.to_numeric(frame["Ag_N_Long"], errors="coerce").to_numpy(dtype=float)
    ag_theory_reflectance = pd.to_numeric(frame["Ag_Theory_Reflectance"], errors="coerce").to_numpy(dtype=float)
    legacy_abs_reflectance = pd.to_numeric(frame["Absolute_Reflectance"], errors="coerce").to_numpy(dtype=float)

    ag_nir_counts_ms, hybrid_counts_ms = build_hybrid_reference(frame)
    hybrid_abs_reflectance = (sample_hdr_counts_ms / hybrid_counts_ms) * ag_theory_reflectance

    plot_comparison(wavelength_nm, legacy_abs_reflectance, hybrid_abs_reflectance, FIGURE_PATH)
    write_log(
        wavelength_nm=wavelength_nm,
        sample_hdr_counts_ms=sample_hdr_counts_ms,
        ag_visible_counts_ms=ag_visible_counts_ms,
        ag_nir_counts_ms=ag_nir_counts_ms,
        hybrid_counts_ms=hybrid_counts_ms,
        legacy_abs_reflectance=legacy_abs_reflectance,
        hybrid_abs_reflectance=hybrid_abs_reflectance,
        output_path=LOG_PATH,
    )

    nir_mask = (wavelength_nm >= HYBRID_SWITCH_NM) & (wavelength_nm <= 1055.4603242295705)
    print(f"[{PHASE_NAME}] 图像已输出: {FIGURE_PATH}")
    print(f"[{PHASE_NAME}] 日志已输出: {LOG_PATH}")
    print(
        f"[{PHASE_NAME}] 850-1055 nm median old/new = "
        f"{np.median(legacy_abs_reflectance[nir_mask]) * 100.0:.3f}% / "
        f"{np.median(hybrid_abs_reflectance[nir_mask]) * 100.0:.3f}%"
    )


if __name__ == "__main__":
    main()
