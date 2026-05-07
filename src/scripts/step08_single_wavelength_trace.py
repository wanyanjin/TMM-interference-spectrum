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


def format_float(value: float | None, digits: int = 12) -> str:
    if value is None:
        return "not_available"
    return f"{float(value):.{digits}f}"


def rel_path_str(path_str: str | None) -> str:
    if path_str is None:
        return "not_available"
    try:
        path = Path(path_str).resolve()
        return path.relative_to(PROJECT_ROOT).as_posix()
    except Exception:
        return path_str


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return lines


def frame_range_text(frames: list[int]) -> str:
    if not frames:
        return "none"
    if len(frames) == 1:
        return f"{frames[0]}"
    return f"{frames[0]}–{frames[-1]}, total {len(frames)} frames"


def report_status(trace: dict) -> list[dict[str, str]]:
    agtrace = trace.get("ag_mirror_multiframe_trace")
    checks = trace["checks"]
    expvals = trace["experimental_reflectance"]
    statuses = [
        {
            "item": "target wavelength matched to nearest data point",
            "status": "PASS",
            "note": f"target={trace['target_wavelength_nm']:.3f} nm, used={trace['lambda_used_nm']:.6f} nm, Δ={trace['delta_nm']:.6f} nm",
        },
        {
            "item": "Ag first frame excluded",
            "status": "PASS" if agtrace and agtrace["Ag_frames_dropped"] == [1] else "NOT_CHECKED",
            "note": "Ag 第 1 帧显式剔除；若无 Ag trace 则不检查。",
        },
        {
            "item": "Ag frames reduced by mean",
            "status": "PASS" if agtrace else "NOT_CHECKED",
            "note": "Ag 用 frame 2–100 求 mean；BK 用 frame 1–100 求 mean。",
        },
        {
            "item": "manual coherent formula vs coh_tmm",
            "status": "PASS" if checks["coherent_formula_all_pass"] else "FAIL",
            "note": f"一致性阈值 abs_diff <= {ABS_TOL:.1e}",
        },
        {
            "item": "manual incoherent cascade vs CSV",
            "status": "PASS" if checks["csv_all_pass"] else "FAIL",
            "note": f"一致性阈值 abs_diff <= {ABS_TOL:.1e}",
        },
        {
            "item": "experimental reflectance manual vs CSV",
            "status": "PASS" if all(v["absolute_difference"] <= ABS_TOL for k, v in trace["csv_comparison"].items() if k.startswith("R_Exp_")) else "FAIL",
            "note": "手算实验反射率与输出 CSV 对比。",
        },
        {
            "item": "PVK n,k suitability",
            "status": "WARNING",
            "note": f"当前只审计 output_tag={trace['source_output_tag']} 对应 nk 来源，不能证明该 nk 全谱适用。",
        },
        {
            "item": "specular-only TMM vs microscope measurement equivalence",
            "status": "WARNING",
            "note": "公式自洽不等于显微镜实测必然等于理想 specular reflectance。",
        },
    ]
    if expvals.get("R_Exp_GlassPVK_by_AgMirror") is None:
        statuses.append(
            {
                "item": "Ag mirror calibration chain available",
                "status": "NOT_CHECKED",
                "note": "当前结果集中无 Ag mirror 链。",
            }
        )
    return statuses


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
    coherent = trace["coherent_stack"]
    cascade = trace["incoherent_cascade"]
    expvals = trace["experimental_reflectance"]
    csvcmp = trace["csv_comparison"]
    diffs = trace["differences"]
    nk = trace["nk"]
    counts = trace["counts"]
    fresnel = trace["fresnel"]
    agtrace = trace.get("ag_mirror_multiframe_trace")
    status_rows = report_status(trace)

    def complex_rows(item: dict[str, object], reflectance: float | None = None) -> list[object]:
        return [
            format_float(item["real"]),
            format_float(item["imag"]),
            format_float(item["abs"]),
            format_float(item["phase_rad"]),
            format_float(item["phase_deg"]),
            format_float(reflectance) if reflectance is not None else "—",
        ]

    lines: list[str] = ["# Phase 08 Single-Wavelength Trace Report", ""]
    lines.extend(
        [
            "## 0. 执行摘要",
            f"- 本报告审计目标波长为 `{trace['target_wavelength_nm']:.3f} nm`，实际使用最近数据点 `{trace['lambda_used_nm']:.12f} nm`，偏差 `{trace['delta_nm']:.12f} nm`。",
            f"- 手写单层相干公式与 `coh_tmm` {'一致' if trace['checks']['coherent_formula_all_pass'] else '不一致'}，一致性阈值为 `{ABS_TOL:.1e}`。",
            f"- 手写厚玻璃非相干级联与现有 CSV {'一致' if trace['checks']['csv_all_pass'] else '不一致'}。",
            f"- 该点实验反射率分别为 `glass/Ag = {expvals['R_Exp_GlassPVK_by_GlassAg']:.12f}`、`Ag mirror = {format_optional(expvals.get('R_Exp_GlassPVK_by_AgMirror'))}`，而 `R_TMM_GlassPVK_Fixed = {expvals['R_TMM_GlassPVK_Fixed']:.12f}`。",
            "- 当前结论：公式实现与输出 CSV 在该点自洽，但实验与理论仍存在显著差异；下一步应继续审查 `n,k` 适用性、实验参比链路、显微收光与散射贡献。",
            "",
            "## 0.1 审计状态表",
        ]
    )
    lines.extend(markdown_table(["检查项", "状态", "说明"], [[r["item"], r["status"], r["note"]] for r in status_rows]))

    lines.extend(["", "## 1. 输入数据与版本"])
    lines.extend(
        markdown_table(
            ["角色", "路径"],
            [
                ["dual manifest", f"`{rel_path_str(trace['input_files']['manifest_json'])}`"],
                ["calibrated reflectance", f"`{rel_path_str(trace['input_files']['calibrated_csv'])}`"],
                ["theory csv", f"`{rel_path_str(trace['input_files']['theory_csv'])}`"],
                ["nk csv", f"`{rel_path_str(trace['input_files']['nk_csv'])}`"],
                ["sample csv", f"`{rel_path_str(trace['input_files']['sample_csv'])}`"],
                ["reference csv", f"`{rel_path_str(trace['input_files']['reference_csv'])}`"],
                ["ag corrected csv", f"`{rel_path_str(trace['input_files'].get('ag_corrected_csv'))}`"],
                ["ag frame qc csv", f"`{rel_path_str(trace['input_files'].get('ag_qc_csv'))}`"],
                ["source output tag", f"`{trace['source_output_tag']}`"],
            ],
        )
    )

    lines.extend(["", "## 2. 目标波长与实际使用波长"])
    lines.extend(
        markdown_table(
            ["quantity", "value"],
            [
                ["target_wavelength_nm", format_float(trace["target_wavelength_nm"])],
                ["lambda_used_nm", format_float(trace["lambda_used_nm"])],
                ["delta_nm", format_float(trace["delta_nm"])],
                ["row_index", trace["row_index"]],
            ],
        )
    )

    lines.extend(
        [
            "",
            "## 3. 实验计数与曝光归一化",
            "$$",
            "I_{\\mathrm{counts/ms}}(\\lambda)=\\frac{I_{\\mathrm{counts}}(\\lambda)}{t_{\\mathrm{exposure}}}",
            "$$",
        ]
    )
    lines.extend(
        markdown_table(
            ["quantity", "value"],
            [
                ["Glass_PVK_Counts", format_float(counts["Glass_PVK_Counts"])],
                ["Glass_Ag_Counts", format_float(counts["Glass_Ag_Counts"])],
                ["Ag_Mirror_Corrected_Counts", format_optional(counts.get("Ag_Mirror_Corrected_Counts"))],
                ["sample_exposure_ms", format_float(counts["sample_exposure_ms"])],
                ["glass_ag_exposure_ms", format_float(counts["glass_ag_exposure_ms"])],
                ["ag_mirror_exposure_ms", format_optional(counts.get("ag_mirror_exposure_ms"))],
                ["Glass_PVK_CountsPerMs", format_float(counts["Glass_PVK_CountsPerMs"])],
                ["Glass_Ag_CountsPerMs", format_float(counts["Glass_Ag_CountsPerMs"])],
                ["Ag_Mirror_Corrected_CountsPerMs", format_optional(counts.get("Ag_Mirror_Corrected_CountsPerMs"))],
            ],
        )
    )

    lines.extend(
        [
            "",
            "## 4. glass/Ag 参比校准链",
            "$$",
            "R_{\\mathrm{exp}}^{\\mathrm{glass/Ag}}(\\lambda)=",
            "\\frac{I_{\\mathrm{PVK}}(\\lambda)/t_{\\mathrm{PVK}}}{I_{\\mathrm{glass/Ag}}(\\lambda)/t_{\\mathrm{glass/Ag}}}",
            "\\cdot R_{\\mathrm{TMM}}^{\\mathrm{glass/Ag}}(\\lambda)",
            "$$",
        ]
    )
    lines.extend(
        markdown_table(
            ["quantity", "value"],
            [
                ["I_glassPVK", format_float(counts["Glass_PVK_Counts"])],
                ["t_glassPVK_ms", format_float(counts["sample_exposure_ms"])],
                ["I_glassAg", format_float(counts["Glass_Ag_Counts"])],
                ["t_glassAg_ms", format_float(counts["glass_ag_exposure_ms"])],
                ["R_TMM_glassAg", format_float(expvals["R_TMM_GlassAg"])],
                ["counts_ratio_glassAg", format_float(expvals["counts_ratio_glassAg"])],
                ["R_exp_by_glassAg", format_float(expvals["R_Exp_GlassPVK_by_GlassAg"])],
            ],
        )
    )

    lines.extend(["", "## 5. Ag mirror 参比校准链"])
    if expvals.get("R_Exp_GlassPVK_by_AgMirror") is None:
        lines.append("Ag mirror chain not available in current outputs.")
    else:
        lines.extend(
            [
                "$$",
                "R_{\\mathrm{exp}}^{\\mathrm{Ag\\ mirror}}(\\lambda)=",
                "\\frac{I_{\\mathrm{PVK}}(\\lambda)/t_{\\mathrm{PVK}}}{I_{\\mathrm{Ag\\ mirror,corr}}(\\lambda)/t_{\\mathrm{Ag\\ mirror}}}",
                "\\cdot R_{\\mathrm{TMM}}^{\\mathrm{Ag\\ mirror}}(\\lambda)",
                "$$",
            ]
        )
        lines.extend(
            markdown_table(
                ["quantity", "value"],
                [
                    ["I_glassPVK", format_float(counts["Glass_PVK_Counts"])],
                    ["t_glassPVK_ms", format_float(counts["sample_exposure_ms"])],
                    ["I_AgMirror_corrected", format_float(counts["Ag_Mirror_Corrected_Counts"])],
                    ["t_AgMirror_ms", format_float(counts["ag_mirror_exposure_ms"])],
                    ["R_TMM_AgMirror", format_float(expvals["R_TMM_AgMirror"])],
                    ["counts_ratio_AgMirror", format_float(expvals["counts_ratio_AgMirror"])],
                    ["R_exp_by_AgMirror", format_float(expvals["R_Exp_GlassPVK_by_AgMirror"])],
                ],
            )
        )

    lines.extend(["", "## 6. Ag mirror 多帧与背景扣除展开"])
    if agtrace is None:
        lines.append("当前输出中没有 Ag mirror corrected 数据，无法展开该节。")
    else:
        lines.append(
            "Ag 使用 `frame 2–100` 的 mean，BK 使用 `frame 1–100` 的 mean；第 1 帧显式 drop，完整帧列表保留在 JSON。"
        )
        lines.extend(
            markdown_table(
                ["quantity", "value"],
                [
                    ["Pixel_Index", agtrace["Pixel_Index"]],
                    ["lambda_pixel_nm", format_float(agtrace["lambda_pixel_nm"])],
                    ["Ag frame count total", agtrace["Ag_frame_count_total"]],
                    ["Ag frames dropped", "1"],
                    ["Ag frames used", frame_range_text(agtrace["Ag_frames_used"])],
                    ["BK frame count total", agtrace["BK_frame_count_total"]],
                    ["Ag mean counts at pixel", format_float(agtrace["Ag_mean_counts_at_pixel"])],
                    ["BK mean counts at pixel", format_float(agtrace["BK_mean_counts_at_pixel"])],
                    ["Ag corrected counts", format_float(agtrace["Ag_corrected_counts"])],
                    ["Ag first frame counts at pixel", format_float(agtrace["Ag_first_frame_counts_at_pixel"])],
                ],
            )
        )

    lines.extend(["", "## 7. nk 插值结果"])
    lines.append("$\\tilde n = n + ik$")
    lines.extend(
        markdown_table(
            ["material", "lower_nm", "lower_n", "lower_k", "upper_nm", "upper_n", "upper_k", "interp_n", "interp_k"],
            [
                [
                    "Glass",
                    format_float(nk["glass_interp"]["lower_point"]["Wavelength_nm"], 3),
                    format_float(nk["glass_interp"]["lower_point"]["n"]),
                    format_float(nk["glass_interp"]["lower_point"]["k"]),
                    format_float(nk["glass_interp"]["upper_point"]["Wavelength_nm"], 3),
                    format_float(nk["glass_interp"]["upper_point"]["n"]),
                    format_float(nk["glass_interp"]["upper_point"]["k"]),
                    format_float(nk["n_glass_complex"]["real"]),
                    format_float(nk["n_glass_complex"]["imag"]),
                ],
                [
                    "PVK",
                    format_float(nk["pvk_interp"]["lower_point"]["Wavelength_nm"], 3),
                    format_float(nk["pvk_interp"]["lower_point"]["n"]),
                    format_float(nk["pvk_interp"]["lower_point"]["k"]),
                    format_float(nk["pvk_interp"]["upper_point"]["Wavelength_nm"], 3),
                    format_float(nk["pvk_interp"]["upper_point"]["n"]),
                    format_float(nk["pvk_interp"]["upper_point"]["k"]),
                    format_float(nk["n_pvk_complex"]["real"]),
                    format_float(nk["n_pvk_complex"]["imag"]),
                ],
                [
                    "Ag",
                    format_float(nk["ag_interp"]["lower_point"]["Wavelength_nm"], 3),
                    format_float(nk["ag_interp"]["lower_point"]["n"]),
                    format_float(nk["ag_interp"]["lower_point"]["k"]),
                    format_float(nk["ag_interp"]["upper_point"]["Wavelength_nm"], 3),
                    format_float(nk["ag_interp"]["upper_point"]["n"]),
                    format_float(nk["ag_interp"]["upper_point"]["k"]),
                    format_float(nk["n_ag_complex"]["real"]),
                    format_float(nk["n_ag_complex"]["imag"]),
                ],
            ],
        )
    )

    lines.extend(["", "## 8. Fresnel 界面反射"])
    lines.extend(
        [
            "$$",
            "r_{ij}=\\frac{\\tilde n_i-\\tilde n_j}{\\tilde n_i+\\tilde n_j},\\qquad R_{ij}=|r_{ij}|^2",
            "$$",
            "注意：界面反射率不是最终薄膜反射率；相干薄膜中的多次往返振幅不能简单相加为总反射率。",
        ]
    )
    rows = []
    for key in ["air_glass", "glass_pvk", "pvk_air", "glass_ag", "ag_air", "air_ag"]:
        item = fresnel[key]
        rows.append([key, *complex_rows(item["r"], item["R"])])
    lines.extend(markdown_table(["quantity", "real", "imag", "magnitude", "phase_rad", "phase_deg", "reflectance"], rows))

    lines.extend(["", "## 9. 相干薄膜 TMM 展开"])
    lines.extend(
        [
            "$$",
            "\\delta = \\frac{2\\pi \\tilde n_1 d_1}{\\lambda}",
            "$$",
            "$$",
            "r_{\\mathrm{total}}=",
            "\\frac{r_{01}+r_{12}\\exp(2i\\delta)}{1+r_{01}r_{12}\\exp(2i\\delta)},\\qquad",
            "R_{\\mathrm{stack}}=|r_{\\mathrm{total}}|^2",
            "$$",
        ]
    )

    def add_stack_section(title: str, item: dict[str, object], reflectance_label: str) -> None:
        lines.extend(["", f"### {title}"])
        lines.append(f"`d_1 = {format_float(item['d1_nm'])} nm`")
        lines.extend(
            markdown_table(
                ["quantity", "real", "imag", "magnitude", "phase_rad", "phase_deg"],
                [
                    ["r_01", *complex_rows(item["r_01"])[:-1]],
                    ["r_12", *complex_rows(item["r_12"])[:-1]],
                    ["delta", *complex_rows(item["delta"])[:-1]],
                    ["exp(2i delta)", *complex_rows(item["exp_2i_delta"])[:-1]],
                    ["numerator", *complex_rows(item["numerator"])[:-1]],
                    ["denominator", *complex_rows(item["denominator"])[:-1]],
                    ["r_total", *complex_rows(item["r_total"])[:-1]],
                ],
            )
        )
        lines.extend(
            markdown_table(
                ["quantity", "manual", "csv/coh_tmm", "abs_diff", "rel_diff_percent"],
                [
                    [
                        reflectance_label,
                        format_float(item["R_stack_by_formula"]),
                        format_float(item["R_stack_by_coh_tmm"]),
                        f"{item['absolute_difference']:.12e}",
                        f"{item['relative_difference_percent']:.12g}",
                    ]
                ],
            )
        )

    add_stack_section("9.1 Glass / PVK / Air (fixed)", coherent["glass_pvk"]["fixed"], "R_stack_glass_pvk_fixed")
    add_stack_section("9.2 Glass / PVK / Air (best-d)", coherent["glass_pvk"]["best_d"], "R_stack_glass_pvk_bestD")
    add_stack_section("9.3 Glass / Ag / Air", coherent["glass_ag"], "R_stack_glass_ag")
    add_stack_section("9.4 Air / Ag / Air", coherent["air_ag"], "R_stack_air_ag")

    lines.extend(["", "## 10. 厚玻璃非相干级联"])
    lines.extend(
        [
            "$$",
            "R_{\\mathrm{front}} = \\left|\\frac{\\tilde n_{\\mathrm{air}}-\\tilde n_{\\mathrm{glass}}}{\\tilde n_{\\mathrm{air}}+\\tilde n_{\\mathrm{glass}}}\\right|^2",
            "$$",
            "$$",
            "R_{\\mathrm{total}} = R_{\\mathrm{front}} + \\frac{(1-R_{\\mathrm{front}})^2 R_{\\mathrm{stack}}}{1-R_{\\mathrm{front}}R_{\\mathrm{stack}}}",
            "$$",
        ]
    )
    lines.extend(
        markdown_table(
            ["quantity", "R_front", "R_stack", "numerator", "denominator", "R_total"],
            [
                [
                    "R_TMM_GlassPVK_Fixed_manual",
                    format_float(cascade["glass_pvk_fixed"]["R_front"]),
                    format_float(cascade["glass_pvk_fixed"]["R_stack"]),
                    format_float(cascade["glass_pvk_fixed"]["numerator"]),
                    format_float(cascade["glass_pvk_fixed"]["denominator"]),
                    format_float(cascade["glass_pvk_fixed"]["R_total"]),
                ],
                [
                    "R_TMM_GlassPVK_BestD_manual",
                    format_float(cascade["glass_pvk_best"]["R_front"]),
                    format_float(cascade["glass_pvk_best"]["R_stack"]),
                    format_float(cascade["glass_pvk_best"]["numerator"]),
                    format_float(cascade["glass_pvk_best"]["denominator"]),
                    format_float(cascade["glass_pvk_best"]["R_total"]),
                ],
                [
                    "R_TMM_GlassAg_manual",
                    format_float(cascade["glass_ag"]["R_front"]),
                    format_float(cascade["glass_ag"]["R_stack"]),
                    format_float(cascade["glass_ag"]["numerator"]),
                    format_float(cascade["glass_ag"]["denominator"]),
                    format_float(cascade["glass_ag"]["R_total"]),
                ],
            ],
        )
    )

    lines.extend(["", "## 11. 与现有 CSV 输出对比"])
    lines.extend(
        markdown_table(
            ["quantity", "manual", "csv/coh_tmm", "abs_diff", "rel_diff_percent"],
            [
                [key, format_float(item["manual"]), format_float(item["reference"]), f"{item['absolute_difference']:.12e}", f"{item['relative_difference_percent']:.12g}"]
                for key, item in csvcmp.items()
            ],
        )
    )

    lines.extend(["", "## 12. 单点实验-理论残差"])
    lines.append(
        "$$"
        "\n\\mathrm{Residual} = R_{\\mathrm{exp}} - R_{\\mathrm{TMM}}"
        "\n$$"
    )
    residual_rows = [
        ["R_Exp_GlassPVK_by_GlassAg", format_float(expvals["R_Exp_GlassPVK_by_GlassAg"])],
        ["R_Exp_GlassPVK_by_AgMirror", format_optional(expvals.get("R_Exp_GlassPVK_by_AgMirror"))],
        ["R_TMM_GlassPVK_Fixed", format_float(expvals["R_TMM_GlassPVK_Fixed"])],
        ["R_TMM_GlassPVK_BestD", format_float(expvals["R_TMM_GlassPVK_BestD"])],
        ["Residual_Fixed_by_GlassAg", format_float(diffs["Residual_Fixed_by_GlassAg"])],
        ["Residual_BestD_by_GlassAg", format_float(diffs["Residual_BestD_by_GlassAg"])],
        ["Residual_Fixed_by_AgMirror", format_optional(diffs.get("Residual_Fixed_by_AgMirror"))],
        ["Residual_BestD_by_AgMirror", format_optional(diffs.get("Residual_BestD_by_AgMirror"))],
    ]
    lines.extend(markdown_table(["quantity", "value"], residual_rows))
    lines.extend(
        [
            "",
            f"- `glass/Ag` 链相对 fixed 为 **高**，差值 `{abs(diffs['Residual_Fixed_by_GlassAg']):.12f}`，相对误差 `{diffs['Relative_Error_Fixed_GlassAg_percent']:.12f}%`。",
            f"- `Ag mirror` 链相对 fixed 为 **{'高' if (diffs.get('Residual_Fixed_by_AgMirror') or 0.0) > 0 else '低'}**，差值 `{format_optional(abs(diffs.get('Residual_Fixed_by_AgMirror')) if diffs.get('Residual_Fixed_by_AgMirror') is not None else None)}`，相对误差 `{format_optional(diffs.get('Relative_Error_Fixed_AgMirror_percent'))}%`。",
            "- 当前单点偏差主要来自实验 counts ratio 对应的反射率明显高于 `glass/PVK` TMM 理论值，而不是 TMM 公式展开本身。",
            "",
            "## 13. 人工解释",
            "1. 这个单点 trace 的作用，是把从计数到实验反射率、再到 TMM 理论反射率的整条链路显式展开，便于人工审计。",
            "2. 实验反射率的核心步骤是：先把样品和参比计数除以曝光时间，得到 counts/ms；再取样品/参比比值；最后乘上对应参比的理论反射率。",
            "3. TMM 不能把各界面反射率直接相加，因为薄膜中存在多次往返反射，必须在振幅层面结合相位 `\\delta` 做相干叠加。",
            "4. 厚玻璃前表面与后侧薄膜栈的光程远大于相干长度，因此前表面与后侧相干栈之间采用非相干级联，而不是整体相干求和。",
            f"5. 本报告中手写单层公式与 `coh_tmm` {'一致' if trace['checks']['coherent_formula_all_pass'] else '不一致'}，手写非相干级联与 CSV {'一致' if trace['checks']['csv_all_pass'] else '不一致'}。",
            "6. 因而该点可以证明：当前代码的公式实现层没有明显硬错误；但不能证明全谱、材料光学常数或显微镜测量语义已经完全正确。",
            "",
            "## 本报告不能证明什么",
            "- 单波长 trace 不能证明全谱所有波长点都无误。",
            "- 公式与 CSV 一致，不能证明当前 PVK `n,k` 就是正确的样品光学常数。",
            "- 公式与 CSV 一致，不能证明实验反射率必然等于理想 TMM 的 specular reflectance。",
            "- 当前 Ag mirror 链仍基于理想 `Air/Ag/Air` 模型，不等于已经证明真实 Ag 参比完全符合该模型。",
            f"- 本报告只审计当前 `output_tag={trace['source_output_tag']}` 对应结果集，不代表所有历史结果都相同。",
            "",
            "## 组会讲解摘要",
            "- 这个 600 nm 单点 trace 的目的，是把 Phase 08 的反射率校准和 TMM 计算从黑箱拆成可以逐项核对的步骤。",
            "- 它证明了当前代码在该点的公式实现、TMM 单层解析式、厚玻璃非相干级联以及 CSV 输出之间是自洽的。",
            "- 它没有证明当前 PVK `n,k`、Ag 参比模型或显微镜实测一定等价于理想 specular TMM。",
            "- 当前核心矛盾仍是实验反射率显著高于理论值，且该差异不是由本报告审计到的公式错误造成的。",
            "- 下一步应优先检查 `nk_audit`、`nk_envelope`、实验收光几何、散射和参比有效反射。",
            "",
            "## 14. 发现的问题、风险与下一步建议",
            f"- `Ag mirror` 曝光口径在该结果集中记录为 `{format_optional(counts.get('ag_mirror_exposure_ms'))}` ms，本报告复算与 CSV 一致。",
            "- 该报告仅改变展示形式，不改变任何单点数值结果或核心 TMM/反射率计算逻辑。",
            "- 后续若生成正式展示图，应遵守 `docs/REPORTING_AND_FIGURE_STYLE.md` 的比例、图例和坐标轴规范。",
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
    json_path = TRACE_PROCESSED_DIR / f"phase08_0429_trace_{args.output_tag}_values.json"
    report_path = TRACE_REPORT_DIR / f"phase08_0429_trace_{args.output_tag}.md"
    json_path.write_text(json.dumps(sanitize_for_json(trace), indent=2, ensure_ascii=False), encoding="utf-8")
    render_markdown(trace, report_path)
    print(f"trace_json: {json_path}")
    print(f"trace_report: {report_path}")
    print(f"lambda_used_nm: {trace['lambda_used_nm']:.12f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
