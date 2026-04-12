"""Phase 07 raw received spectra plot.

Directly plot the spectrometer received counts on a log y-axis without any
exposure normalization, HDR blending, or calibration coefficients.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PHASE_NAME = "Phase 07"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
HDR_CURVE_PATH = PROJECT_ROOT / "test_data" / "phase7_data" / "DEVICE-1-withAg-P1_hdr_curves.csv"
FIGURE_PATH = PROJECT_ROOT / "results" / "figures" / "phase07" / "phase07_raw_received_spectra_log.png"
LOG_PATH = PROJECT_ROOT / "results" / "logs" / "phase07" / "phase07_raw_received_spectra_log.md"


def ensure_output_dirs() -> None:
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_curves() -> tuple[np.ndarray, dict[str, np.ndarray]]:
    frame = pd.read_csv(HDR_CURVE_PATH)
    wavelength_nm = pd.to_numeric(frame["Wavelength_nm"], errors="coerce").to_numpy(dtype=float)

    curves = {
        "Ag mirror 500 us": pd.to_numeric(frame["Ag_Counts_Short_Mean"], errors="coerce").to_numpy(dtype=float),
        "Ag mirror 10 ms": pd.to_numeric(frame["Ag_Counts_Long_Mean"], errors="coerce").to_numpy(dtype=float),
        "DEVICE-1-withAg-P1 150 ms": pd.to_numeric(
            frame["Sample_Counts_Short_Mean"], errors="coerce"
        ).to_numpy(dtype=float),
        "DEVICE-1-withAg-P1 2000 ms": pd.to_numeric(
            frame["Sample_Counts_Long_Mean"], errors="coerce"
        ).to_numpy(dtype=float),
    }
    return wavelength_nm, curves


def finite_positive_mask(wavelength_nm: np.ndarray, counts: np.ndarray) -> np.ndarray:
    return np.isfinite(wavelength_nm) & np.isfinite(counts) & (counts > 0.0)


def plot_curves(wavelength_nm: np.ndarray, curves: dict[str, np.ndarray]) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 8.5), dpi=320, constrained_layout=True)

    panel_specs = (
        (
            axes[0],
            ("Ag mirror 500 us", "Ag mirror 10 ms"),
            "Ag mirror: direct spectrometer counts",
            ("#2e7d32", "#6a1b9a"),
        ),
        (
            axes[1],
            ("DEVICE-1-withAg-P1 150 ms", "DEVICE-1-withAg-P1 2000 ms"),
            "Same-position sample (DEVICE-1-withAg-P1): direct spectrometer counts",
            ("#ef6c00", "#1565c0"),
        ),
    )

    for axis, labels, title, colors in panel_specs:
        for label, color in zip(labels, colors, strict=True):
            counts = curves[label]
            mask = finite_positive_mask(wavelength_nm, counts)
            axis.plot(wavelength_nm[mask], counts[mask], linewidth=1.8, color=color, label=label)

        axis.set_xlim(500.0, 1055.5)
        axis.set_yscale("log")
        axis.set_xlabel("Wavelength (nm)")
        axis.set_ylabel("Received counts (log)")
        axis.set_title(f"{PHASE_NAME} {title}")
        axis.grid(True, linestyle="--", alpha=0.25)
        axis.legend()

    fig.savefig(FIGURE_PATH, dpi=320, bbox_inches="tight")
    plt.close(fig)


def write_log(wavelength_nm: np.ndarray, curves: dict[str, np.ndarray]) -> None:
    lines = [
        f"# {PHASE_NAME} Raw Received Spectra",
        "",
        f"- source: `{HDR_CURVE_PATH}`",
        f"- figure: `{FIGURE_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        "- note: directly plotted spectrometer received counts on log y-axis",
        "- note: no exposure normalization, no HDR weighting, no calibration coefficients",
        "- selected same-position sample group: `DEVICE-1-withAg-P1` (`150 ms` vs `2000 ms`)",
        "",
        "## Curve Statistics",
        "",
    ]

    for label, counts in curves.items():
        mask = finite_positive_mask(wavelength_nm, counts)
        valid_counts = counts[mask]
        lines.extend(
            [
                f"- {label}",
                f"  - valid_points: `{int(valid_counts.size)}`",
                f"  - min_counts: `{float(np.min(valid_counts)):.6f}`",
                f"  - median_counts: `{float(np.median(valid_counts)):.6f}`",
                f"  - max_counts: `{float(np.max(valid_counts)):.6f}`",
            ]
        )

    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_output_dirs()
    wavelength_nm, curves = load_curves()
    plot_curves(wavelength_nm, curves)
    write_log(wavelength_nm, curves)
    print(f"[{PHASE_NAME}] figure saved to: {FIGURE_PATH}")
    print(f"[{PHASE_NAME}] log saved to: {LOG_PATH}")


if __name__ == "__main__":
    main()
