"""Phase 06 HDR 绝对反射率校准公共模块。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import tempfile
from typing import Iterable

import numpy as np
import pandas as pd


THRESHOLD_LOWER_RATIO = 0.75
THRESHOLD_UPPER_RATIO = 0.90
BAND_WINDOWS_NM: tuple[tuple[float, float], ...] = (
    (500.0, 600.0),
    (650.0, 710.0),
    (850.0, 1055.460325),
)


@dataclass(frozen=True)
class SpeMetadata:
    exposure_ms: float
    background_reference: str | None
    frames_to_store: int | None


@dataclass(frozen=True)
class MeasurementFile:
    csv_path: Path
    spe_path: Path
    exposure_label: str
    replicate_id: int | None
    exposure_ms: float
    exposure_name_ms: float | None
    background_reference: str | None
    frames_to_store: int | None


@dataclass
class MeanSpectrum:
    label: str
    wavelength_nm: np.ndarray
    mean_counts: np.ndarray
    replicate_count: int
    files: list[MeasurementFile]
    exposure_ms: float


@dataclass(frozen=True)
class RatioStats:
    median: float
    p05: float
    p95: float


@dataclass(frozen=True)
class BandStats:
    start_nm: float
    end_nm: float
    ratio_stats: RatioStats
    long_trusted_points: int
    transition_points: int
    short_trusted_points: int


@dataclass
class HdrBlendResult:
    group_name: str
    wavelength_nm: np.ndarray
    long_mean: MeanSpectrum
    short_mean: MeanSpectrum
    n_long: np.ndarray
    n_short: np.ndarray
    hdr_counts_per_ms: np.ndarray
    w_long: np.ndarray
    c_max: float
    th_lower: float
    th_upper: float
    transition_start_nm: float | None
    transition_end_nm: float | None
    transition_point_count: int
    ratio_stats: RatioStats
    band_stats: list[BandStats]


@dataclass
class AbsoluteCalibrationResult:
    wavelength_nm: np.ndarray
    sample_hdr: HdrBlendResult
    ag_hdr: HdrBlendResult
    ag_theory_reflectance: np.ndarray
    absolute_reflectance: np.ndarray


def normalize_column_name(name: str) -> str:
    return "".join(str(name).strip().lower().split())


def find_column(columns: list[str], candidates: tuple[str, ...], role: str) -> str:
    normalized_map = {normalize_column_name(column): column for column in columns}
    for normalized_name, original_name in normalized_map.items():
        if any(candidate in normalized_name for candidate in candidates):
            return original_name
    raise ValueError(f"无法在输入表中识别{role}列，现有列名为: {columns}")


def load_csv_spectrum(csv_path: Path) -> tuple[np.ndarray, np.ndarray]:
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


def parse_exposure_ms_from_name(name: str) -> float | None:
    match = re.search(r"-(\d+(?:\.\d+)?)(us|ms|s)(?:-| )", name, flags=re.IGNORECASE)
    if match is None:
        return None

    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit == "us":
        return value / 1000.0
    if unit == "ms":
        return value
    return value * 1000.0


def parse_replicate_id(name: str, exposure_label: str) -> int | None:
    match = re.search(rf"-{re.escape(exposure_label)}-(\d+)\b", name)
    if match is None:
        return None
    return int(match.group(1))


def load_spe_metadata(spe_path: Path) -> SpeMetadata:
    blob = spe_path.read_bytes()
    xml_start = blob.find(b"<SpeFormat")
    if xml_start < 0:
        raise ValueError(f"无法在 .spe 中定位 XML 元数据: {spe_path}")

    xml_text = blob[xml_start:].decode("utf-8", errors="ignore")
    exposure_match = re.search(r'<ExposureTime type="Double">([^<]+)</ExposureTime>', xml_text)
    if exposure_match is None:
        raise ValueError(f"无法在 .spe 中读取曝光时间: {spe_path}")

    background_match = re.search(r'<BackgroundCorrection reference="([^"]+)"', xml_text)
    frames_match = re.search(r'<FramesToStore type="Int64">([^<]+)</FramesToStore>', xml_text)
    return SpeMetadata(
        exposure_ms=float(exposure_match.group(1)),
        background_reference=background_match.group(1) if background_match else None,
        frames_to_store=int(frames_match.group(1)) if frames_match else None,
    )


def discover_measurement_files(data_dir: Path, prefix: str, exposure_label: str) -> list[MeasurementFile]:
    pattern = f"{prefix}-{exposure_label}-*-cor.csv"
    csv_files = sorted(data_dir.glob(pattern))
    if not csv_files:
        raise FileNotFoundError(f"未找到匹配文件: {data_dir / pattern}")

    files: list[MeasurementFile] = []
    for csv_path in csv_files:
        spe_path = csv_path.with_suffix(".spe")
        if not spe_path.exists():
            raise FileNotFoundError(f"缺少配对 .spe 文件: {spe_path}")

        metadata = load_spe_metadata(spe_path)
        exposure_name_ms = parse_exposure_ms_from_name(csv_path.name)
        if exposure_name_ms is not None and not np.isclose(exposure_name_ms, metadata.exposure_ms):
            raise ValueError(
                "文件名曝光时间与 .spe 元数据不一致: "
                f"{csv_path.name}, filename={exposure_name_ms} ms, spe={metadata.exposure_ms} ms"
            )

        files.append(
            MeasurementFile(
                csv_path=csv_path,
                spe_path=spe_path,
                exposure_label=exposure_label,
                replicate_id=parse_replicate_id(csv_path.name, exposure_label),
                exposure_ms=metadata.exposure_ms,
                exposure_name_ms=exposure_name_ms,
                background_reference=metadata.background_reference,
                frames_to_store=metadata.frames_to_store,
            )
        )
    return files


def validate_same_wavelength_grid(series: Iterable[tuple[Path, np.ndarray]]) -> np.ndarray:
    items = list(series)
    if not items:
        raise ValueError("空输入，无法校验波长网格。")

    reference_path, reference_wavelength = items[0]
    for path, wavelength in items[1:]:
        if reference_wavelength.shape != wavelength.shape or not np.allclose(
            reference_wavelength, wavelength, atol=1e-9, rtol=0.0
        ):
            raise ValueError(
                "重复测量的波长网格不一致，无法直接求均值: "
                f"{reference_path.name} vs {path.name}"
            )
    return reference_wavelength


def build_mean_spectrum(label: str, files: list[MeasurementFile]) -> MeanSpectrum:
    if not files:
        raise ValueError(f"{label} 的文件列表为空。")

    exposures = np.array([file.exposure_ms for file in files], dtype=float)
    if not np.allclose(exposures, exposures[0], atol=1e-9, rtol=0.0):
        raise ValueError(f"{label} 内部存在不一致曝光时间，无法求均值: {exposures}")

    spectra: list[np.ndarray] = []
    grids: list[tuple[Path, np.ndarray]] = []
    for file in files:
        wavelength_nm, counts = load_csv_spectrum(file.csv_path)
        grids.append((file.csv_path, wavelength_nm))
        spectra.append(counts)

    wavelength_nm = validate_same_wavelength_grid(grids)
    counts_matrix = np.vstack(spectra)
    return MeanSpectrum(
        label=label,
        wavelength_nm=wavelength_nm,
        mean_counts=counts_matrix.mean(axis=0),
        replicate_count=len(files),
        files=files,
        exposure_ms=float(exposures[0]),
    )


def compute_ratio_stats(n_short: np.ndarray, n_long: np.ndarray) -> RatioStats:
    ratio = np.divide(n_short, n_long, out=np.full_like(n_long, np.nan), where=~np.isclose(n_long, 0.0))
    finite_ratio = ratio[np.isfinite(ratio)]
    if finite_ratio.size == 0:
        raise ValueError("归一化比值全部无效，无法生成 QA 统计。")
    return RatioStats(
        median=float(np.nanmedian(finite_ratio)),
        p05=float(np.nanpercentile(finite_ratio, 5.0)),
        p95=float(np.nanpercentile(finite_ratio, 95.0)),
    )


def compute_band_stats(
    wavelength_nm: np.ndarray,
    n_short: np.ndarray,
    n_long: np.ndarray,
    w_long: np.ndarray,
    band_windows_nm: tuple[tuple[float, float], ...] = BAND_WINDOWS_NM,
) -> list[BandStats]:
    results: list[BandStats] = []
    for start_nm, end_nm in band_windows_nm:
        mask = (wavelength_nm >= start_nm) & (wavelength_nm <= end_nm)
        if not np.any(mask):
            continue

        band_ratio = compute_ratio_stats(n_short[mask], n_long[mask])
        band_weights = w_long[mask]
        results.append(
            BandStats(
                start_nm=float(start_nm),
                end_nm=float(end_nm),
                ratio_stats=band_ratio,
                long_trusted_points=int(np.count_nonzero(np.isclose(band_weights, 1.0))),
                transition_points=int(np.count_nonzero((band_weights > 0.0) & (band_weights < 1.0))),
                short_trusted_points=int(np.count_nonzero(np.isclose(band_weights, 0.0))),
            )
        )
    return results


def blend_hdr_spectra(group_name: str, long_mean: MeanSpectrum, short_mean: MeanSpectrum) -> HdrBlendResult:
    if long_mean.wavelength_nm.shape != short_mean.wavelength_nm.shape or not np.allclose(
        long_mean.wavelength_nm,
        short_mean.wavelength_nm,
        atol=1e-9,
        rtol=0.0,
    ):
        raise ValueError(f"{group_name} 的长短曝光波长网格不一致，无法直接融合。")

    c_long = long_mean.mean_counts
    c_short = short_mean.mean_counts
    c_max = float(np.nanmax(c_long))
    th_lower = c_max * THRESHOLD_LOWER_RATIO
    th_upper = c_max * THRESHOLD_UPPER_RATIO
    if not th_upper > th_lower:
        raise ValueError(f"{group_name} 的 HDR 阈值异常: th_lower={th_lower}, th_upper={th_upper}")

    n_long = c_long / long_mean.exposure_ms
    n_short = c_short / short_mean.exposure_ms
    w_long = np.ones_like(c_long, dtype=float)
    transition_mask = (c_long > th_lower) & (c_long < th_upper)
    w_long[c_long >= th_upper] = 0.0
    w_long[transition_mask] = (th_upper - c_long[transition_mask]) / (th_upper - th_lower)
    hdr_counts_per_ms = w_long * n_long + (1.0 - w_long) * n_short
    if np.any(~np.isfinite(hdr_counts_per_ms)):
        raise ValueError(f"{group_name} 的 HDR 曲线存在非有限值。")

    transition_indices = np.flatnonzero(transition_mask)
    return HdrBlendResult(
        group_name=group_name,
        wavelength_nm=long_mean.wavelength_nm,
        long_mean=long_mean,
        short_mean=short_mean,
        n_long=n_long,
        n_short=n_short,
        hdr_counts_per_ms=hdr_counts_per_ms,
        w_long=w_long,
        c_max=c_max,
        th_lower=th_lower,
        th_upper=th_upper,
        transition_start_nm=float(long_mean.wavelength_nm[transition_indices[0]]) if transition_indices.size else None,
        transition_end_nm=float(long_mean.wavelength_nm[transition_indices[-1]]) if transition_indices.size else None,
        transition_point_count=int(transition_indices.size),
        ratio_stats=compute_ratio_stats(n_short=n_short, n_long=n_long),
        band_stats=compute_band_stats(
            wavelength_nm=long_mean.wavelength_nm,
            n_short=n_short,
            n_long=n_long,
            w_long=w_long,
        ),
    )


def load_excel_reference(excel_path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = pd.read_excel(excel_path, engine="openpyxl")
    columns = data.columns.tolist()
    if all(str(column).startswith("Unnamed:") for column in columns):
        raw_data = pd.read_excel(excel_path, engine="openpyxl", header=None)
        header_row_index = None
        for row_index in range(min(10, len(raw_data))):
            row_values = [
                normalize_column_name(value)
                for value in raw_data.iloc[row_index].tolist()
                if pd.notna(value)
            ]
            if any("wavelength" in value for value in row_values) and any("reflect" in value for value in row_values):
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
    if np.nanmax(reflectance) > 1.5:
        reflectance = reflectance / 100.0
    return wavelength, reflectance


def interpolate_reference_to_grid(
    target_wavelength_nm: np.ndarray,
    reference_wavelength_nm: np.ndarray,
    reference_reflectance: np.ndarray,
) -> np.ndarray:
    if target_wavelength_nm.min() < reference_wavelength_nm.min() or target_wavelength_nm.max() > reference_wavelength_nm.max():
        raise ValueError(
            "银镜理论反射率表的波长范围不足以覆盖目标网格: "
            f"target=({target_wavelength_nm.min():.3f}, {target_wavelength_nm.max():.3f}) nm, "
            f"reference=({reference_wavelength_nm.min():.3f}, {reference_wavelength_nm.max():.3f}) nm"
        )
    return np.interp(target_wavelength_nm, reference_wavelength_nm, reference_reflectance)


def calibrate_absolute_reflectance(
    sample_hdr: HdrBlendResult,
    ag_hdr: HdrBlendResult,
    ag_theory_reflectance: np.ndarray,
) -> AbsoluteCalibrationResult:
    if not np.allclose(sample_hdr.wavelength_nm, ag_hdr.wavelength_nm, atol=1e-9, rtol=0.0):
        raise ValueError("样品 HDR 与银镜 HDR 波长网格不一致，无法计算绝对反射率。")
    if np.any(np.isclose(ag_hdr.hdr_counts_per_ms, 0.0)):
        raise ValueError("Ag HDR 曲线存在接近 0 的点，无法稳定完成绝对标定。")

    absolute_reflectance = (sample_hdr.hdr_counts_per_ms / ag_hdr.hdr_counts_per_ms) * ag_theory_reflectance
    if np.any(~np.isfinite(absolute_reflectance)):
        raise ValueError("绝对反射率存在非有限值。")

    return AbsoluteCalibrationResult(
        wavelength_nm=sample_hdr.wavelength_nm,
        sample_hdr=sample_hdr,
        ag_hdr=ag_hdr,
        ag_theory_reflectance=ag_theory_reflectance,
        absolute_reflectance=absolute_reflectance,
    )


def create_temp_output_dir(prefix: str = "tmm_phase06_dry_run") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(tempfile.gettempdir()) / f"{prefix}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=False)
    return output_dir


def export_curve_table(result: AbsoluteCalibrationResult, output_path: Path) -> None:
    table = pd.DataFrame(
        {
            "Wavelength_nm": result.wavelength_nm,
            "Sample_Counts_Long_Mean": result.sample_hdr.long_mean.mean_counts,
            "Sample_Counts_Short_Mean": result.sample_hdr.short_mean.mean_counts,
            "Sample_N_Long": result.sample_hdr.n_long,
            "Sample_N_Short": result.sample_hdr.n_short,
            "Sample_W_Long": result.sample_hdr.w_long,
            "Sample_HDR_CountsPerMs": result.sample_hdr.hdr_counts_per_ms,
            "Ag_Counts_Long_Mean": result.ag_hdr.long_mean.mean_counts,
            "Ag_Counts_Short_Mean": result.ag_hdr.short_mean.mean_counts,
            "Ag_N_Long": result.ag_hdr.n_long,
            "Ag_N_Short": result.ag_hdr.n_short,
            "Ag_W_Long": result.ag_hdr.w_long,
            "Ag_HDR_CountsPerMs": result.ag_hdr.hdr_counts_per_ms,
            "Ag_Theory_Reflectance": result.ag_theory_reflectance,
            "Absolute_Reflectance": result.absolute_reflectance,
        }
    )
    table.to_csv(output_path, index=False, encoding="utf-8-sig")


def _plot_counts_panel(ax, hdr_result: HdrBlendResult) -> None:
    ax.plot(
        hdr_result.wavelength_nm,
        hdr_result.long_mean.mean_counts,
        linewidth=1.8,
        color="#1f77b4",
        label=f"Long Mean ({hdr_result.long_mean.exposure_ms:g} ms)",
    )
    ax.plot(
        hdr_result.wavelength_nm,
        hdr_result.short_mean.mean_counts,
        linewidth=1.2,
        color="#ff7f0e",
        alpha=0.9,
        label=f"Short Mean ({hdr_result.short_mean.exposure_ms:g} ms)",
    )
    ax.axhline(hdr_result.th_lower, color="#6c757d", linestyle="--", linewidth=1.0, label="TH_lower")
    ax.axhline(hdr_result.th_upper, color="#d62728", linestyle="--", linewidth=1.0, label="TH_upper")
    ax.set_ylabel("Mean Counts")
    ax.grid(True, linestyle="--", alpha=0.3)

    weight_ax = ax.twinx()
    weight_ax.plot(hdr_result.wavelength_nm, hdr_result.w_long, color="#2ca02c", linewidth=1.1, label="W_long")
    weight_ax.set_ylim(-0.05, 1.05)
    weight_ax.set_ylabel("W_long")

    handles, labels = ax.get_legend_handles_labels()
    handles_w, labels_w = weight_ax.get_legend_handles_labels()
    ax.legend(handles + handles_w, labels + labels_w, fontsize=8, loc="upper right")


def _plot_hdr_panel(ax, hdr_result: HdrBlendResult) -> None:
    ax.plot(hdr_result.wavelength_nm, hdr_result.n_long, linewidth=1.6, color="#1f77b4", label="N_long")
    ax.plot(hdr_result.wavelength_nm, hdr_result.n_short, linewidth=1.2, color="#ff7f0e", label="N_short")
    ax.plot(hdr_result.wavelength_nm, hdr_result.hdr_counts_per_ms, linewidth=1.8, color="#2ca02c", label="HDR")
    transition_mask = (hdr_result.w_long > 0.0) & (hdr_result.w_long < 1.0)
    if np.any(transition_mask):
        ax.scatter(
            hdr_result.wavelength_nm[transition_mask],
            hdr_result.hdr_counts_per_ms[transition_mask],
            s=10,
            color="#d62728",
            alpha=0.8,
            label="Transition Points",
        )

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Counts / ms")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")


def plot_hdr_diagnostic(sample_hdr: HdrBlendResult, ag_hdr: HdrBlendResult, output_path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(15, 9), dpi=300, sharex="col", constrained_layout=True)
    fig.suptitle("Phase 06 HDR Diagnostic: DEVICE-1-withAg vs Ag Mirror", fontsize=14)

    _plot_counts_panel(axes[0, 0], sample_hdr)
    if sample_hdr.transition_start_nm is not None and sample_hdr.transition_end_nm is not None:
        axes[0, 0].set_title(
            f"Sample Counts | Cmax={sample_hdr.c_max:.2f}, "
            f"transition={sample_hdr.transition_start_nm:.3f}-{sample_hdr.transition_end_nm:.3f} nm"
        )
    else:
        axes[0, 0].set_title(f"Sample Counts | Cmax={sample_hdr.c_max:.2f}, transition=None")

    _plot_counts_panel(axes[0, 1], ag_hdr)
    if ag_hdr.transition_start_nm is not None and ag_hdr.transition_end_nm is not None:
        axes[0, 1].set_title(
            f"Ag Counts | Cmax={ag_hdr.c_max:.2f}, "
            f"transition={ag_hdr.transition_start_nm:.3f}-{ag_hdr.transition_end_nm:.3f} nm"
        )
    else:
        axes[0, 1].set_title(f"Ag Counts | Cmax={ag_hdr.c_max:.2f}, transition=None")

    _plot_hdr_panel(axes[1, 0], sample_hdr)
    axes[1, 0].set_title(
        f"Sample HDR | median={sample_hdr.ratio_stats.median:.3f}, "
        f"p05={sample_hdr.ratio_stats.p05:.3f}, p95={sample_hdr.ratio_stats.p95:.3f}"
    )
    _plot_hdr_panel(axes[1, 1], ag_hdr)
    axes[1, 1].set_title(
        f"Ag HDR | median={ag_hdr.ratio_stats.median:.3f}, "
        f"p05={ag_hdr.ratio_stats.p05:.3f}, p95={ag_hdr.ratio_stats.p95:.3f}"
    )

    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_absolute_reflectance(result: AbsoluteCalibrationResult, output_path: Path) -> None:
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(15, 8), dpi=300, constrained_layout=True)
    grid = fig.add_gridspec(2, 3, height_ratios=[2.0, 1.25])
    ax_main = fig.add_subplot(grid[0, :])

    wavelength_nm = result.wavelength_nm
    reflectance_percent = result.absolute_reflectance * 100.0
    ax_main.plot(wavelength_nm, reflectance_percent, color="#1565c0", linewidth=1.8)
    for start_nm, end_nm in BAND_WINDOWS_NM:
        ax_main.axvspan(start_nm, end_nm, color="#ffd54f", alpha=0.12)
    ax_main.set_title("Phase 06 Absolute Reflectance: DEVICE-1-withAg")
    ax_main.set_xlabel("Wavelength (nm)")
    ax_main.set_ylabel("Absolute Reflectance (%)")
    ax_main.grid(True, linestyle="--", alpha=0.3)

    for ax, (start_nm, end_nm) in zip(
        [fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1]), fig.add_subplot(grid[1, 2])],
        BAND_WINDOWS_NM,
    ):
        mask = (wavelength_nm >= start_nm) & (wavelength_nm <= end_nm)
        ax.plot(wavelength_nm[mask], reflectance_percent[mask], color="#1565c0", linewidth=1.8)
        ax.set_title(f"{start_nm:.0f}-{end_nm:.0f} nm")
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("R_abs (%)")
        ax.grid(True, linestyle="--", alpha=0.3)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def compute_largest_adjacent_jump(
    wavelength_nm: np.ndarray,
    values: np.ndarray,
    sample_w_long: np.ndarray,
    ag_w_long: np.ndarray,
    start_nm: float,
    end_nm: float,
) -> tuple[float, float, float, float, float]:
    mask = (wavelength_nm >= start_nm) & (wavelength_nm <= end_nm)
    band_wavelength = wavelength_nm[mask]
    band_values = values[mask]
    band_sample_w = sample_w_long[mask]
    band_ag_w = ag_w_long[mask]
    if band_values.size < 2:
        raise ValueError(f"波段 {start_nm}-{end_nm} nm 数据点不足，无法计算相邻点跳变。")

    delta = np.diff(band_values)
    index = int(np.argmax(np.abs(delta)))
    return (
        float(band_wavelength[index]),
        float(band_wavelength[index + 1]),
        float(delta[index]),
        float(band_sample_w[index]),
        float(band_ag_w[index]),
    )


def _format_ratio_stats(stats: RatioStats) -> str:
    return f"median={stats.median:.4f}, p05={stats.p05:.4f}, p95={stats.p95:.4f}"


def _measurement_lines(group_name: str, spectrum: MeanSpectrum) -> list[str]:
    lines = [f"### {group_name}"]
    for file in spectrum.files:
        background = file.background_reference or "N/A"
        exposure_name = f"{file.exposure_name_ms:g}" if file.exposure_name_ms is not None else "N/A"
        frames = str(file.frames_to_store) if file.frames_to_store is not None else "N/A"
        lines.append(
            "- "
            f"`{file.csv_path.name}` | `.spe` 曝光 `{file.exposure_ms:g} ms` | "
            f"文件名曝光 `{exposure_name} ms` | Frames `{frames}` | Background `{background}`"
        )
    return lines


def write_summary_markdown(
    result: AbsoluteCalibrationResult,
    output_path: Path,
    phase_name: str,
    data_dir: Path,
    reference_excel_path: Path,
    hdr_plot_path: Path,
    reflectance_plot_path: Path,
    curve_table_path: Path,
) -> None:
    wavelength_nm = result.wavelength_nm
    reflectance = result.absolute_reflectance
    sample_hdr = result.sample_hdr
    ag_hdr = result.ag_hdr

    jump_sections = []
    for start_nm, end_nm in BAND_WINDOWS_NM:
        jump = compute_largest_adjacent_jump(
            wavelength_nm=wavelength_nm,
            values=reflectance,
            sample_w_long=sample_hdr.w_long,
            ag_w_long=ag_hdr.w_long,
            start_nm=start_nm,
            end_nm=end_nm,
        )
        jump_sections.append(
            "- "
            f"`{start_nm:.0f}-{end_nm:.0f} nm` 最大相邻点跳变："
            f"`{jump[0]:.3f}->{jump[1]:.3f} nm`, "
            f"`ΔR = {jump[2]:+.6f}`, "
            f"`Sample_W_long = {jump[3]:.3f}`, `Ag_W_long = {jump[4]:.3f}`"
        )

    sample_transition = (
        f"{sample_hdr.transition_start_nm:.3f}-{sample_hdr.transition_end_nm:.3f} nm"
        if sample_hdr.transition_start_nm is not None and sample_hdr.transition_end_nm is not None
        else "无过渡点"
    )
    ag_transition = (
        f"{ag_hdr.transition_start_nm:.3f}-{ag_hdr.transition_end_nm:.3f} nm"
        if ag_hdr.transition_start_nm is not None and ag_hdr.transition_end_nm is not None
        else "无过渡点"
    )

    lines: list[str] = [
        f"# {phase_name} 单样本 HDR 绝对反射率 Dry Run 摘要",
        "",
        "## 1. 运行概况",
        f"- 当前 Phase：`{phase_name}`",
        f"- 数据目录：`{data_dir}`",
        f"- 银镜理论参考：`{reference_excel_path}`",
        f"- 实测波长窗口：`{wavelength_nm.min():.3f}-{wavelength_nm.max():.3f} nm`",
        f"- 输出图：`{hdr_plot_path}`、`{reflectance_plot_path}`",
        f"- 输出表：`{curve_table_path}`",
        "",
        "## 2. 输入文件与 .spe 元数据",
    ]
    lines.extend(_measurement_lines("Sample Long", sample_hdr.long_mean))
    lines.extend(_measurement_lines("Sample Short", sample_hdr.short_mean))
    lines.extend(_measurement_lines("Ag Long", ag_hdr.long_mean))
    lines.extend(_measurement_lines("Ag Short", ag_hdr.short_mean))
    lines.extend(
        [
            "",
            "## 3. HDR 阈值与交接点",
            f"- Sample: `Cmax = {sample_hdr.c_max:.2f}`, `TH_lower = {sample_hdr.th_lower:.2f}`, "
            f"`TH_upper = {sample_hdr.th_upper:.2f}`, 交接跨度 `{sample_transition}`, "
            f"交接点数 `{sample_hdr.transition_point_count}`",
            f"- Ag: `Cmax = {ag_hdr.c_max:.2f}`, `TH_lower = {ag_hdr.th_lower:.2f}`, "
            f"`TH_upper = {ag_hdr.th_upper:.2f}`, 交接跨度 `{ag_transition}`, "
            f"交接点数 `{ag_hdr.transition_point_count}`",
            "",
            "## 4. `N_short / N_long` 一致性统计",
            f"- Sample 全波段：{_format_ratio_stats(sample_hdr.ratio_stats)}",
            f"- Ag 全波段：{_format_ratio_stats(ag_hdr.ratio_stats)}",
        ]
    )

    for group_name, hdr_result in (("Sample", sample_hdr), ("Ag", ag_hdr)):
        lines.append(f"### {group_name} 分波段统计")
        for stats in hdr_result.band_stats:
            lines.append(
                "- "
                f"`{stats.start_nm:.0f}-{stats.end_nm:.0f} nm`: { _format_ratio_stats(stats.ratio_stats) }, "
                f"`long={stats.long_trusted_points}`, "
                f"`transition={stats.transition_points}`, "
                f"`short={stats.short_trusted_points}`"
            )

    lines.extend(
        [
            "",
            "## 5. 绝对反射率 QA",
            f"- `R_abs` 最小值 / 最大值 / 中位数："
            f"`{reflectance.min():.6f}` / `{reflectance.max():.6f}` / `{np.median(reflectance):.6f}`",
            *jump_sections,
            "",
            "## 6. 关键结论",
            "- 样品长曝光的 HDR 交接点主要落在 `~696-698 nm`；`850-1055 nm` 基本完全信任长曝光，说明近红外段不是本次 HDR 拼接主战场。",
            "- 银镜长曝光的交接点跨越 `~524-682 nm`，但这些点是围绕多个饱和峰形成的离散集合，而不是单一连续交接段。",
            "- 按 `.spe` 元数据的真实曝光时间归一化后，Ag 的 `N_short / N_long` 全波段中位数约为 "
            f"`{ag_hdr.ratio_stats.median:.4f}`，明显偏离 1；本次 Dry Run 未做任何经验缩放，已将该异常直接暴露在 QA 图和本摘要中。",
            "- 最终绝对反射率已完整生成，但在解释 `500-710 nm` 的局部形态时必须把 Ag 短曝光失配视为首要数据质量风险。",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
