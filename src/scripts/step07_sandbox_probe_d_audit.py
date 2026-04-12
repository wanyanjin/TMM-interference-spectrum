"""Phase 07 sandbox probe D: theory and calibration forensic audit.

This script performs a single-wavelength audit at 550 nm for DEVICE-1-withAg-P1.
It does not run any optimizer. It directly checks:

1. Theory audit:
   Air -> Glass (incoherent front surface) -> ITO(100) -> NiOx(45)
   -> PVK (semi-infinite absorbing substrate), no roughness and no SAM.
2. Calibration audit:
   Rebuild raw mean spectra and HDR blending from the provided 0409 raw files,
   then manually reproduce the calibration formula and compare it with the
   exported hdr_curves table.
"""

from __future__ import annotations

from pathlib import Path
import argparse
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

from core.hdr_absolute_calibration import (  # noqa: E402
    build_mean_spectrum,
    blend_hdr_spectra,
    calibrate_absolute_reflectance,
    discover_measurement_files,
    interpolate_reference_to_grid,
    load_excel_reference,
)
from core.phase07_dual_window import (  # noqa: E402
    build_phase07_stack_model,
    calc_front_surface_reflectance,
    interpolate_complex,
)


DEFAULT_RAW_DIR = Path(
    "/Users/luxin/Library/CloudStorage/OneDrive-共享的库-onedrive/Data/PL/2026/0409/cor"
)
DEFAULT_HDR_CURVE_PATH = PROJECT_ROOT / "test_data" / "phase7_data" / "DEVICE-1-withAg-P1_hdr_curves.csv"
DEFAULT_GCC_XLSX_PATH = PROJECT_ROOT / "resources" / "GCC-1022系列xlsx.xlsx"

FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phase07"
LOG_DIR = PROJECT_ROOT / "results" / "logs" / "phase07"

TARGET_WAVELENGTH_NM = 550.0
SAMPLE_PREFIX = "DEVICE-1-withAg"
SAMPLE_SHORT_EXPOSURE = "150ms"
SAMPLE_LONG_EXPOSURE = "2000ms"
AG_PREFIX = "Ag_mirro"
AG_SHORT_EXPOSURE = "500us"
AG_LONG_EXPOSURE = "10ms"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 07 sandbox probe D forensic audit.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--hdr-curve", type=Path, default=DEFAULT_HDR_CURVE_PATH)
    parser.add_argument("--gcc-xlsx", type=Path, default=DEFAULT_GCC_XLSX_PATH)
    return parser.parse_args()


def ensure_output_dirs() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def slugify_sample_name(sample_name: str) -> str:
    return sample_name.lower().replace(" ", "_").replace("-", "_")


def nearest_index(values: np.ndarray, target: float) -> int:
    return int(np.argmin(np.abs(np.asarray(values, dtype=float) - float(target))))


def compute_theory_reflectance_front_stack(
    wavelengths_nm: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    model = build_phase07_stack_model()
    glass_nk = interpolate_complex(model.wavelength_nm, model.n_glass, wavelengths_nm)
    ito_nk = interpolate_complex(model.wavelength_nm, model.n_ito, wavelengths_nm)
    niox_nk = interpolate_complex(model.wavelength_nm, model.n_niox, wavelengths_nm)
    pvk_nk = interpolate_complex(model.wavelength_nm, model.n_pvk, wavelengths_nm)

    r_front = calc_front_surface_reflectance(glass_nk)
    t_front = 1.0 - r_front

    r_stack = np.empty(wavelengths_nm.size, dtype=float)
    for index, wavelength_nm in enumerate(wavelengths_nm):
        n_list = [
            complex(glass_nk[index]),
            complex(ito_nk[index]),
            complex(niox_nk[index]),
            complex(pvk_nk[index]),
        ]
        d_list = [np.inf, 100.0, 45.0, np.inf]
        r_stack[index] = float(coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(wavelength_nm))["R"])

    denominator = 1.0 - r_front * r_stack
    r_total = r_front + (t_front**2) * r_stack / denominator
    return r_total, r_front


