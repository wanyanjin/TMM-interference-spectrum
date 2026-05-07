from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from workflows.reflectance_qc_workflow import (
    ReflectanceQCWorkflowConfig,
    run_reflectance_qc_workflow,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run minimal reflectance QC on sample/reference spectra.")
    parser.add_argument("--sample-csv", required=True)
    parser.add_argument("--reference-csv", required=True)
    parser.add_argument("--sample-exposure-ms", type=float)
    parser.add_argument("--reference-exposure-ms", type=float)
    parser.add_argument("--exposure-normalize", action="store_true")
    parser.add_argument("--wavelength-range", help="Format: min-max, e.g. 400-750")
    parser.add_argument("--output-root", default=str(REPO_ROOT))
    parser.add_argument("--output-tag")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def parse_wavelength_range(value: str | None) -> tuple[float | None, float | None]:
    if value is None:
        return None, None
    try:
        lower_text, upper_text = value.split("-", maxsplit=1)
        return float(lower_text), float(upper_text)
    except ValueError as exc:
        raise SystemExit(f"Invalid --wavelength-range value: {value}. Expected format min-max.") from exc


def main() -> int:
    args = parse_args()
    wavelength_min_nm, wavelength_max_nm = parse_wavelength_range(args.wavelength_range)
    config = ReflectanceQCWorkflowConfig(
        sample_path=Path(args.sample_csv),
        reference_path=Path(args.reference_csv),
        output_root=Path(args.output_root),
        output_tag=args.output_tag,
        sample_exposure_ms=args.sample_exposure_ms,
        reference_exposure_ms=args.reference_exposure_ms,
        exposure_normalization_enabled=args.exposure_normalize,
        wavelength_min_nm=wavelength_min_nm,
        wavelength_max_nm=wavelength_max_nm,
    )

    if args.dry_run:
        print("Reflectance QC dry run.")
        print(f"sample_csv: {config.sample_path}")
        print(f"reference_csv: {config.reference_path}")
        print(f"output_root: {config.output_root}")
        print(f"wavelength_range: {config.wavelength_min_nm}-{config.wavelength_max_nm}")
        print(f"exposure_normalization_enabled: {config.exposure_normalization_enabled}")
        return 0

    result = run_reflectance_qc_workflow(config)
    print("Reflectance QC completed.")
    print(f"overall_status: {result['qc_summary'].overall_status}")
    print(f"processed_csv: {result['processed_csv']}")
    print(f"qc_summary_json: {result['qc_summary_json']}")
    print(f"qc_report_md: {result['qc_report_md']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
