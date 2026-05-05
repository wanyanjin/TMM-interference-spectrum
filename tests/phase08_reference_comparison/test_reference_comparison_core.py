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

    def test_multiframe_column_recognition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "mf.csv"
            csv_path.write_text("1,2,400.0,0,0,100\n1,2,401.0,0,1,120\n", encoding="utf-8")
            df = rc.load_multiframe_spectrum_csv(csv_path)
            self.assertEqual(list(df.columns), ["Frame_Index", "Wavelength_nm", "Pixel_Index", "Counts"])
            self.assertEqual(df.shape[0], 2)

    def test_ag_bk_pixel_alignment_and_drop_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ag_path = Path(tmp) / "ag.csv"
            bk_path = Path(tmp) / "bk.csv"
            ag_rows = [
                "1,1,400,0,0,65535",
                "1,1,401,0,1,65535",
                "1,2,400,0,0,1000",
                "1,2,401,0,1,1200",
                "1,3,400,0,0,1100",
                "1,3,401,0,1,1300",
            ]
            bk_rows = [
                "1,1,550,0,0,100",
                "1,1,551,0,1,200",
                "1,2,550,0,0,120",
                "1,2,551,0,1,220",
            ]
            ag_path.write_text("\n".join(ag_rows) + "\n", encoding="utf-8")
            bk_path.write_text("\n".join(bk_rows) + "\n", encoding="utf-8")
            corrected, qc, diag = rc.build_ag_mirror_corrected_spectrum(
                ag_csv=ag_path,
                bk_csv=bk_path,
                drop_frames=(1,),
                align_mode="pixel",
            )
            self.assertEqual(corrected.shape[0], 2)
            # Ag mean: [1050,1250], bk mean: [110,210]
            np.testing.assert_allclose(corrected["Intensity"].to_numpy(dtype=float), np.array([940.0, 1040.0]))
            self.assertGreater(diag["bk_wavelength_offset_median_nm"], 100.0)
            ag_qc = qc[qc["Source"] == "Ag"]
            used_f1 = ag_qc.loc[ag_qc["Frame_Index"] == 1, "Used_For_Average"].iloc[0]
            self.assertFalse(bool(used_f1))


if __name__ == "__main__":
    unittest.main()
