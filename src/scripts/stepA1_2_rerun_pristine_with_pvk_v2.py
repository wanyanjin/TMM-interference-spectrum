"""Phase A-1.2 pristine baseline rerun with PVK surrogate v2."""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

import matplotlib
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (str(PROJECT_ROOT / "src"), str(SCRIPT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import stepA1_pristine_baseline as phase_a1  # noqa: E402


PHASE_NAME = "Phase A-1.2"
ALIGNED_V1_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk.csv"
ALIGNED_V2_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_pvk_v2.csv"
BASELINE_V1_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA1" / "phaseA1_pristine_baseline.csv"
SURROGATE_BUILD_LOG_PATH = PROJECT_ROOT / "results" / "logs" / "phaseA1_2" / "phaseA1_2_pvk_surrogate_build.md"
LOCAL_COMPARISON_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA1_2" / "pvk_v1_v2_local_comparison.csv"
CANDIDATE_METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "phaseA1_2" / "pvk_v2_candidate_metrics.csv"

ZOOM_WINDOW = (720.0, 780.0)
FRINGE_WINDOW = (810.0, 1100.0)
SEAM_LEFT_NM = 749.0
SEAM_RIGHT_NM = 750.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rerun pristine baseline with PVK surrogate v2.")
    parser.add_argument("--nk-csv-v2", type=Path, default=ALIGNED_V2_PATH)
    return parser.parse_args()


def ensure_output_dirs() -> tuple[Path, Path, Path]:
    processed_dir = PROJECT_ROOT / "data" / "processed" / "phaseA1_2"
    figure_dir = PROJECT_ROOT / "results" / "figures" / "phaseA1_2"
    log_dir = PROJECT_ROOT / "results" / "logs" / "phaseA1_2"
    processed_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir, figure_dir, log_dir


def seam_step(values: np.ndarray, wavelength_nm: np.ndarray) -> float:
    idx_749 = int(np.argmin(np.abs(wavelength_nm - SEAM_LEFT_NM)))
    idx_750 = int(np.argmin(np.abs(wavelength_nm - SEAM_RIGHT_NM)))
    return float(values[idx_750] - values[idx_749])


def compute_derivative(values: np.ndarray, wavelength_nm: np.ndarray) -> np.ndarray:
    return np.gradient(np.asarray(values, dtype=float), np.asarray(wavelength_nm, dtype=float))


def compute_second_difference(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return np.gradient(np.gradient(array))


def load_baseline_from_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    return frame


def run_baseline_with_v2(nk_csv_path: Path) -> pd.DataFrame:
    stack, _, _ = phase_a1.load_optical_stack_from_aligned_csv(nk_csv_path)
    decomposition = stack.compute_pristine_baseline_decomposition(
        wavelengths_nm=phase_a1.EXPECTED_WAVELENGTHS_NM,
        use_constant_glass=True,
        constant_glass_nk=phase_a1.DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode=phase_a1.AG_BOUNDARY_FINITE_FILM,
    )
    frame = pd.DataFrame(decomposition)
    frame["zone_label"] = phase_a1.build_zone_labels(frame["Wavelength_nm"].to_numpy(dtype=float))
    frame = frame[["Wavelength_nm", "zone_label", "R_front", "T_front", "R_stack", "R_total"]]
    phase_a1.validate_outputs(frame)
    return frame


def save_phase_a1_2_outputs(frame: pd.DataFrame, processed_dir: Path, figure_dir: Path) -> Path:
    csv_path = processed_dir / "phaseA1_2_pristine_baseline.csv"
    frame.to_csv(csv_path, index=False, encoding="utf-8-sig")
    phase_a1.plot_pristine_decomposition(frame, figure_dir / "phaseA1_2_pristine_decomposition.png")
    phase_a1.plot_pristine_three_zones(frame, figure_dir / "phaseA1_2_pristine_3zones.png")
    return csv_path


def save_comparison_figures(v1: pd.DataFrame, v2: pd.DataFrame, figure_dir: Path) -> None:
    wl = v1["Wavelength_nm"].to_numpy(dtype=float)
    zoom_mask = (wl >= ZOOM_WINDOW[0]) & (wl <= ZOOM_WINDOW[1])

    fig, ax = plt.subplots(figsize=(10.8, 5.4), dpi=320)
    ax.plot(wl[zoom_mask], v1.loc[zoom_mask, "R_stack"].to_numpy(dtype=float) * 100.0, color="#616161", linewidth=1.8, label="R_stack_v1")
    ax.plot(wl[zoom_mask], v2.loc[zoom_mask, "R_stack"].to_numpy(dtype=float) * 100.0, color="#005b96", linewidth=1.8, label="R_stack_v2")
    ax.plot(wl[zoom_mask], v1.loc[zoom_mask, "R_total"].to_numpy(dtype=float) * 100.0, color="#8d6e63", linewidth=1.8, linestyle="--", label="R_total_v1")
    ax.plot(wl[zoom_mask], v2.loc[zoom_mask, "R_total"].to_numpy(dtype=float) * 100.0, color="#b03a2e", linewidth=1.8, linestyle="--", label="R_total_v2")
    ax.axvline(SEAM_LEFT_NM, color="#8e244d", linestyle="--", linewidth=1.0)
    ax.axvline(SEAM_RIGHT_NM, color="#d84315", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Reflectance (%)")
    ax.set_title("Phase A-1.2 v1 vs v2 Baseline Zoom (720-780 nm)")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(figure_dir / "phaseA1_2_pristine_720_780_zoom.png", dpi=320, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(11.2, 8.8), dpi=320, constrained_layout=True, sharex=True)
    axes[0].plot(wl, v1["R_stack"].to_numpy(dtype=float) * 100.0, color="#616161", linewidth=1.8, label="R_stack_v1")
    axes[0].plot(wl, v2["R_stack"].to_numpy(dtype=float) * 100.0, color="#005b96", linewidth=1.8, label="R_stack_v2")
    axes[0].set_ylabel("R_stack (%)")
    axes[0].set_title("Full-Spectrum Comparison: R_stack")
    axes[0].grid(True, linestyle="--", alpha=0.25)
    axes[0].legend(loc="best")

    axes[1].plot(wl, v1["R_total"].to_numpy(dtype=float) * 100.0, color="#8d6e63", linewidth=1.8, label="R_total_v1")
    axes[1].plot(wl, v2["R_total"].to_numpy(dtype=float) * 100.0, color="#b03a2e", linewidth=1.8, label="R_total_v2")
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_ylabel("R_total (%)")
    axes[1].set_title("Full-Spectrum Comparison: R_total")
    axes[1].grid(True, linestyle="--", alpha=0.25)
    axes[1].legend(loc="best")
    fig.savefig(figure_dir / "phaseA1_2_pristine_v1_vs_v2_full_spectrum.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def compare_peak_positions(v1: np.ndarray, v2: np.ndarray, wavelength_nm: np.ndarray) -> float:
    v1 = np.asarray(v1, dtype=float)
    v2 = np.asarray(v2, dtype=float)
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    prominence = max((float(np.max(v1)) - float(np.min(v1))) * 0.08, 1e-6)
    shifts: list[float] = []
    for signal_a, signal_b in ((v1, v2), (-v1, -v2)):
        peaks_a, props_a = find_peaks(signal_a, prominence=prominence)
        peaks_b, _ = find_peaks(signal_b, prominence=prominence)
        if peaks_a.size == 0 or peaks_b.size == 0:
            continue
        order = np.argsort(props_a["prominences"])[::-1]
        for idx in peaks_a[order[: min(3, len(order))]]:
            shifts.append(float(np.min(np.abs(wavelength_nm[peaks_b] - wavelength_nm[idx]))))
    if not shifts:
        return float("nan")
    return float(np.mean(shifts))


def write_log(
    v1: pd.DataFrame,
    v2: pd.DataFrame,
    figure_dir: Path,
    processed_dir: Path,
    log_dir: Path,
) -> None:
    wl = v1["Wavelength_nm"].to_numpy(dtype=float)
    local = pd.read_csv(LOCAL_COMPARISON_PATH)
    candidate_metrics = pd.read_csv(CANDIDATE_METRICS_PATH)
    best = candidate_metrics.sort_values(["score", "end_nm"]).iloc[0]

    delta_r_stack_v1 = seam_step(v1["R_stack"].to_numpy(dtype=float), wl)
    delta_r_stack_v2 = seam_step(v2["R_stack"].to_numpy(dtype=float), wl)
    delta_r_total_v1 = seam_step(v1["R_total"].to_numpy(dtype=float), wl)
    delta_r_total_v2 = seam_step(v2["R_total"].to_numpy(dtype=float), wl)
    delta_n_v1 = seam_step(local["n_v1"].to_numpy(dtype=float), local["Wavelength_nm"].to_numpy(dtype=float))
    delta_n_v2 = seam_step(local["n_v2"].to_numpy(dtype=float), local["Wavelength_nm"].to_numpy(dtype=float))
    delta_k_v1 = seam_step(local["k_v1"].to_numpy(dtype=float), local["Wavelength_nm"].to_numpy(dtype=float))
    delta_k_v2 = seam_step(local["k_v2"].to_numpy(dtype=float), local["Wavelength_nm"].to_numpy(dtype=float))
    delta_eps2_v1 = seam_step(local["eps2_v1"].to_numpy(dtype=float), local["Wavelength_nm"].to_numpy(dtype=float))
    delta_eps2_v2 = seam_step(local["eps2_v2"].to_numpy(dtype=float), local["Wavelength_nm"].to_numpy(dtype=float))

    seam_mask = (local["Wavelength_nm"] >= 740.0) & (local["Wavelength_nm"] <= 780.0)
    fringe_mask = (wl >= FRINGE_WINDOW[0]) & (wl <= FRINGE_WINDOW[1])
    fringe_v1 = v1.loc[fringe_mask, "R_total"].to_numpy(dtype=float)
    fringe_v2 = v2.loc[fringe_mask, "R_total"].to_numpy(dtype=float)
    wl_fringe = wl[fringe_mask]
    fringe_rmse = float(np.sqrt(np.mean((fringe_v2 - fringe_v1) ** 2)))
    fringe_corr = float(np.corrcoef(fringe_v1, fringe_v2)[0, 1])
    fringe_peak_shift = compare_peak_positions(fringe_v1, fringe_v2, wl_fringe)

    max_dn_v1 = float(np.max(np.abs(local.loc[seam_mask, "dn_v1_dlambda"].to_numpy(dtype=float))))
    max_dn_v2 = float(np.max(np.abs(local.loc[seam_mask, "dn_v2_dlambda"].to_numpy(dtype=float))))
    max_dk_v1 = float(np.max(np.abs(local.loc[seam_mask, "dk_v1_dlambda"].to_numpy(dtype=float))))
    max_dk_v2 = float(np.max(np.abs(local.loc[seam_mask, "dk_v2_dlambda"].to_numpy(dtype=float))))
    max_d2n_v1 = float(np.max(np.abs(compute_second_difference(local.loc[seam_mask, "n_v1"].to_numpy(dtype=float)))))
    max_d2n_v2 = float(np.max(np.abs(compute_second_difference(local.loc[seam_mask, "n_v2"].to_numpy(dtype=float)))))
    max_d2k_v1 = float(np.max(np.abs(compute_second_difference(local.loc[seam_mask, "k_v1"].to_numpy(dtype=float)))))
    max_d2k_v2 = float(np.max(np.abs(compute_second_difference(local.loc[seam_mask, "k_v2"].to_numpy(dtype=float)))))

    seam_repaired = abs(delta_r_total_v2) < 0.35 * abs(delta_r_total_v1)
    band_edge_continuous = abs(delta_k_v2) < 0.35 * abs(delta_k_v1) and abs(delta_eps2_v2) < 0.35 * abs(delta_eps2_v1)
    fringe_preserved = fringe_corr > 0.995 and fringe_rmse < 0.01

    lines = [
        f"# {PHASE_NAME} PVK Surrogate Rebuild + Pristine Rerun",
        "",
        "## Inputs",
        "",
        f"- aligned v1: `{ALIGNED_V1_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- aligned v2: `{ALIGNED_V2_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- baseline v1: `{BASELINE_V1_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- local PVK comparison: `{LOCAL_COMPARISON_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- candidate metrics: `{CANDIDATE_METRICS_PATH.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Surrogate Build Choice",
        "",
        f"- selected transition zone: `{best['start_nm']:.0f}-{best['end_nm']:.0f} nm`",
        "- blend / bridge method: `smoothstep blend in transition zone + cosine-tail k decay + relaxed n target toward extended trend`",
        "- right-side hard zero at 750 nm: `removed`",
        "",
        "## Seam Metrics",
        "",
        f"- `Δn(749->750)`: v1 `{delta_n_v1:+.6f}`, v2 `{delta_n_v2:+.6f}`",
        f"- `Δk(749->750)`: v1 `{delta_k_v1:+.6f}`, v2 `{delta_k_v2:+.6f}`",
        f"- `Δeps2(749->750)`: v1 `{delta_eps2_v1:+.6f}`, v2 `{delta_eps2_v2:+.6f}`",
        f"- `ΔR_stack(749->750)`: v1 `{delta_r_stack_v1:+.6f}`, v2 `{delta_r_stack_v2:+.6f}`",
        f"- `ΔR_total(749->750)`: v1 `{delta_r_total_v1:+.6f}`, v2 `{delta_r_total_v2:+.6f}`",
        "",
        "## Local Smoothness Metrics (740-780 nm)",
        "",
        f"- `max(|dn/dlambda|)`: v1 `{max_dn_v1:.6f}`, v2 `{max_dn_v2:.6f}`",
        f"- `max(|dk/dlambda|)`: v1 `{max_dk_v1:.6f}`, v2 `{max_dk_v2:.6f}`",
        f"- `max(|Δ²n|)`: v1 `{max_d2n_v1:.6f}`, v2 `{max_d2n_v2:.6f}`",
        f"- `max(|Δ²k|)`: v1 `{max_d2k_v1:.6f}`, v2 `{max_d2k_v2:.6f}`",
        "",
        "## Fringe Preservation (810-1100 nm)",
        "",
        f"- `R_total fringe RMSE`: `{fringe_rmse:.6f}`",
        f"- `R_total fringe correlation`: `{fringe_corr:.6f}`",
        f"- mean peak/valley shift: `{fringe_peak_shift:.3f} nm`",
        "",
        "## Judgement",
        "",
        f"- seam removed enough: `{seam_repaired}`",
        f"- band-edge jump downgraded to continuous transition: `{band_edge_continuous}`",
        f"- rear-window fringe preserved: `{fringe_preserved}`",
        (
            "- 750 nm 附近的原始台阶已从明显跳变压低为连续但较陡的 band-edge 过渡。"
            if seam_repaired and band_edge_continuous
            else "- 750 nm 附近的台阶虽有改善，但仍未完全降级为连续过渡。"
        ),
        (
            "- 修复主要局限在 740-800 nm，810-1100 nm 后窗微腔结构基本保留。"
            if fringe_preserved
            else "- 修复对后窗 fringe 造成了可见扰动，仍需谨慎。"
        ),
        "",
        "## Outputs",
        "",
        f"- baseline csv: `{(processed_dir / 'phaseA1_2_pristine_baseline.csv').relative_to(PROJECT_ROOT).as_posix()}`",
        f"- decomposition figure: `{(figure_dir / 'phaseA1_2_pristine_decomposition.png').relative_to(PROJECT_ROOT).as_posix()}`",
        f"- 3-zone figure: `{(figure_dir / 'phaseA1_2_pristine_3zones.png').relative_to(PROJECT_ROOT).as_posix()}`",
        f"- zoom figure: `{(figure_dir / 'phaseA1_2_pristine_720_780_zoom.png').relative_to(PROJECT_ROOT).as_posix()}`",
        f"- full-spectrum comparison: `{(figure_dir / 'phaseA1_2_pristine_v1_vs_v2_full_spectrum.png').relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Next Direction",
        "",
        "- 建议下一步优先进入 `d_PVK thickness scan`。当前 zero-defect baseline 已去掉最显著 seam artifact，且后窗 fringe 仍保持，可直接用于评估 `d_PVK` 对条纹相位与周期的灵敏度。",
        "- `PVK uncertainty ensemble` 适合作为紧随其后的第二步，用于量化 band-edge surrogate 不确定性对 baseline 的传播。",
    ]
    (log_dir / "phaseA1_2_pvk_surrogate_rebuild.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    processed_dir, figure_dir, log_dir = ensure_output_dirs()
    baseline_v1 = load_baseline_from_csv(BASELINE_V1_PATH)
    baseline_v2 = run_baseline_with_v2(args.nk_csv_v2.resolve())
    save_phase_a1_2_outputs(baseline_v2, processed_dir, figure_dir)
    save_comparison_figures(baseline_v1, baseline_v2, figure_dir)
    write_log(baseline_v1, baseline_v2, figure_dir, processed_dir, log_dir)

    print(f"baseline_v2_csv={processed_dir / 'phaseA1_2_pristine_baseline.csv'}")
    print(f"log_path={log_dir / 'phaseA1_2_pvk_surrogate_rebuild.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