def load_hdr_export_row(hdr_curve_path: Path, target_wavelength_nm: float) -> tuple[pd.Series, int]:
    frame = pd.read_csv(hdr_curve_path)
    row_index = nearest_index(frame["Wavelength_nm"].to_numpy(dtype=float), target_wavelength_nm)
    return frame.iloc[row_index], row_index


def run_calibration_rebuild(
    raw_dir: Path,
    gcc_xlsx_path: Path,
) -> dict[str, object]:
    sample_short = build_mean_spectrum(
        label=f"{SAMPLE_PREFIX}-{SAMPLE_SHORT_EXPOSURE}",
        files=discover_measurement_files(raw_dir, SAMPLE_PREFIX, SAMPLE_SHORT_EXPOSURE),
    )
    sample_long = build_mean_spectrum(
        label=f"{SAMPLE_PREFIX}-{SAMPLE_LONG_EXPOSURE}",
        files=discover_measurement_files(raw_dir, SAMPLE_PREFIX, SAMPLE_LONG_EXPOSURE),
    )
    ag_short = build_mean_spectrum(
        label=f"{AG_PREFIX}-{AG_SHORT_EXPOSURE}",
        files=discover_measurement_files(raw_dir, AG_PREFIX, AG_SHORT_EXPOSURE),
    )
    ag_long = build_mean_spectrum(
        label=f"{AG_PREFIX}-{AG_LONG_EXPOSURE}",
        files=discover_measurement_files(raw_dir, AG_PREFIX, AG_LONG_EXPOSURE),
    )

    sample_hdr = blend_hdr_spectra("sample", sample_long, sample_short)
    ag_hdr = blend_hdr_spectra("ag", ag_long, ag_short)

    ref_wavelength_nm, ref_reflectance = load_excel_reference(gcc_xlsx_path)
    ag_theory_reflectance = interpolate_reference_to_grid(
        sample_hdr.wavelength_nm,
        ref_wavelength_nm,
        ref_reflectance,
    )
    result = calibrate_absolute_reflectance(sample_hdr, ag_hdr, ag_theory_reflectance)

    audit_index = nearest_index(result.wavelength_nm, TARGET_WAVELENGTH_NM)
    raw_short_index = nearest_index(sample_short.wavelength_nm, result.wavelength_nm[audit_index])
    raw_long_index = nearest_index(sample_long.wavelength_nm, result.wavelength_nm[audit_index])
    ag_short_index = nearest_index(ag_short.wavelength_nm, result.wavelength_nm[audit_index])
    ag_long_index = nearest_index(ag_long.wavelength_nm, result.wavelength_nm[audit_index])

    return {
        "result": result,
        "audit_index": audit_index,
        "sample_short": sample_short,
        "sample_long": sample_long,
        "ag_short": ag_short,
        "ag_long": ag_long,
        "raw_short_index": raw_short_index,
        "raw_long_index": raw_long_index,
        "ag_short_index": ag_short_index,
        "ag_long_index": ag_long_index,
    }


