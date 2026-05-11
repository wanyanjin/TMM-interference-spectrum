from __future__ import annotations
import json
from pathlib import Path
from storage.materials.material_registry import MaterialRegistry

def run_material_registry_qc(repo_root: Path)->dict:
    reg=MaterialRegistry(repo_root)
    issues=[]
    for m in reg.list_materials():
        try:
            curve=reg.get_curve(m.material_id)
            meta=reg.get_meta(m.material_id)
            if m.material_id!=meta.material_id: issues.append(f"{m.material_id}: meta material_id mismatch")
            if curve.material_id!=m.material_id: issues.append(f"{m.material_id}: curve filename mismatch")
            if not (meta.wavelength_min_nm<=curve.wavelength_nm[0] and meta.wavelength_max_nm>=curve.wavelength_nm[-1]):
                issues.append(f"{m.material_id}: meta range mismatch")
            if ":/" in m.curve_path or ":\\" in m.curve_path or ":/" in m.meta_path or ":\\" in m.meta_path:
                issues.append(f"{m.material_id}: absolute path detected")
        except Exception as e:
            issues.append(f"{m.material_id}: {e}")
    out_json=repo_root/'data/processed/phase10/material_registry/material_registry_qc_summary.json'
    out_md=repo_root/'results/report/phase10_material_registry/material_registry_qc_report.md'
    out_json.parent.mkdir(parents=True,exist_ok=True); out_md.parent.mkdir(parents=True,exist_ok=True)
    summary={'total':len(reg.list_materials()),'issues':issues,'passed':len(issues)==0}
    out_json.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Material Registry QC Report','',f"- passed: {summary['passed']}",f"- total: {summary['total']}",f"- issue_count: {len(issues)}",'','## Issues']
    lines += [f"- {x}" for x in issues] if issues else ['- none']
    out_md.write_text("\n".join(lines),encoding='utf-8')
    return {'summary':summary,'summary_path':out_json,'report_path':out_md}
