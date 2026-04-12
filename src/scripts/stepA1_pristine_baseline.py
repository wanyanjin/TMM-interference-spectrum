"""Phase A-1 pristine baseline forward modeling.

This script establishes the cleanest forward-only baseline decomposition for an
ideal defect-free stack. It consumes the aligned full-stack optical constants,
forces the thick-glass front medium to a constant 1.515 + 0i in this first
pass, and outputs:

- R_front: Air / Glass Fresnel reflection only
- R_stack: coherent reflection from Glass -> ITO -> NiOx -> SAM -> PVK -> C60 -> Ag
- R_total: thick-glass incoherent intensity cascade of front + stack

The PVK optical constants in the aligned stack ultimately trace back to
[LIT-0001] within the measured window via the project's Phase 05c workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
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

from core.full_stack_microcavity import (  # noqa: E402
    AG_BOUNDARY_FINITE_FILM,
    DEFAULT_CONSTANT_GLASS_INDEX,
    EXPECTED_WAVELENGTHS_NM,
    LayerThicknesses,
    OpticalStackTable,
)


PHASE_NAME = "Phase A-1"
DEFAULT_NK_CSV_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk.csv"
ZONE_1 = (400, 650)
ZONE_2 = (650, 810)
ZONE_3 = (810, 1100)
ZONE_COLORS = {
    ZONE_1: "#e8f3ec",
    ZONE_2: "#fff2cc",
    ZONE_3: "#e7f0fa",
}
ZONE_LABELS = {
    "Zone 1": "Zone 1: 400-650 nm",
    "Zone 2": "Zone 2: 650-810 nm",
    "Zone 3": "Zone 3: 810-1100 nm",
}
REQUIRED_COLUMNS = (
    "Wavelength_nm",
    "n_ITO",
    "k_ITO",
    "n_NiOx",
    "k_NiOx",
    "n_PVK",
    "k_PVK",
    "n_C60",
    "k_C60",
    "n_Ag",
    "k_Ag",
)


@dataclass(frozen=True)
class OutputPaths:
    processed_csv: Path
    decomposition_figure: Path
    zones_figure: Path
    log_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase A-1 pristine baseline forward modeling.")
    parser.add_argument("--nk-csv", type=Path, default=DEFAULT_NK_CSV_PATH)
    return parser.parse_args()


def ensure_output_dirs() -> OutputPaths:
    processed_dir = PROJECT_ROOT / "data" / "processed" / "phaseA1"
    figure_dir = PROJECT_ROOT / "results" / "figures" / "phaseA1"
    log_dir = PROJECT_ROOT / "results" / "logs" / "phaseA1"
    processed_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    return OutputPaths(
        processed_csv=processed_dir / "phaseA1_pristine_baseline.csv",
        decomposition_figure=figure_dir / "phaseA1_pristine_decomposition.png",
        zones_figure=figure_dir / "phaseA1_pristine_3zones.png",
        log_path=log_dir / "phaseA1_pristine_baseline.md",
    )


def load_optical_stack_from_aligned_csv(nk_csv_path: Path) -> tuple[OpticalStackTable, pd.DataFrame, list[str]]:
    frame = pd.read_csv(nk_csv_path)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"{nk_csv_path} 缺少必要列: {missing_columns}")

    wavelength_nm = frame["Wavelength_nm"].to_numpy(dtype=float)
    if wavelength_nm.shape != EXPECTED_WAVELENGTHS_NM.shape or not np.array_equal(wavelength_nm, EXPECTED_WAVELENGTHS_NM):
        raise ValueError(f"{nk_csv_path} 的波长网格不符合 400-1100 nm / 1 nm 约定。")

    numeric_block = frame.loc[:, REQUIRED_COLUMNS[1:]].to_numpy(dtype=float)
    if not np.isfinite(numeric_block).all():
        raise ValueError(f"{nk_csv_path} 含有 NaN/Inf。")

    consistency_notes: list[str] = []
    if {"n_Glass", "k_Glass"}.issubset(frame.columns):
        glass_nk = frame["n_Glass"].to_numpy(dtype=float) + 1j * frame["k_Glass"].to_numpy(dtype=float)
        consistency_notes.append(
            "aligned_full_stack_nk.csv 包含 n_Glass/k_Glass；本轮仅将其作为一致性参考，不参与求解。"
        )
    else:
        glass_nk = np.full(wavelength_nm.shape, DEFAULT_CONSTANT_GLASS_INDEX, dtype=np.complex128)
        consistency_notes.append("aligned_full_stack_nk.csv 不含 n_Glass/k_Glass；本轮使用常数玻璃占位。")

    stack = OpticalStackTable(
        wavelength_nm=wavelength_nm,
        n_glass=glass_nk,
        n_ito=frame["n_ITO"].to_numpy(dtype=float) + 1j * frame["k_ITO"].to_numpy(dtype=float),
        n_niox=frame["n_NiOx"].to_numpy(dtype=float) + 1j * frame["k_NiOx"].to_numpy(dtype=float),
        n_pvk=frame["n_PVK"].to_numpy(dtype=float) + 1j * frame["k_PVK"].to_numpy(dtype=float),
        n_c60=frame["n_C60"].to_numpy(dtype=float) + 1j * frame["k_C60"].to_numpy(dtype=float),
        n_ag=frame["n_Ag"].to_numpy(dtype=float) + 1j * frame["k_Ag"].to_numpy(dtype=float),
        thicknesses=LayerThicknesses(
            ito_nm=100.0,
            niox_nm=45.0,
            sam_nm=5.0,
            pvk_nm=700.0,
            c60_nm=15.0,
            ag_nm=100.0,
        ),
    )
    return stack, frame, consistency_notes


def zone_label_for_wavelength(wavelength_nm: int) -> str:
    if 400 <= wavelength_nm <= 650:
        return "Zone 1"
    if 651 <= wavelength_nm <= 809:
        return "Zone 2"
    if 810 <= wavelength_nm <= 1100:
        return "Zone 3"
    raise ValueError(f"波长 {wavelength_nm} nm 超出 Phase A-1 定义范围。")


def build_zone_labels(wavelength_nm: np.ndarray) -> np.ndarray:
    integer_grid = np.rint(wavelength_nm).astype(int)
    return np.asarray([zone_label_for_wavelength(value) for value in integer_grid], dtype=object)


def add_zone_background(axis: plt.Axes) -> None:
    axis.axvspan(400.0, 650.0, color=ZONE_COLORS[ZONE_1], alpha=0.85)
    axis.axvspan(650.0, 810.0, color=ZONE_COLORS[ZONE_2], alpha=0.9)
    axis.axvspan(810.0, 1100.0, color=ZONE_COLORS[ZONE_3], alpha=0.9)


def plot_pristine_decomposition(frame: pd.DataFrame, output_path: Path) -> None:
    wavelength_nm = frame["Wavelength_nm"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(11.2, 5.8), dpi=320)
    add_zone_background(ax)
    ax.plot(wavelength_nm, frame["R_front"].to_numpy(dtype=float) * 100.0, color="#424242", linewidth=1.8, label="R_front")
    ax.plot(wavelength_nm, frame["R_stack"].to_numpy(dtype=float) * 100.0, color="#005b96", linewidth=1.8, label="R_stack")
    ax.plot(wavelength_nm, frame["R_total"].to_numpy(dtype=float) * 100.0, color="#b03a2e", linewidth=2.1, label="R_total")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Reflectance (%)")
    ax.set_title(f"{PHASE_NAME} Pristine Baseline Decomposition")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def plot_pristine_three_zones(frame: pd.DataFrame, output_path: Path) -> None:
    wavelength_nm = frame["Wavelength_nm"].to_numpy(dtype=float)
    reflectance = frame["R_total"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(11.2, 5.8), dpi=320)
    add_zone_background(ax)
    ax.plot(wavelength_nm, reflectance * 100.0, color="#0d47a1", linewidth=2.2)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Reflectance (%)")
    ax.set_title(f"{PHASE_NAME} Pristine Baseline by Three Zones")
    ax.grid(True, linestyle="--", alpha=0.25)

    y_min, y_max = ax.get_ylim()
    text_y = y_max - 0.05 * (y_max - y_min)
    centers = {
        "Zone 1": 525.0,
        "Zone 2": 730.0,
        "Zone 3": 955.0,
    }
    for zone_name, center in centers.items():
        ax.text(
            center,
            text_y,
            ZONE_LABELS[zone_name],
            ha="center",
            va="top",
            fontsize=9.2,
            color="#263238",
            bbox={"facecolor": "white", "alpha": 0.78, "edgecolor": "none", "pad": 2.5},
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def summarize_zone(frame: pd.DataFrame, zone_name: str) -> dict[str, float]:
    mask = frame["zone_label"] == zone_name
    subset = frame.loc[mask]
    return {
        "mean_front": float(subset["R_front"].mean()),
        "mean_stack": float(subset["R_stack"].mean()),
        "mean_total": float(subset["R_total"].mean()),
        "std_front": float(subset["R_front"].std(ddof=0)),
        "std_stack": float(subset["R_stack"].std(ddof=0)),
        "std_total": float(subset["R_total"].std(ddof=0)),
        "min_total": float(subset["R_total"].min()),
        "max_total": float(subset["R_total"].max()),
    }


def count_local_extrema(values: np.ndarray) -> int:
    gradient = np.diff(values)
    sign = np.sign(gradient)
    sign[sign == 0.0] = 1.0
    return int(np.count_nonzero(np.diff(sign) != 0))


def build_zone_interpretation(frame: pd.DataFrame) -> dict[str, str]:
    zone1 = summarize_zone(frame, "Zone 1")
    zone2 = summarize_zone(frame, "Zone 2")
    zone3 = summarize_zone(frame, "Zone 3")

    zone1_background_ratio = zone1["mean_front"] / max(zone1["mean_total"], 1e-12)
    zone1_structure = "已出现明显结构性调制" if zone1["std_stack"] > 3.0 * max(zone1["std_front"], 1e-12) else "结构性调制仍较弱"
    zone1_front_role = "只是弱背景" if zone1_background_ratio < 0.35 else "占据显著比例"

    zone2_transition = (
        "可以视为从强吸收主导向透明干涉主导的过渡区"
        if zone2["std_total"] > zone1["std_total"] * 0.8
        else "过渡趋势较弱，仍更接近前窗平滑响应"
    )
    zone2_cavity = "微腔效应已经开始显现" if zone2["std_stack"] > zone1["std_stack"] else "微腔效应尚未充分展开"

    zone3_mask = frame["zone_label"] == "Zone 3"
    zone3_total = frame.loc[zone3_mask, "R_total"].to_numpy(dtype=float)
    zone3_extrema = count_local_extrema(zone3_total)
    zone3_range = float(np.max(zone3_total) - np.min(zone3_total))
    zone3_fringe = "已出现清晰干涉条纹" if zone3_extrema >= 3 or zone3_range >= 0.15 else "干涉条纹仍偏弱"
    zone3_origin = "可视为 PVK 与上下边界共同形成的多层微腔效应" if zone3["std_stack"] > 5.0 * max(zone3["std_front"], 1e-12) else "多层微腔效应尚不够强"

    return {
        "Zone 1": (
            f"R_total 主要由后侧 stack 控制，R_front 在该段{zone1_front_role}；"
            f"同时后侧 stack {zone1_structure}。"
        ),
        "Zone 2": f"{zone2_transition}，且 {zone2_cavity}。",
        "Zone 3": f"{zone3_fringe}，这些 fringe 的主导来源 {zone3_origin}。",
    }


def validate_outputs(frame: pd.DataFrame) -> list[str]:
    notes: list[str] = []
    numeric_columns = ["R_front", "T_front", "R_stack", "R_total"]
    values = frame[numeric_columns].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Phase A-1 输出中存在 NaN/Inf。")
    if np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError("Phase A-1 反射率超出物理范围 [0, 1]。")

    closure = frame["R_front"].to_numpy(dtype=float) + (
        frame["T_front"].to_numpy(dtype=float) ** 2
        * frame["R_stack"].to_numpy(dtype=float)
        / (1.0 - frame["R_front"].to_numpy(dtype=float) * frame["R_stack"].to_numpy(dtype=float))
    )
    max_closure_error = float(np.max(np.abs(closure - frame["R_total"].to_numpy(dtype=float))))
    if max_closure_error > 1e-12:
        raise ValueError(f"Phase A-1 级联闭合失败: max_abs_err={max_closure_error:.3e}")
    notes.append(f"强度级联闭合误差 max_abs = {max_closure_error:.3e}")
    return notes


def write_log(
    frame: pd.DataFrame,
    nk_csv_path: Path,
    output_paths: OutputPaths,
    consistency_notes: list[str],
    validation_notes: list[str],
) -> None:
    wavelength_nm = frame["Wavelength_nm"].to_numpy(dtype=float)
    r_front = frame["R_front"].to_numpy(dtype=float)
    r_stack = frame["R_stack"].to_numpy(dtype=float)
    r_total = frame["R_total"].to_numpy(dtype=float)
    idx_550 = int(np.argmin(np.abs(wavelength_nm - 550.0)))
    zone_interpretation = build_zone_interpretation(frame)
    zone1 = summarize_zone(frame, "Zone 1")
    zone2 = summarize_zone(frame, "Zone 2")
    zone3 = summarize_zone(frame, "Zone 3")

    max_index = int(np.argmax(r_total))
    min_index = int(np.argmin(r_total))
    anomaly_lines = ["- 未发现列缺失、波长网格异常、反射率越界、NaN 或 Inf。"]

    lines = [
        f"# {PHASE_NAME} Pristine Baseline",
        "",
        "## Inputs",
        "",
        f"- n-k input: `{nk_csv_path.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- required columns validated: `{', '.join(REQUIRED_COLUMNS)}`",
        *[f"- {note}" for note in consistency_notes],
        "",
        "## Geometry And Solver Contract",
        "",
        "- incidence: `normal incidence`",
        "- front medium: `Air`",
        "- thick glass handling: `1 mm glass treated as incoherent, excluded from phase matrix`",
        "- constant glass override: `n_glass = 1.515`, `k_glass = 0`",
        "- stack geometry: `Glass -> ITO(100 nm) -> NiOx(45 nm) -> SAM(5 nm) -> PVK(700 nm) -> C60(15 nm) -> Ag(100 nm) -> Air`",
        "- Ag boundary mode: `100 nm finite Ag film + semi-infinite Air exit medium`",
        "",
        "## Disabled Modulations",
        "",
        "- `d_air = 0`",
        "- `d_rough = 0`",
        "- `sigma_thickness = 0`",
        "- `ito_alpha = 0`",
        "- `pvk_b_scale = 1`",
        "- `front_scale` unused",
        "- `BEMA` disabled",
        "- empirical background / absorption corrections disabled",
        "",
        "## Key Numbers",
        "",
        f"- `R_front(550 nm) = {r_front[idx_550] * 100.0:.4f}%`",
        f"- `R_stack(550 nm) = {r_stack[idx_550] * 100.0:.4f}%`",
        f"- `R_total(550 nm) = {r_total[idx_550] * 100.0:.4f}%`",
        f"- `R_total` minimum: `{r_total[min_index] * 100.0:.4f}% @ {wavelength_nm[min_index]:.0f} nm`",
        f"- `R_total` maximum: `{r_total[max_index] * 100.0:.4f}% @ {wavelength_nm[max_index]:.0f} nm`",
        f"- Zone 1 mean `R_total`: `{zone1['mean_total'] * 100.0:.4f}%`",
        f"- Zone 2 mean `R_total`: `{zone2['mean_total'] * 100.0:.4f}%`",
        f"- Zone 3 mean `R_total`: `{zone3['mean_total'] * 100.0:.4f}%`",
        "",
        "## Spectral Summary",
        "",
        (
            f"- `R_front` 基本为平滑弱背景，而 `R_stack` 与 `R_total` 在长波端结构更强；"
            f"`R_total` 的主要峰谷范围约为 `{r_total[min_index] * 100.0:.2f}% - {r_total[max_index] * 100.0:.2f}%`。"
        ),
        "",
        "## Three-Zone Interpretation",
        "",
        f"- Zone 1 (`400-650 nm`): {zone_interpretation['Zone 1']}",
        f"- Zone 2 (`650-810 nm`): {zone_interpretation['Zone 2']}",
        f"- Zone 3 (`810-1100 nm`): {zone_interpretation['Zone 3']}",
        "",
        "## Validation",
        "",
        *[f"- {note}" for note in validation_notes],
        "",
        "## Anomalies",
        "",
        *anomaly_lines,
        "",
        "## Outputs",
        "",
        f"- csv: `{output_paths.processed_csv.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- figure (decomposition): `{output_paths.decomposition_figure.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- figure (3 zones): `{output_paths.zones_figure.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- log: `{output_paths.log_path.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Note",
        "",
        "- 后续可在同一 pristine baseline 上做 `constant-glass vs dispersive-glass` sensitivity check。",
    ]
    output_paths.log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    nk_csv_path = args.nk_csv.resolve()
    output_paths = ensure_output_dirs()

    stack, _, consistency_notes = load_optical_stack_from_aligned_csv(nk_csv_path)
    decomposition = stack.compute_pristine_baseline_decomposition(
        wavelengths_nm=EXPECTED_WAVELENGTHS_NM,
        use_constant_glass=True,
        constant_glass_nk=DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode=AG_BOUNDARY_FINITE_FILM,
    )

    frame = pd.DataFrame(decomposition)
    frame["zone_label"] = build_zone_labels(frame["Wavelength_nm"].to_numpy(dtype=float))
    frame = frame[["Wavelength_nm", "zone_label", "R_front", "T_front", "R_stack", "R_total"]]

    validation_notes = validate_outputs(frame)
    frame.to_csv(output_paths.processed_csv, index=False, encoding="utf-8-sig")
    plot_pristine_decomposition(frame, output_paths.decomposition_figure)
    plot_pristine_three_zones(frame, output_paths.zones_figure)
    write_log(frame, nk_csv_path, output_paths, consistency_notes, validation_notes)

    print(f"csv_path={output_paths.processed_csv}")
    print(f"decomposition_figure={output_paths.decomposition_figure}")
    print(f"zones_figure={output_paths.zones_figure}")
    print(f"log_path={output_paths.log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
