"""Phase 06 单样本 Bit-Agnostic HDR 绝对反射率 Dry Run。"""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")


PHASE_NAME = "Phase 06"
DATA_DIR = Path(r"D:\onedrive\Data\PL\2026\0409\cor")
REFERENCE_EXCEL = "GCC-1022系列xlsx.xlsx"
SAMPLE_PREFIX = "DEVICE-1-withAg"
AG_PREFIX = "Ag_mirro"


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = get_project_root()
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core import hdr_absolute_calibration as hdr  # noqa: E402


def main() -> None:
    reference_excel_path = PROJECT_ROOT / "resources" / REFERENCE_EXCEL
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"未找到原始数据目录: {DATA_DIR}")
    if not reference_excel_path.exists():
        raise FileNotFoundError(f"未找到银镜理论参考表: {reference_excel_path}")

    sample_short_files = hdr.discover_measurement_files(DATA_DIR, SAMPLE_PREFIX, "150ms")
    sample_long_files = hdr.discover_measurement_files(DATA_DIR, SAMPLE_PREFIX, "2000ms")
    ag_short_files = hdr.discover_measurement_files(DATA_DIR, AG_PREFIX, "500us")
    ag_long_files = hdr.discover_measurement_files(DATA_DIR, AG_PREFIX, "10ms")

    sample_short_mean = hdr.build_mean_spectrum("DEVICE-1-withAg-150ms", sample_short_files)
    sample_long_mean = hdr.build_mean_spectrum("DEVICE-1-withAg-2000ms", sample_long_files)
    ag_short_mean = hdr.build_mean_spectrum("Ag_mirro-500us", ag_short_files)
    ag_long_mean = hdr.build_mean_spectrum("Ag_mirro-10ms", ag_long_files)

    sample_hdr = hdr.blend_hdr_spectra("DEVICE-1-withAg", sample_long_mean, sample_short_mean)
    ag_hdr = hdr.blend_hdr_spectra("Ag_mirro", ag_long_mean, ag_short_mean)

    reference_wavelength_nm, reference_reflectance = hdr.load_excel_reference(reference_excel_path)
    ag_theory_reflectance = hdr.interpolate_reference_to_grid(
        target_wavelength_nm=sample_hdr.wavelength_nm,
        reference_wavelength_nm=reference_wavelength_nm,
        reference_reflectance=reference_reflectance,
    )
    result = hdr.calibrate_absolute_reflectance(sample_hdr, ag_hdr, ag_theory_reflectance)

    output_dir = hdr.create_temp_output_dir()
    hdr_plot_path = output_dir / "phase06_device1_withag_hdr_diagnostic.png"
    reflectance_plot_path = output_dir / "phase06_device1_withag_absolute_reflectance.png"
    curve_table_path = output_dir / "phase06_device1_withag_curve_table.csv"
    summary_path = output_dir / "phase06_device1_withag_summary.md"

    hdr.plot_hdr_diagnostic(sample_hdr, ag_hdr, hdr_plot_path)
    hdr.plot_absolute_reflectance(result, reflectance_plot_path)
    hdr.export_curve_table(result, curve_table_path)
    hdr.write_summary_markdown(
        result=result,
        output_path=summary_path,
        phase_name=PHASE_NAME,
        data_dir=DATA_DIR,
        reference_excel_path=reference_excel_path,
        hdr_plot_path=hdr_plot_path,
        reflectance_plot_path=reflectance_plot_path,
        curve_table_path=curve_table_path,
    )

    print(f"{PHASE_NAME} Dry Run 完成。")
    print(f"输出目录: {output_dir}")
    print(
        "Sample transition: "
        f"{sample_hdr.transition_start_nm:.3f}-{sample_hdr.transition_end_nm:.3f} nm, "
        f"points={sample_hdr.transition_point_count}"
    )
    print(
        "Ag transition: "
        f"{ag_hdr.transition_start_nm:.3f}-{ag_hdr.transition_end_nm:.3f} nm, "
        f"points={ag_hdr.transition_point_count}"
    )
    print(
        "Ag N_short/N_long median: "
        f"{ag_hdr.ratio_stats.median:.4f} (p05={ag_hdr.ratio_stats.p05:.4f}, p95={ag_hdr.ratio_stats.p95:.4f})"
    )


if __name__ == "__main__":
    main()
