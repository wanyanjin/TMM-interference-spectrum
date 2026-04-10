"""Phase 06c 全量样本 HDR 绝对反射率批量管线。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import sys
import traceback

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PHASE_NAME = "Phase 06c"
DATA_DIR = Path(r"D:\onedrive\Data\PL\2026\0409\cor")
ARCHIVE_DIR = DATA_DIR / "hdr_results"
SAMPLE_EXPOSURES = ("150ms", "2000ms")
AG_PREFIX = "Ag_mirro"
AG_EXPOSURES = ("500us", "10ms")
SUMMARY_FILENAME = "phase06_batch_summary.csv"
ARCHIVE_SUMMARY_FILENAME = "00_batch_summary_0409.csv"


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = get_project_root()
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core import hdr_absolute_calibration as hdr  # noqa: E402


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase06_batch"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures" / "phase06_batch"
REFERENCE_EXCEL_PATH = PROJECT_ROOT / "resources" / "GCC-1022系列xlsx.xlsx"


@dataclass
class SampleBatchResult:
    sample_name: str
    curve_table_path: Path
    qa_plot_path: Path
    archive_curve_path: Path
    archive_qa_path: Path
    sample_scale_factor: float
    transition_start_nm: float | None
    transition_end_nm: float | None
    r_abs_850nm: float
    r_abs_1050nm: float


@dataclass(frozen=True)
class SamplePointGroup:
    prefix: str
    point_id: int
    short_file: hdr.MeasurementFile
    long_file: hdr.MeasurementFile


def ensure_output_dirs() -> None:
    for path in (PROCESSED_DIR, FIGURES_DIR, ARCHIVE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def clear_previous_outputs() -> None:
    for pattern in ("*_curve_table.csv", SUMMARY_FILENAME, "phase06_batch_failures.csv"):
        for path in PROCESSED_DIR.glob(pattern):
            path.unlink()
    for pattern in ("*_hdr_diagnostic.png", "*_absolute_reflectance.png", "*_QA_plot.png"):
        for path in FIGURES_DIR.glob(pattern):
            path.unlink()
    for pattern in ("*_hdr_curves.csv", "*_hdr_qa.png", ARCHIVE_SUMMARY_FILENAME, "99_batch_failures_0409.csv"):
        for path in ARCHIVE_DIR.glob(pattern):
            path.unlink()


def discover_sample_point_groups() -> list[SamplePointGroup]:
    groups: list[SamplePointGroup] = []
    prefixes: set[str] = set()
    for csv_path in DATA_DIR.glob("*-cor.csv"):
        stem = csv_path.name.split(" 20", 1)[0]
        parts = stem.split("-")
        if len(parts) < 3:
            continue
        prefix = "-".join(parts[:-2])
        if prefix != AG_PREFIX:
            prefixes.add(prefix)

    for prefix in sorted(prefixes):
        short_files = hdr.discover_measurement_files(DATA_DIR, prefix, SAMPLE_EXPOSURES[0])
        long_files = hdr.discover_measurement_files(DATA_DIR, prefix, SAMPLE_EXPOSURES[1])
        short_map = {file.replicate_id: file for file in short_files}
        long_map = {file.replicate_id: file for file in long_files}
        point_ids = sorted(set(short_map) & set(long_map))

        missing_short = sorted(set(long_map) - set(short_map))
        missing_long = sorted(set(short_map) - set(long_map))
        if missing_short or missing_long:
            raise ValueError(
                f"{prefix} 的点位配对不完整: missing_short={missing_short}, missing_long={missing_long}"
            )

        for point_id in point_ids:
            if point_id is None:
                raise ValueError(f"{prefix} 存在无法识别的点位编号。")
            groups.append(
                SamplePointGroup(
                    prefix=prefix,
                    point_id=point_id,
                    short_file=short_map[point_id],
                    long_file=long_map[point_id],
                )
            )
    return groups


def interpolate_at(wavelength_nm: np.ndarray, values: np.ndarray, target_nm: float) -> float:
    if target_nm < wavelength_nm.min() or target_nm > wavelength_nm.max():
        raise ValueError(
            f"目标插值点 {target_nm} nm 超出波长范围 "
            f"{wavelength_nm.min():.3f}-{wavelength_nm.max():.3f} nm"
        )
    return float(np.interp(target_nm, wavelength_nm, values))


def build_ag_reference() -> tuple[hdr.HdrBlendResult, np.ndarray]:
    ag_short_files = hdr.discover_measurement_files(DATA_DIR, AG_PREFIX, AG_EXPOSURES[0])
    ag_long_files = hdr.discover_measurement_files(DATA_DIR, AG_PREFIX, AG_EXPOSURES[1])
    ag_short_mean = hdr.build_mean_spectrum(f"{AG_PREFIX}-{AG_EXPOSURES[0]}", ag_short_files)
    ag_long_mean = hdr.build_mean_spectrum(f"{AG_PREFIX}-{AG_EXPOSURES[1]}", ag_long_files)
    ag_hdr = hdr.blend_hdr_spectra(AG_PREFIX, ag_long_mean, ag_short_mean)

    reference_wavelength_nm, reference_reflectance = hdr.load_excel_reference(REFERENCE_EXCEL_PATH)
    ag_theory_reflectance = hdr.interpolate_reference_to_grid(
        target_wavelength_nm=ag_hdr.wavelength_nm,
        reference_wavelength_nm=reference_wavelength_nm,
        reference_reflectance=reference_reflectance,
    )
    return ag_hdr, ag_theory_reflectance


def combine_qa_plot(
    sample_name: str,
    hdr_diagnostic_path: Path,
    reflectance_plot_path: Path,
    output_path: Path,
) -> None:
    hdr_image = plt.imread(hdr_diagnostic_path)
    reflectance_image = plt.imread(reflectance_plot_path)

    fig, axes = plt.subplots(2, 1, figsize=(14, 14), dpi=250, constrained_layout=True)
    fig.suptitle(f"{PHASE_NAME} QA: {sample_name}", fontsize=16)
    axes[0].imshow(hdr_image)
    axes[0].axis("off")
    axes[0].set_title("HDR Diagnostic")
    axes[1].imshow(reflectance_image)
    axes[1].axis("off")
    axes[1].set_title("Absolute Reflectance")
    fig.savefig(output_path, dpi=250)
    plt.close(fig)


def process_single_sample(
    sample_group: SamplePointGroup,
    ag_hdr: hdr.HdrBlendResult,
    ag_theory_reflectance: np.ndarray,
) -> SampleBatchResult:
    sample_name = f"{sample_group.prefix}-P{sample_group.point_id}"
    sample_short_mean = hdr.build_mean_spectrum(
        f"{sample_name}-{SAMPLE_EXPOSURES[0]}", [sample_group.short_file]
    )
    sample_long_mean = hdr.build_mean_spectrum(
        f"{sample_name}-{SAMPLE_EXPOSURES[1]}", [sample_group.long_file]
    )
    sample_hdr = hdr.blend_hdr_spectra(sample_name, sample_long_mean, sample_short_mean)
    absolute_result = hdr.calibrate_absolute_reflectance(sample_hdr, ag_hdr, ag_theory_reflectance)

    sample_slug = sample_name.replace(" ", "_")
    curve_table_path = PROCESSED_DIR / f"{sample_slug}_curve_table.csv"
    hdr_plot_path = FIGURES_DIR / f"{sample_slug}_hdr_diagnostic.png"
    reflectance_plot_path = FIGURES_DIR / f"{sample_slug}_absolute_reflectance.png"
    qa_plot_path = FIGURES_DIR / f"{sample_slug}_QA_plot.png"

    hdr.export_curve_table(absolute_result, curve_table_path)
    hdr.plot_hdr_diagnostic(sample_hdr, ag_hdr, hdr_plot_path)
    hdr.plot_absolute_reflectance(absolute_result, reflectance_plot_path)
    combine_qa_plot(sample_name, hdr_plot_path, reflectance_plot_path, qa_plot_path)

    archive_curve_path = ARCHIVE_DIR / f"{sample_slug}_hdr_curves.csv"
    archive_qa_path = ARCHIVE_DIR / f"{sample_slug}_hdr_qa.png"
    shutil.copy2(curve_table_path, archive_curve_path)
    shutil.copy2(qa_plot_path, archive_qa_path)

    return SampleBatchResult(
        sample_name=sample_name,
        curve_table_path=curve_table_path,
        qa_plot_path=qa_plot_path,
        archive_curve_path=archive_curve_path,
        archive_qa_path=archive_qa_path,
        sample_scale_factor=sample_hdr.scale_factor,
        transition_start_nm=sample_hdr.transition_start_nm,
        transition_end_nm=sample_hdr.transition_end_nm,
        r_abs_850nm=interpolate_at(
            absolute_result.wavelength_nm, absolute_result.absolute_reflectance, 850.0
        ),
        r_abs_1050nm=interpolate_at(
            absolute_result.wavelength_nm, absolute_result.absolute_reflectance, 1050.0
        ),
    )


def write_batch_summary(results: list[SampleBatchResult]) -> tuple[Path, Path]:
    summary_df = pd.DataFrame(
        [
            {
                "Sample_Name": item.sample_name,
                "Sample_Scale_Factor": item.sample_scale_factor,
                "Transition_Start_nm": item.transition_start_nm,
                "Transition_End_nm": item.transition_end_nm,
                "R_abs_850nm": item.r_abs_850nm,
                "R_abs_1050nm": item.r_abs_1050nm,
            }
            for item in results
        ]
    ).sort_values("Sample_Name")

    summary_path = PROCESSED_DIR / SUMMARY_FILENAME
    archive_summary_path = ARCHIVE_DIR / ARCHIVE_SUMMARY_FILENAME
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    shutil.copy2(summary_path, archive_summary_path)
    return summary_path, archive_summary_path


def main() -> None:
    ensure_output_dirs()
    clear_previous_outputs()
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"未找到输入数据目录: {DATA_DIR}")
    if not REFERENCE_EXCEL_PATH.exists():
        raise FileNotFoundError(f"未找到银镜参考表: {REFERENCE_EXCEL_PATH}")

    sample_groups = discover_sample_point_groups()
    if not sample_groups:
        raise RuntimeError("未发现任何可处理样本。")

    ag_hdr, ag_theory_reflectance = build_ag_reference()

    successes: list[SampleBatchResult] = []
    failures: list[dict[str, str]] = []
    for sample_group in sample_groups:
        sample_name = f"{sample_group.prefix}-P{sample_group.point_id}"
        try:
            result = process_single_sample(sample_group, ag_hdr, ag_theory_reflectance)
            successes.append(result)
            print(
                f"[OK] {sample_name}: scale_factor={result.sample_scale_factor:.4f}, "
                f"transition={result.transition_start_nm}-{result.transition_end_nm}"
            )
        except Exception as exc:
            failures.append(
                {
                    "Sample_Name": sample_name,
                    "Error_Type": type(exc).__name__,
                    "Error_Message": str(exc),
                    "Traceback": traceback.format_exc(),
                }
            )
            print(f"[FAIL] {sample_name}: {type(exc).__name__}: {exc}")

    summary_path = None
    archive_summary_path = None
    if successes:
        summary_path, archive_summary_path = write_batch_summary(successes)

    if failures:
        failure_path = PROCESSED_DIR / "phase06_batch_failures.csv"
        pd.DataFrame(failures).to_csv(failure_path, index=False, encoding="utf-8-sig")
        shutil.copy2(failure_path, ARCHIVE_DIR / "99_batch_failures_0409.csv")

    print(f"{PHASE_NAME} 批处理完成。")
    print(f"样本总数: {len(sample_groups)}")
    print(f"成功样本数: {len(successes)}")
    print(f"失败样本数: {len(failures)}")
    print(f"项目 CSV 目录: {PROCESSED_DIR}")
    print(f"项目图目录: {FIGURES_DIR}")
    print(f"OneDrive 存档目录: {ARCHIVE_DIR}")
    if summary_path is not None and archive_summary_path is not None:
        print(f"汇总台账: {summary_path}")
        print(f"存档台账: {archive_summary_path}")


if __name__ == "__main__":
    main()
