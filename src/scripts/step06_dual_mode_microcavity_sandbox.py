"""Phase 06 全器件双模式微腔缺陷沙盒。

本脚本直接消费 Phase 05c 生成的 ``aligned_full_stack_nk.csv``，不再引入
Phase 03/04 的拟合扰动参数，而是将全器件视为纯前向读表问题：

- Baseline: Glass / ITO / NiOx / PVK / C60 / Ag
- Case A:   Glass / ITO / NiOx / PVK / C60 / Air_Gap / Ag
- Case B:   Glass / ITO / NiOx / PVK / Air_Gap / C60 / Ag

几何假设：
- Air -> Glass 前表面作为厚玻璃非相干反射
- Glass 后侧薄膜堆栈作为相干 TMM
- 法向入射
- Ag 作为半无限背电极
"""

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

from core.full_stack_microcavity import MODE_BASELINE, MODE_CASE_A, MODE_CASE_B, OpticalStackTable


PHASE_NAME = "Phase 06"
D_AIR_VALUES_NM = np.arange(0.0, 51.0, 1.0, dtype=float)
DELTA_COMPARE_DAIR_NM = 40.0
LOW_SIGNAL_BAND = (400.0, 650.0)
HIGH_SIGNAL_BAND = (850.0, 1100.0)
ZERO_MATCH_TOLERANCE = 1e-12

MODE_LABELS = {
    MODE_CASE_A: "Case A: Glass/ITO/NiOx/PVK/C60/Air/Ag",
    MODE_CASE_B: "Case B: Glass/ITO/NiOx/PVK/Air/C60/Ag",
}


@dataclass(frozen=True)
class SweepResult:
    mode: str
    reflectance_map: np.ndarray
    delta_map: np.ndarray
    zero_gap_baseline_error: float
    low_band_max_abs_delta: float
    high_band_max_abs_delta: float
    low_band_max_abs_delta_at_40nm: float
    high_band_max_abs_delta_at_40nm: float


def ensure_output_dirs() -> tuple[Path, Path, Path]:
    processed_dir = PROJECT_ROOT / "data" / "processed" / "phase06"
    figures_dir = PROJECT_ROOT / "results" / "figures"
    logs_dir = PROJECT_ROOT / "results" / "logs"
    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir, figures_dir, logs_dir


def build_band_mask(wavelength_nm: np.ndarray, band: tuple[float, float]) -> np.ndarray:
    lower_nm, upper_nm = band
    return (wavelength_nm >= lower_nm) & (wavelength_nm <= upper_nm)


def summarize_mode(
    model: OpticalStackTable,
    mode: str,
    baseline_reflectance: np.ndarray,
    reflectance_map: np.ndarray,
    delta_map: np.ndarray,
) -> SweepResult:
    zero_gap_reflectance = reflectance_map[0]
    zero_gap_baseline_error = float(np.max(np.abs(zero_gap_reflectance - baseline_reflectance)))
    if zero_gap_baseline_error > ZERO_MATCH_TOLERANCE:
        raise ValueError(
            f"{mode} 在 d_air=0 nm 时未退化到 baseline: max_abs_diff={zero_gap_baseline_error:.3e}"
        )

    wavelength_nm = model.wavelength_nm
    low_mask = build_band_mask(wavelength_nm, LOW_SIGNAL_BAND)
    high_mask = build_band_mask(wavelength_nm, HIGH_SIGNAL_BAND)
    target_row = int(np.where(np.isclose(D_AIR_VALUES_NM, DELTA_COMPARE_DAIR_NM))[0][0])

    return SweepResult(
        mode=mode,
        reflectance_map=reflectance_map,
        delta_map=delta_map,
        zero_gap_baseline_error=zero_gap_baseline_error,
        low_band_max_abs_delta=float(np.max(np.abs(delta_map[:, low_mask]))),
        high_band_max_abs_delta=float(np.max(np.abs(delta_map[:, high_mask]))),
        low_band_max_abs_delta_at_40nm=float(np.max(np.abs(delta_map[target_row, low_mask]))),
        high_band_max_abs_delta_at_40nm=float(np.max(np.abs(delta_map[target_row, high_mask]))),
    )


def build_dictionary_frame(
    wavelength_nm: np.ndarray,
    d_air_values_nm: np.ndarray,
    sweep_result: SweepResult,
) -> pd.DataFrame:
    n_air = d_air_values_nm.size
    n_wavelength = wavelength_nm.size
    return pd.DataFrame(
        {
            "mode": np.full(n_air * n_wavelength, sweep_result.mode),
            "d_air_nm": np.repeat(d_air_values_nm, n_wavelength),
            "wavelength_nm": np.tile(wavelength_nm.astype(int), n_air),
            "reflectance": sweep_result.reflectance_map.reshape(-1),
            "delta_r": sweep_result.delta_map.reshape(-1),
        }
    )


