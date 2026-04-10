"""Phase 07 dual-window inversion pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import sys

import matplotlib
import pandas as pd

matplotlib.use("Agg")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core import hdr_absolute_calibration as hdr  # noqa: E402
from core.phase07_dual_window import (  # noqa: E402
    Phase07Config,
    Phase07FitResult,
    Phase07SampleInput,
    build_phase07_stack_model,
    export_fit_curve_table,
    export_fit_summary_table,
    fit_dual_window_sample,
    load_phase07_sample_input,
    plot_dual_window_zoom,
    plot_measured_vs_fitted_full_spectrum,
    plot_rear_basin_scan,
    plot_residual_diagnostics,
    write_optimizer_log,
    write_phase07_fit_input,
)


PHASE_NAME = "Phase 07"
DEFAULT_INPUT_DIR = PROJECT_ROOT / "test_data" / "phase7_data"
REFERENCE_EXCEL_PATH = PROJECT_ROOT / "resources" / "GCC-1022系列xlsx.xlsx"
SAMPLE_EXPOSURES = ("150ms", "2000ms")
AG_PREFIX = "Ag_mirro"
AG_EXPOSURES = ("500us", "10ms")


@dataclass(frozen=True)
class RawSamplePointGroup:
    prefix: str
    point_id: int
    short_file: hdr.MeasurementFile
    long_file: hdr.MeasurementFile

    @property
    def sample_name(self) -> str:
        return f"{self.prefix}-P{self.point_id}"


@dataclass(frozen=True)
class SampleSourceRecord:
    sample_name: str
    with_ag: bool
    source_mode: str
    input_path: Path
    hdr_curve_path: Path
    fit_input_path: Path


def slugify_sample_name(sample_name: str) -> str:
    return sample_name.lower().replace(" ", "_").replace("-", "_")


def infer_with_ag(sample_name: str) -> bool:
    normalized = sample_name.lower()
    if "withoutag" in normalized:
        return False
    if "withag" in normalized:
        return True
    raise ValueError(f"无法从样本名推断 withAg/withoutAg: {sample_name}")


def ensure_output_dirs() -> dict[str, Path]:
    paths = {
        "processed_root": PROJECT_ROOT / "data" / "processed" / "phase07",
        "fit_inputs": PROJECT_ROOT / "data" / "processed" / "phase07" / "fit_inputs",
        "hdr_curves": PROJECT_ROOT / "data" / "processed" / "phase07" / "hdr_curves",
        "fit_results": PROJECT_ROOT / "data" / "processed" / "phase07" / "fit_results",
        "figures": PROJECT_ROOT / "results" / "figures" / "phase07",
        "logs": PROJECT_ROOT / "results" / "logs" / "phase07",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def discover_raw_sample_point_groups(data_dir: Path) -> list[RawSamplePointGroup]:
    groups: list[RawSamplePointGroup] = []
    prefixes: set[str] = set()
    for csv_path in data_dir.glob("*-cor.csv"):
        stem = csv_path.name.split(" 20", 1)[0]
        parts = stem.split("-")
        if len(parts) < 3:
            continue
        prefix = "-".join(parts[:-2])
        if prefix != AG_PREFIX:
            prefixes.add(prefix)

    for prefix in sorted(prefixes):
        short_files = hdr.discover_measurement_files(data_dir, prefix, SAMPLE_EXPOSURES[0])
        long_files = hdr.discover_measurement_files(data_dir, prefix, SAMPLE_EXPOSURES[1])
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
                RawSamplePointGroup(
                    prefix=prefix,
                    point_id=point_id,
                    short_file=short_map[point_id],
                    long_file=long_map[point_id],
                )
            )
    return groups


def build_ag_reference(data_dir: Path) -> tuple[hdr.HdrBlendResult, pd.Series]:
    ag_short_files = hdr.discover_measurement_files(data_dir, AG_PREFIX, AG_EXPOSURES[0])
    ag_long_files = hdr.discover_measurement_files(data_dir, AG_PREFIX, AG_EXPOSURES[1])
    ag_short_mean = hdr.build_mean_spectrum(f"{AG_PREFIX}-{AG_EXPOSURES[0]}", ag_short_files)
    ag_long_mean = hdr.build_mean_spectrum(f"{AG_PREFIX}-{AG_EXPOSURES[1]}", ag_long_files)
    ag_hdr = hdr.blend_hdr_spectra(AG_PREFIX, ag_long_mean, ag_short_mean)
    reference_wavelength_nm, reference_reflectance = hdr.load_excel_reference(REFERENCE_EXCEL_PATH)
    ag_theory_reflectance = hdr.interpolate_reference_to_grid(
        target_wavelength_nm=ag_hdr.wavelength_nm,
        reference_wavelength_nm=reference_wavelength_nm,
        reference_reflectance=reference_reflectance,
    )
    return ag_hdr, pd.Series(ag_theory_reflectance)


def build_fit_input_from_raw_group(
    sample_group: RawSamplePointGroup,
    ag_hdr: hdr.HdrBlendResult,
    ag_theory_reflectance: pd.Series,
    output_dirs: dict[str, Path],
) -> SampleSourceRecord:
    sample_name = sample_group.sample_name
    sample_slug = slugify_sample_name(sample_name)
    with_ag = infer_with_ag(sample_name)

    sample_short_mean = hdr.build_mean_spectrum(
        f"{sample_name}-{SAMPLE_EXPOSURES[0]}",
        [sample_group.short_file],
    )
    sample_long_mean = hdr.build_mean_spectrum(
        f"{sample_name}-{SAMPLE_EXPOSURES[1]}",
        [sample_group.long_file],
    )
    sample_hdr = hdr.blend_hdr_spectra(sample_name, sample_long_mean, sample_short_mean)
    absolute_result = hdr.calibrate_absolute_reflectance(
        sample_hdr=sample_hdr,
        ag_hdr=ag_hdr,
        ag_theory_reflectance=ag_theory_reflectance.to_numpy(dtype=float),
    )

    hdr_curve_path = output_dirs["hdr_curves"] / f"phase07_{sample_slug}_hdr_curves.csv"
    fit_input_path = output_dirs["fit_inputs"] / f"phase07_{sample_slug}_fit_input.csv"
    hdr.export_curve_table(absolute_result, hdr_curve_path)
    write_phase07_fit_input(
        source_table_path=hdr_curve_path,
        output_path=fit_input_path,
        sample_name=sample_name,
        with_ag=with_ag,
    )

    return SampleSourceRecord(
        sample_name=sample_name,
        with_ag=with_ag,
        source_mode="raw",
        input_path=sample_group.short_file.csv_path.parent,
        hdr_curve_path=hdr_curve_path,
        fit_input_path=fit_input_path,
    )


def build_fit_input_from_hdr_csv(
    hdr_curve_path: Path,
    output_dirs: dict[str, Path],
) -> SampleSourceRecord:
    sample_name = hdr_curve_path.stem.replace("_hdr_curves", "")
    sample_slug = slugify_sample_name(sample_name)
    with_ag = infer_with_ag(sample_name)
    fit_input_path = output_dirs["fit_inputs"] / f"phase07_{sample_slug}_fit_input.csv"
    write_phase07_fit_input(
        source_table_path=hdr_curve_path,
        output_path=fit_input_path,
        sample_name=sample_name,
        with_ag=with_ag,
    )
    return SampleSourceRecord(
        sample_name=sample_name,
        with_ag=with_ag,
        source_mode="hdr_csv",
        input_path=hdr_curve_path,
        hdr_curve_path=hdr_curve_path,
        fit_input_path=fit_input_path,
    )


def discover_sample_sources(data_dir: Path, output_dirs: dict[str, Path]) -> list[SampleSourceRecord]:
    source_map: dict[str, SampleSourceRecord] = {}

    raw_groups = discover_raw_sample_point_groups(data_dir)
    if raw_groups:
        ag_hdr, ag_theory_reflectance = build_ag_reference(data_dir)
        for group in raw_groups:
            record = build_fit_input_from_raw_group(group, ag_hdr, ag_theory_reflectance, output_dirs)
            source_map[record.sample_name] = record

    for hdr_curve_path in sorted(data_dir.glob("*_hdr_curves.csv")):
        record = build_fit_input_from_hdr_csv(hdr_curve_path, output_dirs)
        source_map.setdefault(record.sample_name, record)

    if not source_map:
        raise FileNotFoundError(
            f"{data_dir} 中既未发现原始 `*-cor.csv` 组，也未发现 `*_hdr_curves.csv`。"
        )
    return sorted(source_map.values(), key=lambda item: item.sample_name)


def export_source_manifest(records: list[SampleSourceRecord], output_path: Path) -> None:
    pd.DataFrame(
        [
            {
                "sample_name": item.sample_name,
                "with_ag": item.with_ag,
                "source_mode": item.source_mode,
                "input_path": item.input_path.as_posix(),
                "hdr_curve_path": item.hdr_curve_path.as_posix(),
                "fit_input_path": item.fit_input_path.as_posix(),
            }
            for item in records
        ]
    ).to_csv(output_path, index=False, encoding="utf-8-sig")


def export_batch_fit_summary(results: list[Phase07FitResult], output_path: Path) -> None:
    rows: list[dict[str, object]] = []
    for result in results:
        row: dict[str, object] = {
            "sample_name": result.sample_input.sample_name,
            "with_ag": result.sample_input.with_ag,
            "source_mode": result.sample_input.source_mode,
            "d_C60_bulk_best": result.d_c60_bulk_best,
            "window_cost_front": result.window_cost_front,
            "window_cost_rear": result.window_cost_rear,
            "total_cost": result.total_cost,
            "rear_derivative_correlation": result.rear_derivative_correlation,
            "masked_residual_max_abs": result.masked_band_residual_stats.max_abs,
            "warnings": json_dumps(list(result.warnings)),
            "bound_hit_flags": json_dumps(result.bound_hit_flags),
        }
        for key, value in result.best_params.items():
            row[key] = value
        rows.append(row)
    pd.DataFrame(rows).sort_values("sample_name").to_csv(output_path, index=False, encoding="utf-8-sig")


def json_dumps(payload: object) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def run_single_sample(
    record: SampleSourceRecord,
    model,
    config: Phase07Config,
    output_dirs: dict[str, Path],
) -> Phase07FitResult:
    sample_input: Phase07SampleInput = load_phase07_sample_input(
        fit_input_path=record.fit_input_path,
        sample_name=record.sample_name,
        source_mode=record.source_mode,
        source_path=record.input_path,
        with_ag=record.with_ag,
    )
    result = fit_dual_window_sample(sample_input=sample_input, model=model, config=config)

    sample_slug = slugify_sample_name(record.sample_name)
    curve_table_path = output_dirs["fit_results"] / f"phase07_{sample_slug}_fit_curve.csv"
    summary_path = output_dirs["fit_results"] / f"phase07_{sample_slug}_fit_summary.csv"
    full_figure_path = output_dirs["figures"] / f"phase07_{sample_slug}_full_spectrum.png"
    zoom_figure_path = output_dirs["figures"] / f"phase07_{sample_slug}_dual_window_zoom.png"
    residual_figure_path = output_dirs["figures"] / f"phase07_{sample_slug}_residual_diagnostics.png"
    basin_figure_path = output_dirs["figures"] / f"phase07_{sample_slug}_rear_basin_scan.png"
    log_path = output_dirs["logs"] / f"phase07_{sample_slug}_optimizer_log.md"

    export_fit_curve_table(result, curve_table_path)
    export_fit_summary_table(result, summary_path)
    plot_measured_vs_fitted_full_spectrum(result, full_figure_path)
    plot_dual_window_zoom(result, zoom_figure_path)
    plot_residual_diagnostics(result, residual_figure_path)
    plot_rear_basin_scan(result, basin_figure_path)
    write_optimizer_log(result, log_path)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 07 dual-window inversion pipeline.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Phase 07 输入目录，可同时包含原始多曝光文件或 *_hdr_curves.csv。",
    )
    parser.add_argument(
        "--sample",
        action="append",
        default=None,
        help="仅处理指定 sample_name，可重复传入多次。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    if not input_dir.exists():
        raise FileNotFoundError(f"未找到输入目录: {input_dir}")

    output_dirs = ensure_output_dirs()
    records = discover_sample_sources(input_dir, output_dirs)
    if args.sample:
        requested = set(args.sample)
        records = [item for item in records if item.sample_name in requested]
        if not records:
            raise ValueError(f"未找到任何匹配样本: {sorted(requested)}")

    manifest_path = output_dirs["processed_root"] / "phase07_source_manifest.csv"
    export_source_manifest(records, manifest_path)

    model = build_phase07_stack_model()
    config = Phase07Config.default()
    results: list[Phase07FitResult] = []
    for record in records:
        print(f"[{PHASE_NAME}] Processing {record.sample_name} ({record.source_mode})")
        results.append(run_single_sample(record, model, config, output_dirs))

    batch_summary_path = output_dirs["processed_root"] / "phase07_fit_summary.csv"
    export_batch_fit_summary(results, batch_summary_path)
    print(f"[{PHASE_NAME}] 完成 {len(results)} 个样本。")
    print(f"Source manifest: {manifest_path}")
    print(f"Batch fit summary: {batch_summary_path}")


if __name__ == "__main__":
    main()
