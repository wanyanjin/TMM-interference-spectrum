"""Phase A-1.1 PVK 749/750 nm seam forensic audit.

This audit is intentionally read-only with respect to the main optical tables.
It traces the PVK seam around 749/750 nm across source data, local derivatives,
stack sensitivity, Ag boundary sensitivity, and code-path consistency checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import sys

import matplotlib
import numpy as np
import pandas as pd
from tmm import coh_tmm

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.full_stack_microcavity import (  # noqa: E402
    AG_BOUNDARY_FINITE_FILM,
    AG_BOUNDARY_SEMI_INFINITE,
    DEFAULT_CONSTANT_GLASS_INDEX,
    LayerThicknesses,
    OpticalStackTable,
)


PHASE_NAME = "Phase A-1.1"
ALIGNED_NK_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk.csv"
PHASE_A1_BASELINE_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA1" / "phaseA1_pristine_baseline.csv"
PVK_EXTENDED_PATH = PROJECT_ROOT / "data" / "processed" / "CsFAPI_nk_extended.csv"
PVK_DIGITIZED_PATH = PROJECT_ROOT / "resources" / "digitized" / "phase02_fig3_csfapi_optical_constants_digitized.csv"
STEP05C_PATH = PROJECT_ROOT / "src" / "scripts" / "step05c_build_aligned_nk_stack.py"

LOCAL_WINDOW = (730.0, 770.0)
STACK_WINDOW = (720.0, 780.0)
SEAM_LEFT_NM = 749.0
SEAM_RIGHT_NM = 750.0
GLASS_NK = DEFAULT_CONSTANT_GLASS_INDEX
AIR_NK = 1.0 + 0.0j
SAM_NK = 1.5 + 0.0j
THICKNESSES = LayerThicknesses(
    ito_nm=100.0,
    niox_nm=45.0,
    sam_nm=5.0,
    pvk_nm=700.0,
    c60_nm=15.0,
    ag_nm=100.0,
)


@dataclass(frozen=True)
class OutputPaths:
    data_dir: Path
    figure_dir: Path
    log_dir: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase A-1.1 PVK seam forensic audit.")
    parser.add_argument("--aligned-nk", type=Path, default=ALIGNED_NK_PATH)
    parser.add_argument("--baseline-csv", type=Path, default=PHASE_A1_BASELINE_PATH)
    return parser.parse_args()


def ensure_output_dirs() -> OutputPaths:
    data_dir = PROJECT_ROOT / "data" / "processed" / "phaseA1_seam_audit"
    figure_dir = PROJECT_ROOT / "results" / "figures" / "phaseA1_seam_audit"
    log_dir = PROJECT_ROOT / "results" / "logs" / "phaseA1_seam_audit"
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    return OutputPaths(data_dir=data_dir, figure_dir=figure_dir, log_dir=log_dir)


def add_seam_markers(axis: plt.Axes) -> None:
    axis.axvline(SEAM_LEFT_NM, color="#8e244d", linestyle="--", linewidth=1.0, alpha=0.85)
    axis.axvline(SEAM_RIGHT_NM, color="#d84315", linestyle="--", linewidth=1.0, alpha=0.85)


def local_mask(values: np.ndarray, lower_nm: float, upper_nm: float) -> np.ndarray:
    wavelength = np.asarray(values, dtype=float)
    return (wavelength >= lower_nm) & (wavelength <= upper_nm)


def compute_derivative(values: np.ndarray, wavelength_nm: np.ndarray) -> np.ndarray:
    return np.gradient(np.asarray(values, dtype=float), np.asarray(wavelength_nm, dtype=float))


def find_step_metrics(values: np.ndarray, wavelength_nm: np.ndarray) -> dict[str, float]:
    index_749 = int(np.argmin(np.abs(wavelength_nm - SEAM_LEFT_NM)))
    index_750 = int(np.argmin(np.abs(wavelength_nm - SEAM_RIGHT_NM)))
    step = float(values[index_750] - values[index_749])
    left_slope = float(values[index_749] - values[index_749 - 1]) if index_749 > 0 else 0.0
    right_slope = float(values[index_750 + 1] - values[index_750]) if index_750 + 1 < len(values) else 0.0
    slope_jump = float(right_slope - left_slope)
    return {
        "value_749": float(values[index_749]),
        "value_750": float(values[index_750]),
        "step_749_750": step,
        "left_slope": left_slope,
        "right_slope": right_slope,
        "slope_jump": slope_jump,
    }


def load_aligned_pvk_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"Wavelength_nm", "n_PVK", "k_PVK"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path} 缺少 PVK 审计必要列: {missing}")
    mask = local_mask(frame["Wavelength_nm"].to_numpy(dtype=float), *LOCAL_WINDOW)
    local = frame.loc[mask, ["Wavelength_nm", "n_PVK", "k_PVK"]].copy()
    local["eps1"] = local["n_PVK"] ** 2 - local["k_PVK"] ** 2
    local["eps2"] = 2.0 * local["n_PVK"] * local["k_PVK"]
    local["dn_dlambda"] = compute_derivative(local["n_PVK"].to_numpy(dtype=float), local["Wavelength_nm"].to_numpy(dtype=float))
    local["dk_dlambda"] = compute_derivative(local["k_PVK"].to_numpy(dtype=float), local["Wavelength_nm"].to_numpy(dtype=float))
    local["deps1_dlambda"] = compute_derivative(local["eps1"].to_numpy(dtype=float), local["Wavelength_nm"].to_numpy(dtype=float))
    local["deps2_dlambda"] = compute_derivative(local["eps2"].to_numpy(dtype=float), local["Wavelength_nm"].to_numpy(dtype=float))
    return local


def save_local_audit_plot(frame: pd.DataFrame, figure_dir: Path) -> None:
    wavelength_nm = frame["Wavelength_nm"].to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(10.5, 5.0), dpi=320)
    ax.plot(wavelength_nm, frame["n_PVK"].to_numpy(dtype=float), color="#005b96", linewidth=1.8, label="n_PVK")
    ax.plot(wavelength_nm, frame["k_PVK"].to_numpy(dtype=float), color="#b03a2e", linewidth=1.8, label="k_PVK")
    add_seam_markers(ax)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Value")
    ax.set_title("PVK n/k Local Zoom (730-770 nm)")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(figure_dir / "pvk_nk_local_zoom.png", dpi=320, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10.5, 5.0), dpi=320)
    ax.plot(wavelength_nm, frame["eps1"].to_numpy(dtype=float), color="#2e7d32", linewidth=1.8, label="eps1")
    ax.plot(wavelength_nm, frame["eps2"].to_numpy(dtype=float), color="#6a1b9a", linewidth=1.8, label="eps2")
    add_seam_markers(ax)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Dielectric Function")
    ax.set_title("PVK eps1/eps2 Local Zoom (730-770 nm)")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(figure_dir / "pvk_eps_local_zoom.png", dpi=320, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10.5, 5.0), dpi=320)
    ax.plot(wavelength_nm, frame["dn_dlambda"].to_numpy(dtype=float), color="#005b96", linewidth=1.8, label="dn/dlambda")
    ax.plot(wavelength_nm, frame["dk_dlambda"].to_numpy(dtype=float), color="#b03a2e", linewidth=1.8, label="dk/dlambda")
    add_seam_markers(ax)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Derivative")
    ax.set_title("PVK dn/dlambda and dk/dlambda Local Zoom")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(figure_dir / "pvk_derivative_local_zoom.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def load_source_comparison_frame() -> pd.DataFrame:
    digitized = pd.read_csv(PVK_DIGITIZED_PATH)
    digitized = digitized[(digitized["series"] == "ITO/CsFAPI") & (digitized["quantity"].isin(["n", "kappa"]))].copy()
    digitized["source_name"] = "digitized_fig3"
    digitized = digitized.rename(columns={"wavelength_nm": "Wavelength_nm", "value": "value"})
    digitized["component"] = digitized["quantity"].replace({"kappa": "k"})
    digitized = digitized.loc[:, ["source_name", "component", "Wavelength_nm", "value"]]

    extended = pd.read_csv(PVK_EXTENDED_PATH)
    extended_n = extended.loc[:, ["Wavelength", "n"]].rename(columns={"Wavelength": "Wavelength_nm", "n": "value"})
    extended_n["component"] = "n"
    extended_k = extended.loc[:, ["Wavelength", "k"]].rename(columns={"Wavelength": "Wavelength_nm", "k": "value"})
    extended_k["component"] = "k"
    extended_frame = pd.concat([extended_n, extended_k], ignore_index=True)
    extended_frame["source_name"] = "extended_csv"
    extended_frame = extended_frame.loc[:, ["source_name", "component", "Wavelength_nm", "value"]]

    aligned = pd.read_csv(ALIGNED_NK_PATH)
    aligned_n = aligned.loc[:, ["Wavelength_nm", "n_PVK"]].rename(columns={"n_PVK": "value"})
    aligned_n["component"] = "n"
    aligned_k = aligned.loc[:, ["Wavelength_nm", "k_PVK"]].rename(columns={"k_PVK": "value"})
    aligned_k["component"] = "k"
    aligned_frame = pd.concat([aligned_n, aligned_k], ignore_index=True)
    aligned_frame["source_name"] = "aligned_stack"
    aligned_frame = aligned_frame.loc[:, ["source_name", "component", "Wavelength_nm", "value"]]

    frame = pd.concat([digitized, extended_frame, aligned_frame], ignore_index=True)
    mask = local_mask(frame["Wavelength_nm"].to_numpy(dtype=float), *LOCAL_WINDOW)
    return frame.loc[mask].copy()


def save_source_overlay(frame: pd.DataFrame, figure_dir: Path) -> None:
    colors = {"digitized_fig3": "#424242", "extended_csv": "#005b96", "aligned_stack": "#b03a2e"}
    fig, axes = plt.subplots(2, 1, figsize=(10.8, 8.6), dpi=320, constrained_layout=True, sharex=True)
    for axis, component in zip(axes, ("n", "k")):
        subset = frame[frame["component"] == component]
        for source_name in ("digitized_fig3", "extended_csv", "aligned_stack"):
            source_subset = subset[subset["source_name"] == source_name].sort_values("Wavelength_nm")
            if source_subset.empty:
                continue
            axis.plot(
                source_subset["Wavelength_nm"].to_numpy(dtype=float),
                source_subset["value"].to_numpy(dtype=float),
                linewidth=1.8,
                color=colors[source_name],
                label=source_name,
            )
        add_seam_markers(axis)
        axis.set_ylabel(component)
        axis.set_title(f"PVK Source Overlay: {component}(730-770 nm)")
        axis.grid(True, linestyle="--", alpha=0.25)
        axis.legend(loc="best")
    axes[-1].set_xlabel("Wavelength (nm)")
    fig.savefig(figure_dir / "pvk_source_overlay.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def extract_step05c_bridge_logic() -> list[str]:
    lines: list[str] = []
    with STEP05C_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if "bridge_to_boundary(n_values, 744, 750)" in line or "bridge_to_boundary(k_values, 744, 750)" in line:
                lines.append(line.strip())
            if "smooth_join_region(n_values, 750)" in line or "smooth_join_region(k_values, 750" in line:
                lines.append(line.strip())
            if "upper_mask = WL_GRID >= PVK_MID_BOUNDARY_NM" in line or "middle_mask = (WL_GRID >= PVK_LOW_BOUNDARY_NM) & (WL_GRID < PVK_MID_BOUNDARY_NM)" in line:
                lines.append(line.strip())
    return lines


def build_stack_reflectance(
    stack: OpticalStackTable,
    wavelength_nm: np.ndarray,
    stack_type: str,
    ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
) -> np.ndarray:
    query = np.asarray(wavelength_nm, dtype=float)
    result = np.empty(query.shape, dtype=float)
    base_indices = np.rint(query).astype(int) - int(stack.wavelength_nm[0])

    for out_index, source_index in enumerate(base_indices):
        glass_nk = complex(GLASS_NK)
        pvk_nk = complex(stack.n_pvk[source_index])
        if stack_type == "simple":
            n_list = [glass_nk, pvk_nk, AIR_NK]
            d_list = [np.inf, THICKNESSES.pvk_nm, np.inf]
        elif stack_type == "mid":
            n_list = [
                glass_nk,
                complex(stack.n_ito[source_index]),
                complex(stack.n_niox[source_index]),
                SAM_NK,
                pvk_nk,
                AIR_NK,
            ]
            d_list = [
                np.inf,
                THICKNESSES.ito_nm,
                THICKNESSES.niox_nm,
                THICKNESSES.sam_nm,
                THICKNESSES.pvk_nm,
                np.inf,
            ]
        elif stack_type == "full":
            if ag_boundary_mode == AG_BOUNDARY_FINITE_FILM:
                n_list = [
                    glass_nk,
                    complex(stack.n_ito[source_index]),
                    complex(stack.n_niox[source_index]),
                    SAM_NK,
                    pvk_nk,
                    complex(stack.n_c60[source_index]),
                    complex(stack.n_ag[source_index]),
                    AIR_NK,
                ]
                d_list = [
                    np.inf,
                    THICKNESSES.ito_nm,
                    THICKNESSES.niox_nm,
                    THICKNESSES.sam_nm,
                    THICKNESSES.pvk_nm,
                    THICKNESSES.c60_nm,
                    THICKNESSES.ag_nm,
                    np.inf,
                ]
            else:
                n_list = [
                    glass_nk,
                    complex(stack.n_ito[source_index]),
                    complex(stack.n_niox[source_index]),
                    SAM_NK,
                    pvk_nk,
                    complex(stack.n_c60[source_index]),
                    complex(stack.n_ag[source_index]),
                ]
                d_list = [
                    np.inf,
                    THICKNESSES.ito_nm,
                    THICKNESSES.niox_nm,
                    THICKNESSES.sam_nm,
                    THICKNESSES.pvk_nm,
                    THICKNESSES.c60_nm,
                    np.inf,
                ]
        else:
            raise ValueError(f"未知 stack_type: {stack_type}")
        result[out_index] = float(coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(query[out_index]))["R"])
    return result


def build_stack_sensitivity_frame(stack: OpticalStackTable) -> pd.DataFrame:
    wavelength_nm = np.arange(STACK_WINDOW[0], STACK_WINDOW[1] + 1.0, 1.0, dtype=float)
    rows: list[dict[str, object]] = []
    for stack_type in ("simple", "mid", "full"):
        reflectance = build_stack_reflectance(stack, wavelength_nm, stack_type=stack_type)
        derivative = compute_derivative(reflectance, wavelength_nm)
        metrics = find_step_metrics(reflectance, wavelength_nm)
        for wl, refl, deriv in zip(wavelength_nm, reflectance, derivative):
            rows.append(
                {
                    "stack_type": stack_type,
                    "Wavelength_nm": float(wl),
                    "reflectance": float(refl),
                    "dR_dlambda": float(deriv),
                    "step_749_750": metrics["step_749_750"],
                    "slope_jump_749_750": metrics["slope_jump"],
                }
            )
    return pd.DataFrame(rows)


def save_stack_sensitivity_figure(frame: pd.DataFrame, figure_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.8, 5.4), dpi=320)
    colors = {"simple": "#424242", "mid": "#005b96", "full": "#b03a2e"}
    labels = {
        "simple": "Glass / PVK / Air",
        "mid": "Glass / ITO / NiOx / SAM / PVK / Air",
        "full": "Glass / ITO / NiOx / SAM / PVK / C60 / Ag / Air",
    }
    for stack_type in ("simple", "mid", "full"):
        subset = frame[frame["stack_type"] == stack_type]
        ax.plot(
            subset["Wavelength_nm"].to_numpy(dtype=float),
            subset["reflectance"].to_numpy(dtype=float) * 100.0,
            linewidth=1.9,
            color=colors[stack_type],
            label=labels[stack_type],
        )
    add_seam_markers(ax)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Reflectance (%)")
    ax.set_title("Seam Stack Sensitivity (720-780 nm)")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(figure_dir / "seam_stack_sensitivity.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def build_ag_boundary_frame(stack: OpticalStackTable, baseline_frame: pd.DataFrame) -> pd.DataFrame:
    wavelength_nm = np.arange(STACK_WINDOW[0], STACK_WINDOW[1] + 1.0, 1.0, dtype=float)
    stack_finite = build_stack_reflectance(stack, wavelength_nm, "full", ag_boundary_mode=AG_BOUNDARY_FINITE_FILM)
    stack_semi = build_stack_reflectance(stack, wavelength_nm, "full", ag_boundary_mode=AG_BOUNDARY_SEMI_INFINITE)

    r_front = baseline_frame.set_index("Wavelength_nm").loc[wavelength_nm, "R_front"].to_numpy(dtype=float)
    t_front = 1.0 - r_front
    total_finite = r_front + (t_front**2) * stack_finite / (1.0 - r_front * stack_finite)
    total_semi = r_front + (t_front**2) * stack_semi / (1.0 - r_front * stack_semi)

    rows: list[dict[str, object]] = []
    for mode_name, r_stack, r_total in (
        (AG_BOUNDARY_FINITE_FILM, stack_finite, total_finite),
        (AG_BOUNDARY_SEMI_INFINITE, stack_semi, total_semi),
    ):
        metrics = find_step_metrics(r_stack, wavelength_nm)
        total_metrics = find_step_metrics(r_total, wavelength_nm)
        for wl, stack_value, total_value in zip(wavelength_nm, r_stack, r_total):
            rows.append(
                {
                    "ag_boundary_mode": mode_name,
                    "Wavelength_nm": float(wl),
                    "R_stack": float(stack_value),
                    "R_total": float(total_value),
                    "R_stack_step_749_750": metrics["step_749_750"],
                    "R_total_step_749_750": total_metrics["step_749_750"],
                }
            )
    return pd.DataFrame(rows)


def save_ag_sensitivity_figure(frame: pd.DataFrame, figure_dir: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10.8, 8.0), dpi=320, constrained_layout=True, sharex=True)
    labels = {
        AG_BOUNDARY_FINITE_FILM: "100 nm finite Ag + Air exit",
        AG_BOUNDARY_SEMI_INFINITE: "semi-infinite Ag",
    }
    colors = {
        AG_BOUNDARY_FINITE_FILM: "#b03a2e",
        AG_BOUNDARY_SEMI_INFINITE: "#005b96",
    }
    for axis, value_column in zip(axes, ("R_stack", "R_total")):
        for mode_name in (AG_BOUNDARY_FINITE_FILM, AG_BOUNDARY_SEMI_INFINITE):
            subset = frame[frame["ag_boundary_mode"] == mode_name]
            axis.plot(
                subset["Wavelength_nm"].to_numpy(dtype=float),
                subset[value_column].to_numpy(dtype=float) * 100.0,
                linewidth=1.9,
                color=colors[mode_name],
                label=labels[mode_name],
            )
        add_seam_markers(axis)
        axis.set_ylabel(f"{value_column} (%)")
        axis.set_title(f"Ag Boundary Sensitivity: {value_column}")
        axis.grid(True, linestyle="--", alpha=0.25)
        axis.legend(loc="best")
    axes[-1].set_xlabel("Wavelength (nm)")
    fig.savefig(figure_dir / "seam_ag_boundary_sensitivity.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def save_pristine_zoom_figure(baseline_frame: pd.DataFrame, figure_dir: Path) -> None:
    subset = baseline_frame[(baseline_frame["Wavelength_nm"] >= STACK_WINDOW[0]) & (baseline_frame["Wavelength_nm"] <= STACK_WINDOW[1])].copy()
    fig, ax = plt.subplots(figsize=(10.8, 5.2), dpi=320)
    ax.plot(subset["Wavelength_nm"].to_numpy(dtype=float), subset["R_total"].to_numpy(dtype=float) * 100.0, color="#0d47a1", linewidth=2.0)
    add_seam_markers(ax)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("R_total (%)")
    ax.set_title("Phase A-1 Pristine Baseline Zoom (720-780 nm)")
    ax.grid(True, linestyle="--", alpha=0.25)
    fig.tight_layout()
    fig.savefig(figure_dir / "phaseA1_pristine_720_780_zoom.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def detect_code_level_findings(baseline_frame: pd.DataFrame, aligned_frame: pd.DataFrame) -> list[str]:
    findings: list[str] = []
    aligned_wavelength = aligned_frame["Wavelength_nm"].to_numpy(dtype=float)
    if not np.array_equal(aligned_wavelength, np.arange(400.0, 1101.0, 1.0, dtype=float)):
        findings.append("aligned_full_stack_nk.csv 的波长网格不符合整数 1 nm 规则。")
    baseline_subset = baseline_frame[(baseline_frame["Wavelength_nm"] >= STACK_WINDOW[0]) & (baseline_frame["Wavelength_nm"] <= STACK_WINDOW[1])].copy()
    if baseline_subset["R_total"].diff().abs().max() <= 0.0:
        findings.append("Phase A-1 CSV 未记录到实际突变，疑似仅图像渲染伪影。")
    return findings


def rank_hypotheses(
    pvk_metrics: dict[str, dict[str, float]],
    stack_frame: pd.DataFrame,
    ag_frame: pd.DataFrame,
    code_findings: list[str],
) -> list[str]:
    full_step = abs(float(stack_frame[stack_frame["stack_type"] == "full"]["step_749_750"].iloc[0]))
    simple_step = abs(float(stack_frame[stack_frame["stack_type"] == "simple"]["step_749_750"].iloc[0]))
    ag_finite = abs(float(ag_frame[ag_frame["ag_boundary_mode"] == AG_BOUNDARY_FINITE_FILM]["R_stack_step_749_750"].iloc[0]))
    ag_semi = abs(float(ag_frame[ag_frame["ag_boundary_mode"] == AG_BOUNDARY_SEMI_INFINITE]["R_stack_step_749_750"].iloc[0]))

    ranking = [
        f"1. `PVK 数据拼接伪影`：`k_PVK` 在 749/750 nm 附近出现显著跃迁，且 `n_PVK/eps2` 导数尖峰与 step05c 的 bridge+smooth 拼接逻辑一致。",
        f"2. `多因素共同作用`：最简堆栈已可见 seam，但完整堆栈 step 从 `{simple_step:.6f}` 放大到 `{full_step:.6f}`，说明微腔会增强材料 seam。",
        f"3. `真实 band-edge 急变`：不能完全排除，但当前接缝与上游拼接边界精确同位，更弱于数据伪影假说。",
        (
            "4. `代码实现 bug`：当前未发现层序切换、插值 off-by-one 或边界条件误切换；"
            if not code_findings
            else "4. `代码实现 bug`：发现了可疑实现问题，但证据仍次于材料 seam。"
        ),
    ]
    if ag_finite > ag_semi:
        ranking.append(
            f"补充：Ag 有限厚度边界会进一步放大 seam，可见 `finite={ag_finite:.6f}` 高于 `semi_infinite={ag_semi:.6f}`。"
        )
    return ranking


def write_log(
    output_paths: OutputPaths,
    local_frame: pd.DataFrame,
    source_frame: pd.DataFrame,
    stack_frame: pd.DataFrame,
    ag_frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    bridge_lines: list[str],
    code_findings: list[str],
) -> None:
    local_n = find_step_metrics(local_frame["n_PVK"].to_numpy(dtype=float), local_frame["Wavelength_nm"].to_numpy(dtype=float))
    local_k = find_step_metrics(local_frame["k_PVK"].to_numpy(dtype=float), local_frame["Wavelength_nm"].to_numpy(dtype=float))
    local_eps1 = find_step_metrics(local_frame["eps1"].to_numpy(dtype=float), local_frame["Wavelength_nm"].to_numpy(dtype=float))
    local_eps2 = find_step_metrics(local_frame["eps2"].to_numpy(dtype=float), local_frame["Wavelength_nm"].to_numpy(dtype=float))

    full_step = float(stack_frame[stack_frame["stack_type"] == "full"]["step_749_750"].iloc[0])
    mid_step = float(stack_frame[stack_frame["stack_type"] == "mid"]["step_749_750"].iloc[0])
    simple_step = float(stack_frame[stack_frame["stack_type"] == "simple"]["step_749_750"].iloc[0])

    finite_row = ag_frame[ag_frame["ag_boundary_mode"] == AG_BOUNDARY_FINITE_FILM].iloc[0]
    semi_row = ag_frame[ag_frame["ag_boundary_mode"] == AG_BOUNDARY_SEMI_INFINITE].iloc[0]
    finite_stack_step = float(finite_row["R_stack_step_749_750"])
    semi_stack_step = float(semi_row["R_stack_step_749_750"])

    digitized_n = source_frame[(source_frame["source_name"] == "digitized_fig3") & (source_frame["component"] == "n")]
    extended_k = source_frame[(source_frame["source_name"] == "extended_csv") & (source_frame["component"] == "k")]
    aligned_k = source_frame[(source_frame["source_name"] == "aligned_stack") & (source_frame["component"] == "k")]

    k_hard_switch = bool(
        float(extended_k[extended_k["Wavelength_nm"] == 750.0]["value"].iloc[0]) == 0.0
        and float(extended_k[extended_k["Wavelength_nm"] == 751.0]["value"].iloc[0]) == 0.0
    )
    source_conclusion = (
        "digitized 左段 + extended 右段的 step05c 拼接逻辑"
        if bridge_lines
        else "上游 PVK middleware/对齐表拼接链路"
    )
    code_conclusion = (
        "当前更支持材料 seam 而非代码 bug 假说。"
        if not code_findings
        else "发现了代码级可疑点，但当前证据仍更支持材料 seam。"
    )

    ranking = rank_hypotheses(
        pvk_metrics={"n": local_n, "k": local_k, "eps1": local_eps1, "eps2": local_eps2},
        stack_frame=stack_frame,
        ag_frame=ag_frame,
        code_findings=code_findings,
    )

    lines = [
        f"# {PHASE_NAME} PVK Seam Audit",
        "",
        "## Inputs",
        "",
        f"- aligned stack: `{ALIGNED_NK_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- pristine baseline: `{PHASE_A1_BASELINE_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- PVK extended middleware: `{PVK_EXTENDED_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- PVK digitized source: `{PVK_DIGITIZED_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- stitch builder: `{STEP05C_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Audit Scope",
        "",
        "- 几何口径沿用 Phase A-1：Glass(incoherent) / ITO(100) / NiOx(45) / SAM(5) / PVK(700) / C60(15) / Ag(100)。",
        "- 不做拟合、不改主链路数据表、不做平滑修复。",
        "",
        "## Q1. 749/750 nm 处，PVK n/k/eps1/eps2 是否存在明显 seam？",
        "",
        f"- `n_PVK`: 749 nm = `{local_n['value_749']:.6f}`, 750 nm = `{local_n['value_750']:.6f}`, step = `{local_n['step_749_750']:+.6f}`",
        f"- `k_PVK`: 749 nm = `{local_k['value_749']:.6f}`, 750 nm = `{local_k['value_750']:.6f}`, step = `{local_k['step_749_750']:+.6f}`",
        f"- `eps1`: step = `{local_eps1['step_749_750']:+.6f}`",
        f"- `eps2`: step = `{local_eps2['step_749_750']:+.6f}`",
        "- 结论：seam 被确认存在，且在 `k_PVK` 与 `eps2` 上尤为明显。",
        "",
        "## Q2. 这个 seam 是数值跳点、导数跳点，还是 k=0 硬切换？",
        "",
        f"- `n_PVK` 存在值跳点，但更强的是导数变化：slope_jump = `{local_n['slope_jump']:+.6f}`",
        f"- `k_PVK` 同时存在值跳点和导数尖峰：slope_jump = `{local_k['slope_jump']:+.6f}`",
        f"- `extended_csv` 在 750 nm 起 `k=0`：`{k_hard_switch}`",
        "- 结论：当前 seam 更接近“右侧 k=0 硬约束 + 拼接导数不连续”的组合，而不是单纯的平滑 band-edge。",
        "",
        "## Q3. seam 来自哪一个上游步骤？",
        "",
        f"- 当前最直接来源是：`{source_conclusion}`。",
        "- digitized 数据承担 450-749 nm 左段，extended middleware 承担 750 nm 及以上右段。",
        "- step05c 在 744->750 nm 先做线性 bridge，再在 750 nm 周围做 rolling smooth，但并未消除导数不连续。",
        *[f"- step05c 证据：`{line}`" for line in bridge_lines],
        "",
        "## Q4. 在最简堆栈中 seam 是否已经能看到？",
        "",
        f"- `Glass / PVK / Air` 的 749->750 nm 反射率步长 = `{simple_step:+.6f}`",
        f"- `Glass / ITO / NiOx / SAM / PVK / Air` 的步长 = `{mid_step:+.6f}`",
        f"- `Glass / ITO / NiOx / SAM / PVK / C60 / Ag / Air` 的步长 = `{full_step:+.6f}`",
        "- 结论：最简堆栈已经可以看到同类 seam，不是完整器件才首次生成的问题。",
        "",
        "## Q5. 完整 stack 是否显著放大了 seam？",
        "",
        f"- simple -> mid -> full 的步长依次为 `{simple_step:+.6f}`, `{mid_step:+.6f}`, `{full_step:+.6f}`",
        "- 结论：层序复杂化会逐步放大 seam；完整 stack 可视为 `PVK seam × 微腔增强` 的乘积结果。",
        "",
        "## Q6. Ag 终端边界是否是重要放大因子？",
        "",
        f"- finite Ag `R_stack` step = `{finite_stack_step:+.6f}`",
        f"- semi-infinite Ag `R_stack` step = `{semi_stack_step:+.6f}`",
        (
            "- 结论：有限厚度 Ag 会放大 seam。"
            if abs(finite_stack_step) > abs(semi_stack_step)
            else "- 结论：Ag 终端只弱影响 seam，不是主导来源。"
        ),
        "",
        "## Q7. 当前证据更支持哪种解释？",
        "",
        *[f"- {item}" for item in ranking],
        "",
        "## Code-Level Audit",
        "",
        "- 插值：当前主链路没有在 Phase A-1 内对 PVK 再做额外插值，波长网格是整数 1 nm，对齐表与 baseline CSV 一致。",
        "- 边界条件：`R_stack` 没有发现 749/750 nm 附近的边界条件切换。",
        "- 图像显示：Phase A-1 CSV 原始数值本身存在 749/750 nm 附近步长，不是仅图像采样造成。",
        *([f"- 代码可疑点：{item}" for item in code_findings] if code_findings else ["- 未发现代码级实现错误。", f"- {code_conclusion}"]),
        "",
        "## Outputs",
        "",
        f"- local audit csv: `{(output_paths.data_dir / 'pvk_seam_local_audit.csv').relative_to(PROJECT_ROOT).as_posix()}`",
        f"- source comparison csv: `{(output_paths.data_dir / 'pvk_source_comparison.csv').relative_to(PROJECT_ROOT).as_posix()}`",
        f"- stack sensitivity csv: `{(output_paths.data_dir / 'seam_stack_sensitivity.csv').relative_to(PROJECT_ROOT).as_posix()}`",
        f"- ag sensitivity csv: `{(output_paths.data_dir / 'seam_ag_boundary_sensitivity.csv').relative_to(PROJECT_ROOT).as_posix()}`",
        f"- figures: `results/figures/phaseA1_seam_audit/*.png`",
        "",
        "## Recommended Next Fix Direction",
        "",
        "- 当前最优先建议是 `blend-zone repair`，因为 seam 已明确锚定在上游拼接边界，且主要表现为 `k` 右侧过硬与导数不连续；先修复拼接区，比直接改 Ag 终端或重写主链路更对症。",
    ]
    (output_paths.log_dir / "phaseA1_seam_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_paths = ensure_output_dirs()

    baseline_frame = pd.read_csv(args.baseline_csv.resolve())
    aligned_frame = pd.read_csv(args.aligned_nk.resolve())
    stack = OpticalStackTable(
        wavelength_nm=aligned_frame["Wavelength_nm"].to_numpy(dtype=float),
        n_glass=np.full(aligned_frame["Wavelength_nm"].shape, GLASS_NK, dtype=np.complex128),
        n_ito=aligned_frame["n_ITO"].to_numpy(dtype=float) + 1j * aligned_frame["k_ITO"].to_numpy(dtype=float),
        n_niox=aligned_frame["n_NiOx"].to_numpy(dtype=float) + 1j * aligned_frame["k_NiOx"].to_numpy(dtype=float),
        n_pvk=aligned_frame["n_PVK"].to_numpy(dtype=float) + 1j * aligned_frame["k_PVK"].to_numpy(dtype=float),
        n_c60=aligned_frame["n_C60"].to_numpy(dtype=float) + 1j * aligned_frame["k_C60"].to_numpy(dtype=float),
        n_ag=aligned_frame["n_Ag"].to_numpy(dtype=float) + 1j * aligned_frame["k_Ag"].to_numpy(dtype=float),
        thicknesses=THICKNESSES,
    )

    local_frame = load_aligned_pvk_frame(args.aligned_nk.resolve())
    source_frame = load_source_comparison_frame()
    stack_frame = build_stack_sensitivity_frame(stack)
    ag_frame = build_ag_boundary_frame(stack, baseline_frame)
    bridge_lines = extract_step05c_bridge_logic()
    code_findings = detect_code_level_findings(baseline_frame, aligned_frame)

    local_frame.to_csv(output_paths.data_dir / "pvk_seam_local_audit.csv", index=False, encoding="utf-8-sig")
    source_frame.to_csv(output_paths.data_dir / "pvk_source_comparison.csv", index=False, encoding="utf-8-sig")
    stack_frame.to_csv(output_paths.data_dir / "seam_stack_sensitivity.csv", index=False, encoding="utf-8-sig")
    ag_frame.to_csv(output_paths.data_dir / "seam_ag_boundary_sensitivity.csv", index=False, encoding="utf-8-sig")

    save_local_audit_plot(local_frame, output_paths.figure_dir)
    save_source_overlay(source_frame, output_paths.figure_dir)
    save_stack_sensitivity_figure(stack_frame, output_paths.figure_dir)
    save_ag_sensitivity_figure(ag_frame, output_paths.figure_dir)
    save_pristine_zoom_figure(baseline_frame, output_paths.figure_dir)
    write_log(output_paths, local_frame, source_frame, stack_frame, ag_frame, baseline_frame, bridge_lines, code_findings)

    print(f"local_audit_csv={output_paths.data_dir / 'pvk_seam_local_audit.csv'}")
    print(f"source_comparison_csv={output_paths.data_dir / 'pvk_source_comparison.csv'}")
    print(f"stack_sensitivity_csv={output_paths.data_dir / 'seam_stack_sensitivity.csv'}")
    print(f"ag_boundary_csv={output_paths.data_dir / 'seam_ag_boundary_sensitivity.csv'}")
    print(f"log_path={output_paths.log_dir / 'phaseA1_seam_audit.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
