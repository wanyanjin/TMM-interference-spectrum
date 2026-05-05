from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import sys

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core import reference_comparison as rc


class ReferenceComparisonCoreTest(unittest.TestCase):
    def test_csv_column_recognition_with_wavelength_intensity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "sample.csv"
            csv_path.write_text("Wavelength,Intensity\n400,100\n401,120\n", encoding="utf-8")
            df = rc.load_measurement_csv(csv_path)
            self.assertEqual(list(df.columns), ["Wavelength_nm", "Counts"])
            self.assertEqual(df.shape[0], 2)

    def test_reflectance_formula_with_exposure_normalization(self) -> None:
        i_pvk = np.array([100.0, 200.0])
        i_ag = np.array([50.0, 100.0])
        t_pvk = 20.0
        t_ag = 20.0
        r_tmm_ag = np.array([0.8, 0.6])
        r_exp = (i_pvk / t_pvk) / (i_ag / t_ag) * r_tmm_ag
        np.testing.assert_allclose(r_exp, np.array([1.6, 1.2]), rtol=0.0, atol=1e-12)

    def test_mask_logic_floor_and_reason(self) -> None:
        sample = np.array([-1.0, 1.0, 12.0, 30.0], dtype=float)
        ref = np.array([5.0, -2.0, 8.0, 31.0], dtype=float)
        loose, strict, floor = rc.build_masks(sample, ref)
        self.assertEqual(floor, 10.0)
        self.assertEqual(loose.tolist(), [False, False, True, True])
        self.assertEqual(strict.tolist(), [False, False, False, True])
        reasons = rc.build_mask_reason(
            counts_sample=sample,
            counts_ref=ref,
            finite_mask=np.isfinite(sample) & np.isfinite(ref),
            loose_mask=loose,
            strict_mask=strict,
            floor=floor,
        )
        self.assertEqual(reasons[-1], "ok")

    def test_tmm_output_smoke_finite_and_nonnegative(self) -> None:
        nk = pd.read_csv("resources/aligned_full_stack_nk.csv")
        wl = nk["Wavelength_nm"].to_numpy(dtype=float)[::50]
        n_glass = (nk["n_Glass"] + 1j * nk["k_Glass"]).to_numpy(dtype=np.complex128)[::50]
        n_ag = (nk["n_Ag"] + 1j * nk["k_Ag"]).to_numpy(dtype=np.complex128)[::50]
        n_pvk = (nk["n_PVK"] + 1j * nk["k_PVK"]).to_numpy(dtype=np.complex128)[::50]
        r_front = rc.front_surface_reflectance(n_glass)
        r_ag_stack = rc.calc_stack_reflectance_glass_ag(wl, n_glass, n_ag, d_ag_nm=100.0)
        r_pvk_stack = rc.calc_stack_reflectance_glass_pvk(wl, n_glass, n_pvk, d_pvk_nm=700.0)
        r_ag = rc.calc_macro_reflectance(r_front, r_ag_stack)
        r_pvk = rc.calc_macro_reflectance(r_front, r_pvk_stack)
        self.assertTrue(np.isfinite(r_ag).all())
        self.assertTrue(np.isfinite(r_pvk).all())
        self.assertTrue((r_ag >= 0.0).all())
        self.assertTrue((r_pvk >= 0.0).all())


if __name__ == "__main__":
    unittest.main()