def plot_delta_comparison(
    wavelength_nm: np.ndarray,
    case_a_delta: np.ndarray,
    case_b_delta: np.ndarray,
    output_path: Path,
) -> None:
    mask = build_band_mask(wavelength_nm, HIGH_SIGNAL_BAND)
    fig, ax = plt.subplots(figsize=(9.6, 5.2), dpi=320)
    ax.axhline(0.0, color="black", linewidth=1.0, linestyle="--")
    ax.plot(
        wavelength_nm[mask],
        case_a_delta[mask] * 100.0,
        color="#1565c0",
        linewidth=2.2,
        label="Case A (40 nm)",
    )
    ax.plot(
        wavelength_nm[mask],
        case_b_delta[mask] * 100.0,
        color="#ef6c00",
        linewidth=2.2,
        label="Case B (40 nm)",
    )
    ax.set_title(f"{PHASE_NAME} Dual-Mode Delta R Comparison at d_air = {DELTA_COMPARE_DAIR_NM:.0f} nm")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Delta R (%)")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_radar_map(
    wavelength_nm: np.ndarray,
    d_air_values_nm: np.ndarray,
    case_a_delta_map: np.ndarray,
    case_b_delta_map: np.ndarray,
    output_path: Path,
) -> None:
    plot_case_a = case_a_delta_map * 100.0
    plot_case_b = case_b_delta_map * 100.0
    max_abs = float(max(np.max(np.abs(plot_case_a)), np.max(np.abs(plot_case_b))))

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(14.5, 5.4),
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

    image_left = axes[0].imshow(
        plot_case_a,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap="RdBu_r",
        vmin=-max_abs,
        vmax=max_abs,
    )
    axes[0].set_title("Case A Radar Map")
    axes[0].set_xlabel("Wavelength (nm)")
    axes[0].set_ylabel("d_air (nm)")

    axes[1].imshow(
        plot_case_b,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap="RdBu_r",
        vmin=-max_abs,
        vmax=max_abs,
    )
    axes[1].set_title("Case B Radar Map")
    axes[1].set_xlabel("Wavelength (nm)")

    for axis in axes:
        axis.grid(False)

    cbar = fig.colorbar(image_left, ax=axes, shrink=0.94, pad=0.03)
    cbar.set_label("Delta R (%)")
    fig.suptitle(f"{PHASE_NAME} Dual-Mode Microcavity Radar Map", y=1.02)
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def write_summary_log(
    model: OpticalStackTable,
    case_a: SweepResult,
    case_b: SweepResult,
    dictionary_rows: int,
    dictionary_path: Path,
    delta_compare_path: Path,
    radar_map_path: Path,
    log_path: Path,
) -> None:
    lines = [
        f"# {PHASE_NAME} Dual-Mode Microcavity Defect Sandbox",
        "",
        "## Stack Definition",
        "",
        "- Baseline: `Glass / ITO / NiOx / PVK / C60 / Ag`",
        "- Case A: `Glass / ITO / NiOx / PVK / C60 / Air_Gap / Ag`",
        "- Case B: `Glass / ITO / NiOx / PVK / Air_Gap / C60 / Ag`",
        "- Geometry: `Air -> Glass` front surface incoherent, rear thin-film stack coherent, normal incidence, Ag semi-infinite.",
        "",
        "## Thicknesses",
        "",
        f"- ITO: `{model.thicknesses.ito_nm:.3f} nm`",
        f"- NiOx: `{model.thicknesses.niox_nm:.3f} nm`",
        f"- PVK: `{model.thicknesses.pvk_nm:.3f} nm`",
        f"- C60: `{model.thicknesses.c60_nm:.3f} nm`",
        "",
        "## Consistency Checks",
        "",
        f"- Case A zero-gap fallback vs baseline: `max_abs_diff = {case_a.zero_gap_baseline_error:.3e}`",
        f"- Case B zero-gap fallback vs baseline: `max_abs_diff = {case_b.zero_gap_baseline_error:.3e}`",
        f"- Dictionary rows: `{dictionary_rows}`",
        f"- Expected rows: `{2 * len(D_AIR_VALUES_NM) * len(model.wavelength_nm)}`",
        "",
        "## Band Metrics",
        "",
    ]

    for result in (case_a, case_b):
        label = MODE_LABELS[result.mode]
        lines.extend(
            [
                f"### {label}",
                "",
                f"- max(|Delta R|) over 400-650 nm, all d_air: `{result.low_band_max_abs_delta * 100.0:.4f}%`",
                f"- max(|Delta R|) over 850-1100 nm, all d_air: `{result.high_band_max_abs_delta * 100.0:.4f}%`",
                f"- max(|Delta R|) over 400-650 nm, d_air=40 nm: `{result.low_band_max_abs_delta_at_40nm * 100.0:.4f}%`",
                f"- max(|Delta R|) over 850-1100 nm, d_air=40 nm: `{result.high_band_max_abs_delta_at_40nm * 100.0:.4f}%`",
                "",
            ]
        )

    lines.extend(
        [
            "## Outputs",
            "",
            f"- Dictionary: `{dictionary_path.relative_to(PROJECT_ROOT).as_posix()}`",
            f"- Delta comparison figure: `{delta_compare_path.relative_to(PROJECT_ROOT).as_posix()}`",
            f"- Radar map figure: `{radar_map_path.relative_to(PROJECT_ROOT).as_posix()}`",
            "",
            "## Interpretation Note",
            "",
            "- 本轮不对 400-650 nm 人为清零；该波段是否接近零响应，仅作为全栈前向模型的数值结果记录。",
            "- `aligned_full_stack_nk.csv` 中的 NiOx 长波 k 与 PVK 400-449 nm 仍属于 Phase 05c 的工程补齐层，不应直接视为最终材料真值。",
        ]
    )
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    processed_dir, figures_dir, logs_dir = ensure_output_dirs()
    nk_csv_path = PROJECT_ROOT / "resources" / "aligned_full_stack_nk.csv"
    material_db_path = PROJECT_ROOT / "resources" / "materials_master_db.json"

    model = OpticalStackTable.from_files(
        nk_csv_path=nk_csv_path,
        material_db_path=material_db_path,
    )
    baseline_reflectance = model.calc_macro_reflectance(mode=MODE_BASELINE, d_air_nm=0.0)
    case_a_reflectance, case_a_delta = model.sweep_air_gap(mode=MODE_CASE_A, d_air_values_nm=D_AIR_VALUES_NM)
    case_b_reflectance, case_b_delta = model.sweep_air_gap(mode=MODE_CASE_B, d_air_values_nm=D_AIR_VALUES_NM)

    case_a_result = summarize_mode(model, MODE_CASE_A, baseline_reflectance, case_a_reflectance, case_a_delta)
    case_b_result = summarize_mode(model, MODE_CASE_B, baseline_reflectance, case_b_reflectance, case_b_delta)

    dictionary_frames = [
        build_dictionary_frame(model.wavelength_nm, D_AIR_VALUES_NM, case_a_result),
        build_dictionary_frame(model.wavelength_nm, D_AIR_VALUES_NM, case_b_result),
    ]
    dictionary_frame = pd.concat(dictionary_frames, ignore_index=True)
    expected_rows = 2 * len(D_AIR_VALUES_NM) * len(model.wavelength_nm)
    if len(dictionary_frame) != expected_rows:
        raise ValueError(f"Phase 06 字典行数错误: expected={expected_rows}, actual={len(dictionary_frame)}")
    if not np.isfinite(dictionary_frame[["reflectance", "delta_r"]].to_numpy(dtype=float)).all():
        raise ValueError("Phase 06 字典包含非有限数值。")
    if ((dictionary_frame["reflectance"] < 0.0) | (dictionary_frame["reflectance"] > 1.0)).any():
        raise ValueError("Phase 06 反射率超出物理范围 [0, 1]。")
    if not np.allclose(
        dictionary_frame.loc[dictionary_frame["d_air_nm"] == 0.0, "delta_r"].to_numpy(dtype=float),
        0.0,
    ):
        raise ValueError("d_air = 0 nm 的 delta_r 不为零。")

    dictionary_path = processed_dir / "phase06_dual_mode_fingerprint_dictionary.csv"
    delta_compare_path = figures_dir / "phase06_dual_mode_delta_r_40nm_850_1100.png"
    radar_map_path = figures_dir / "phase06_dual_mode_radar_map.png"
    log_path = logs_dir / "phase06_dual_mode_microcavity_sandbox.md"

    dictionary_frame.to_csv(dictionary_path, index=False)

    target_row = int(np.where(np.isclose(D_AIR_VALUES_NM, DELTA_COMPARE_DAIR_NM))[0][0])
    plot_delta_comparison(
        wavelength_nm=model.wavelength_nm,
        case_a_delta=case_a_result.delta_map[target_row],
        case_b_delta=case_b_result.delta_map[target_row],
        output_path=delta_compare_path,
    )
    plot_radar_map(
        wavelength_nm=model.wavelength_nm,
        d_air_values_nm=D_AIR_VALUES_NM,
        case_a_delta_map=case_a_result.delta_map,
        case_b_delta_map=case_b_result.delta_map,
        output_path=radar_map_path,
    )
    write_summary_log(
        model=model,
        case_a=case_a_result,
        case_b=case_b_result,
        dictionary_rows=len(dictionary_frame),
        dictionary_path=dictionary_path,
        delta_compare_path=delta_compare_path,
        radar_map_path=radar_map_path,
        log_path=log_path,
    )

    print(f"{PHASE_NAME} dual-mode microcavity sandbox complete.")
    print(f"Dictionary: {dictionary_path}")
    print(f"Figure 1: {delta_compare_path}")
    print(f"Figure 2: {radar_map_path}")
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()
