"""Phase 03 多位置样品批量校准与六参数拟合脚本。

本脚本不修改 step01 / step02 主流程源码，而是通过模块导入复用：
1. step01 的绝对反射率标定辅助函数
2. step02 的六参数 TMM 拟合引擎

输入：
- OneDrive 原始样品目录下的多个 CSV（Wavelength / Intensity）
- test_data/Ag-mirro.csv
- resources/GCC-1022系列xlsx.xlsx
- resources/ITO_20 Ohm_105 nm_e1e2.mat
- data/processed/CsFAPI_nk_extended.csv

输出：
- 仓库内单样品对照图
- 仓库内单样品拟合曲线 CSV
- 仓库内长表 / 透视表汇总 CSV
- OneDrive 侧镜像输出
"""

from __future__ import annotations

import importlib.util
import re
import shutil
from pathlib import Path
from types import ModuleType

import matplotlib
import numpy as np
import pandas as pd
from lmfit import Parameters, minimize
from scipy.signal import savgol_filter

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ONEDRIVE_SAMPLE_DIR = Path(
    "/Users/luxin/Library/CloudStorage/OneDrive-共享的库-onedrive/Data/PL/2026/0403/cor/data-0403"
)
ONEDRIVE_OUTPUT_DIR = ONEDRIVE_SAMPLE_DIR / "batch-fit-results"


def load_module(module_name: str, script_path: Path) -> ModuleType:
    """从脚本路径动态导入模块，避免修改既有单样品脚本。"""
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法为脚本创建导入 spec: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_project_root() -> Path:
    """根据当前脚本位置反推出项目根目录。"""
    return Path(__file__).resolve().parents[2]


def parse_sample_identifiers(file_path: Path, seen_sample_ids: dict[str, int]) -> tuple[str, str]:
    """从文件名中解析样品 ID 和唯一 sample_key。"""
    match = re.match(
        r"^(good|bad)-(\d+)-glass-700-1250nm-100ms-850lp(?:-(\d+))?\s+"
        r"\d{4}\s+\S+\s+\d+\s+(\d{2})_(\d{2})_(\d{2})-+cor\.csv$",
        file_path.name,
    )
    if match is None:
        raise ValueError(f"无法按既定规则解析样品文件名: {file_path.name}")

    quality, batch_id, replicate, hour, minute, second = match.groups()
    replicate_id = replicate or "1"
    sample_id = f"{quality}-{batch_id}-{replicate_id}"
    time_suffix = f"{hour}{minute}{second}"

    seen_sample_ids[sample_id] = seen_sample_ids.get(sample_id, 0) + 1
    if seen_sample_ids[sample_id] > 1:
        sample_key = f"{sample_id}__{time_suffix}"
    else:
        sample_key = sample_id
    return sample_id, sample_key


