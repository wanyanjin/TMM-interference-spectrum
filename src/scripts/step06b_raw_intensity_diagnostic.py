"""Phase 06b raw intensity diagnostic.

This script prefers raw `*-cor.csv` files if they exist. When the local
workspace only contains exported `*_hdr_curves.csv`, it falls back to the
embedded long-exposure mean counts so the absolute Counts/ms comparison can
still be inspected.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
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

from core.hdr_absolute_calibration import load_csv_spectrum  # noqa: E402


PHASE_NAME = "Phase 06b"
DATA_DIR = PROJECT_ROOT / "test_data" / "phase7_data"
FIGURE_PATH = PROJECT_ROOT / "results" / "figures" / "phase06b_raw_counts_ms_diagnostic.png"
LOG_PATH = PROJECT_ROOT / "results" / "logs" / "phase06b_raw_counts_ms_diagnostic.md"

REPRESENTATIVE_PREFIXES = (
    "DEVICE-1-withAg",
    "DEVICE-1-withoutAg",
    "Ag_mirro",
)
REPRESENTATIVE_EXPOSURES = {
    "DEVICE-1-withAg": ("2000ms",),
    "DEVICE-1-withoutAg": ("2000ms",),
    "Ag_mirro": ("10ms", "500us"),
}
FALLBACK_EXPOSURE_MS = {
    "DEVICE-1-withAg": {"long": 2000.0},
    "DEVICE-1-withoutAg": {"long": 2000.0},
    "Ag_mirro": {"long": 10.0, "short": 0.5},
}


@dataclass(frozen=True)
class DiagnosticCurve:
    label: str
    source_mode: str
    csv_path: Path
    wavelength_nm: np.ndarray
    counts: np.ndarray
    exposure_ms: float
    counts_per_ms: np.ndarray


def parse_exposure_ms_from_name(name: str) -> float:
    match = re.search(r"-(\d+(?:\.\d+)?)(us|ms|s)(?:-|_| )", name, flags=re.IGNORECASE)
    if match is None:
        raise ValueError(f"无法从文件名提取曝光时间: {name}")
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit == "us":
        return value / 1000.0
    if unit == "ms":
        return value
    return value * 1000.0


def ensure_output_dirs() -> None:
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_raw_curve(csv_path: Path, label: str) -> DiagnosticCurve:
    wavelength_nm, counts = load_csv_spectrum(csv_path)
    exposure_ms = parse_exposure_ms_from_name(csv_path.name)
    return DiagnosticCurve(
        label=label,
        source_mode="raw_csv",
        csv_path=csv_path,
        wavelength_nm=wavelength_nm,
        counts=counts,
        exposure_ms=exposure_ms,
        counts_per_ms=counts / exposure_ms,
    )


def build_curves_from_hdr_export(hdr_curve_path: Path) -> list[DiagnosticCurve]:
    frame = pd.read_csv(hdr_curve_path)
    wavelength_nm = pd.to_numeric(frame["Wavelength_nm"], errors="coerce").to_numpy(dtype=float)

    if "DEVICE-1-withAg" in hdr_curve_path.name:
        sample_prefix = "DEVICE-1-withAg"
    elif "DEVICE-1-withoutAg" in hdr_curve_path.name:
        sample_prefix = "DEVICE-1-withoutAg"
    else:
        raise ValueError(f"无法从 hdr_curves 文件名识别样品类型: {hdr_curve_path.name}")

    curves = [
        DiagnosticCurve(
            label=f"{sample_prefix} (2000ms)",
            source_mode="hdr_curve_long_mean",
            csv_path=hdr_curve_path,
            wavelength_nm=wavelength_nm,
            counts=pd.to_numeric(frame["Sample_Counts_Long_Mean"], errors="coerce").to_numpy(dtype=float),
            exposure_ms=FALLBACK_EXPOSURE_MS[sample_prefix]["long"],
            counts_per_ms=pd.to_numeric(frame["Sample_N_Long"], errors="coerce").to_numpy(dtype=float),
        )
    ]

    if sample_prefix == "DEVICE-1-withAg":
        curves.append(
            DiagnosticCurve(
                label="Ag_mirro (10ms)",
                source_mode="hdr_curve_long_mean",
                csv_path=hdr_curve_path,
                wavelength_nm=wavelength_nm,
                counts=pd.to_numeric(frame["Ag_Counts_Long_Mean"], errors="coerce").to_numpy(dtype=float),
                exposure_ms=FALLBACK_EXPOSURE_MS["Ag_mirro"]["long"],
                counts_per_ms=pd.to_numeric(frame["Ag_N_Long"], errors="coerce").to_numpy(dtype=float),
            )
        )
        curves.append(
            DiagnosticCurve(
                label="Ag_mirro (500us)",
                source_mode="hdr_curve_short_mean",
                csv_path=hdr_curve_path,
                wavelength_nm=wavelength_nm,
                counts=pd.to_numeric(frame["Ag_Counts_Short_Mean"], errors="coerce").to_numpy(dtype=float),
                exposure_ms=FALLBACK_EXPOSURE_MS["Ag_mirro"]["short"],
                counts_per_ms=pd.to_numeric(frame["Ag_Counts_Short_Mean"], errors="coerce").to_numpy(dtype=float)
                / FALLBACK_EXPOSURE_MS["Ag_mirro"]["short"],
            )
        )
    return curves


def discover_raw_curves(data_dir: Path) -> list[DiagnosticCurve]:
    curves: list[DiagnosticCurve] = []
    for prefix in REPRESENTATIVE_PREFIXES:
        for exposure_label in REPRESENTATIVE_EXPOSURES[prefix]:
            matches = sorted(data_dir.glob(f"{prefix}-{exposure_label}-*-cor.csv"))
            if not matches:
                continue
            curves.append(load_raw_curve(matches[0], f"{prefix} ({exposure_label})"))
    return curves


def discover_diagnostic_curves(data_dir: Path) -> list[DiagnosticCurve]:
    raw_curves = discover_raw_curves(data_dir)
    if raw_curves:
        return raw_curves

    hdr_exports = sorted(data_dir.glob("*_hdr_curves.csv"))
    if not hdr_exports:
        raise FileNotFoundError(f"{data_dir} 中未找到原始 `*-cor.csv` 或 `*_hdr_curves.csv`。")

    curves: list[DiagnosticCurve] = []
    seen_labels: set[str] = set()
    for hdr_curve_path in hdr_exports:
        for curve in build_curves_from_hdr_export(hdr_curve_path):
            if curve.label in seen_labels:
                continue
            seen_labels.add(curve.label)
            curves.append(curve)
    return curves


def curve_color(label: str) -> str:
    if "withAg" in label:
        return "#1565c0"
    if "withoutAg" in label:
        return "#c62828"
    if "500us" in label:
        return "#2e7d32"
    return "#6a1b9a"


def plot_diagnostic(curves: list[DiagnosticCurve], output_path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(12.0, 9.2), dpi=320, constrained_layout=True)

    for curve in curves:
        axes[0].plot(
            curve.wavelength_nm,
            curve.counts_per_ms,
            linewidth=1.7,
            label=curve.label,
            color=curve_color(curve.label),
        )
        nir_mask = (curve.wavelength_nm >= 850.0) & (curve.wavelength_nm <= 1055.0)
        axes[1].plot(
            curve.wavelength_nm[nir_mask],
            curve.counts_per_ms[nir_mask],
            linewidth=1.8,
            label=curve.label,
            color=curve_color(curve.label),
        )

    axes[0].set_xlim(500.0, 1055.0)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Wavelength (nm)")
    axes[0].set_ylabel("Counts / ms (log)")
    axes[0].set_title(f"{PHASE_NAME} Raw Intensity Diagnostic: Full Window")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend()

    axes[1].set_xlim(850.0, 1055.0)
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("Counts / ms")
    axes[1].set_title(f"{PHASE_NAME} Raw Intensity Diagnostic: 850-1055 nm")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend()

    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def write_log(curves: list[DiagnosticCurve], output_path: Path) -> None:
    lines = [
        f"# {PHASE_NAME} Raw Intensity Diagnostic",
        "",
        f"- data_dir: `{DATA_DIR}`",
        f"- figure: `{FIGURE_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Curves",
        "",
    ]
    for curve in curves:
        nir_mask = (curve.wavelength_nm >= 850.0) & (curve.wavelength_nm <= 1055.0)
        lines.extend(
            [
                f"- {curve.label}",
                f"  - source_mode: `{curve.source_mode}`",
                f"  - source_path: `{curve.csv_path}`",
                f"  - exposure_ms: `{curve.exposure_ms}`",
                f"  - Counts/ms @ 850-1055 nm: min=`{float(np.min(curve.counts_per_ms[nir_mask])):.6f}`, "
                f"median=`{float(np.median(curve.counts_per_ms[nir_mask])):.6f}`, "
                f"max=`{float(np.max(curve.counts_per_ms[nir_mask])):.6f}`",
            ]
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_output_dirs()
    curves = discover_diagnostic_curves(DATA_DIR)
    plot_diagnostic(curves, FIGURE_PATH)
    write_log(curves, LOG_PATH)
    print(f"[{PHASE_NAME}] 图像已输出: {FIGURE_PATH}")
    print(f"[{PHASE_NAME}] 日志已输出: {LOG_PATH}")
    for curve in curves:
        print(f"- {curve.label}: source_mode={curve.source_mode}, exposure_ms={curve.exposure_ms}")


if __name__ == "__main__":
    main()
