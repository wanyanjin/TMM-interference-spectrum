from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from core.si_reference_curve import build_si_reference_curve
from storage.writers.si_reference_curve_writer import write_metadata_json, write_plot, write_si_reference_csv

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SI_NK_CSV = REPO_ROOT / "resources" / "optical_constants" / "si" / "si_crystalline_green_2008_nk.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "resources" / "reference_curves" / "si"


@dataclass(frozen=True)
class SiReferenceCurveWorkflowConfig:
    si_nk_csv: Path = DEFAULT_SI_NK_CSV
    output_root: Path = DEFAULT_OUTPUT_DIR
    output_tag: str | None = None
    wavelength_min_nm: float = 400.0
    wavelength_max_nm: float = 1000.0
    oxide_thickness_nm: tuple[float, ...] = (0.0, 1.0, 2.0, 3.0, 5.0)


def run_si_reference_curve_workflow(config: SiReferenceCurveWorkflowConfig) -> dict[str, Path]:
    nk = pd.read_csv(config.si_nk_csv).sort_values("wavelength_nm")
    if config.wavelength_min_nm < float(nk["wavelength_nm"].min()) or config.wavelength_max_nm > float(nk["wavelength_nm"].max()):
        raise ValueError("Requested wavelength range is outside Si/Green-2008 source range")
    sel = nk[(nk["wavelength_nm"] >= config.wavelength_min_nm) & (nk["wavelength_nm"] <= config.wavelength_max_nm)]
    wl = sel["wavelength_nm"].to_numpy(dtype=float)
    result = build_si_reference_curve(
        wavelength_nm=wl,
        n_si=sel["n_si"].to_numpy(dtype=float),
        k_si=sel["k_si"].to_numpy(dtype=float),
        oxide_nm=list(config.oxide_thickness_nm),
        n_sio2=1.46,
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = f"_{config.output_tag}" if config.output_tag else ""
    stem = f"{timestamp}_si_reference_curve{tag}"
    output_dir = config.output_root
    csv_path = output_dir / "si_air_reflectance_green_2008_400_1000nm.csv"
    meta_path = output_dir / "metadata.json"
    fig_full = output_dir / f"{stem}_400_1000nm.png"
    fig_zoom = output_dir / f"{stem}_500_750nm.png"
    write_si_reference_csv(result, csv_path)
    write_plot(result, fig_full, 400.0, 1000.0)
    write_plot(result, fig_zoom, 500.0, 750.0)
    metadata = {"generated_at": datetime.now().isoformat(), "model": "Air/Si and Air/SiO2/Si", "reflectance_unit": "0-1"}
    write_metadata_json(metadata, meta_path)
    return {"csv": csv_path, "metadata": meta_path, "figure_full": fig_full, "figure_zoom": fig_zoom}
