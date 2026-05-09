from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import unittest

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "src" / "scripts" / "step09d_two_layer_interference_spectra.py"
SPEC = importlib.util.spec_from_file_location("step09d_two_layer_interference_spectra", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class Step09DTwoLayerInterferenceTest(unittest.TestCase):
    def test_build_output_frame_contains_expected_columns(self) -> None:
        nk_frame = MODULE.load_nk_table(REPO_ROOT / "resources" / "aligned_full_stack_nk.csv")
        output = MODULE.build_output_frame(nk_frame)
        self.assertEqual(float(output["Wavelength_nm"].min()), 400.0)
        self.assertEqual(float(output["Wavelength_nm"].max()), 1100.0)
        expected = {
            "Wavelength_nm",
            "R_glass_1mm_pvk_700nm",
            "T_glass_1mm_pvk_700nm",
            "A_glass_1mm_pvk_700nm",
            "R_pvk_700nm_glass_1mm",
            "T_pvk_700nm_glass_1mm",
            "A_pvk_700nm_glass_1mm",
        }
        self.assertEqual(set(output.columns), expected)
        numeric = output.drop(columns=["Wavelength_nm"]).to_numpy(dtype=float)
        self.assertTrue(np.isfinite(numeric).all())
        self.assertTrue((output.filter(regex="^(R|T|A)_").to_numpy(dtype=float) >= -1e-9).all())

    def test_manifest_summary_is_consistent(self) -> None:
        nk_frame = MODULE.load_nk_table(REPO_ROOT / "resources" / "aligned_full_stack_nk.csv")
        output = MODULE.build_output_frame(nk_frame)
        manifest = MODULE.build_manifest(
            output_frame=output,
            csv_path=REPO_ROOT / "data" / "processed" / "phase09" / "two_layer_interference" / "out.csv",
            png_path=REPO_ROOT / "results" / "figures" / "phase09" / "two_layer_interference" / "out.png",
            pdf_path=REPO_ROOT / "results" / "figures" / "phase09" / "two_layer_interference" / "out.pdf",
            report_path=REPO_ROOT / "results" / "report" / "phase09_two_layer_interference" / "out.md",
        )
        summary = manifest["summary"]
        self.assertEqual(summary["point_count"], 701)
        self.assertAlmostEqual(summary["wavelength_min_nm"], 400.0, places=9)
        self.assertAlmostEqual(summary["wavelength_max_nm"], 1100.0, places=9)


if __name__ == "__main__":
    unittest.main()
