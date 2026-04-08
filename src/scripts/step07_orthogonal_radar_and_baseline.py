"""Phase 07 全谱基准三分区与前后界面正交雷达沙盒。"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.full_stack_microcavity import (
    INTERFACE_BACK,
    INTERFACE_FRONT,
    forward_model_for_fitting,
    load_default_optical_stack_table,
)


PHASE_NAME = "Phase 07"
D_AIR_VALUES_NM = np.arange(0.0, 51.0, 1.0, dtype=float)
ZERO_MATCH_TOLERANCE = 1e-12
ZONE_1 = (400.0, 650.0)
ZONE_2 = (650.0, 810.0)
ZONE_3 = (810.0, 1100.0)
ZONE_LABELS = {
    ZONE_1: "Zone 1: Complete Absorption (Front-only Probe)",
    ZONE_2: "Zone 2: Chaos & PL (Masked in Fitting)",
    ZONE_3: "Zone 3: Transparent Cavity (Thickness Fitting)",
}
ZONE_COLORS = {
    ZONE_1: "#eceff1",
    ZONE_2: "#ffebee",
    ZONE_3: "#e3f2fd",
}
INTERFACE_LABELS = {
    INTERFACE_FRONT: "Front (NiOx/Air/PVK)",
    INTERFACE_BACK: "Back (PVK/Air/C60)",
}


@dataclass(frozen=True)
class SweepSummary:
    interface_type: str
    reflectance_map: np.ndarray
    delta_map: np.ndarray
    zero_gap_baseline_error: float
    zone1_max_abs_delta: float
    zone2_max_abs_delta: float
    zone3_max_abs_delta: float


def ensure_output_dirs() -> tuple[Path, Path, Path]:
    processed_dir = PROJECT_ROOT / "data" / "processed" / "phase07"
    figures_dir = PROJECT_ROOT / "results" / "figures"
    logs_dir = PROJECT_ROOT / "results" / "logs"
    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir, figures_dir, logs_dir


def zone_mask(wavelength_nm: np.ndarray, zone: tuple[float, float]) -> np.ndarray:
    lower_nm, upper_nm = zone
    if zone == ZONE_2:
        return (wavelength_nm > lower_nm) & (wavelength_nm < upper_nm)
    return (wavelength_nm >= lower_nm) & (wavelength_nm <= upper_nm)


def build_dictionary_frame(
    wavelength_nm: np.ndarray,
    d_air_values_nm: np.ndarray,
    summary: SweepSummary,
) -> pd.DataFrame:
    n_air = d_air_values_nm.size
    n_wavelength = wavelength_nm.size
    return pd.DataFrame(
        {
            "interface_type": np.full(n_air * n_wavelength, summary.interface_type),
            "d_air_nm": np.repeat(d_air_values_nm, n_wavelength),
            "wavelength_nm": np.tile(wavelength_nm.astype(int), n_air),
            "reflectance": summary.reflectance_map.reshape(-1),
            "delta_r": summary.delta_map.reshape(-1),
        }
    )


def plot_baseline_three_zones(
    wavelength_nm: np.ndarray,
    baseline_reflectance: np.ndarray,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(11.0, 5.6), dpi=320)
    for zone in (ZONE_1, ZONE_2, ZONE_3):
        lower_nm, upper_nm = zone
        ax.axvspan(lower_nm, upper_nm, color=ZONE_COLORS[zone], alpha=0.9)
    ax.plot(wavelength_nm, baseline_reflectance * 100.0, color="#0d47a1", linewidth=2.2)
    ax.set_title(f"{PHASE_NAME} Pristine Baseline with Spectral Anatomy")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Reflectance R (%)")
    ax.grid(True, linestyle="--", alpha=0.28)

    y_min, y_max = ax.get_ylim()
    text_y = y_max - 0.06 * (y_max - y_min)
    for zone in (ZONE_1, ZONE_2, ZONE_3):
        lower_nm, upper_nm = zone
        ax.text(
            0.5 * (lower_nm + upper_nm),
            text_y,
            ZONE_LABELS[zone],
            ha="center",
            va="top",
            fontsize=9.2,
            color="#263238",
            bbox={"facecolor": "white", "alpha": 0.78, "edgecolor": "none", "pad": 2.5},
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_orthogonal_radar(
    wavelength_nm: np.ndarray,
    d_air_values_nm: np.ndarray,
    front_delta_map: np.ndarray,
    back_delta_map: np.ndarray,
    output_path: Path,
) -> None:
    front_percent = front_delta_map * 100.0
    back_percent = back_delta_map * 100.0
    max_abs = float(max(np.max(np.abs(front_percent)), np.max(np.abs(back_percent))))

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(14.8, 5.6),
        dpi=320,
        sharey=True,
        constrained_layout=True,
    )
    extent = [
        float(wavelength_nm.min()),
        float(wavelength_nm.max()),
        float(d_air_values_nm.min()),
        float(d_air_values_nm.max()),
    ]

    left_image = axes[0].imshow(
        front_percent,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap="RdBu_r",
        vmin=-max_abs,
        vmax=max_abs,
    )
    axes[0].set_title("Front Interface Radar")
    axes[0].set_xlabel("Wavelength (nm)")
    axes[0].set_ylabel("d_air (nm)")

    axes[1].imshow(
        back_percent,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap="RdBu_r",
        vmin=-max_abs,
        vmax=max_abs,
    )
    axes[1].set_title("Back Interface Radar")
    axes[1].set_xlabel("Wavelength (nm)")

    for axis in axes:
        axis.grid(False)

    colorbar = fig.colorbar(left_image, ax=axes, shrink=0.94, pad=0.03)
    colorbar.set_label("Delta R (%)")
    fig.suptitle(f"{PHASE_NAME} Orthogonal Front/Back Radar", y=1.02)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def summarize_interface(
    wavelength_nm: np.ndarray,
    baseline_reflectance: np.ndarray,
    interface_type: str,
    reflectance_map: np.ndarray,
    delta_map: np.ndarray,
) -> SweepSummary:
    zero_gap_error = float(np.max(np.abs(reflectance_map[0] - baseline_reflectance)))
    if zero_gap_error > ZERO_MATCH_TOLERANCE:
        raise ValueError(
            f"{interface_type} 在 d_air=0 nm 时未退化到 baseline: max_abs_diff={zero_gap_error:.3e}"
        )

    zone1 = zone_mask(wavelength_nm, ZONE_1)
    zone2 = zone_mask(wavelength_nm, ZONE_2)
    zone3 = zone_mask(wavelength_nm, ZONE_3)
    return SweepSummary(
        interface_type=interface_type,
        reflectance_map=reflectance_map,
        delta_map=delta_map,
        zero_gap_baseline_error=zero_gap_error,
        zone1_max_abs_delta=float(np.max(np.abs(delta_map[:, zone1]))),
        zone2_max_abs_delta=float(np.max(np.abs(delta_map[:, zone2]))),
        zone3_max_abs_delta=float(np.max(np.abs(delta_map[:, zone3]))),
    )


def write_diagnostic_log(
    baseline_reflectance: np.ndarray,
    wavelength_nm: np.ndarray,
    front_summary: SweepSummary,
    back_summary: SweepSummary,
    dictionary_rows: int,
    dictionary_path: Path,
    baseline_figure_path: Path,
    radar_figure_path: Path,
    log_path: Path,
) -> None:
    baseline_zone_means = {}
    for zone in (ZONE_1, ZONE_2, ZONE_3):
        zone_values = baseline_reflectance[zone_mask(wavelength_nm, zone)] * 100.0
        baseline_zone_means[zone] = float(np.mean(zone_values))

    front_advantage = front_summary.zone1_max_abs_delta > back_summary.zone1_max_abs_delta
    lines = [
        f"# {PHASE_NAME} Orthogonal Radar Diagnostic",
        "",
        "## Spectral Anatomy",
        "",
        f"- 400-650 nm: `{ZONE_LABELS[ZONE_1]}`",
        f"- 650-810 nm: `{ZONE_LABELS[ZONE_2]}`",
        f"- 810-1100 nm: `{ZONE_LABELS[ZONE_3]}`",
        "",
        "## Baseline",
        "",
        f"- Zone 1 mean reflectance: `{baseline_zone_means[ZONE_1]:.4f}%`",
        f"- Zone 2 mean reflectance: `{baseline_zone_means[ZONE_2]:.4f}%`",
        f"- Zone 3 mean reflectance: `{baseline_zone_means[ZONE_3]:.4f}%`",
        "",
        "## Consistency Checks",
        "",
        f"- Dictionary rows: `{dictionary_rows}`",
        f"- Expected rows: `{2 * len(D_AIR_VALUES_NM) * len(wavelength_nm)}`",
        f"- Front zero-gap fallback: `{front_summary.zero_gap_baseline_error:.3e}`",
        f"- Back zero-gap fallback: `{back_summary.zero_gap_baseline_error:.3e}`",
        "",
        "## Max |Delta R| by Zone",
        "",
        f"- Front / Zone 1: `{front_summary.zone1_max_abs_delta * 100.0:.4f}%`",
        f"- Front / Zone 2: `{front_summary.zone2_max_abs_delta * 100.0:.4f}%`",
        f"- Front / Zone 3: `{front_summary.zone3_max_abs_delta * 100.0:.4f}%`",
        f"- Back / Zone 1: `{back_summary.zone1_max_abs_delta * 100.0:.4f}%`",
        f"- Back / Zone 2: `{back_summary.zone2_max_abs_delta * 100.0:.4f}%`",
        f"- Back / Zone 3: `{back_summary.zone3_max_abs_delta * 100.0:.4f}%`",
        "",
        "## Phase 07 Conclusion",
        "",
        f"- Front stronger than back in Zone 1: `{front_advantage}`",
        "- Zone 2 is retained for visualization but should be masked in the later LM weighting design.",
        "- Zone 3 remains the primary transparent-cavity region for thickness-phase fitting.",
        "",
        "## Outputs",
        "",
        f"- Baseline figure: `{baseline_figure_path.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- Radar figure: `{radar_figure_path.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- Dictionary: `{dictionary_path.relative_to(PROJECT_ROOT).as_posix()}`",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    processed_dir, figures_dir, logs_dir = ensure_output_dirs()
    model = load_default_optical_stack_table()
    wavelength_nm = model.wavelength_nm.copy()

    baseline_reflectance = forward_model_for_fitting(
        wavelengths_nm=wavelength_nm,
        d_air_nm=0.0,
        interface_type=INTERFACE_BACK,
    )

    front_reflectance_map = np.vstack(
        [
            forward_model_for_fitting(
                wavelengths_nm=wavelength_nm,
                d_air_nm=float(d_air_nm),
                interface_type=INTERFACE_FRONT,
            )
            for d_air_nm in D_AIR_VALUES_NM
        ]
    )
    back_reflectance_map = np.vstack(
        [
            forward_model_for_fitting(
                wavelengths_nm=wavelength_nm,
                d_air_nm=float(d_air_nm),
                interface_type=INTERFACE_BACK,
            )
            for d_air_nm in D_AIR_VALUES_NM
        ]
    )
    front_delta_map = front_reflectance_map - baseline_reflectance[np.newaxis, :]
    back_delta_map = back_reflectance_map - baseline_reflectance[np.newaxis, :]

    front_summary = summarize_interface(
        wavelength_nm=wavelength_nm,
        baseline_reflectance=baseline_reflectance,
        interface_type=INTERFACE_FRONT,
        reflectance_map=front_reflectance_map,
        delta_map=front_delta_map,
    )
    back_summary = summarize_interface(
        wavelength_nm=wavelength_nm,
        baseline_reflectance=baseline_reflectance,
        interface_type=INTERFACE_BACK,
        reflectance_map=back_reflectance_map,
        delta_map=back_delta_map,
    )

    dictionary_frame = pd.concat(
        [
            build_dictionary_frame(wavelength_nm, D_AIR_VALUES_NM, front_summary),
            build_dictionary_frame(wavelength_nm, D_AIR_VALUES_NM, back_summary),
        ],
        ignore_index=True,
    )
    expected_rows = 2 * len(D_AIR_VALUES_NM) * len(wavelength_nm)
    if len(dictionary_frame) != expected_rows:
        raise ValueError(f"Phase 07 字典行数错误: expected={expected_rows}, actual={len(dictionary_frame)}")
    if not np.isfinite(dictionary_frame[["reflectance", "delta_r"]].to_numpy(dtype=float)).all():
        raise ValueError("Phase 07 字典包含 NaN/Inf。")
    if ((dictionary_frame["reflectance"] < 0.0) | (dictionary_frame["reflectance"] > 1.0)).any():
        raise ValueError("Phase 07 反射率超出物理范围 [0, 1]。")

    baseline_figure_path = figures_dir / "phase07_baseline_3zones.png"
    radar_figure_path = figures_dir / "phase07_orthogonal_radar.png"
    dictionary_path = processed_dir / "phase07_orthogonal_fingerprint_dictionary.csv"
    log_path = logs_dir / "phase07_orthogonal_radar_diagnostic.md"

    dictionary_frame.to_csv(dictionary_path, index=False)
    plot_baseline_three_zones(wavelength_nm, baseline_reflectance, baseline_figure_path)
    plot_orthogonal_radar(
        wavelength_nm=wavelength_nm,
        d_air_values_nm=D_AIR_VALUES_NM,
        front_delta_map=front_delta_map,
        back_delta_map=back_delta_map,
        output_path=radar_figure_path,
    )
    write_diagnostic_log(
        baseline_reflectance=baseline_reflectance,
        wavelength_nm=wavelength_nm,
        front_summary=front_summary,
        back_summary=back_summary,
        dictionary_rows=len(dictionary_frame),
        dictionary_path=dictionary_path,
        baseline_figure_path=baseline_figure_path,
        radar_figure_path=radar_figure_path,
        log_path=log_path,
    )

    print(f"{PHASE_NAME} orthogonal radar and baseline complete.")
    print(f"Dictionary: {dictionary_path}")
    print(f"Baseline figure: {baseline_figure_path}")
    print(f"Radar figure: {radar_figure_path}")
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()
