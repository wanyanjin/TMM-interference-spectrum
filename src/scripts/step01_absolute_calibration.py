"""半导体薄膜绝对反射率标定与可视化脚本。

本脚本严格按照项目目录结构工作：
1. 样品数据：test_data/sample.csv（曝光 100 ms）
2. 银镜数据：test_data/Ag-mirro.csv（曝光 25 ms）
3. 厂家银镜基准：resources/GCC-1022系列xlsx.xlsx
4. 输出图片：results/figures/absolute_reflectance_interference.png

核心物理逻辑：
- 先对银镜测量信号做曝光时间归一化，使其等效到 100 ms。
- 再把厂家提供的银镜反射率基准插值到样品波长网格。
- 最后按 R_meas = (S_sample / S_mirror_norm) * R_mirror_excel_interp
  将器件原始计数转换为绝对反射率。
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

# 使用非交互式后端，保证脚本在无显示器的终端环境中也能正常保存图片。
matplotlib.use("Agg")
import matplotlib.pyplot as plt


WAVELENGTH_MIN_NM = 850.0
WAVELENGTH_MAX_NM = 1100.0
SAMPLE_EXPOSURE_MS = 100.0
MIRROR_EXPOSURE_MS = 25.0
DEFAULT_SAVGOL_WINDOW = 51
DEFAULT_SAVGOL_POLYORDER = 3


def get_project_root() -> Path:
    """根据脚本所在位置反推出项目根目录。"""
    return Path(__file__).resolve().parents[2]


def normalize_column_name(name: str) -> str:
    """将列名统一为易比较的形式，便于做大小写和空格容错。"""
    return "".join(str(name).strip().lower().split())


def find_column(columns: list[str], candidates: tuple[str, ...], role: str) -> str:
    """在 DataFrame 列名中查找目标列。

    role 只是为了报错时给出更清晰的中文提示。
    """
    normalized_map = {normalize_column_name(column): column for column in columns}
    for normalized_name, original_name in normalized_map.items():
        if any(candidate in normalized_name for candidate in candidates):
            return original_name
    raise ValueError(f"无法在输入表中识别{role}列，现有列名为: {columns}")


def load_csv_spectrum(csv_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """读取 CSV 光谱，并自动识别波长列与强度列。"""
    data = pd.read_csv(csv_path)
    wavelength_col = find_column(data.columns.tolist(), ("wavelength",), "波长")
    intensity_col = find_column(data.columns.tolist(), ("counts", "intensity"), "强度")

    wavelength = pd.to_numeric(data[wavelength_col], errors="coerce").to_numpy(dtype=float)
    intensity = pd.to_numeric(data[intensity_col], errors="coerce").to_numpy(dtype=float)

    valid_mask = np.isfinite(wavelength) & np.isfinite(intensity)
    wavelength = wavelength[valid_mask]
    intensity = intensity[valid_mask]

    sort_index = np.argsort(wavelength)
    return wavelength[sort_index], intensity[sort_index]


def load_excel_reference(excel_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """读取厂家银镜基准曲线。

    Excel 当前已知结构为：
    - 第 1 个 sheet
    - 第一列为 Wavelength
    - 第二列为 Reflection
    - 第二行是单位说明（例如 nm 与 %）

    这里不依赖固定表头行号，而是统一做数值化清洗，这样即便夹杂单位行也能自动跳过。
    """
    data = pd.read_excel(excel_path, engine="openpyxl")
    columns = data.columns.tolist()

    # 某些 Excel 文件虽然视觉上第一行是表头，但 pandas 读取时会给出 Unnamed 列，
    # 并把真正的字段名留在首行数据里。这里主动做一次兜底扫描，
    # 从前几行里寻找包含 Wavelength/Reflection 的那一行，再重建列名。
    if all(str(column).startswith("Unnamed:") for column in columns):
        raw_data = pd.read_excel(excel_path, engine="openpyxl", header=None)
        header_row_index = None
        for row_index in range(min(10, len(raw_data))):
            row_values = [
                normalize_column_name(value)
                for value in raw_data.iloc[row_index].tolist()
                if pd.notna(value)
            ]
            has_wavelength = any("wavelength" in value for value in row_values)
            has_reflection = any("reflect" in value for value in row_values)
            if has_wavelength and has_reflection:
                header_row_index = row_index
                break

        if header_row_index is None:
            raise ValueError("无法在 Excel 前 10 行中定位包含 Wavelength/Reflection 的表头行。")

        data = raw_data.iloc[header_row_index + 1 :].copy()
        data.columns = raw_data.iloc[header_row_index].tolist()
        columns = data.columns.tolist()

    wavelength_col = find_column(columns, ("wavelength",), "Excel 波长")
    reflectance_col = find_column(columns, ("reflect",), "Excel 反射率")

    wavelength = pd.to_numeric(data[wavelength_col], errors="coerce").to_numpy(dtype=float)
    reflectance = pd.to_numeric(data[reflectance_col], errors="coerce").to_numpy(dtype=float)

    valid_mask = np.isfinite(wavelength) & np.isfinite(reflectance)
    wavelength = wavelength[valid_mask]
    reflectance = reflectance[valid_mask]

    sort_index = np.argsort(wavelength)
    wavelength = wavelength[sort_index]
    reflectance = reflectance[sort_index]

    # 厂家 Excel 可能给的是百分比（例如 98.3），也可能已经是 0-1 小数。
    # 这里通过数值范围自动判别并统一为 0-1 的小数，后续物理公式才有一致单位。
    if np.nanmax(reflectance) > 1.5:
        reflectance = reflectance / 100.0

    return wavelength, reflectance


def crop_spectrum(
    wavelength: np.ndarray,
    intensity: np.ndarray,
    min_nm: float = WAVELENGTH_MIN_NM,
    max_nm: float = WAVELENGTH_MAX_NM,
) -> tuple[np.ndarray, np.ndarray]:
    """截取目标波段 850-1100 nm。"""
    band_mask = (wavelength >= min_nm) & (wavelength <= max_nm)
    return wavelength[band_mask], intensity[band_mask]


def validate_interp_domain(
    target_wavelength: np.ndarray,
    source_wavelength: np.ndarray,
    source_name: str,
) -> None:
    """确保插值源波长范围覆盖目标网格，避免静默外推。"""
    if target_wavelength.size == 0:
        raise ValueError("目标波长数组为空，无法继续计算。")
    if source_wavelength.size == 0:
        raise ValueError(f"{source_name} 数据为空，无法插值。")
    if target_wavelength.min() < source_wavelength.min() or target_wavelength.max() > source_wavelength.max():
        raise ValueError(
            f"{source_name} 的波长范围不足以覆盖目标波段: "
            f"target=({target_wavelength.min():.2f}, {target_wavelength.max():.2f}) nm, "
            f"source=({source_wavelength.min():.2f}, {source_wavelength.max():.2f}) nm"
        )


def compute_valid_savgol_window(size: int, desired_window: int, polyorder: int) -> int:
    """计算合法的 Savitzky-Golay 奇数窗长。

    要求：
    - 不超过样本点数
    - 必须是奇数
    - 必须大于 polyorder
    """
    if size <= polyorder:
        raise ValueError(
            f"目标波段数据点数仅为 {size}，不足以进行 polyorder={polyorder} 的 Savitzky-Golay 平滑。"
        )

    window = min(desired_window, size)
    if window % 2 == 0:
        window -= 1
    min_valid_window = polyorder + 2 if (polyorder + 2) % 2 == 1 else polyorder + 3
    if window < min_valid_window:
        window = min_valid_window
    if window > size:
        window = size if size % 2 == 1 else size - 1
    if window <= polyorder:
        raise ValueError(f"无法为 size={size}, polyorder={polyorder} 生成合法的奇数窗长。")
    return window


def main() -> None:
    project_root = get_project_root()

    sample_csv = project_root / "test_data" / "sample.csv"
    mirror_csv = project_root / "test_data" / "Ag-mirro.csv"
    reference_excel = project_root / "resources" / "GCC-1022系列xlsx.xlsx"
    output_path = project_root / "results" / "figures" / "absolute_reflectance_interference.png"
    processed_output_path = project_root / "data" / "processed" / "target_reflectance.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed_output_path.parent.mkdir(parents=True, exist_ok=True)

    for path in (sample_csv, mirror_csv, reference_excel):
        if not path.exists():
            raise FileNotFoundError(f"未找到输入文件: {path}")

    # 读取样品与银镜原始光谱。
    sample_wavelength_raw, sample_signal_raw = load_csv_spectrum(sample_csv)
    mirror_wavelength_raw, mirror_signal_raw = load_csv_spectrum(mirror_csv)

    # 只保留目标物理波段 850-1100 nm，避免无关波段影响插值和绘图。
    sample_wavelength, sample_signal = crop_spectrum(sample_wavelength_raw, sample_signal_raw)
    mirror_wavelength, mirror_signal = crop_spectrum(mirror_wavelength_raw, mirror_signal_raw)

    if sample_wavelength.size == 0 or mirror_wavelength.size == 0:
        raise ValueError("样品或银镜在 850-1100 nm 内无有效数据。")

    # 读取厂家提供的银镜绝对反射率基准，并清洗成 0-1 小数形式。
    excel_wavelength, excel_reflectance = load_excel_reference(reference_excel)
    excel_wavelength, excel_reflectance = crop_spectrum(excel_wavelength, excel_reflectance)

    validate_interp_domain(sample_wavelength, mirror_wavelength, "银镜 CSV")
    validate_interp_domain(sample_wavelength, excel_wavelength, "银镜 Excel 基准")

    # 以样品波长网格作为统一坐标。
    # 即使当前样品和银镜采样点已经一致，这里仍然明确做插值，保证脚本对未来数据更稳健。
    sample_signal_on_grid = sample_signal
    mirror_signal_on_grid = np.interp(sample_wavelength, mirror_wavelength, mirror_signal)

    # 厂家给出的理论银镜反射率曲线也要插值到样品波长网格，
    # 这样才能和逐点测得的样品/银镜信号相乘除，完成绝对标定。
    r_mirror_excel_interp = np.interp(sample_wavelength, excel_wavelength, excel_reflectance)

    # 银镜在实验中只曝光了 25 ms，而样品曝光了 100 ms。
    # 因此需要把银镜计数乘以 100/25 = 4，得到等效于 100 ms 的镜面信号，
    # 否则会把曝光时间差误判为器件反射率差异。
    s_mirror_norm = mirror_signal_on_grid * (SAMPLE_EXPOSURE_MS / MIRROR_EXPOSURE_MS)

    if np.any(np.isclose(s_mirror_norm, 0.0)):
        raise ValueError("归一化后的银镜信号存在接近 0 的点，无法稳定完成绝对反射率换算。")

    # 绝对反射率标定公式：
    # R_meas = (S_sample / S_mirror_norm) * R_mirror_excel_interp
    # 含义是：先用样品/银镜的相对信号比值消除仪器响应，再乘上厂家已知的镜面绝对反射率，
    # 从而得到器件的绝对反射率。
    r_meas = (sample_signal_on_grid / s_mirror_norm) * r_mirror_excel_interp

    # 对最终器件反射率做轻度 Savitzky-Golay 平滑。
    # 目标是抑制暗噪声带来的高频毛刺，同时尽量保持干涉条纹的主形态不被抹平。
    savgol_window = compute_valid_savgol_window(
        size=r_meas.size,
        desired_window=DEFAULT_SAVGOL_WINDOW,
        polyorder=DEFAULT_SAVGOL_POLYORDER,
    )
    r_meas_smooth = savgol_filter(r_meas, window_length=savgol_window, polyorder=DEFAULT_SAVGOL_POLYORDER)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    # 灰色虚线：厂家银镜理论基准，用于检查 Excel 插值是否合理。
    ax.plot(
        sample_wavelength,
        r_mirror_excel_interp * 100.0,
        linestyle="--",
        color="gray",
        linewidth=1.5,
        label="Mirror Reference (Excel)",
    )

    # 浅红色半透明实线：器件原始绝对反射率，保留给用户观察噪声水平。
    ax.plot(
        sample_wavelength,
        r_meas * 100.0,
        color="#f28b82",
        alpha=0.45,
        linewidth=1.3,
        label="Sample Reflectance (Raw)",
    )

    # 深红色主实线：平滑后的器件干涉谱，是主要分析对象。
    ax.plot(
        sample_wavelength,
        r_meas_smooth * 100.0,
        color="#b71c1c",
        linewidth=2.0,
        label="Sample Reflectance (Smoothed)",
    )

    ax.set_xlim(WAVELENGTH_MIN_NM, WAVELENGTH_MAX_NM)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Absolute Reflectance (%)")
    ax.set_title("Perovskite Half-Device Absolute Reflectance (850-1100nm)")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    # 为后续 TMM 反演脚本输出标准化的目标曲线文件。
    # 这里明确保存 0-1 单位的平滑绝对反射率，而不是百分比，
    # 这样 step02 在做残差与卡方计算时可以直接使用物理量本身。
    processed_df = pd.DataFrame(
        {
            "Wavelength": sample_wavelength,
            "R_smooth": r_meas_smooth,
        }
    )
    processed_df.to_csv(processed_output_path, index=False)

    print("绝对反射率标定完成。")
    print(f"输出图片已保存到: {output_path}")
    print(f"目标曲线 CSV 已保存到: {processed_output_path}")
    print(f"目标波段点数: {sample_wavelength.size}")
    print(f"Savitzky-Golay 参数: window_length={savgol_window}, polyorder={DEFAULT_SAVGOL_POLYORDER}")


if __name__ == "__main__":
    main()
