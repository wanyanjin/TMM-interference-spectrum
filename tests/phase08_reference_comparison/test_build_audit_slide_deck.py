from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "src" / "scripts" / "step08_build_audit_slide_deck.py"
SPEC = importlib.util.spec_from_file_location("step08_build_audit_slide_deck", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class BuildAuditSlideDeckTest(unittest.TestCase):
    def test_context_600nm_values_match_expected(self) -> None:
        ctx = MODULE.load_context()
        row = ctx.row_600
        self.assertAlmostEqual(float(row["R_Exp_GlassPVK_by_GlassAg"]), 0.290941137958624, places=12)
        self.assertAlmostEqual(float(row["R_Exp_GlassPVK_by_AgMirror"]), 0.2639502808767898, places=12)
        self.assertAlmostEqual(float(row["R_TMM_GlassPVK_Fixed"]), 0.1287618702077688, places=12)

    def test_generated_html_has_no_absolute_paths_or_external_urls(self) -> None:
        MODULE.ensure_dirs()
        ctx = MODULE.load_context()
        assets = MODULE.generate_assets(ctx)
        deck_html = MODULE.build_deck_html(ctx, assets)
        report_html = MODULE.build_technical_report_html(ctx, assets)
        self.assertNotIn("/Users/luxin/", deck_html)
        self.assertNotIn("/Users/luxin/", report_html)
        self.assertNotIn("http://", deck_html)
        self.assertNotIn("https://", deck_html)
        self.assertIn("phase08_reference_audit_deck.html", str(MODULE.DECK_HTML))


if __name__ == "__main__":
    unittest.main()
