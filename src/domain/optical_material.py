from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class OpticalMaterialMeta:
    material_id: str
    material_family: str
    source_type: str
    status: str
    confidence_level: str
    wavelength_min_nm: float
    wavelength_max_nm: float

@dataclass(frozen=True)
class OpticalConstantCurve:
    material_id: str
    wavelength_nm: list[float]
    n: list[float]
    k: list[float]
    region: list[str]
    quality_flag: list[str]

@dataclass(frozen=True)
class MaterialIndexEntry:
    material_id: str
    material_family: str
    display_name: str
    curve_path: str
    meta_path: str
    status: str
    confidence_level: str

@dataclass(frozen=True)
class MaterialRegistryIndex:
    schema_version: str
    materials: list[MaterialIndexEntry]

@dataclass(frozen=True)
class MaterialQCResult:
    material_id: str
    passed: bool
    issues: list[str]
