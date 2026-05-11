from __future__ import annotations
import json
from pathlib import Path
from domain.optical_material import MaterialIndexEntry, MaterialRegistryIndex
from storage.materials.material_curve_reader import read_material_curve, read_material_meta

class MaterialRegistry:
    def __init__(self, repo_root: Path, index_path: Path|None=None):
        self.repo_root=repo_root
        self.index_path=index_path or repo_root/"resources/materials/registry/materials_index.json"
        raw=json.loads(self.index_path.read_text(encoding="utf-8"))
        mats=[MaterialIndexEntry(**m) for m in raw["materials"]]
        self.index=MaterialRegistryIndex(raw.get("schema_version","1.0"), mats)
        self._by_id={m.material_id:m for m in mats}
    def list_materials(self): return list(self.index.materials)
    def get_entry(self, material_id:str):
        if material_id not in self._by_id: raise KeyError(f"Unknown material_id: {material_id}")
        return self._by_id[material_id]
    def get_curve(self, material_id:str):
        e=self.get_entry(material_id); return read_material_curve(self.repo_root/e.curve_path)
    def get_meta(self, material_id:str):
        e=self.get_entry(material_id); return read_material_meta(self.repo_root/e.meta_path)
    def list_by_family(self,family:str): return [m for m in self.index.materials if m.material_family==family]
    def covers(self, material_id:str, wmin:float, wmax:float)->bool:
        m=self.get_meta(material_id); return m.wavelength_min_nm<=wmin and m.wavelength_max_nm>=wmax
    def requires_extrapolation(self, material_id:str, wmin:float, wmax:float)->bool: return not self.covers(material_id,wmin,wmax)