def compute_absolute_reflectance(
    sample_csv: Path,
    mirror_wavelength_nm: np.ndarray,
    mirror_signal_raw: np.ndarray,
    excel_wavelength_nm: np.ndarray,
    excel_reflectance: np.ndarray,
    step01: ModuleType,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """复用 step01 辅助函数，将原始样品计数转换为绝对反射率。"""
    sample_wavelength_raw, sample_signal_raw = step01.load_csv_spectrum(sample_csv)
    sample_wavelength_nm, sample_signal = step01.crop_spectrum(sample_wavelength_raw, sample_signal_raw)

    if sample_wavelength_nm.size == 0:
        raise ValueError("样品在 850-1100 nm 内无有效数据。")

    step01.validate_interp_domain(sample_wavelength_nm, mirror_wavelength_nm, "银镜 CSV")
    step01.validate_interp_domain(sample_wavelength_nm, excel_wavelength_nm, "银镜 Excel 基准")

    mirror_signal_on_grid = np.interp(sample_wavelength_nm, mirror_wavelength_nm, mirror_signal_raw)
    mirror_reflectance_on_grid = np.interp(sample_wavelength_nm, excel_wavelength_nm, excel_reflectance)
    mirror_signal_norm = mirror_signal_on_grid * (
        step01.SAMPLE_EXPOSURE_MS / step01.MIRROR_EXPOSURE_MS
    )

    if np.any(np.isclose(mirror_signal_norm, 0.0)):
        raise ValueError("归一化后的银镜信号存在接近 0 的点，无法完成绝对反射率换算。")

    reflectance_raw = (sample_signal / mirror_signal_norm) * mirror_reflectance_on_grid
    savgol_window = step01.compute_valid_savgol_window(
        size=reflectance_raw.size,
        desired_window=step01.DEFAULT_SAVGOL_WINDOW,
        polyorder=step01.DEFAULT_SAVGOL_POLYORDER,
    )
    reflectance_smooth = savgol_filter(
        reflectance_raw,
        window_length=savgol_window,
        polyorder=step01.DEFAULT_SAVGOL_POLYORDER,
    )
    return sample_wavelength_nm, reflectance_raw, reflectance_smooth


def build_material_interpolators(step02: ModuleType, project_root: Path):
    """预加载 ITO / PVK 色散，避免每个样品重复解析资源文件。"""
    pvk_csv = project_root / "data" / "processed" / "CsFAPI_nk_extended.csv"
    ito_path = project_root / "resources" / "ITO_20 Ohm_105 nm_e1e2.mat"

    ito_wavelength_nm, ito_e1, ito_e2 = step02.load_ito_dispersion(ito_path)
    ito_nk = step02.convert_dielectric_to_nk(ito_e1, ito_e2)
    get_ito_nk = step02.build_ito_interpolator(ito_wavelength_nm, ito_nk)

    pvk_wavelength_nm, pvk_n, pvk_k = step02.load_pvk_dispersion(pvk_csv)
    get_pvk_nk = step02.build_pvk_interpolator(pvk_wavelength_nm, pvk_n, pvk_k)
    return get_ito_nk, get_pvk_nk


def build_default_params(step02: ModuleType) -> Parameters:
    """构造与 step02 主流程一致的六参数初值与边界。"""
    params = Parameters()
    params.add(
        "d_bulk",
        value=step02.INITIAL_PVK_BULK_THICKNESS_NM,
        min=step02.MIN_PVK_BULK_THICKNESS_NM,
        max=step02.MAX_PVK_BULK_THICKNESS_NM,
    )
    params.add(
        "d_rough",
        value=step02.INITIAL_PVK_ROUGHNESS_THICKNESS_NM,
        min=step02.MIN_PVK_ROUGHNESS_THICKNESS_NM,
        max=step02.MAX_PVK_ROUGHNESS_THICKNESS_NM,
    )
    params.add(
        "ito_alpha",
        value=step02.INITIAL_ITO_ALPHA,
        min=step02.MIN_ITO_ALPHA,
        max=step02.MAX_ITO_ALPHA,
    )
    params.add(
        "sigma_thickness",
        value=step02.INITIAL_THICKNESS_SIGMA_NM,
        min=step02.MIN_THICKNESS_SIGMA_NM,
        max=step02.MAX_THICKNESS_SIGMA_NM,
    )
    params.add(
        "pvk_b_scale",
        value=step02.INITIAL_PVK_B_SCALE,
        min=step02.MIN_PVK_B_SCALE,
        max=step02.MAX_PVK_B_SCALE,
    )
    params.add(
        "niox_k",
        value=step02.INITIAL_NIOX_K,
        min=step02.MIN_NIOX_K,
        max=step02.MAX_NIOX_K,
    )
    return params


def plot_batch_fit_result(
    wavelength_nm: np.ndarray,
    reflectance_raw: np.ndarray,
    reflectance_smooth: np.ndarray,
    reflectance_fit: np.ndarray,
    result_row: dict[str, object],
    output_path: Path,
) -> None:
    """绘制原始散点与六参数拟合曲线对照图。"""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    ax.scatter(
        wavelength_nm,
        reflectance_raw * 100.0,
        color="#9e9e9e",
        s=12,
        alpha=0.55,
        label="Measured Raw Points",
    )
    ax.plot(
        wavelength_nm,
        reflectance_smooth * 100.0,
        color="gray",
        linewidth=2.0,
        alpha=0.85,
        label="Measured Smooth",
    )
    ax.plot(
        wavelength_nm,
        reflectance_fit * 100.0,
        color="#1565c0",
        linewidth=2.0,
        linestyle="--",
        label="Best TMM Fit",
    )

    textbox = (
        f"{result_row['sample_key']}\n"
        f"d_bulk = {result_row['d_bulk_nm']:.1f} nm\n"
        f"d_rough = {result_row['d_rough_nm']:.1f} nm\n"
        f"d_total = {result_row['d_total_nm']:.1f} nm\n"
        f"ITO IR Alpha = {result_row['ito_alpha']:.3f}\n"
        f"Thickness Sigma = {result_row['sigma_thickness_nm']:.1f} nm\n"
        f"PVK B-Scale = {result_row['pvk_b_scale']:.3f}\n"
        f"NiOx k = {result_row['niox_k']:.4f}\n"
        f"Chi-Square = {result_row['chisqr']:.4f}"
    )
    ax.text(
        0.03,
        0.97,
        textbox,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85, "edgecolor": "#666666"},
    )

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Absolute Reflectance (%)")
    ax.set_title(f"Phase 03 Batch Fit: {result_row['sample_key']}")
    ax.set_xlim(float(wavelength_nm.min()), float(wavelength_nm.max()))
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def export_curve_csv(
    output_path: Path,
    wavelength_nm: np.ndarray,
    reflectance_raw: np.ndarray,
    reflectance_smooth: np.ndarray,
    reflectance_fit: np.ndarray,
) -> None:
    """导出单样品拟合曲线 CSV。"""
    residual = reflectance_fit - reflectance_smooth
    curve_df = pd.DataFrame(
        {
            "Wavelength": wavelength_nm,
            "R_measured_raw": reflectance_raw,
            "R_measured_smooth": reflectance_smooth,
            "R_fit": reflectance_fit,
            "Residual": residual,
        }
    )
    curve_df.to_csv(output_path, index=False)


