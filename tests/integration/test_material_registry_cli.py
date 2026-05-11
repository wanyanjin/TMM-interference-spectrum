from pathlib import Path
import subprocess, sys
REPO_ROOT=Path(__file__).resolve().parents[2]

def test_cli_list_runs():
    p=subprocess.run([sys.executable,'src/cli/material_registry.py','list'],cwd=REPO_ROOT,capture_output=True,text=True)
    assert p.returncode==0
    assert 'pvk__csfapi_phase05c_aligned__v1' in p.stdout
