from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "src" / "scripts" / "step09f_si_air_interface_reflectance.py"
SPEC = importlib.util.spec_from_file_location("step09f_si_air_interface_reflectance", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class Step09FSiAirInterfaceReflectanceTest(unittest.TestCase):
    def test_fresnel_reflectance_finite_and_bounded(self) -> None:
        si_frame = MODULE.load_si_nk(REPO_ROOT / "resources" / "refractiveindex_info" / "normalized" / "si_schinke_2015_nk.csv")
        output = MODULE.build_output_frame(si_frame)
        reflectance = output["R_Si_Air"].to_numpy(dtype=float)
        self.assertEqual(float(output["Wavelength_nm"].min()), 400.0)
        self.assertEqual(float(output["Wavelength_nm"].max()), 1100.0)
        self.assertEqual(output.shape[0], 71)
        self.assertTrue(np.isfinite(reflectance).all())
        self.assertTrue((reflectance >= 0.0).all())
        self.assertTrue((reflectance <= 1.0).all())

    def test_manifest_contains_expected_summary_keys(self) -> None:
        si_frame = MODULE.load_si_nk(REPO_ROOT / "resources" / "refractiveindex_info" / "normalized" / "si_schinke_2015_nk.csv")
        output = MODULE.build_output_frame(si_frame)
        manifest = MODULE.build_manifest(
            output,
            REPO_ROOT / "data" / "processed" / "phase09" / "si_air_interface" / "x.csv",
            REPO_ROOT / "results" / "figures" / "phase09" / "si_air_interface" / "x.png",
            REPO_ROOT / "results" / "figures" / "phase09" / "si_air_interface" / "x.pdf",
            REPO_ROOT / "results" / "report" / "phase09_si_air_interface" / "x.md",
        )
        summary = manifest["summary"]
        self.assertIn("reflectance_400nm", summary)
        self.assertIn("reflectance_600nm", summary)
        self.assertIn("reflectance_1100nm", summary)


if __name__ == "__main__":
    unittest.main()
