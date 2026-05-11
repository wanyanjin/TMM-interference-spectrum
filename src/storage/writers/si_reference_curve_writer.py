from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from domain.si_reference import SiReferenceCurveResult


def write_si_reference_csv(result: SiReferenceCurveResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "wavelength_nm": result.wavelength_nm,
        "n_si": result.n_si,
        "k_si": result.k_si,
        "R_air_si": result.r_air_si,
    }
    data.update(result.oxide_curves)
    pd.DataFrame(data).to_csv(output_path, index=False)
    return output_path


def write_metadata_json(metadata: dict[str, object], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def write_plot(result: SiReferenceCurveResult, output_path: Path, x_min: float, x_max: float) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mask = (result.wavelength_nm >= x_min) & (result.wavelength_nm <= x_max)
    plt.figure(figsize=(9, 6))
    plt.plot(result.wavelength_nm[mask], result.r_air_si[mask], label="R_air_si", linewidth=2.0)
    for key, values in result.oxide_curves.items():
        plt.plot(result.wavelength_nm[mask], values[mask], label=key, linewidth=1.4)
    plt.xlim(x_min, x_max)
    plt.ylim(0.0, 1.0)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance (0-1)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()
    return output_path
