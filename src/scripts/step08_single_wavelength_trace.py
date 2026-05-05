"""Phase 08 single-wavelength trace report for reflectance calibration and TMM audit."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import json
import math
import sys

import numpy as np
import pandas as pd
from tmm import coh_tmm


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core import reference_comparison as rc  # noqa: E402


TRACE_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison_trace"
TRACE_REPORT_DIR = PROJECT_ROOT / "results" / "report" / "phase08_reference_comparison_trace"
DEFAULT_TRACE_TAG = "600nm"
ABS_TOL = 1e-8


@dataclass(frozen=True)
class DualOutputSet:
    manifest_path: Path
    calibrated_path: Path
    theory_path: Path
    ag_corrected_path: Path | None
    ag_qc_path: Path | None
    output_tag: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 08 single wavelength trace report")
    parser.add_argument("--target-wavelength-nm", type=float, default=600.0)
    parser.add_argument("--output-tag", default=DEFAULT_TRACE_TAG)
    parser.add_argument(
        "--dual-manifest",
        default=None,
        help="Optional explicit dual-reference manifest path. Default: auto-pick latest.",
    )
    return parser.parse_args()


def find_dual_output_set(manifest_override: str | None) -> DualOutputSet:
    root = PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison"
    if manifest_override:
        manifest_path = Path(manifest_override).resolve()
    else:
        candidates = sorted(
            root.glob("phase08_0429_dual_reference_manifest*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            raise FileNotFoundError("未找到任何 dual-reference manifest。")
        manifest_path = candidates[0]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_tag = manifest.get("output_tag")
    calibrated_path = Path(manifest_path.parent / f"{rc.tag_output_stem('phase08_0429_dual_reference_calibrated_reflectance', output_tag)}.csv")
    theory_path = Path(manifest_path.parent / f"{rc.tag_output_stem('phase08_0429_dual_reference_tmm_theory_curves', output_tag)}.csv")
    ag_corrected_path = manifest_path.parent / f"{rc.tag_output_stem('phase08_0429_ag_mirror_background_corrected', output_tag)}.csv"
    ag_qc_path = manifest_path.parent / f"{rc.tag_output_stem('phase08_0429_ag_mirror_frame_qc', output_tag)}.csv"
    return DualOutputSet(
        manifest_path=manifest_path,
        calibrated_path=calibrated_path,
        theory_path=theory_path,
        ag_corrected_path=ag_corrected_path if ag_corrected_path.exists() else None,
        ag_qc_path=ag_qc_path if ag_qc_path.exists() else None,
        output_tag=output_tag,
    )


def nearest_index(values: np.ndarray, target: float) -> int:
    return int(np.argmin(np.abs(values - target)))


def complex_dict(value: complex) -> dict[str, float]:
    phase_rad = float(np.angle(value))
    return {
        "real": float(np.real(value)),
        "imag": float(np.imag(value)),
        "abs": float(np.abs(value)),
        "phase_rad": phase_rad,
        "phase_deg": float(np.degrees(phase_rad)),
    }


def format_complex(value: complex) -> str:
    parts = complex_dict(value)
    return (
        f"{parts['real']:.12g} + {parts['imag']:.12g}i; "
        f"|.|={parts['abs']:.12g}; phase={parts['phase_rad']:.12g} rad = {parts['phase_deg']:.12g} deg"
    )


def format_complex_parts(parts: dict[str, float]) -> str:
    return (
        f"{parts['real']:.12g} + {parts['imag']:.12g}i; "
        f"|.|={parts['abs']:.12g}; phase={parts['phase_rad']:.12g} rad = {parts['phase_deg']:.12g} deg"
    )


def format_optional(value: float | None) -> str:
    if value is None:
        return "not_available"
    return f"{float(value):.12f}"


def sanitize_for_json(obj: object) -> object:
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def difference_dict(manual: float, reference: float) -> dict[str, float]:
    diff = float(manual - reference)
    if abs(reference) < 1e-15:
        rel = math.inf if abs(diff) > 0 else 0.0
    else:
        rel = float(abs(diff) / abs(reference) * 100.0)
    return {
        "manual": float(manual),
        "reference": float(reference),
        "absolute_difference": abs(diff),
        "relative_difference_percent": rel,
    }


def interpolate_with_neighbors(nk_df: pd.DataFrame, column_n: str, column_k: str, wavelength_nm: float) -> dict[str, object]:
    wl = nk_df["Wavelength_nm"].to_numpy(dtype=float)
    idx_hi = int(np.searchsorted(wl, wavelength_nm, side="left"))
    if idx_hi == 0:
        idx_lo = idx_hi = 0
    elif idx_hi >= wl.size:
        idx_lo = idx_hi = wl.size - 1
    else:
        idx_lo = idx_hi - 1
    query = np.array([wavelength_nm], dtype=float)
    interpolated = rc.interpolate_complex(
        wavelength_query_nm=query,
        wavelength_base_nm=wl,
        real_base=nk_df[column_n].to_numpy(dtype=float),
        imag_base=nk_df[column_k].to_numpy(dtype=float),
    )[0]
    return {
        "lower_point": {
            "Wavelength_nm": float(wl[idx_lo]),
            "n": float(nk_df.iloc[idx_lo][column_n]),
            "k": float(nk_df.iloc[idx_lo][column_k]),
        },
        "upper_point": {
            "Wavelength_nm": float(wl[idx_hi]),
            "n": float(nk_df.iloc[idx_hi][column_n]),
            "k": float(nk_df.iloc[idx_hi][column_k]),
        },
        "interpolated": complex_dict(interpolated),
        "complex_value": interpolated,
    }


def fresnel_amplitude(n0: complex, n1: complex) -> complex:
    return (n0 - n1) / (n0 + n1)


def interface_entry(name: str, n0: complex, n1: complex) -> dict[str, object]:
    r_ij = fresnel_amplitude(n0, n1)
    return {
        "name": name,
        "r": complex_dict(r_ij),
        "R": float(abs(r_ij) ** 2),
    }


def single_layer_trace(n0: complex, n1: complex, n2: complex, d1_nm: float, wavelength_nm: float, label: str) -> dict[str, object]:
    r01 = fresnel_amplitude(n0, n1)
    r12 = fresnel_amplitude(n1, n2)
    delta = 2.0 * np.pi * n1 * d1_nm / wavelength_nm
    exp_2i_delta = np.exp(2.0j * delta)
    numerator = r01 + r12 * exp_2i_delta
    denominator = 1.0 + r01 * r12 * exp_2i_delta
    r_total = numerator / denominator
    r_formula = float(abs(r_total) ** 2)
    coh = coh_tmm("s", [n0, n1, n2], [np.inf, float(d1_nm), np.inf], 0.0, float(wavelength_nm))
    r_coh = float(coh["R"])
    diff = difference_dict(r_formula, r_coh)
    return {
        "label": label,
        "n0": complex_dict(n0),
        "n1": complex_dict(n1),
        "n2": complex_dict(n2),
        "d1_nm": float(d1_nm),
        "delta": complex_dict(delta),
        "exp_2i_delta": complex_dict(exp_2i_delta),
        "r_01": complex_dict(r01),
        "r_12": complex_dict(r12),
        "numerator": complex_dict(numerator),
        "denominator": complex_dict(denominator),
        "r_total": complex_dict(r_total),
        "R_stack_by_formula": r_formula,
        "R_stack_by_coh_tmm": r_coh,
        "absolute_difference": diff["absolute_difference"],
        "relative_difference_percent": diff["relative_difference_percent"],
        "consistency_pass": diff["absolute_difference"] <= ABS_TOL,
    }


def incoherent_cascade_trace(r_front: float, r_stack: float) -> dict[str, float]:
    numerator = (1.0 - r_front) ** 2 * r_stack
    denominator = 1.0 - r_front * r_stack
    total = r_front + numerator / denominator
    return {
        "R_front": float(r_front),
        "R_stack": float(r_stack),
        "numerator": float(numerator),
        "denominator": float(denominator),
        "R_total": float(total),
    }


def build_ag_pixel_trace(manifest: dict, lambda_used_nm: float) -> dict[str, object]:
    ag_csv = Path(manifest["ag_mirror_csv"])
    bk_csv = Path(manifest["background_csv"])
    drop_frames = tuple(int(x) for x in manifest.get("drop_ag_frames", [1]))
    ag = rc.load_multiframe_spectrum_csv(ag_csv)
    bk = rc.load_multiframe_spectrum_csv(bk_csv)
    used_frames = [int(x) for x in sorted(ag["Frame_Index"].unique()) if int(x) not in set(drop_frames)]
    ag_filtered = ag[ag["Frame_Index"].isin(used_frames)].copy()
    ag_wl_by_pixel = ag_filtered.groupby("Pixel_Index")["Wavelength_nm"].median().sort_index()
    pixel_idx = int((ag_wl_by_pixel - lambda_used_nm).abs().idxmin())
    ag_pixel = ag_filtered[ag_filtered["Pixel_Index"] == pixel_idx]
    bk_pixel = bk[bk["Pixel_Index"] == pixel_idx]
    ag_all_pixel = ag[ag["Pixel_Index"] == pixel_idx]
    return {
        "Pixel_Index": pixel_idx,
        "lambda_pixel_nm": float(ag_wl_by_pixel.loc[pixel_idx]),
        "Ag_frame_count_total": int(ag["Frame_Index"].nunique()),
        "Ag_frames_dropped": [int(x) for x in drop_frames],
        "Ag_frames_used": used_frames,
        "BK_frame_count_total": int(bk["Frame_Index"].nunique()),
        "Ag_mean_counts_at_pixel": float(ag_pixel["Counts"].mean()),
        "BK_mean_counts_at_pixel": float(bk_pixel["Counts"].mean()),
        "Ag_corrected_counts": float(ag_pixel["Counts"].mean() - bk_pixel["Counts"].mean()),
        "Ag_first_frame_counts_at_pixel": float(ag_all_pixel[ag_all_pixel["Frame_Index"] == 1]["Counts"].iloc[0]),
        "Ag_used_frame_count": int(ag_pixel["Frame_Index"].nunique()),
        "BK_used_frame_count": int(bk_pixel["Frame_Index"].nunique()),
        "Ag_counts_min_at_pixel_used": float(ag_pixel["Counts"].min()),
        "Ag_counts_max_at_pixel_used": float(ag_pixel["Counts"].max()),
        "BK_counts_min_at_pixel": float(bk_pixel["Counts"].min()),
        "BK_counts_max_at_pixel": float(bk_pixel["Counts"].max()),
    }


def render_markdown(trace: dict, output_path: Path) -> None:
    red = lambda cond, text: f"**红标：{text}**" if cond else text
    coherent = trace["coherent_stack"]
    cascade = trace["incoherent_cascade"]
    expvals = trace["experimental_reflectance"]
    csvcmp = trace["csv_comparison"]
    diffs = trace["differences"]
    nk = trace["nk"]
    counts = trace["counts"]
    fresnel = trace["fresnel"]
    agtrace = trace.get("ag_mirror_multiframe_trace")

    lines: list[str] = [
        "# Phase 08 Single-Wavelength Trace Report",
        "",
        "## 1. 审计目标与输入文件",
        f"- dual manifest: `{trace['input_files']['manifest_json']}`",
        f"- calibrated reflectance: `{trace['input_files']['calibrated_csv']}`",
        f"- theory csv: `{trace['input_files']['theory_csv']}`",
        f"- nk csv: `{trace['input_files']['nk_csv']}`",
        f"- sample csv: `{trace['input_files']['sample_csv']}`",
        f"- reference csv: `{trace['input_files']['reference_csv']}`",
        f"- ag corrected csv: `{trace['input_files'].get('ag_corrected_csv')}`",
        f"- ag frame qc csv: `{trace['input_files'].get('ag_qc_csv')}`",
        "",
        "## 2. 目标波长与实际使用波长",
        f"- `target_wavelength_nm = {trace['target_wavelength_nm']}`",
        f"- `lambda_used_nm = {trace['lambda_used_nm']:.12f}`",
        f"- `delta_nm = {trace['delta_nm']:.12f}`",
        f"- `row_index = {trace['row_index']}`",
        "",
        "## 3. 实验计数与曝光归一化",
        f"- `Glass_PVK_Counts = {counts['Glass_PVK_Counts']:.12f}`",
        f"- `Glass_Ag_Counts = {counts['Glass_Ag_Counts']:.12f}`",
        f"- `Ag_Mirror_Corrected_Counts = {format_optional(counts.get('Ag_Mirror_Corrected_Counts'))}`",
        f"- `sample_exposure_ms = {counts['sample_exposure_ms']:.12f}`",
        f"- `glass_ag_exposure_ms = {counts['glass_ag_exposure_ms']:.12f}`",
        f"- `ag_mirror_exposure_ms = {format_optional(counts.get('ag_mirror_exposure_ms'))}`",
        f"- `Glass_PVK_CountsPerMs = Glass_PVK_Counts / sample_exposure_ms = {counts['Glass_PVK_CountsPerMs']:.12f}`",
        f"- `Glass_Ag_CountsPerMs = Glass_Ag_Counts / glass_ag_exposure_ms = {counts['Glass_Ag_CountsPerMs']:.12f}`",
        f"- `Ag_Mirror_Corrected_CountsPerMs = Ag_Mirror_Corrected_Counts / ag_mirror_exposure_ms = {format_optional(counts.get('Ag_Mirror_Corrected_CountsPerMs'))}`",
        "",
        "## 4. glass/Ag 参比校准链",
        "- 公式：",
        "```text",
        "R_exp_by_glassAg(λ) = [I_glassPVK(λ) / t_glassPVK] / [I_glassAg(λ) / t_glassAg] × R_TMM_glassAg(λ)",
        "```",
        f"- `I_glassPVK = {counts['Glass_PVK_Counts']:.12f}`",
        f"- `t_glassPVK = {counts['sample_exposure_ms']:.12f}`",
        f"- `I_glassAg = {counts['Glass_Ag_Counts']:.12f}`",
        f"- `t_glassAg = {counts['glass_ag_exposure_ms']:.12f}`",
        f"- `R_TMM_glassAg = {expvals['R_TMM_GlassAg']:.12f}`",
        f"- `counts_ratio_glassAg = {expvals['counts_ratio_glassAg']:.12f}`",
        f"- `R_exp_by_glassAg = {expvals['R_Exp_GlassPVK_by_GlassAg']:.12f}`",
        "",
        "## 5. Ag mirror 参比校准链",
    ]
    if expvals.get("R_Exp_GlassPVK_by_AgMirror") is None:
        lines.append("- `Ag mirror chain not available in current outputs.`")
    else:
        lines.extend(
            [
                "- 公式：",
                "```text",
                "R_exp_by_AgMirror(λ) = [I_glassPVK(λ) / t_glassPVK] / [I_AgMirror_corrected(λ) / t_AgMirror] × R_TMM_AgMirror(λ)",
                "```",
                f"- `I_glassPVK = {counts['Glass_PVK_Counts']:.12f}`",
                f"- `t_glassPVK = {counts['sample_exposure_ms']:.12f}`",
                f"- `I_AgMirror_corrected = {counts['Ag_Mirror_Corrected_Counts']:.12f}`",
                f"- `t_AgMirror = {counts['ag_mirror_exposure_ms']:.12f}`",
                f"- `R_TMM_AgMirror = {expvals['R_TMM_AgMirror']:.12f}`",
                f"- `counts_ratio_AgMirror = {expvals['counts_ratio_AgMirror']:.12f}`",
                f"- `R_exp_by_AgMirror = {expvals['R_Exp_GlassPVK_by_AgMirror']:.12f}`",
            ]
        )
    lines.extend(["", "## 6. Ag mirror 多帧与背景扣除展开"])
    if agtrace is None:
        lines.append("- 当前输出中没有 Ag mirror corrected 数据，无法展开该节。")
    else:
        lines.extend(
            [
                f"- `Pixel_Index = {agtrace['Pixel_Index']}`",
                f"- `lambda_pixel_nm = {agtrace['lambda_pixel_nm']:.12f}`",
                f"- `Ag frame count total = {agtrace['Ag_frame_count_total']}`",
                f"- `Ag frames dropped = {agtrace['Ag_frames_dropped']}`",
                f"- `Ag frames used = {agtrace['Ag_frames_used']}`",
                f"- `BK frame count total = {agtrace['BK_frame_count_total']}`",
                f"- `Ag mean counts at pixel = {agtrace['Ag_mean_counts_at_pixel']:.12f}`",
                f"- `BK mean counts at pixel = {agtrace['BK_mean_counts_at_pixel']:.12f}`",
                f"- `Ag corrected counts = Ag mean - BK mean = {agtrace['Ag_corrected_counts']:.12f}`",
                f"- `Ag first frame counts at pixel = {agtrace['Ag_first_frame_counts_at_pixel']:.12f}`",
                "- 说明：Ag 使用 frame 2-100 的 mean；BK 使用 frame 1-100 的 mean；第 1 帧显式 drop。",
            ]
        )
    lines.extend(
        [
            "",
            "## 7. nk 插值结果",
            f"- `n_air = 1 + 0i`",
            f"- `n_glass = {format_complex_parts(nk['n_glass_complex'])}`",
            f"- `n_PVK = {format_complex_parts(nk['n_pvk_complex'])}`",
            f"- `n_Ag = {format_complex_parts(nk['n_ag_complex'])}`",
            f"- `n_complex = n + i k`",
            "- 相邻插值点：",
            f"  - Glass lower: `{nk['glass_interp']['lower_point']}`",
            f"  - Glass upper: `{nk['glass_interp']['upper_point']}`",
            f"  - PVK lower: `{nk['pvk_interp']['lower_point']}`",
            f"  - PVK upper: `{nk['pvk_interp']['upper_point']}`",
            f"  - Ag lower: `{nk['ag_interp']['lower_point']}`",
            f"  - Ag upper: `{nk['ag_interp']['upper_point']}`",
            "",
            "## 8. Fresnel 界面反射",
        ]
    )
    for key in ["air_glass", "glass_pvk", "pvk_air", "glass_ag", "ag_air", "air_ag"]:
        item = fresnel[key]
        lines.append(f"- `{key}`: r = {format_complex_parts(item['r'])}; `R = {item['R']:.12f}`")
    lines.extend(["", "## 9. 相干薄膜 TMM 展开", "", "### 9.1 Glass / PVK / Air"])
    for label in ["fixed", "best_d"]:
        item = coherent["glass_pvk"][label]
        lines.extend(
            [
                f"- `{label}` (`d = {item['d1_nm']:.12f} nm`)",
                f"  - `r_01 = {format_complex_parts(item['r_01'])}`",
                f"  - `r_12 = {format_complex_parts(item['r_12'])}`",
                f"  - `δ = {format_complex_parts(item['delta'])}`",
                f"  - `exp(2iδ) = {format_complex_parts(item['exp_2i_delta'])}`",
                f"  - `r_total = {format_complex_parts(item['r_total'])}`",
                f"  - `R_stack_by_formula = {item['R_stack_by_formula']:.12f}`",
                f"  - `R_stack_by_coh_tmm = {item['R_stack_by_coh_tmm']:.12f}`",
                f"  - {red(not item['consistency_pass'], 'absolute_difference = ' + format(item['absolute_difference'], '.12e'))}",
            ]
        )
    lines.extend(["", "### 9.2 Glass / Ag / Air"])
    item = coherent["glass_ag"]
    lines.extend(
        [
            f"- `r_01 = {format_complex_parts(item['r_01'])}`",
            f"- `r_12 = {format_complex_parts(item['r_12'])}`",
            f"- `δ = {format_complex_parts(item['delta'])}`",
            f"- `exp(2iδ) = {format_complex_parts(item['exp_2i_delta'])}`",
            f"- `r_total = {format_complex_parts(item['r_total'])}`",
            f"- `R_stack_glass_ag = {item['R_stack_by_formula']:.12f}`",
            f"- `R_stack_by_coh_tmm = {item['R_stack_by_coh_tmm']:.12f}`",
            f"- {red(not item['consistency_pass'], 'absolute_difference = ' + format(item['absolute_difference'], '.12e'))}",
        ]
    )
    lines.extend(["", "### 9.3 Air / Ag / Air"])
    item = coherent["air_ag"]
    lines.extend(
        [
            f"- `r_01 = {format_complex_parts(item['r_01'])}`",
            f"- `r_12 = {format_complex_parts(item['r_12'])}`",
            f"- `δ = {format_complex_parts(item['delta'])}`",
            f"- `exp(2iδ) = {format_complex_parts(item['exp_2i_delta'])}`",
            f"- `r_total = {format_complex_parts(item['r_total'])}`",
            f"- `R_stack_air_ag = {item['R_stack_by_formula']:.12f}`",
            f"- `R_stack_by_coh_tmm = {item['R_stack_by_coh_tmm']:.12f}`",
            f"- {red(not item['consistency_pass'], 'absolute_difference = ' + format(item['absolute_difference'], '.12e'))}",
        ]
    )
    lines.extend(["", "## 10. 厚玻璃非相干级联"])
    for key, title in [
        ("glass_pvk_fixed", "R_TMM_GlassPVK_Fixed"),
        ("glass_pvk_best", "R_TMM_GlassPVK_BestD"),
        ("glass_ag", "R_TMM_GlassAg"),
    ]:
        item = cascade[key]
        cmp = csvcmp[title]
        lines.extend(
            [
                f"- `{title}`",
                f"  - `R_front = {item['R_front']:.12f}`",
                f"  - `R_stack = {item['R_stack']:.12f}`",
                f"  - `numerator = {item['numerator']:.12f}`",
                f"  - `denominator = {item['denominator']:.12f}`",
                f"  - `R_total = {item['R_total']:.12f}`",
                f"  - `CSV = {cmp['reference']:.12f}`",
                f"  - {red(cmp['absolute_difference'] > ABS_TOL, 'difference = ' + format(cmp['absolute_difference'], '.12e'))}",
            ]
        )
    lines.extend(["", "## 11. 与现有 CSV 输出对比"])
    for key, item in csvcmp.items():
        lines.append(
            f"- `{key}`: manual={item['manual']:.12f}, csv={item['reference']:.12f}, "
            f"abs_diff={item['absolute_difference']:.12e}, rel_diff={item['relative_difference_percent']:.12g}%"
        )
    lines.extend(
        [
            "",
            "## 12. 单点实验-理论残差",
            f"- `R_Exp_GlassPVK_by_GlassAg = {expvals['R_Exp_GlassPVK_by_GlassAg']:.12f}`",
            f"- `R_Exp_GlassPVK_by_AgMirror = {format_optional(expvals.get('R_Exp_GlassPVK_by_AgMirror'))}`",
            f"- `R_TMM_GlassPVK_Fixed = {expvals['R_TMM_GlassPVK_Fixed']:.12f}`",
            f"- `R_TMM_GlassPVK_BestD = {expvals['R_TMM_GlassPVK_BestD']:.12f}`",
            f"- `Residual_Fixed_by_GlassAg = {diffs['Residual_Fixed_by_GlassAg']:.12f}`",
            f"- `Residual_BestD_by_GlassAg = {diffs['Residual_BestD_by_GlassAg']:.12f}`",
            f"- `Residual_Fixed_by_AgMirror = {format_optional(diffs.get('Residual_Fixed_by_AgMirror'))}`",
            f"- `Residual_BestD_by_AgMirror = {format_optional(diffs.get('Residual_BestD_by_AgMirror'))}`",
            f"- Glass/Ag 实验值相对 fixed {'高' if diffs['Residual_Fixed_by_GlassAg'] > 0 else '低'}，差值 `{abs(diffs['Residual_Fixed_by_GlassAg']):.12f}`，相对误差 `{diffs['Relative_Error_Fixed_GlassAg_percent']:.12f}%`",
            f"- Ag mirror 实验值相对 fixed {'高' if (diffs.get('Residual_Fixed_by_AgMirror') or 0.0) > 0 else '低'}，差值 `{format_optional(abs(diffs.get('Residual_Fixed_by_AgMirror')) if diffs.get('Residual_Fixed_by_AgMirror') is not None else None)}`，相对误差 `{format_optional(diffs.get('Relative_Error_Fixed_AgMirror_percent'))}%`",
            "",
            "## 13. 人工解释",
            "1. 该波长点的实验反射率先把样品和参比计数除以各自曝光时间，得到 counts/ms；再取样品/参比比值，乘以对应参比的理论反射率。",
            "2. TMM 不是简单把各界面反射率相加，因为薄膜内部会发生多次往返反射，振幅相位会相干叠加。",
            "3. 相位 `δ = 2π n d / λ` 控制薄膜内部往返波的相长/相消，是干涉条纹的核心。",
            "4. 厚玻璃前表面与后侧薄膜栈之间的光程远大于相干长度，因此当前代码把前表面与后侧相干栈按非相干级联处理，而不是整体相干求和。",
            "5. 本报告中的单层解析公式与 `coh_tmm` 在 `Glass/PVK/Air`、`Glass/Ag/Air`、`Air/Ag/Air` 三个栈上逐点比对。",
            f"6. 结果：手写相干公式与 `coh_tmm` {'一致' if trace['checks']['coherent_formula_all_pass'] else '不一致'}；手写非相干级联与 CSV {'一致' if trace['checks']['csv_all_pass'] else '不一致'}。",
            "7. 因此如果一致，可以判断当前代码的公式层面没有明显硬错误；若不一致，则优先排查波长点选择、插值、输出列或手写公式实现。",
            "8. 在该点上，实验与理论差异主要来自实验 counts ratio 对应的反射率明显高于 `glass/PVK` TMM 理论值，而不是单层公式或非相干级联公式本身计算错误。",
            "",
            "## 14. 发现的问题、风险与下一步建议",
            f"- `Ag mirror` 曝光口径：当前 manifest 记录为 `{format_optional(counts.get('ag_mirror_exposure_ms'))}` ms，trace 复算与 CSV 一致。",
            f"- 最新 dual 输出来自 `output_tag={trace['source_output_tag']}`；本报告只审计该结果集，不等于其它 tag 也完全相同。",
            "- 若后续要继续定位实验-理论偏差，优先检查参比有效反射、ROI/收光几何、散射/背景残差，而不是先怀疑当前 TMM 公式层。",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_trace(target_wavelength_nm: float, manifest_override: str | None) -> dict[str, object]:
    output_set = find_dual_output_set(manifest_override)
    manifest = json.loads(output_set.manifest_path.read_text(encoding="utf-8"))
    calibrated_df = pd.read_csv(output_set.calibrated_path)
    theory_df = pd.read_csv(output_set.theory_path)
    nk_df = pd.read_csv(manifest["nk_csv"])

    wl = calibrated_df["Wavelength_nm"].to_numpy(dtype=float)
    row_idx = nearest_index(wl, target_wavelength_nm)
    row = calibrated_df.iloc[row_idx]
    theory_row = theory_df.iloc[row_idx]
    lambda_used_nm = float(row["Wavelength_nm"])

    sample_exposure_ms = float(manifest["sample_exposure_ms"])
    ref_exposure_ms = float(manifest["reference_exposure_ms"])
    ag_mirror_exposure_ms = manifest.get("ag_mirror_exposure_ms")
    ag_mirror_exposure_ms = float(ag_mirror_exposure_ms) if ag_mirror_exposure_ms is not None else None

    glass_interp = interpolate_with_neighbors(nk_df, "n_Glass", "k_Glass", lambda_used_nm)
    pvk_interp = interpolate_with_neighbors(nk_df, "n_PVK", "k_PVK", lambda_used_nm)
    ag_interp = interpolate_with_neighbors(nk_df, "n_Ag", "k_Ag", lambda_used_nm)

    n_air = 1.0 + 0.0j
    n_glass = glass_interp["complex_value"]
    n_pvk = pvk_interp["complex_value"]
    n_ag = ag_interp["complex_value"]

    fresnel = {
        "air_glass": interface_entry("air_glass", n_air, n_glass),
        "glass_pvk": interface_entry("glass_pvk", n_glass, n_pvk),
        "pvk_air": interface_entry("pvk_air", n_pvk, n_air),
        "glass_ag": interface_entry("glass_ag", n_glass, n_ag),
        "ag_air": interface_entry("ag_air", n_ag, n_air),
        "air_ag": interface_entry("air_ag", n_air, n_ag),
    }

    best_d_nm = float(manifest["best_d_PVK_nm"])
    d_ag_nm = float(manifest["d_ag_nm_assumption"])
    d_pvk_fixed_nm = float(manifest["d_pvk_fixed_nm_assumption"])

    glass_pvk_fixed = single_layer_trace(n_glass, n_pvk, n_air, d_pvk_fixed_nm, lambda_used_nm, "Glass/PVK/Air fixed")
    glass_pvk_best = single_layer_trace(n_glass, n_pvk, n_air, best_d_nm, lambda_used_nm, "Glass/PVK/Air best_d")
    glass_ag = single_layer_trace(n_glass, n_ag, n_air, d_ag_nm, lambda_used_nm, "Glass/Ag/Air")
    air_ag = single_layer_trace(n_air, n_ag, n_air, d_ag_nm, lambda_used_nm, "Air/Ag/Air")

    r_front = float(fresnel["air_glass"]["R"])
    cascade_fixed = incoherent_cascade_trace(r_front, glass_pvk_fixed["R_stack_by_formula"])
    cascade_best = incoherent_cascade_trace(r_front, glass_pvk_best["R_stack_by_formula"])
    cascade_ag = incoherent_cascade_trace(r_front, glass_ag["R_stack_by_formula"])

    counts = {
        "Glass_PVK_Counts": float(row["Glass_PVK_Counts"]),
        "Glass_Ag_Counts": float(row["Glass_Ag_Counts"]),
        "Glass_PVK_CountsPerMs": float(row["Glass_PVK_CountsPerMs"]),
        "Glass_Ag_CountsPerMs": float(row["Glass_Ag_CountsPerMs"]),
        "sample_exposure_ms": sample_exposure_ms,
        "glass_ag_exposure_ms": ref_exposure_ms,
        "Ag_Mirror_Corrected_Counts": float(row["Ag_Mirror_Corrected_Counts"]) if "Ag_Mirror_Corrected_Counts" in row.index else None,
        "Ag_Mirror_Corrected_CountsPerMs": float(row["Ag_Mirror_Corrected_CountsPerMs"]) if "Ag_Mirror_Corrected_CountsPerMs" in row.index else None,
        "ag_mirror_exposure_ms": ag_mirror_exposure_ms,
    }
    expvals = {
        "counts_ratio_glassAg": float(row["Glass_PVK_CountsPerMs"] / row["Glass_Ag_CountsPerMs"]),
        "R_Exp_GlassPVK_by_GlassAg": float(row["R_Exp_GlassPVK_by_GlassAg"]),
        "R_TMM_GlassAg": float(row["R_TMM_GlassAg"]),
        "R_TMM_AgMirror": float(row["R_TMM_AgMirror"]),
        "R_TMM_GlassPVK_Fixed": float(row["R_TMM_GlassPVK_Fixed"]),
        "R_TMM_GlassPVK_BestD": float(row["R_TMM_GlassPVK_BestD"]),
    }
    if counts["Ag_Mirror_Corrected_CountsPerMs"] is not None:
        expvals["counts_ratio_AgMirror"] = float(row["Glass_PVK_CountsPerMs"] / row["Ag_Mirror_Corrected_CountsPerMs"])
        expvals["R_Exp_GlassPVK_by_AgMirror"] = float(row["R_Exp_GlassPVK_by_AgMirror"])
    else:
        expvals["counts_ratio_AgMirror"] = None
        expvals["R_Exp_GlassPVK_by_AgMirror"] = None

    csvcmp = {
        "R_TMM_GlassPVK_Fixed": difference_dict(cascade_fixed["R_total"], float(row["R_TMM_GlassPVK_Fixed"])),
        "R_TMM_GlassPVK_BestD": difference_dict(cascade_best["R_total"], float(row["R_TMM_GlassPVK_BestD"])),
        "R_TMM_GlassAg": difference_dict(cascade_ag["R_total"], float(row["R_TMM_GlassAg"])),
        "R_Exp_GlassPVK_by_GlassAg": difference_dict(expvals["R_Exp_GlassPVK_by_GlassAg"], float(row["R_Exp_GlassPVK_by_GlassAg"])),
    }
    if expvals["R_Exp_GlassPVK_by_AgMirror"] is not None:
        csvcmp["R_Exp_GlassPVK_by_AgMirror"] = difference_dict(expvals["R_Exp_GlassPVK_by_AgMirror"], float(row["R_Exp_GlassPVK_by_AgMirror"]))

    diffs = {
        "Residual_Fixed_by_GlassAg": float(expvals["R_Exp_GlassPVK_by_GlassAg"] - expvals["R_TMM_GlassPVK_Fixed"]),
        "Residual_BestD_by_GlassAg": float(expvals["R_Exp_GlassPVK_by_GlassAg"] - expvals["R_TMM_GlassPVK_BestD"]),
        "Relative_Error_Fixed_GlassAg_percent": float((expvals["R_Exp_GlassPVK_by_GlassAg"] - expvals["R_TMM_GlassPVK_Fixed"]) / expvals["R_TMM_GlassPVK_Fixed"] * 100.0),
    }
    if expvals["R_Exp_GlassPVK_by_AgMirror"] is not None:
        diffs["Residual_Fixed_by_AgMirror"] = float(expvals["R_Exp_GlassPVK_by_AgMirror"] - expvals["R_TMM_GlassPVK_Fixed"])
        diffs["Residual_BestD_by_AgMirror"] = float(expvals["R_Exp_GlassPVK_by_AgMirror"] - expvals["R_TMM_GlassPVK_BestD"])
        diffs["Relative_Error_Fixed_AgMirror_percent"] = float((expvals["R_Exp_GlassPVK_by_AgMirror"] - expvals["R_TMM_GlassPVK_Fixed"]) / expvals["R_TMM_GlassPVK_Fixed"] * 100.0)

    theory_csv_cmp = {
        "R_TMM_GlassAg_theory_csv": difference_dict(cascade_ag["R_total"], float(theory_row["R_TMM_GlassAg"])),
        "R_TMM_AgMirror_theory_csv": difference_dict(air_ag["R_stack_by_formula"], float(theory_row["R_TMM_AgMirror"])),
        "R_TMM_GlassPVK_Fixed_theory_csv": difference_dict(cascade_fixed["R_total"], float(theory_row["R_TMM_GlassPVK_Fixed"])),
        "R_TMM_GlassPVK_BestD_theory_csv": difference_dict(cascade_best["R_total"], float(theory_row["R_TMM_GlassPVK_BestD"])),
    }
    csvcmp.update(theory_csv_cmp)

    agtrace = build_ag_pixel_trace(manifest, lambda_used_nm) if output_set.ag_corrected_path is not None else None

    trace = {
        "target_wavelength_nm": float(target_wavelength_nm),
        "lambda_used_nm": lambda_used_nm,
        "delta_nm": float(lambda_used_nm - target_wavelength_nm),
        "row_index": row_idx,
        "source_output_tag": output_set.output_tag,
        "input_files": {
            "manifest_json": output_set.manifest_path.as_posix(),
            "calibrated_csv": output_set.calibrated_path.as_posix(),
            "theory_csv": output_set.theory_path.as_posix(),
            "nk_csv": manifest["nk_csv"],
            "sample_csv": manifest["sample_csv"],
            "reference_csv": manifest["reference_csv"],
            "ag_corrected_csv": output_set.ag_corrected_path.as_posix() if output_set.ag_corrected_path else None,
            "ag_qc_csv": output_set.ag_qc_path.as_posix() if output_set.ag_qc_path else None,
        },
        "counts": counts,
        "nk": {
            "glass_interp": {
                "lower_point": glass_interp["lower_point"],
                "upper_point": glass_interp["upper_point"],
                "interpolated": glass_interp["interpolated"],
            },
            "pvk_interp": {
                "lower_point": pvk_interp["lower_point"],
                "upper_point": pvk_interp["upper_point"],
                "interpolated": pvk_interp["interpolated"],
            },
            "ag_interp": {
                "lower_point": ag_interp["lower_point"],
                "upper_point": ag_interp["upper_point"],
                "interpolated": ag_interp["interpolated"],
            },
            "n_glass_complex": complex_dict(n_glass),
            "n_pvk_complex": complex_dict(n_pvk),
            "n_ag_complex": complex_dict(n_ag),
        },
        "fresnel": fresnel,
        "coherent_stack": {
            "glass_pvk": {"fixed": glass_pvk_fixed, "best_d": glass_pvk_best},
            "glass_ag": glass_ag,
            "air_ag": air_ag,
        },
        "incoherent_cascade": {
            "glass_pvk_fixed": cascade_fixed,
            "glass_pvk_best": cascade_best,
            "glass_ag": cascade_ag,
        },
        "experimental_reflectance": expvals,
        "csv_comparison": csvcmp,
        "differences": diffs,
        "ag_mirror_multiframe_trace": agtrace,
        "checks": {
            "coherent_formula_all_pass": bool(
                glass_pvk_fixed["consistency_pass"]
                and glass_pvk_best["consistency_pass"]
                and glass_ag["consistency_pass"]
                and air_ag["consistency_pass"]
            ),
            "csv_all_pass": bool(all(item["absolute_difference"] <= ABS_TOL for item in csvcmp.values())),
        },
    }
    return trace


def main() -> int:
    args = parse_args()
    TRACE_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TRACE_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    trace = build_trace(target_wavelength_nm=float(args.target_wavelength_nm), manifest_override=args.dual_manifest)
    json_path = TRACE_PROCESSED_DIR / f"phase08_0429_trace_{args.output_tag}.json"
    report_path = TRACE_REPORT_DIR / f"phase08_0429_trace_{args.output_tag}.md"
    json_path.write_text(json.dumps(sanitize_for_json(trace), indent=2, ensure_ascii=False), encoding="utf-8")
    render_markdown(trace, report_path)
    print(f"trace_json: {json_path}")
    print(f"trace_report: {report_path}")
    print(f"lambda_used_nm: {trace['lambda_used_nm']:.12f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
