from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path


class ReferenceComparisonCliTest(unittest.TestCase):
    def test_cli_dry_run(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        sample = repo / "test_data" / "0429" / "glass-PVK-withoutfliter-20ms 2026 四月 29 14_45_45.csv"
        reference = repo / "test_data" / "0429" / "glass-Ag-withoutfliter-20ms 2026 四月 29 14_42_25.csv"
        cmd = [
            str(repo / ".venv" / "bin" / "python"),
            str(repo / "src" / "cli" / "reference_comparison.py"),
            "--sample-csv",
            str(sample),
            "--reference-csv",
            str(reference),
            "--dry-run",
        ]
        env = os.environ.copy()
        env["MPLCONFIGDIR"] = "/private/tmp/.mpl"
        result = subprocess.run(cmd, check=True, text=True, capture_output=True, cwd=repo, env=env)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "dry_run")
        self.assertGreater(payload["strict_point_count_primary"], 0)
        self.assertEqual(payload["sample_exposure_source"], "filename_inference")


if __name__ == "__main__":
    unittest.main()