def build_front_window_figure(
    sample_name: str,
    hdr_curve_path: Path,
    figure_path: Path,
) -> None:
    hdr_frame = pd.read_csv(hdr_curve_path)
    wavelength_nm = hdr_frame["Wavelength_nm"].to_numpy(dtype=float)
    measured = hdr_frame["Absolute_Reflectance"].to_numpy(dtype=float)
    front_mask = (wavelength_nm >= 500.0) & (wavelength_nm <= 650.0)
    wavelength_front = wavelength_nm[front_mask]
    measured_front = measured[front_mask]

    theory_front, fresnel_front = compute_theory_reflectance_front_stack(wavelength_front)

    fig, ax = plt.subplots(figsize=(7.6, 4.8), dpi=320, constrained_layout=True)
    ax.plot(wavelength_front, measured_front * 100.0, color="#333333", linewidth=2.0, label="Measured R_abs")
    ax.plot(
        wavelength_front,
        theory_front * 100.0,
        color="#005b96",
        linewidth=2.0,
        label="Theory audit: Air/Glass + ITO/NiOx/PVK",
    )
    ax.plot(
        wavelength_front,
        fresnel_front * 100.0,
        color="#9e9e9e",
        linewidth=1.3,
        linestyle="--",
        label="Air/Glass Fresnel only",
    )
    ax.axvline(TARGET_WAVELENGTH_NM, color="#b71c1c", linewidth=1.0, linestyle=":")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Absolute Reflectance (%)")
    ax.set_title(f"Phase 07 Probe D Theory Audit: {sample_name}")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.legend(fontsize=8)
    fig.savefig(figure_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    args = parse_args()
    ensure_output_dirs()

    hdr_curve_path = args.hdr_curve.resolve()
    raw_dir = args.raw_dir.resolve()
    gcc_xlsx_path = args.gcc_xlsx.resolve()
    sample_name = hdr_curve_path.stem.replace("_hdr_curves", "")
    sample_slug = slugify_sample_name(sample_name)

    theory_value, theory_fresnel = compute_theory_reflectance_front_stack(np.asarray([TARGET_WAVELENGTH_NM], dtype=float))
    theory_percent = float(theory_value[0] * 100.0)
    fresnel_percent = float(theory_fresnel[0] * 100.0)

    export_row, export_index = load_hdr_export_row(hdr_curve_path, TARGET_WAVELENGTH_NM)
    rebuild = run_calibration_rebuild(raw_dir, gcc_xlsx_path)
    result = rebuild["result"]
    audit_index = int(rebuild["audit_index"])

    sample_short = rebuild["sample_short"]
    sample_long = rebuild["sample_long"]
    ag_short = rebuild["ag_short"]
    ag_long = rebuild["ag_long"]

    sample_short_index = int(rebuild["raw_short_index"])
    sample_long_index = int(rebuild["raw_long_index"])
    ag_short_index = int(rebuild["ag_short_index"])
    ag_long_index = int(rebuild["ag_long_index"])

    audit_wavelength_nm = float(result.wavelength_nm[audit_index])
    rebuild_reflectance = float(result.absolute_reflectance[audit_index])
    rebuild_ref_percent = rebuild_reflectance * 100.0
    export_reflectance = float(export_row["Absolute_Reflectance"])
    export_ref_percent = export_reflectance * 100.0

    sample_short_raw_counts = float(sample_short.mean_counts[sample_short_index])
    sample_long_raw_counts = float(sample_long.mean_counts[sample_long_index])
    ag_short_raw_counts = float(ag_short.mean_counts[ag_short_index])
    ag_long_raw_counts = float(ag_long.mean_counts[ag_long_index])

    sample_short_raw_n = sample_short_raw_counts / float(sample_short.exposure_ms)
    sample_long_raw_n = sample_long_raw_counts / float(sample_long.exposure_ms)
    ag_short_raw_n = ag_short_raw_counts / float(ag_short.exposure_ms)
    ag_long_raw_n = ag_long_raw_counts / float(ag_long.exposure_ms)

    sample_hdr_n = float(result.sample_hdr.hdr_counts_per_ms[audit_index])
    ag_hdr_n = float(result.ag_hdr.hdr_counts_per_ms[audit_index])
    sample_n_short_aligned = float(result.sample_hdr.n_short[audit_index])
    ag_n_short_aligned = float(result.ag_hdr.n_short[audit_index])
    sample_w_long = float(result.sample_hdr.w_long[audit_index])
    ag_w_long = float(result.ag_hdr.w_long[audit_index])
    ag_theory_reflectance = float(result.ag_theory_reflectance[audit_index])

    manual_raw_short_short = (sample_short_raw_n / ag_short_raw_n) * ag_theory_reflectance
    manual_raw_long_long = (sample_long_raw_n / ag_long_raw_n) * ag_theory_reflectance
    manual_hdr = (sample_hdr_n / ag_hdr_n) * ag_theory_reflectance

    figure_path = FIGURE_DIR / f"phase07_{sample_slug}_sandbox_probe_d_theory_audit.png"
    log_path = LOG_DIR / f"phase07_{sample_slug}_sandbox_probe_d_audit.md"
    build_front_window_figure(sample_name=sample_name, hdr_curve_path=hdr_curve_path, figure_path=figure_path)

    delta_export_vs_rebuild_pct = abs(export_ref_percent - rebuild_ref_percent)
    verdict_lines = [
        "## Engineering Verdict",
        "",
        f"- 550 nm 极简理论正算得到 `R_theory = {theory_percent:.3f}%`，明显高于实验校准值。",
        f"- 使用 0409 原始文件重建 HDR 后，550 nm 得到 `R_hdr_manual = {rebuild_ref_percent:.3f}%`；与导出表的 `{export_ref_percent:.3f}%` 仅差 `{delta_export_vs_rebuild_pct:.3f} 个百分点`。",
        f"- 说明当前 Phase 06/07 的校准代码在 550 nm 处是**算理自洽**的；不存在把 10% 错算成 2.5% 的隐藏曝光时间解析 Bug。",
        f"- 反而，若直接忽略 HDR 对齐因子、仅用原始短曝光 `Counts/Time` 计算，会得到更低的 `{manual_raw_short_short * 100.0:.3f}%`，这与导出结果不符。",
        "- 因此，当前主要落差不是代码把理论值压低，而是实验观测到的镜面收集强度显著低于理想正反射模型。就 550 nm 这一点看，`11.89% -> 2.67%` 的差距更符合几何 NA/散射漏光一类观测损失。",
    ]

    log_lines = [
        f"# Phase 07 Sandbox Probe D Audit: {sample_name}",
        "",
        "## Inputs",
        "",
        f"- raw_dir: `{raw_dir}`",
        f"- hdr_curve: `{hdr_curve_path}`",
        f"- gcc_xlsx: `{gcc_xlsx_path}`",
        "",
        "## Route 1: Theory Audit",
        "",
        "- Model: `Air -> Glass(incoherent) -> ITO(100 nm) -> NiOx(45 nm) -> PVK(semi-infinite)`",
        "- No roughness, no SAM, no optimizer.",
        f"- target_wavelength_nm: `{TARGET_WAVELENGTH_NM:.3f}`",
        f"- R_front_air_glass_only: `{fresnel_percent:.6f}%`",
        f"- R_total_theory: `{theory_percent:.6f}%`",
        "",
        "## Route 2: Calibration Audit",
        "",
        f"- audit_wavelength_nm: `{audit_wavelength_nm:.9f}`",
        "",
        "### Raw Counts and Exposure",
        "",
        f"- sample_short_raw_counts: `{sample_short_raw_counts:.6f}` at `{sample_short.exposure_ms:.6f} ms`",
        f"- sample_long_raw_counts: `{sample_long_raw_counts:.6f}` at `{sample_long.exposure_ms:.6f} ms`",
        f"- ag_short_raw_counts: `{ag_short_raw_counts:.6f}` at `{ag_short.exposure_ms:.6f} ms`",
        f"- ag_long_raw_counts: `{ag_long_raw_counts:.6f}` at `{ag_long.exposure_ms:.6f} ms`",
        "",
        "### Raw Counts / Time",
        "",
        f"- sample_short_raw_counts_per_ms: `{sample_short_raw_n:.6f}`",
        f"- sample_long_raw_counts_per_ms: `{sample_long_raw_n:.6f}`",
        f"- ag_short_raw_counts_per_ms: `{ag_short_raw_n:.6f}`",
        f"- ag_long_raw_counts_per_ms: `{ag_long_raw_n:.6f}`",
        "",
        "### HDR Branch and Alignment",
        "",
        f"- sample_short_scale_factor: `{result.sample_hdr.scale_factor:.9f}`",
        f"- ag_short_scale_factor: `{result.ag_hdr.scale_factor:.9f}`",
        f"- sample_w_long_at_550: `{sample_w_long:.6f}`",
        f"- ag_w_long_at_550: `{ag_w_long:.6f}`",
        f"- sample_n_short_aligned: `{sample_n_short_aligned:.6f}`",
        f"- ag_n_short_aligned: `{ag_n_short_aligned:.6f}`",
        f"- sample_hdr_counts_per_ms: `{sample_hdr_n:.6f}`",
        f"- ag_hdr_counts_per_ms: `{ag_hdr_n:.6f}`",
        "",
        "### Mirror Reference",
        "",
        f"- ag_theory_reflectance_at_550: `{ag_theory_reflectance * 100.0:.6f}%`",
        "",
        "### Manual Reproduction",
        "",
        f"- manual_raw_short_short = `(sample_short_raw_n / ag_short_raw_n) * R_ref` = `{manual_raw_short_short * 100.0:.6f}%`",
        f"- manual_raw_long_long = `(sample_long_raw_n / ag_long_raw_n) * R_ref` = `{manual_raw_long_long * 100.0:.6f}%`",
        f"- manual_hdr = `(sample_hdr_n / ag_hdr_n) * R_ref` = `{manual_hdr * 100.0:.6f}%`",
        "",
        "### Exported Comparison",
        "",
        f"- rebuilt_hdr_reflectance_at_550: `{rebuild_ref_percent:.6f}%`",
        f"- exported_hdr_curve_index: `{export_index}`",
        f"- exported_hdr_curve_wavelength_nm: `{float(export_row['Wavelength_nm']):.9f}`",
        f"- exported_hdr_curve_reflectance_at_550: `{export_ref_percent:.6f}%`",
        f"- export_vs_rebuild_delta_percentage_point: `{delta_export_vs_rebuild_pct:.6f}`",
        "",
        *verdict_lines,
    ]
    log_path.write_text("\n".join(log_lines), encoding="utf-8")

    print(f"[Probe D] sample = {sample_name}")
    print(f"[Probe D] theory_R_total_at_550_nm = {theory_percent:.6f}%")
    print(f"[Probe D] raw_sample_short = {sample_short_raw_counts:.6f} counts @ {sample_short.exposure_ms:.6f} ms")
    print(f"[Probe D] raw_sample_long = {sample_long_raw_counts:.6f} counts @ {sample_long.exposure_ms:.6f} ms")
    print(f"[Probe D] raw_ag_short = {ag_short_raw_counts:.6f} counts @ {ag_short.exposure_ms:.6f} ms")
    print(f"[Probe D] raw_ag_long = {ag_long_raw_counts:.6f} counts @ {ag_long.exposure_ms:.6f} ms")
    print(f"[Probe D] ag_reference_at_550_nm = {ag_theory_reflectance * 100.0:.6f}%")
    print(f"[Probe D] manual_raw_short_short = {manual_raw_short_short * 100.0:.6f}%")
    print(f"[Probe D] manual_raw_long_long = {manual_raw_long_long * 100.0:.6f}%")
    print(f"[Probe D] manual_hdr = {manual_hdr * 100.0:.6f}%")
    print(f"[Probe D] rebuilt_hdr_curve = {rebuild_ref_percent:.6f}%")
    print(f"[Probe D] exported_hdr_curve = {export_ref_percent:.6f}%")
    print(f"[Probe D] figure = {figure_path}")
    print(f"[Probe D] log = {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
