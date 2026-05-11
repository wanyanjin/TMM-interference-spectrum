from pathlib import Path
import sys
REPO_ROOT=Path(__file__).resolve().parents[2]
SRC_ROOT=REPO_ROOT/'src'
if str(SRC_ROOT) not in sys.path: sys.path.insert(0,str(SRC_ROOT))
from storage.materials.material_registry import MaterialRegistry

def test_registry_load_and_list():
    r=MaterialRegistry(REPO_ROOT)
    assert len(r.list_materials())>=9

def test_missing_material_error():
    r=MaterialRegistry(REPO_ROOT)
    try:
        r.get_entry('nope')
        assert False
    except KeyError:
        assert True
