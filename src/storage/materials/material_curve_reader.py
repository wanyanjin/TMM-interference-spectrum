from __future__ import annotations
import csv
import json
import math
from pathlib import Path
from domain.optical_material import OpticalConstantCurve, OpticalMaterialMeta
REQ_COLS=["wavelength_nm","n","k","region","quality_flag"]

def read_material_curve(curve_path: Path) -> OpticalConstantCurve:
    with curve_path.open("r",encoding="utf-8",newline="") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("empty csv")
        miss=[c for c in REQ_COLS if c not in reader.fieldnames]
        if miss:
            raise ValueError(f"Missing columns: {miss}")
        w=[]; n=[]; k=[]; region=[]; q=[]
        for row in reader:
            wf=float(row["wavelength_nm"]); nf=float(row["n"]); kf=float(row["k"])
            if not (math.isfinite(wf) and math.isfinite(nf) and math.isfinite(kf)):
                raise ValueError("NaN/Inf detected")
            if kf<0: raise ValueError("k must be >= 0")
            w.append(wf); n.append(nf); k.append(kf); region.append(str(row["region"])); q.append(str(row["quality_flag"]))
    if any(w[i]>=w[i+1] for i in range(len(w)-1)):
        raise ValueError("wavelength_nm must be strictly increasing")
    return OpticalConstantCurve(curve_path.stem,w,n,k,region,q)

def read_material_meta(meta_path: Path) -> OpticalMaterialMeta:
    m=json.loads(meta_path.read_text(encoding="utf-8")); r=m["wavelength_range_nm"]
    return OpticalMaterialMeta(m["material_id"],m["material_family"],m["source_type"],m["status"],m["confidence_level"],float(r["min"]),float(r["max"]))
