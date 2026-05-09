from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import tempfile
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "src" / "scripts" / "step09e_fetch_refractiveindex_materials.py"
SPEC = importlib.util.spec_from_file_location("step09e_fetch_refractiveindex_materials", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


SI_YAML = """# header
REFERENCES: |
    ref line
COMMENTS: |
    test comment
DATA:
  - type: tabulated nk
    data: |
        0.40 5.623 3.2627E-01
        0.41 5.341 2.4127E-01
        0.42 5.110 1.7694E-01
CONDITIONS:
    temperature: 295
"""

SIO2_YAML = """# header
REFERENCES: |
    ref line
COMMENTS: |
    Fused silica
DATA:
  - type: formula 1
    wavelength_range: 0.21 6.7
    coefficients: 0 0.6961663 0.0684043 0.4079426 0.1162414 0.8974794 9.896161
CONDITIONS:
    temperature: 293
"""


class Step09EFetchRefractiveindexMaterialsTest(unittest.TestCase):
    def test_parse_tabulated_nk_yaml(self) -> None:
        frame = MODULE.parse_tabulated_nk_yaml(SI_YAML)
        self.assertEqual(frame.columns.tolist(), ["Wavelength_nm", "n", "k"])
        self.assertEqual(frame.shape[0], 3)
        self.assertAlmostEqual(frame["Wavelength_nm"].iloc[0], 400.0, places=9)
        self.assertTrue((frame["k"].to_numpy(dtype=float) >= 0.0).all())

    def test_build_sio2_formula_csv(self) -> None:
        frame = MODULE.build_sio2_formula_csv(SIO2_YAML)
        self.assertEqual(frame["Wavelength_nm"].iloc[0], 400.0)
        self.assertEqual(frame["Wavelength_nm"].iloc[-1], 1100.0)
        self.assertEqual(frame.shape[0], 701)
        self.assertTrue(np.isfinite(frame[["n", "k"]].to_numpy(dtype=float)).all())
        self.assertTrue((frame["k"].to_numpy(dtype=float) == 0.0).all())

    def test_extract_literal_block(self) -> None:
        references = MODULE.extract_literal_block(SIO2_YAML, "REFERENCES", ("COMMENTS", "DATA", "CONDITIONS"))
        comments = MODULE.extract_literal_block(SIO2_YAML, "COMMENTS", ("DATA", "CONDITIONS"))
        self.assertIn("ref line", references)
        self.assertEqual(comments, "Fused silica")

    def test_dry_run_returns_selected_materials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            args = MODULE.parse_args.__globals__["argparse"].Namespace(
                materials=["Si", "SiO2"],
                output_root=Path(tmp),
                timeout_seconds=5.0,
                dry_run=True,
            )
            payload = MODULE.run(args)
            self.assertEqual(len(payload["materials"]), 2)
            self.assertIn("page_url", payload["materials"][0])


if __name__ == "__main__":
    unittest.main()
