from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from gui.reflectance_qc.io import load_processed_reflectance_csv, load_qc_summary_json
from gui.reflectance_qc.main_window import ReflectanceQCMainWindow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reflectance QC GUI (Phase 09C-2)")
    parser.add_argument("--processed-csv", type=Path, default=None)
    parser.add_argument("--qc-summary-json", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = QApplication(sys.argv)
    window = ReflectanceQCMainWindow()
    if args.processed_csv:
        window._loaded_data = load_processed_reflectance_csv(args.processed_csv)
        window._processed_csv_path = args.processed_csv
    if args.qc_summary_json:
        window._qc_summary = load_qc_summary_json(args.qc_summary_json)
        window._qc_json_path = args.qc_summary_json
    window.show()
    if window._loaded_data is not None:
        window._refresh_plot()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
