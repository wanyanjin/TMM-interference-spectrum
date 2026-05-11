from __future__ import annotations
import argparse
from pathlib import Path
import sys
REPO_ROOT=Path(__file__).resolve().parents[2]
SRC_ROOT=REPO_ROOT/'src'
if str(SRC_ROOT) not in sys.path: sys.path.insert(0,str(SRC_ROOT))
from storage.materials.material_registry import MaterialRegistry
from workflows.material_registry_workflow import run_material_registry_qc

def main()->int:
    p=argparse.ArgumentParser(); sp=p.add_subparsers(dest='cmd',required=True)
    sp.add_parser('list')
    sh=sp.add_parser('show'); sh.add_argument('--material-id',required=True)
    sp.add_parser('qc')
    a=p.parse_args(); reg=MaterialRegistry(REPO_ROOT)
    if a.cmd=='list':
        for m in reg.list_materials(): print(f"{m.material_id}	{m.material_family}	{m.status}")
    elif a.cmd=='show':
        m=reg.get_entry(a.material_id); print(m)
    else:
        r=run_material_registry_qc(REPO_ROOT); print(r['summary'])
    return 0
if __name__=='__main__': raise SystemExit(main())
