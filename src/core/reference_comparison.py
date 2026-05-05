"""Phase 08 glass/PVK vs glass/Ag reference comparison core."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import re

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from tmm import coh_tmm

from core import hdr_absolute_calibration as hdr


@dataclass(frozen=True)
class RuntimeConfig:
    sample_csv: Path
    reference_csv: Path
    nk_csv: Path
    output_processed_dir: Path
    output_figures_dir: Path
    output_logs_dir: Path
    output_report_dir: Path
    d_ag_nm: float
    d_pvk_fixed_nm: float
    d_pvk_scan_min_nm: float
    d_pvk_scan_max_nm: float
    d_pvk_scan_step_nm: float
    primary_min_nm: float
    primary_max_nm: float
    extended_min_nm: float
    extended_max_nm: float
    smooth_for_plot: bool
    smooth_window: int
    smooth_polyorder: int
    reference_type: str
    comparison_mode: str
    ag_mirror_csv: Path | None
    background_csv: Path | None
    drop_ag_frames: tuple[int, ...]
    ag_background_align: str
    ag_reference_model: str
    review_min_nm: float
    review_max_nm: float
    output_tag: str | None


def parse_range(text: str) -> tuple[float, float]:
    parts = str(text).split("-")
    if len(parts) != 2:
        raise ValueError(f"波段参数格式错误，期望 min-max，实际为: {text}")
    start = float(parts[0].strip())
    end = float(parts[1].strip())
    if not (start < end):
        raise ValueError(f"波段参数无效，要求 min < max，实际为: {text}")
    return start, end


def parse_exposure_ms_from_filename(path: Path) -> tuple[float | None, str]:
    name = path.name
    value = hdr.parse_exposure_ms_from_name(name)
    if value is None:
        return None, "unknown"
    return float(value), "filename_inference"


def tag_output_stem(base_stem: str, output_tag: str | None) -> str:
    if output_tag is None or str(output_tag).strip() == "":
        return base_stem
    return f"{base_stem}_{str(output_tag).strip()}"


def load_measurement_csv(path: Path) -> pd.DataFrame:
    wavelength_nm, intensity = hdr.load_csv_spectrum(path)
    frame = pd.DataFrame(
        {
            "Wavelength_nm": wavelength_nm.astype(float),
            "Counts": intensity.astype(float),
        }
    )
    return frame


def load_multiframe_spectrum_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, header=None)
    if frame.shape[1] < 6:
        raise ValueError(f"{path} 多帧 CSV 列数不足，至少需要 6 列。")
    out = pd.DataFrame(
        {
            "Frame_Index": pd.to_numeric(frame.iloc[:, 1], errors="coerce"),
            "Wavelength_nm": pd.to_numeric(frame.iloc[:, 2], errors="coerce"),
            "Pixel_Index": pd.to_numeric(frame.iloc[:, 4], errors="coerce"),
            "Counts": pd.to_numeric(frame.iloc[:, 5], errors="coerce"),
        }
    )
    if out.isna().any().any():
        raise ValueError(f"{path} 存在无法解析为数值的关键列。")
    out["Frame_Index"] = out["Frame_Index"].astype(int)
    out["Pixel_Index"] = out["Pixel_Index"].astype(int)
    return out


def calc_stack_reflectance_air_ag_air(
    wavelength_nm: np.ndarray,
    n_ag: np.ndarray,
    d_ag_nm: float,
) -> np.ndarray:
    output = np.zeros_like(wavelength_nm, dtype=float)
    for idx, lam in enumerate(wavelength_nm):
        n_list = [1.0 + 0.0j, complex(n_ag[idx]), 1.0 + 0.0j]
        d_list = [np.inf, float(d_ag_nm), np.inf]
        output[idx] = float(coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(lam))["R"])
    return output


def _frame_qc(frame_df: pd.DataFrame, label: str, used_frames: set[int]) -> pd.DataFrame:
    grouped = (
        frame_df.groupby("Frame_Index", as_index=False)
        .agg(
            Point_Count=("Counts", "size"),
            Counts_Min=("Counts", "min"),
            Counts_Median=("Counts", "median"),
            Counts_Mean=("Counts", "mean"),
            Counts_Max=("Counts", "max"),
            Saturated_65535_Count=("Counts", lambda s: int(np.count_nonzero(np.asarray(s) >= 65535))),
        )
        .sort_values("Frame_Index")
    )
    grouped["Source"] = label
    grouped["Used_For_Average"] = grouped["Frame_Index"].isin(used_frames)
    return grouped


def build_ag_mirror_corrected_spectrum(
    ag_csv: Path,
    bk_csv: Path,
    drop_frames: tuple[int, ...],
    align_mode: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if align_mode != "pixel":
        raise ValueError("首版仅支持 ag_background_align=pixel。")
    ag = load_multiframe_spectrum_csv(ag_csv)
    bk = load_multiframe_spectrum_csv(bk_csv)

    ag_frames = sorted(ag["Frame_Index"].unique().tolist())
    bk_frames = sorted(bk["Frame_Index"].unique().tolist())
    ag_use_frames = [x for x in ag_frames if x not in set(drop_frames)]
    if len(ag_use_frames) == 0:
        raise ValueError("Ag 可用帧为空。")

    ag_filtered = ag[ag["Frame_Index"].isin(ag_use_frames)].copy()
    ag_pixels = sorted(ag_filtered["Pixel_Index"].unique().tolist())
    bk_pixels = sorted(bk["Pixel_Index"].unique().tolist())
    if ag_pixels != bk_pixels:
        raise ValueError("Ag 与 bk 的 Pixel_Index 集合不一致，无法按 pixel 对齐背景扣除。")

    ag_wl_by_pixel = ag_filtered.groupby("Pixel_Index")["Wavelength_nm"].median().sort_index()
    bk_wl_by_pixel = bk.groupby("Pixel_Index")["Wavelength_nm"].median().sort_index()
    wl_diff = (bk_wl_by_pixel - ag_wl_by_pixel).to_numpy(dtype=float)

    ag_mean_by_pixel = ag_filtered.groupby("Pixel_Index")["Counts"].mean().sort_index()
    bk_mean_by_pixel = bk.groupby("Pixel_Index")["Counts"].mean().sort_index()
    corrected = ag_mean_by_pixel - bk_mean_by_pixel

    corrected_df = pd.DataFrame(
        {
            "Wavelength": ag_wl_by_pixel.to_numpy(dtype=float),
            "Intensity": corrected.to_numpy(dtype=float),
        }
    )
    qc_df = pd.concat(
        [
            _frame_qc(ag, "Ag", set(ag_use_frames)),
            _frame_qc(bk, "BK", set(bk_frames)),
        ],
        ignore_index=True,
    )
    diagnostics = {
        "ag_frame_count_total": len(ag_frames),
        "ag_frames_used": ag_use_frames,
        "ag_frames_dropped": list(drop_frames),
        "bk_frame_count_total": len(bk_frames),
        "pixel_count": len(ag_pixels),
        "bk_wavelength_offset_min_nm": float(np.min(wl_diff)),
        "bk_wavelength_offset_median_nm": float(np.median(wl_diff)),
        "bk_wavelength_offset_max_nm": float(np.max(wl_diff)),
    }
    return corrected_df, qc_df, diagnostics


def load_nk_table(nk_csv: Path) -> pd.DataFrame:
    frame = pd.read_csv(nk_csv)
    required = [
        "Wavelength_nm",
        "n_Glass",
        "k_Glass",
        "n_PVK",
        "k_PVK",
        "n_Ag",
        "k_Ag",
    ]
    missing = [c for c in required if c not in frame.columns]
    if missing:
        raise ValueError(f"{nk_csv} 缺少必要列: {missing}")
    return frame


def interpolate_complex(
    wavelength_query_nm: np.ndarray,
    wavelength_base_nm: np.ndarray,
    real_base: np.ndarray,
    imag_base: np.ndarray,
) -> np.ndarray:
    real_interp = np.interp(wavelength_query_nm, wavelength_base_nm, real_base)
    imag_interp = np.interp(wavelength_query_nm, wavelength_base_nm, imag_base)
    return real_interp + 1j * imag_interp


def front_surface_reflectance(glass_nk: np.ndarray) -> np.ndarray:
    n_air = 1.0 + 0.0j
    reflection = (n_air - glass_nk) / (n_air + glass_nk)
    return np.abs(reflection) ** 2


def calc_stack_reflectance_glass_ag(
    wavelength_nm: np.ndarray,
    n_glass: np.ndarray,
    n_ag: np.ndarray,
    d_ag_nm: float,
) -> np.ndarray:
    output = np.zeros_like(wavelength_nm, dtype=float)
    for idx, lam in enumerate(wavelength_nm):
        n_list = [complex(n_glass[idx]), complex(n_ag[idx]), 1.0 + 0.0j]
        d_list = [np.inf, float(d_ag_nm), np.inf]
        output[idx] = float(coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(lam))["R"])
    return output


def calc_stack_reflectance_glass_pvk(
    wavelength_nm: np.ndarray,
    n_glass: np.ndarray,
    n_pvk: np.ndarray,
    d_pvk_nm: float,
) -> np.ndarray:
    output = np.zeros_like(wavelength_nm, dtype=float)
    for idx, lam in enumerate(wavelength_nm):
        n_list = [complex(n_glass[idx]), complex(n_pvk[idx]), 1.0 + 0.0j]
        d_list = [np.inf, float(d_pvk_nm), np.inf]
        output[idx] = float(coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(lam))["R"])
    return output


def calc_macro_reflectance(r_front: np.ndarray, r_stack: np.ndarray) -> np.ndarray:
    t_front = 1.0 - r_front
    denom = 1.0 - r_front * r_stack
    if np.any(np.isclose(denom, 0.0)):
        raise ValueError("非相干级联分母接近 0，无法稳定计算。")
    return r_front + (t_front**2) * r_stack / denom


def build_masks(counts_sample: np.ndarray, counts_ref: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    finite_mask = np.isfinite(counts_sample) & np.isfinite(counts_ref)
    loose_mask = finite_mask & (counts_sample > 0.0) & (counts_ref > 0.0)
    min_negative = 0.0
    negatives = np.concatenate([counts_sample[counts_sample < 0.0], counts_ref[counts_ref < 0.0]])
    if negatives.size > 0:
        min_negative = float(np.min(negatives))
    floor = max(10.0, 5.0 * abs(min_negative))
    strict_mask = finite_mask & (counts_sample > floor) & (counts_ref > floor)
    return loose_mask, strict_mask, float(floor)


def build_mask_reason(
    counts_sample: np.ndarray,
    counts_ref: np.ndarray,
    finite_mask: np.ndarray,
    loose_mask: np.ndarray,
    strict_mask: np.ndarray,
    floor: float,
) -> list[str]:
    reasons: list[str] = []
    for idx in range(counts_sample.size):
        if not finite_mask[idx]:
            reasons.append("non_finite")
            continue
        if not loose_mask[idx]:
            if counts_sample[idx] <= 0.0 and counts_ref[idx] <= 0.0:
                reasons.append("sample_ref_nonpositive")
            elif counts_sample[idx] <= 0.0:
                reasons.append("sample_nonpositive")
            else:
                reasons.append("ref_nonpositive")
            continue
        if not strict_mask[idx]:
            if counts_sample[idx] <= floor and counts_ref[idx] <= floor:
                reasons.append("sample_ref_below_floor")
            elif counts_sample[idx] <= floor:
                reasons.append("sample_below_floor")
            else:
                reasons.append("ref_below_floor")
            continue
        reasons.append("ok")
    return reasons


def fit_diagnostic_scale_offset(y_exp: np.ndarray, y_tmm: np.ndarray) -> tuple[float, float]:
    def model(x: np.ndarray, a: float, b: float) -> np.ndarray:
        return a * x + b

    (a, b), _ = curve_fit(model, y_tmm, y_exp, p0=(1.0, 0.0), maxfev=20000)
    return float(a), float(b)


def band_metrics(y_exp: np.ndarray, y_model: np.ndarray) -> dict[str, float]:
    residual = y_exp - y_model
    mae = float(np.mean(np.abs(residual)))
    rmse = float(np.sqrt(np.mean(residual**2)))
    bias = float(np.mean(residual))
    max_abs = float(np.max(np.abs(residual)))
    if y_exp.size < 2 or np.std(y_exp) < 1e-15 or np.std(y_model) < 1e-15:
        corr = 0.0
    else:
        corr = float(np.corrcoef(y_exp, y_model)[0, 1])
    return {
        "MAE": mae,
        "RMSE": rmse,
        "Mean_Bias": bias,
        "Max_Abs_Error": max_abs,
        "Pearson_Correlation": corr,
    }


def collect_band_rows(
    wavelength_nm: np.ndarray,
    strict_mask: np.ndarray,
    y_exp: np.ndarray,
    y_fixed: np.ndarray,
    y_best: np.ndarray,
    bands: list[tuple[str, float, float]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for band_name, band_min, band_max in bands:
        band_mask = strict_mask & (wavelength_nm >= band_min) & (wavelength_nm <= band_max)
        if np.count_nonzero(band_mask) == 0:
            continue
        fixed_m = band_metrics(y_exp[band_mask], y_fixed[band_mask])
        best_m = band_metrics(y_exp[band_mask], y_best[band_mask])
        rows.append(
            {
                "Band": band_name,
                "Wavelength_Min_nm": band_min,
                "Wavelength_Max_nm": band_max,
                "Point_Count_Strict": int(np.count_nonzero(band_mask)),
                "Model": "fixed",
                **fixed_m,
            }
        )
        rows.append(
            {
                "Band": band_name,
                "Wavelength_Min_nm": band_min,
                "Wavelength_Max_nm": band_max,
                "Point_Count_Strict": int(np.count_nonzero(band_mask)),
                "Model": "best_d",
                **best_m,
            }
        )
    return rows


def run_reference_comparison(config: RuntimeConfig, dry_run: bool = False) -> dict[str, Any]:
    if config.reference_type != "glass_ag":
        raise ValueError("第一版仅支持 reference_type=glass_ag")
    if config.comparison_mode not in {"single_reference", "dual_reference"}:
        raise ValueError("comparison_mode 仅支持 single_reference / dual_reference。")

    sample_exposure_ms, sample_exposure_source = parse_exposure_ms_from_filename(config.sample_csv)
    ref_exposure_ms, ref_exposure_source = parse_exposure_ms_from_filename(config.reference_csv)
    if sample_exposure_ms is None or ref_exposure_ms is None:
        raise ValueError("无法从文件名推断曝光时间，请先确保文件名包含 ms/us/s。")
    ag_mirror_exposure_ms: float | None = None
    ag_mirror_exposure_source: str | None = None

    sample_df = load_measurement_csv(config.sample_csv)
    ref_df = load_measurement_csv(config.reference_csv)
    if sample_df.shape[0] != ref_df.shape[0] or not np.allclose(
        sample_df["Wavelength_nm"].to_numpy(dtype=float),
        ref_df["Wavelength_nm"].to_numpy(dtype=float),
        atol=1e-9,
        rtol=0.0,
    ):
        raise ValueError("sample/reference 波长网格不一致。")

    wavelength_nm_raw = sample_df["Wavelength_nm"].to_numpy(dtype=float)
    counts_sample_raw = sample_df["Counts"].to_numpy(dtype=float)
    counts_ref_raw = ref_df["Counts"].to_numpy(dtype=float)

    ag_mirror_df: pd.DataFrame | None = None
    ag_qc_df: pd.DataFrame | None = None
    ag_diag: dict[str, Any] | None = None
    if config.comparison_mode == "dual_reference":
        if config.ag_mirror_csv is None or config.background_csv is None:
            raise ValueError("dual_reference 模式必须提供 ag_mirror_csv 和 background_csv。")
        ag_mirror_exposure_ms, ag_mirror_exposure_source = parse_exposure_ms_from_filename(config.ag_mirror_csv)
        if ag_mirror_exposure_ms is None:
            raise ValueError("无法从 Ag mirror 文件名推断曝光时间，请先确保文件名包含 ms/us/s。")
        ag_mirror_df, ag_qc_df, ag_diag = build_ag_mirror_corrected_spectrum(
            ag_csv=config.ag_mirror_csv,
            bk_csv=config.background_csv,
            drop_frames=config.drop_ag_frames,
            align_mode=config.ag_background_align,
        )

    nk = load_nk_table(config.nk_csv)
    nk_wl = nk["Wavelength_nm"].to_numpy(dtype=float)
    overlap_min = max(float(wavelength_nm_raw.min()), float(nk_wl.min()))
    overlap_max = min(float(wavelength_nm_raw.max()), float(nk_wl.max()))
    overlap_mask = (wavelength_nm_raw >= overlap_min) & (wavelength_nm_raw <= overlap_max)
    if np.count_nonzero(overlap_mask) < 10:
        raise ValueError("测量数据与 nk 数据的波长交集不足，无法计算。")

    wavelength_nm = wavelength_nm_raw[overlap_mask]
    counts_sample = counts_sample_raw[overlap_mask]
    counts_ref = counts_ref_raw[overlap_mask]
    counts_ag_mirror: np.ndarray | None = None
    if ag_mirror_df is not None:
        ag_wl = ag_mirror_df["Wavelength"].to_numpy(dtype=float)
        ag_counts = ag_mirror_df["Intensity"].to_numpy(dtype=float)
        if ag_wl.shape[0] != wavelength_nm_raw.shape[0] or not np.allclose(
            ag_wl,
            wavelength_nm_raw,
            atol=1e-6,
            rtol=0.0,
        ):
            raise ValueError("Ag mirror 校准谱与 sample 波长网格不一致。")
        counts_ag_mirror = ag_counts[overlap_mask]

    loose_mask, strict_mask, floor = build_masks(counts_sample, counts_ref)
    finite_mask = np.isfinite(counts_sample) & np.isfinite(counts_ref)
    mask_reason = build_mask_reason(
        counts_sample=counts_sample,
        counts_ref=counts_ref,
        finite_mask=finite_mask,
        loose_mask=loose_mask,
        strict_mask=strict_mask,
        floor=floor,
    )

    primary_mask = (wavelength_nm >= config.primary_min_nm) & (wavelength_nm <= config.primary_max_nm)
    extended_mask = (wavelength_nm >= config.extended_min_nm) & (wavelength_nm <= config.extended_max_nm)

    n_glass = interpolate_complex(
        wavelength_query_nm=wavelength_nm,
        wavelength_base_nm=nk_wl,
        real_base=nk["n_Glass"].to_numpy(dtype=float),
        imag_base=nk["k_Glass"].to_numpy(dtype=float),
    )
    n_ag = interpolate_complex(
        wavelength_query_nm=wavelength_nm,
        wavelength_base_nm=nk_wl,
        real_base=nk["n_Ag"].to_numpy(dtype=float),
        imag_base=nk["k_Ag"].to_numpy(dtype=float),
    )
    n_pvk = interpolate_complex(
        wavelength_query_nm=wavelength_nm,
        wavelength_base_nm=nk_wl,
        real_base=nk["n_PVK"].to_numpy(dtype=float),
        imag_base=nk["k_PVK"].to_numpy(dtype=float),
    )

    r_front = front_surface_reflectance(n_glass)
    r_stack_ag = calc_stack_reflectance_glass_ag(
        wavelength_nm=wavelength_nm,
        n_glass=n_glass,
        n_ag=n_ag,
        d_ag_nm=config.d_ag_nm,
    )
    r_tmm_glass_ag = calc_macro_reflectance(r_front=r_front, r_stack=r_stack_ag)
    r_tmm_ag_mirror = calc_stack_reflectance_air_ag_air(
        wavelength_nm=wavelength_nm,
        n_ag=n_ag,
        d_ag_nm=config.d_ag_nm,
    )

    counts_sample_ms = counts_sample / sample_exposure_ms
    counts_ref_ms = counts_ref / ref_exposure_ms
    safe_ratio = np.full_like(counts_sample_ms, np.nan)
    valid_ratio = counts_ref_ms > 0.0
    safe_ratio[valid_ratio] = counts_sample_ms[valid_ratio] / counts_ref_ms[valid_ratio]
    r_exp = safe_ratio * r_tmm_glass_ag
    counts_ag_mirror_ms: np.ndarray | None = None
    r_exp_ag_mirror: np.ndarray | None = None
    if counts_ag_mirror is not None:
        counts_ag_mirror_ms = counts_ag_mirror / ag_mirror_exposure_ms
        ag_ratio = np.full_like(counts_sample_ms, np.nan)
        valid_ag_ratio = counts_ag_mirror_ms > 0.0
        ag_ratio[valid_ag_ratio] = counts_sample_ms[valid_ag_ratio] / counts_ag_mirror_ms[valid_ag_ratio]
        r_exp_ag_mirror = ag_ratio * r_tmm_ag_mirror

    r_stack_pvk_fixed = calc_stack_reflectance_glass_pvk(
        wavelength_nm=wavelength_nm,
        n_glass=n_glass,
        n_pvk=n_pvk,
        d_pvk_nm=config.d_pvk_fixed_nm,
    )
    r_tmm_pvk_fixed = calc_macro_reflectance(r_front=r_front, r_stack=r_stack_pvk_fixed)

    scan_values = np.arange(
        config.d_pvk_scan_min_nm,
        config.d_pvk_scan_max_nm + 0.5 * config.d_pvk_scan_step_nm,
        config.d_pvk_scan_step_nm,
        dtype=float,
    )
    objective_mask = strict_mask & primary_mask & np.isfinite(r_exp)
    if np.count_nonzero(objective_mask) < 10:
        raise ValueError("strict mask 下主波段有效点不足，无法执行厚度拟合。")

    scan_cost = np.full(scan_values.shape, np.nan, dtype=float)
    best_idx = -1
    best_cost = np.inf
    best_curve = np.full_like(r_exp, np.nan)
    for idx, d_pvk in enumerate(scan_values):
        r_stack = calc_stack_reflectance_glass_pvk(
            wavelength_nm=wavelength_nm,
            n_glass=n_glass,
            n_pvk=n_pvk,
            d_pvk_nm=float(d_pvk),
        )
        r_curve = calc_macro_reflectance(r_front=r_front, r_stack=r_stack)
        residual = r_exp[objective_mask] - r_curve[objective_mask]
        cost = float(np.mean(residual**2))
        scan_cost[idx] = cost
        if cost < best_cost:
            best_cost = cost
            best_idx = idx
            best_curve = r_curve

    best_d_pvk_nm = float(scan_values[best_idx])
    r_tmm_pvk_best = best_curve

    residual_fixed = r_exp - r_tmm_pvk_fixed
    residual_best = r_exp - r_tmm_pvk_best

    diag_mask = objective_mask
    a_fixed, b_fixed = fit_diagnostic_scale_offset(r_exp[diag_mask], r_tmm_pvk_fixed[diag_mask])
    a_best, b_best = fit_diagnostic_scale_offset(r_exp[diag_mask], r_tmm_pvk_best[diag_mask])

    band_defs = [
        ("400_450", 400.0, 450.0),
        ("450_500", 450.0, 500.0),
        ("500_650", 500.0, 650.0),
        ("650_750", 650.0, 750.0),
        ("400_750_primary", config.primary_min_nm, config.primary_max_nm),
        ("750_931_extended_qc", config.extended_min_nm, config.extended_max_nm),
    ]
    metric_rows = collect_band_rows(
        wavelength_nm=wavelength_nm,
        strict_mask=strict_mask & np.isfinite(r_exp),
        y_exp=r_exp,
        y_fixed=r_tmm_pvk_fixed,
        y_best=r_tmm_pvk_best,
        bands=band_defs,
    )

    if dry_run:
        payload = {
            "mode": "dry_run",
            "sample_csv": str(config.sample_csv),
            "reference_csv": str(config.reference_csv),
            "comparison_mode": config.comparison_mode,
            "point_count": int(wavelength_nm.size),
            "strict_point_count_primary": int(np.count_nonzero(objective_mask)),
            "floor": float(floor),
            "sample_exposure_ms": sample_exposure_ms,
            "reference_exposure_ms": ref_exposure_ms,
            "sample_exposure_source": sample_exposure_source,
            "reference_exposure_source": ref_exposure_source,
        }
        if ag_diag is not None:
            payload["ag_background_diagnostics"] = ag_diag
        return payload

    config.output_processed_dir.mkdir(parents=True, exist_ok=True)
    config.output_figures_dir.mkdir(parents=True, exist_ok=True)
    config.output_logs_dir.mkdir(parents=True, exist_ok=True)
    config.output_report_dir.mkdir(parents=True, exist_ok=True)

    exposure_source = (
        sample_exposure_source
        if sample_exposure_source == ref_exposure_source
        else f"sample={sample_exposure_source};reference={ref_exposure_source}"
    )

    calibrated_df = pd.DataFrame(
        {
            "Wavelength_nm": wavelength_nm,
            "Glass_PVK_Counts": counts_sample,
            "Glass_Ag_Counts": counts_ref,
            "Glass_PVK_CountsPerMs": counts_sample_ms,
            "Glass_Ag_CountsPerMs": counts_ref_ms,
            "Valid_Loose": loose_mask,
            "Valid_Strict": strict_mask,
            "Mask_Reason": mask_reason,
            "Exposure_Source": np.full(wavelength_nm.size, exposure_source, dtype=object),
            "R_Exp_GlassPVK_by_GlassAg": r_exp,
            "R_TMM_GlassAg": r_tmm_glass_ag,
            "R_TMM_AgMirror": r_tmm_ag_mirror,
            "R_TMM_GlassPVK_Fixed": r_tmm_pvk_fixed,
            "R_TMM_GlassPVK_BestD": r_tmm_pvk_best,
            "Residual_Fixed": residual_fixed,
            "Residual_BestD": residual_best,
        }
    )
    if counts_ag_mirror is not None and counts_ag_mirror_ms is not None and r_exp_ag_mirror is not None:
        calibrated_df["Ag_Mirror_Corrected_Counts"] = counts_ag_mirror
        calibrated_df["Ag_Mirror_Corrected_CountsPerMs"] = counts_ag_mirror_ms
        calibrated_df["R_Exp_GlassPVK_by_AgMirror"] = r_exp_ag_mirror
        calibrated_df["Residual_Fixed_AgMirror"] = r_exp_ag_mirror - r_tmm_pvk_fixed
        calibrated_df["Residual_BestD_AgMirror"] = r_exp_ag_mirror - r_tmm_pvk_best
    theory_df = pd.DataFrame(
        {
            "Wavelength_nm": wavelength_nm,
            "R_TMM_GlassAg": r_tmm_glass_ag,
            "R_TMM_AgMirror": r_tmm_ag_mirror,
            "R_TMM_GlassPVK_Fixed": r_tmm_pvk_fixed,
            "R_TMM_GlassPVK_BestD": r_tmm_pvk_best,
        }
    )
    metrics_df = pd.DataFrame(metric_rows)
    inventory_df = pd.DataFrame(
        [
            {
                "sample_csv": config.sample_csv.as_posix(),
                "reference_csv": config.reference_csv.as_posix(),
                "reference_type": config.reference_type,
                "sample_exposure_ms": sample_exposure_ms,
                "reference_exposure_ms": ref_exposure_ms,
                "ag_mirror_exposure_ms": ag_mirror_exposure_ms,
                "sample_exposure_source": sample_exposure_source,
                "reference_exposure_source": ref_exposure_source,
                "ag_mirror_exposure_source": ag_mirror_exposure_source,
                "wavelength_min_nm_raw": float(np.min(wavelength_nm_raw)),
                "wavelength_max_nm_raw": float(np.max(wavelength_nm_raw)),
                "wavelength_min_nm_used": float(np.min(wavelength_nm)),
                "wavelength_max_nm_used": float(np.max(wavelength_nm)),
                "point_count": int(wavelength_nm.size),
                "strict_primary_point_count": int(np.count_nonzero(objective_mask)),
            }
        ]
    )
    scan_df = pd.DataFrame(
        {
            "d_PVK_nm": scan_values,
            "thickness_scan_cost": scan_cost,
        }
    )

    prefix = "phase08_0429_dual_reference" if config.comparison_mode == "dual_reference" else "phase08_0429"
    input_inventory_path = config.output_processed_dir / f"{tag_output_stem(f'{prefix}_input_inventory', config.output_tag)}.csv"
    calibrated_path = config.output_processed_dir / f"{tag_output_stem(f'{prefix}_calibrated_reflectance', config.output_tag)}.csv"
    theory_path = config.output_processed_dir / f"{tag_output_stem(f'{prefix}_tmm_theory_curves', config.output_tag)}.csv"
    metrics_path = config.output_processed_dir / f"{tag_output_stem(f'{prefix}_error_metrics', config.output_tag)}.csv"
    manifest_path = config.output_processed_dir / f"{tag_output_stem(f'{prefix}_manifest', config.output_tag)}.json"
    scan_path = config.output_processed_dir / f"{tag_output_stem(f'{prefix}_thickness_scan_cost', config.output_tag)}.csv"
    ag_mirror_path = config.output_processed_dir / f"{tag_output_stem('phase08_0429_ag_mirror_background_corrected', config.output_tag)}.csv"
    ag_qc_path = config.output_processed_dir / f"{tag_output_stem('phase08_0429_ag_mirror_frame_qc', config.output_tag)}.csv"

    inventory_df.to_csv(input_inventory_path, index=False, encoding="utf-8-sig")
    calibrated_df.to_csv(calibrated_path, index=False, encoding="utf-8-sig")
    theory_df.to_csv(theory_path, index=False, encoding="utf-8-sig")
    metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")
    scan_df.to_csv(scan_path, index=False, encoding="utf-8-sig")
    if ag_mirror_df is not None and ag_qc_df is not None:
        ag_mirror_df.to_csv(ag_mirror_path, index=False, encoding="utf-8-sig")
        ag_qc_df.to_csv(ag_qc_path, index=False, encoding="utf-8-sig")

    manifest = {
        "reference_type": config.reference_type,
        "comparison_mode": config.comparison_mode,
        "sample_csv": config.sample_csv.as_posix(),
        "reference_csv": config.reference_csv.as_posix(),
        "nk_csv": config.nk_csv.as_posix(),
        "output_tag": config.output_tag,
        "sample_exposure_ms": sample_exposure_ms,
        "reference_exposure_ms": ref_exposure_ms,
        "sample_exposure_source": sample_exposure_source,
        "reference_exposure_source": ref_exposure_source,
        "wavelength_min_nm_raw": float(np.min(wavelength_nm_raw)),
        "wavelength_max_nm_raw": float(np.max(wavelength_nm_raw)),
        "wavelength_min_nm_used": float(np.min(wavelength_nm)),
        "wavelength_max_nm_used": float(np.max(wavelength_nm)),
        "primary_range_nm": [config.primary_min_nm, config.primary_max_nm],
        "extended_qc_range_nm": [config.extended_min_nm, config.extended_max_nm],
        "valid_mask_loose": "finite && sample_counts>0 && reference_counts>0",
        "valid_mask_strict": f"finite && sample_counts>{floor} && reference_counts>{floor}",
        "strict_floor_counts": floor,
        "smoothing_enabled_for_metrics": False,
        "smoothing_enabled_for_plot": config.smooth_for_plot,
        "smoothing_window": config.smooth_window if config.smooth_for_plot else None,
        "smoothing_polyorder": config.smooth_polyorder if config.smooth_for_plot else None,
        "d_ag_nm_assumption": config.d_ag_nm,
        "ag_reference_model": config.ag_reference_model,
        "d_pvk_fixed_nm_assumption": config.d_pvk_fixed_nm,
        "d_pvk_scan_min_nm": config.d_pvk_scan_min_nm,
        "d_pvk_scan_max_nm": config.d_pvk_scan_max_nm,
        "d_pvk_scan_step_nm": config.d_pvk_scan_step_nm,
        "best_d_PVK_nm": best_d_pvk_nm,
        "diagnostic_scale_a_fixed": a_fixed,
        "diagnostic_offset_b_fixed": b_fixed,
        "diagnostic_scale_a_best_d": a_best,
        "diagnostic_offset_b_best_d": b_best,
        "review_range_nm": [config.review_min_nm, config.review_max_nm],
    }
    if ag_diag is not None:
        manifest["ag_background_diagnostics"] = ag_diag
        manifest["ag_mirror_csv"] = config.ag_mirror_csv.as_posix() if config.ag_mirror_csv else None
        manifest["background_csv"] = config.background_csv.as_posix() if config.background_csv else None
        manifest["ag_mirror_exposure_ms"] = ag_mirror_exposure_ms
        manifest["ag_mirror_exposure_source"] = ag_mirror_exposure_source
        manifest["ag_background_align"] = config.ag_background_align
        manifest["drop_ag_frames"] = list(config.drop_ag_frames)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "mode": "full_run",
        "manifest": manifest,
        "paths": {
            "input_inventory_csv": input_inventory_path.as_posix(),
            "calibrated_csv": calibrated_path.as_posix(),
            "theory_csv": theory_path.as_posix(),
            "metrics_csv": metrics_path.as_posix(),
            "thickness_scan_csv": scan_path.as_posix(),
            "manifest_json": manifest_path.as_posix(),
        },
        "arrays": {
            "wavelength_nm": wavelength_nm,
            "counts_sample": counts_sample,
            "counts_ref": counts_ref,
            "counts_sample_ms": counts_sample_ms,
            "counts_ref_ms": counts_ref_ms,
            "r_exp": r_exp,
            "r_tmm_glass_ag": r_tmm_glass_ag,
            "r_tmm_ag_mirror": r_tmm_ag_mirror,
            "r_tmm_pvk_fixed": r_tmm_pvk_fixed,
            "r_tmm_pvk_best": r_tmm_pvk_best,
            "r_exp_ag_mirror": r_exp_ag_mirror,
            "residual_fixed": residual_fixed,
            "residual_best": residual_best,
            "scan_values": scan_values,
            "scan_cost": scan_cost,
            "primary_mask": primary_mask,
            "extended_mask": extended_mask,
            "strict_mask": strict_mask,
        },
    }
