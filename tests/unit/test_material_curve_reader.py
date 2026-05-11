from pathlib import Path
import sys
REPO_ROOT=Path(__file__).resolve().parents[2]
SRC_ROOT=REPO_ROOT/'src'
if str(SRC_ROOT) not in sys.path: sys.path.insert(0,str(SRC_ROOT))
from storage.materials.material_curve_reader import read_material_curve

def test_read_pvk_curve():
    c=read_material_curve(REPO_ROOT/'resources/materials/curves/pvk/pvk__csfapi_phase05c_aligned__v1.csv')
    assert len(c.wavelength_nm)>0