def copy_outputs_to_onedrive(
    repo_figure_dir: Path,
    repo_curve_dir: Path,
    repo_log_dir: Path,
    onedrive_output_root: Path,
) -> None:
    """将仓库内结果镜像复制到 OneDrive 目录。"""
    onedrive_figure_dir = onedrive_output_root / "figures"
    onedrive_curve_dir = onedrive_output_root / "fitted_csv"
    onedrive_summary_dir = onedrive_output_root / "summary"

    onedrive_figure_dir.mkdir(parents=True, exist_ok=True)
    onedrive_curve_dir.mkdir(parents=True, exist_ok=True)
    onedrive_summary_dir.mkdir(parents=True, exist_ok=True)

    for source_file in repo_figure_dir.glob("*.png"):
        shutil.copy2(source_file, onedrive_figure_dir / source_file.name)
    for source_file in repo_curve_dir.glob("*.csv"):
        shutil.copy2(source_file, onedrive_curve_dir / source_file.name)
    for source_file in repo_log_dir.glob("*.csv"):
        shutil.copy2(source_file, onedrive_summary_dir / source_file.name)


def main() -> None:
    project_root = get_project_root()
    step01 = load_module("step01_absolute_calibration", project_root / "src" / "scripts" / "step01_absolute_calibration.py")
    step02 = load_module("step02_tmm_inversion", project_root / "src" / "scripts" / "step02_tmm_inversion.py")

    sample_files = sorted(
        [
            file_path
            for file_path in ONEDRIVE_SAMPLE_DIR.glob("*.csv")
            if file_path.is_file() and file_path.suffix.lower() == ".csv"
        ]
    )
    if not sample_files:
        raise FileNotFoundError(f"未在目录中找到样品 CSV: {ONEDRIVE_SAMPLE_DIR}")

    repo_figure_dir = project_root / "results" / "figures" / "phase03_batch_fit"
    repo_curve_dir = project_root / "data" / "processed" / "phase03_batch_fit"
    repo_log_dir = project_root / "results" / "logs" / "phase03_batch_fit"
    repo_figure_dir.mkdir(parents=True, exist_ok=True)
    repo_curve_dir.mkdir(parents=True, exist_ok=True)
    repo_log_dir.mkdir(parents=True, exist_ok=True)

    mirror_csv = project_root / "test_data" / "Ag-mirro.csv"
    reference_excel = project_root / "resources" / "GCC-1022系列xlsx.xlsx"
    mirror_wavelength_raw, mirror_signal_raw = step01.load_csv_spectrum(mirror_csv)
    mirror_wavelength_nm, mirror_signal = step01.crop_spectrum(mirror_wavelength_raw, mirror_signal_raw)
    excel_wavelength_raw, excel_reflectance_raw = step01.load_excel_reference(reference_excel)
    excel_wavelength_nm, excel_reflectance = step01.crop_spectrum(excel_wavelength_raw, excel_reflectance_raw)

    get_ito_nk, get_pvk_nk = build_material_interpolators(step02, project_root)

    summary_rows: list[dict[str, object]] = []
    seen_sample_ids: dict[str, int] = {}

    print(f"批处理开始，共检测到 {len(sample_files)} 个样品 CSV。")
    for sample_file in sample_files:
        sample_id = ""
        sample_key = ""
        try:
            sample_id, sample_key = parse_sample_identifiers(sample_file, seen_sample_ids)
            wavelength_nm, reflectance_raw, reflectance_smooth = compute_absolute_reflectance(
                sample_file,
                mirror_wavelength_nm,
                mirror_signal,
                excel_wavelength_nm,
                excel_reflectance,
                step01,
            )

            step02.validate_interp_domain(wavelength_nm, mirror_wavelength_nm, "银镜 CSV")
            params = build_default_params(step02)
            result = minimize(
                step02.residual,
                params,
                args=(wavelength_nm, reflectance_smooth, get_ito_nk, get_pvk_nk),
                method="leastsq",
            )

            d_bulk_nm = float(result.params["d_bulk"].value)
            d_rough_nm = float(result.params["d_rough"].value)
            d_total_nm = d_bulk_nm + d_rough_nm
            ito_alpha = float(result.params["ito_alpha"].value)
            sigma_thickness_nm = float(result.params["sigma_thickness"].value)
            pvk_b_scale = float(result.params["pvk_b_scale"].value)
            niox_k = float(result.params["niox_k"].value)
            reflectance_fit = step02.calc_macro_reflectance(
                d_bulk_nm,
                d_rough_nm,
                ito_alpha,
                sigma_thickness_nm,
                pvk_b_scale,
                niox_k,
                wavelength_nm,
                get_ito_nk,
                get_pvk_nk,
            )

            if np.any(~np.isfinite(reflectance_fit)):
                raise ValueError("拟合曲线中出现 NaN 或 Inf。")

            result_row = {
                "sample_key": sample_key,
                "sample_id": sample_id,
                "source_filename": sample_file.name,
                "d_bulk_nm": d_bulk_nm,
                "d_rough_nm": d_rough_nm,
                "d_total_nm": d_total_nm,
                "ito_alpha": ito_alpha,
                "sigma_thickness_nm": sigma_thickness_nm,
                "pvk_b_scale": pvk_b_scale,
                "niox_k": niox_k,
                "chisqr": float(result.chisqr),
                "success": bool(result.success),
                "nfev": int(result.nfev),
                "error_message": "",
            }
            summary_rows.append(result_row)

            figure_output = repo_figure_dir / f"{sample_key}.png"
            curve_output = repo_curve_dir / f"{sample_key}.csv"
            plot_batch_fit_result(
                wavelength_nm,
                reflectance_raw,
                reflectance_smooth,
                reflectance_fit,
                result_row,
                figure_output,
            )
            export_curve_csv(
                curve_output,
                wavelength_nm,
                reflectance_raw,
                reflectance_smooth,
                reflectance_fit,
            )
            print(
                f"[OK] {sample_key}: d_bulk={d_bulk_nm:.2f} nm, "
                f"d_total={d_total_nm:.2f} nm, chisqr={float(result.chisqr):.6f}"
            )
        except Exception as exc:
            fallback_key = sample_key or sample_file.stem
            summary_rows.append(
                {
                    "sample_key": fallback_key,
                    "sample_id": sample_id,
                    "source_filename": sample_file.name,
                    "d_bulk_nm": np.nan,
                    "d_rough_nm": np.nan,
                    "d_total_nm": np.nan,
                    "ito_alpha": np.nan,
                    "sigma_thickness_nm": np.nan,
                    "pvk_b_scale": np.nan,
                    "niox_k": np.nan,
                    "chisqr": np.nan,
                    "success": False,
                    "nfev": np.nan,
                    "error_message": str(exc),
                }
            )
            print(f"[FAIL] {fallback_key}: {exc}")

    summary_df = pd.DataFrame(summary_rows)
    summary_columns = [
        "sample_key",
        "sample_id",
        "source_filename",
        "d_bulk_nm",
        "d_rough_nm",
        "d_total_nm",
        "ito_alpha",
        "sigma_thickness_nm",
        "pvk_b_scale",
        "niox_k",
        "chisqr",
        "success",
        "nfev",
        "error_message",
    ]
    summary_df = summary_df[summary_columns]

    summary_output = repo_log_dir / "phase03_batch_fit_summary.csv"
    pivot_output = repo_log_dir / "phase03_batch_fit_pivot.csv"
    summary_df.to_csv(summary_output, index=False)

    success_df = summary_df[summary_df["success"] == True].copy()
    pivot_source = success_df.set_index("sample_key")[
        [
            "d_bulk_nm",
            "d_rough_nm",
            "d_total_nm",
            "ito_alpha",
            "sigma_thickness_nm",
            "pvk_b_scale",
            "niox_k",
            "chisqr",
        ]
    ]
    pivot_df = pivot_source.transpose()
    pivot_df.index.name = "parameter"
    pivot_df.to_csv(pivot_output)

    copy_outputs_to_onedrive(repo_figure_dir, repo_curve_dir, repo_log_dir, ONEDRIVE_OUTPUT_DIR)

    print(f"批处理完成：成功 {int(success_df.shape[0])} / 总计 {len(summary_df)}")
    print(f"仓库内图像目录: {repo_figure_dir}")
    print(f"仓库内拟合 CSV 目录: {repo_curve_dir}")
    print(f"仓库内汇总目录: {repo_log_dir}")
    print(f"OneDrive 输出目录: {ONEDRIVE_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
