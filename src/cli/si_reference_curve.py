from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from workflows.si_reference_curve_workflow import SiReferenceCurveWorkflowConfig, run_si_reference_curve_workflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Si theoretical reference reflectance curve.")
    parser.add_argument("--si-nk-csv", default=str(REPO_ROOT / "resources/optical_constants/si/si_crystalline_green_2008_nk.csv"))
    parser.add_argument("--output-root", default=str(REPO_ROOT / "resources/reference_curves/si"))
    parser.add_argument("--output-tag")
    parser.add_argument("--wavelength-range", default="400-1000")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    wl_min, wl_max = [float(x) for x in args.wavelength_range.split("-", maxsplit=1)]
    outputs = run_si_reference_curve_workflow(
        SiReferenceCurveWorkflowConfig(
            si_nk_csv=Path(args.si_nk_csv),
            output_root=Path(args.output_root),
            output_tag=args.output_tag,
            wavelength_min_nm=wl_min,
            wavelength_max_nm=wl_max,
        )
    )
    print("si_reference_curve completed")
    for key, value in outputs.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
