"""基于数字化 CsFAPI 光学常数的近红外柯西外推脚本。

本脚本读取 [LIT-0001] 数字化得到的 ITO/CsFAPI 折射率数据，
截取 750-1000 nm 透明窗口，用 Cauchy 模型外推到 1100 nm，
并将结果落盘为 step02 可直接消费的标准中间件。
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

matplotlib.use("Agg")
import matplotlib.pyplot as plt


SERIES_NAME = "ITO/CsFAPI"
QUANTITY_NAME = "n"
FIT_MIN_WAVELENGTH_NM = 750.0
FIT_MAX_WAVELENGTH_NM = 1000.0
EXTRAPOLATION_MAX_WAVELENGTH_NM = 1100.0
GRID_STEP_NM = 1.0


def get_project_root() -> Path:
    """根据脚本位置推导项目根目录。"""
    return Path(__file__).resolve().parents[2]


def cauchy_model(wavelength_nm: np.ndarray, a_param: float, b_param: float) -> np.ndarray:
    """Cauchy 色散模型，波长以 um 进入平方项以保持数值稳定。"""
    wavelength_um = np.asarray(wavelength_nm, dtype=np.float64) / 1000.0
    return a_param + b_param / (wavelength_um**2)


def load_digitized_csfapi_n(csv_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """读取 [LIT-0001] 的 ITO/CsFAPI 数字化折射率数据。"""
    if not csv_path.exists():
        raise FileNotFoundError(f"未找到数字化 CsFAPI 数据文件: {csv_path}")

    data = pd.read_csv(csv_path)
    required_columns = {"series", "quantity", "wavelength_nm", "value"}
    missing = required_columns.difference(data.columns)
    if missing:
        raise ValueError(f"数字化数据缺少必要列: {sorted(missing)}")

    selected = data[(data["series"] == SERIES_NAME) & (data["quantity"] == QUANTITY_NAME)].copy()
    if selected.empty:
        raise ValueError(
            "数字化数据中未找到 ITO/CsFAPI 的 n 曲线。"
            f"请检查 series={SERIES_NAME!r}, quantity={QUANTITY_NAME!r}。"
        )

    wavelength_nm = pd.to_numeric(selected["wavelength_nm"], errors="coerce").to_numpy(dtype=float)
    refractive_index = pd.to_numeric(selected["value"], errors="coerce").to_numpy(dtype=float)
    valid_mask = np.isfinite(wavelength_nm) & np.isfinite(refractive_index)
    wavelength_nm = wavelength_nm[valid_mask]
    refractive_index = refractive_index[valid_mask]

    sort_index = np.argsort(wavelength_nm)
    wavelength_nm = wavelength_nm[sort_index]
    refractive_index = refractive_index[sort_index]

    if wavelength_nm.size == 0:
        raise ValueError("数字化 ITO/CsFAPI 折射率数据清洗后为空。")
    return wavelength_nm, refractive_index


def extract_transparent_window(
    wavelength_nm: np.ndarray,
    refractive_index: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """提取 750-1000 nm 透明区间用于柯西拟合。"""
    fit_mask = (wavelength_nm >= FIT_MIN_WAVELENGTH_NM) & (wavelength_nm <= FIT_MAX_WAVELENGTH_NM)
    fit_wavelength_nm = wavelength_nm[fit_mask]
    fit_refractive_index = refractive_index[fit_mask]

    if fit_wavelength_nm.size < 3:
        raise ValueError(
            "透明窗口内的数据点不足以执行稳定的柯西拟合。"
            f"当前点数={fit_wavelength_nm.size}。"
        )
    return fit_wavelength_nm, fit_refractive_index


def fit_cauchy_parameters(
    wavelength_nm: np.ndarray,
    refractive_index: np.ndarray,
) -> tuple[float, float]:
    """拟合 Cauchy 模型参数 A, B。"""
    initial_guess = (2.30, 0.05)
    fitted_params, _ = curve_fit(
        cauchy_model,
        wavelength_nm,
        refractive_index,
        p0=initial_guess,
        maxfev=10000,
    )
    return float(fitted_params[0]), float(fitted_params[1])


def build_extended_dispersion(a_param: float, b_param: float) -> pd.DataFrame:
    """生成 750-1100 nm、1 nm 步长的扩展 CsFAPI n-k 表。"""
    wavelength_nm = np.arange(
        FIT_MIN_WAVELENGTH_NM,
        EXTRAPOLATION_MAX_WAVELENGTH_NM + GRID_STEP_NM,
        GRID_STEP_NM,
        dtype=np.float64,
    )
    refractive_index = cauchy_model(wavelength_nm, a_param, b_param)
    extinction_coefficient = np.zeros_like(refractive_index, dtype=np.float64)

    return pd.DataFrame(
        {
            "Wavelength": wavelength_nm,
            "n": refractive_index,
            "k": extinction_coefficient,
        }
    )


def plot_cauchy_extrapolation(
    raw_wavelength_nm: np.ndarray,
    raw_refractive_index: np.ndarray,
    fit_wavelength_nm: np.ndarray,
    fit_refractive_index: np.ndarray,
    extended_table: pd.DataFrame,
    a_param: float,
    b_param: float,
    output_path: Path,
) -> None:
    """输出原始散点与 Cauchy 平滑曲线的 QA 图。"""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    ax.scatter(
        raw_wavelength_nm,
        raw_refractive_index,
        s=18,
        color="#616161",
        alpha=0.65,
        label="Digitized ITO/CsFAPI n",
    )
    ax.scatter(
        fit_wavelength_nm,
        fit_refractive_index,
        s=24,
        color="#ef6c00",
        alpha=0.80,
        label="Fit Window (750-1000 nm)",
    )
    ax.plot(
        extended_table["Wavelength"].to_numpy(dtype=float),
        extended_table["n"].to_numpy(dtype=float),
        color="#1565c0",
        linewidth=2.2,
        label="Cauchy Extrapolation",
    )

    textbox = f"A = {a_param:.6f}\nB = {b_param:.6f} um^2"
    ax.text(
        0.03,
        0.97,
        textbox,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.88, "edgecolor": "#666666"},
    )

    ax.set_xlim(FIT_MIN_WAVELENGTH_NM, EXTRAPOLATION_MAX_WAVELENGTH_NM)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Refractive Index n")
    ax.set_title("Phase 02 Cauchy Extrapolation for ITO/CsFAPI (750-1100 nm)")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    project_root = get_project_root()
    input_csv = project_root / "resources" / "digitized" / "phase02_fig3_csfapi_optical_constants_digitized.csv"
    output_csv = project_root / "data" / "processed" / "CsFAPI_nk_extended.csv"
    output_figure = project_root / "results" / "figures" / "cauchy_extrapolation_check.png"

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_figure.parent.mkdir(parents=True, exist_ok=True)

    raw_wavelength_nm, raw_refractive_index = load_digitized_csfapi_n(input_csv)
    fit_wavelength_nm, fit_refractive_index = extract_transparent_window(raw_wavelength_nm, raw_refractive_index)
    a_param, b_param = fit_cauchy_parameters(fit_wavelength_nm, fit_refractive_index)
    extended_table = build_extended_dispersion(a_param, b_param)

    extended_table.to_csv(output_csv, index=False)
    plot_cauchy_extrapolation(
        raw_wavelength_nm=raw_wavelength_nm,
        raw_refractive_index=raw_refractive_index,
        fit_wavelength_nm=fit_wavelength_nm,
        fit_refractive_index=fit_refractive_index,
        extended_table=extended_table,
        a_param=a_param,
        b_param=b_param,
        output_path=output_figure,
    )

    print("CsFAPI 柯西外推完成。")
    print(f"输入数字化曲线: {input_csv}")
    print(f"输出中间件: {output_csv}")
    print(f"输出验证图: {output_figure}")
    print(f"Fitted A = {a_param:.8f}")
    print(f"Fitted B = {b_param:.8f} um^2")


if __name__ == "__main__":
    main()
