from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "src" / "scripts" / "step08_single_wavelength_trace.py"
SPEC = importlib.util.spec_from_file_location("step08_single_wavelength_trace", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SingleWavelengthTraceTest(unittest.TestCase):
    def test_single_layer_trace_matches_coh_tmm(self) -> None:
        entry = MODULE.single_layer_trace(
            n0=1.515 + 0.0j,
            n1=2.1 + 0.3j,
            n2=1.0 + 0.0j,
            d1_nm=700.0,
            wavelength_nm=600.0,
            label="test",
        )
        self.assertTrue(entry["consistency_pass"])
        self.assertLessEqual(entry["absolute_difference"], MODULE.ABS_TOL)

    def test_incoherent_cascade_matches_reference_formula(self) -> None:
        result = MODULE.incoherent_cascade_trace(0.04, 0.12)
        expected = 0.04 + (1.0 - 0.04) ** 2 * 0.12 / (1.0 - 0.04 * 0.12)
        self.assertAlmostEqual(result["R_total"], expected, places=15)


if __name__ == "__main__":
    unittest.main()
