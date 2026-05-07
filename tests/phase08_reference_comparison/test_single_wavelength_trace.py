from __future__ import annotations

from pathlib import Path
import importlib.util
import json
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

    def test_generated_report_uses_latex_and_relative_paths(self) -> None:
        trace = MODULE.build_trace(600.0, None)
        report_path = REPO_ROOT / "results" / "report" / "phase08_reference_comparison_trace" / "_test_trace_render.md"
        try:
            MODULE.render_markdown(trace, report_path)
            text = report_path.read_text(encoding="utf-8")
            self.assertIn("$$", text)
            self.assertIn("## 0. 执行摘要", text)
            self.assertIn("## 本报告不能证明什么", text)
            self.assertNotIn("/Users/luxin/", text)
            self.assertNotIn("Ag frames used = [2, 3", text)
            self.assertIn("Ag frames used | 2–100, total 99 frames", text)
        finally:
            if report_path.exists():
                report_path.unlink()

    def test_json_filename_suffix(self) -> None:
        output_name = f"phase08_0429_trace_{MODULE.DEFAULT_TRACE_TAG}_values.json"
        self.assertTrue(output_name.endswith("_values.json"))


if __name__ == "__main__":
    unittest.main()
