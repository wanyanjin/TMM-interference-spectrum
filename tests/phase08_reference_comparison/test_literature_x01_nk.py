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

from core import literature_x01_nk as lit_x01


class LiteratureX01NkTest(unittest.TestCase):
    def test_extract_x01_rows_from_docx(self) -> None:
        docx_path = REPO_ROOT / "resources" / "1-s2.0-S0927024818304446-mmc1.docx"
        frame = lit_x01.extract_x01_epsilon_from_docx(docx_path)
        self.assertGreater(frame.shape[0], 600)
        self.assertIn("Photon_Energy_eV", frame.columns)
        self.assertIn("Epsilon1", frame.columns)
        self.assertIn("Epsilon2", frame.columns)
        self.assertAlmostEqual(float(frame.iloc[0]["Photon_Energy_eV"]), 5.88683, places=5)

    def test_epsilon_to_nk_finite_and_sorted(self) -> None:
        epsilon_df = pd.DataFrame(
            {
                "Photon_Energy_eV": [2.0, 1.5],
                "Epsilon1": [4.0, 5.0],
                "Epsilon2": [1.0, 0.5],
            }
        )
        nk_df = lit_x01.epsilon_to_nk_table(epsilon_df)
        self.assertTrue(np.isfinite(nk_df["n"].to_numpy(dtype=float)).all())
        self.assertTrue(np.isfinite(nk_df["k"].to_numpy(dtype=float)).all())
        self.assertTrue((nk_df["k"].to_numpy(dtype=float) >= 0.0).all())
        self.assertTrue(np.all(np.diff(nk_df["Wavelength_nm"].to_numpy(dtype=float)) > 0.0))

    def test_build_phase08_aligned_replaces_only_pvk(self) -> None:
        base_path = REPO_ROOT / "resources" / "aligned_full_stack_nk.csv"
        docx_path = REPO_ROOT / "resources" / "1-s2.0-S0927024818304446-mmc1.docx"
        epsilon_df = lit_x01.extract_x01_epsilon_from_docx(docx_path)
        nk_df = lit_x01.epsilon_to_nk_table(epsilon_df)
        with tempfile.TemporaryDirectory() as tmp:
            nk_csv = Path(tmp) / "x01.csv"
            nk_df.to_csv(nk_csv, index=False, encoding="utf-8-sig")
            aligned = lit_x01.build_phase08_x01_aligned_nk(base_path, nk_csv)
        base_df = pd.read_csv(base_path)
        self.assertEqual(aligned.columns.tolist(), base_df.columns.tolist())
        np.testing.assert_allclose(aligned["n_Glass"].to_numpy(dtype=float), base_df["n_Glass"].to_numpy(dtype=float))
        np.testing.assert_allclose(aligned["k_Ag"].to_numpy(dtype=float), base_df["k_Ag"].to_numpy(dtype=float))
        self.assertFalse(np.allclose(aligned["n_PVK"].to_numpy(dtype=float), base_df["n_PVK"].to_numpy(dtype=float)))


if __name__ == "__main__":
    unittest.main()
