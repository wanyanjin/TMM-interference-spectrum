"""Phase 06 full-stack microcavity sandbox utilities.

This module consumes the Phase 05c engineered optical-constant table and builds
three full-device reflection models:

- Baseline: Glass / ITO / NiOx / PVK / C60 / Ag
- Case A:   Glass / ITO / NiOx / PVK / C60 / Air_Gap / Ag
- Case B:   Glass / ITO / NiOx / PVK / Air_Gap / C60 / Ag

The PVK column in ``aligned_full_stack_nk.csv`` ultimately traces back to the
Phase 05c stitching workflow, which uses [LIT-0001] for the 450-1000 nm source
window and controlled extrapolation outside that window.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from tmm import coh_tmm


WAVELENGTH_MIN_NM = 400
WAVELENGTH_MAX_NM = 1100
WAVELENGTH_STEP_NM = 1
EXPECTED_WAVELENGTHS_NM = np.arange(
    WAVELENGTH_MIN_NM,
    WAVELENGTH_MAX_NM + WAVELENGTH_STEP_NM,
    WAVELENGTH_STEP_NM,
    dtype=float,
)

AIR_INDEX = 1.0 + 0.0j
PVK_THICKNESS_NM = 500.0
ITO_THICKNESS_NM = 19.595
NIOX_THICKNESS_NM = 22.443
C60_THICKNESS_NM = 18.494
THICKNESS_TOLERANCE_NM = 1e-6

MODE_BASELINE = "baseline"
MODE_CASE_A = "case_a"
MODE_CASE_B = "case_b"
SUPPORTED_MODES = (MODE_BASELINE, MODE_CASE_A, MODE_CASE_B)

REQUIRED_COLUMNS = (
    "Wavelength_nm",
    "n_Glass",
    "k_Glass",
    "n_ITO",
    "k_ITO",
    "n_NiOx",
    "k_NiOx",
    "n_PVK",
    "k_PVK",
    "n_C60",
    "k_C60",
    "n_Ag",
    "k_Ag",
)


@dataclass(frozen=True)
class LayerThicknesses:
    ito_nm: float
    niox_nm: float
    pvk_nm: float
    c60_nm: float


@dataclass(frozen=True)
class OpticalStackTable:
    wavelength_nm: np.ndarray
    n_glass: np.ndarray
    n_ito: np.ndarray
    n_niox: np.ndarray
    n_pvk: np.ndarray
    n_c60: np.ndarray
    n_ag: np.ndarray
    thicknesses: LayerThicknesses

    @classmethod
    def from_files(
        cls,
        nk_csv_path: Path,
        material_db_path: Path,
        pvk_thickness_nm: float = PVK_THICKNESS_NM,
    ) -> "OpticalStackTable":
        frame = pd.read_csv(nk_csv_path)
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
        if missing_columns:
            raise ValueError(f"aligned_full_stack_nk.csv 缺少必要列: {missing_columns}")

        wavelength_nm = frame["Wavelength_nm"].to_numpy(dtype=float)
        if wavelength_nm.shape != EXPECTED_WAVELENGTHS_NM.shape or not np.array_equal(
            wavelength_nm,
            EXPECTED_WAVELENGTHS_NM,
        ):
            raise ValueError(
                "aligned_full_stack_nk.csv 的波长网格不符合 400-1100 nm / 1 nm 整数步长约定。"
            )

        numeric_block = frame.loc[:, REQUIRED_COLUMNS[1:]].to_numpy(dtype=float)
        if not np.isfinite(numeric_block).all():
            raise ValueError("aligned_full_stack_nk.csv 含有 NaN/Inf，无法用于 Phase 06 全栈求解。")

        material_db = json.loads(material_db_path.read_text(encoding="utf-8"))
        cls._validate_material_db(material_db)

        thicknesses = LayerThicknesses(
            ito_nm=float(material_db["ITO"]["thickness_nm"]),
            niox_nm=float(material_db["NIOX"]["thickness_nm"]),
            pvk_nm=float(pvk_thickness_nm),
            c60_nm=float(material_db["C60"]["thickness_nm"]),
        )

        return cls(
            wavelength_nm=wavelength_nm,
            n_glass=frame["n_Glass"].to_numpy(dtype=float) + 1j * frame["k_Glass"].to_numpy(dtype=float),
            n_ito=frame["n_ITO"].to_numpy(dtype=float) + 1j * frame["k_ITO"].to_numpy(dtype=float),
            n_niox=frame["n_NiOx"].to_numpy(dtype=float) + 1j * frame["k_NiOx"].to_numpy(dtype=float),
            n_pvk=frame["n_PVK"].to_numpy(dtype=float) + 1j * frame["k_PVK"].to_numpy(dtype=float),
            n_c60=frame["n_C60"].to_numpy(dtype=float) + 1j * frame["k_C60"].to_numpy(dtype=float),
            n_ag=frame["n_Ag"].to_numpy(dtype=float) + 1j * frame["k_Ag"].to_numpy(dtype=float),
            thicknesses=thicknesses,
        )

    @staticmethod
    def _validate_material_db(material_db: dict[str, dict]) -> None:
        required_materials = ("ITO", "NIOX", "C60")
        for material in required_materials:
            if material not in material_db:
                raise ValueError(f"materials_master_db.json 缺少 {material} 条目。")

        expected_thickness_map = {
            "ITO": ITO_THICKNESS_NM,
            "NIOX": NIOX_THICKNESS_NM,
            "C60": C60_THICKNESS_NM,
        }
        for material_name, expected_value in expected_thickness_map.items():
            actual_value = float(material_db[material_name]["thickness_nm"])
            if abs(actual_value - expected_value) > THICKNESS_TOLERANCE_NM:
                raise ValueError(
                    f"{material_name} 厚度口径与 Phase 06 约定不一致: "
                    f"expected={expected_value:.6f} nm, actual={actual_value:.6f} nm"
                )

    def front_surface_reflectance(self) -> np.ndarray:
        reflection = (AIR_INDEX - self.n_glass) / (AIR_INDEX + self.n_glass)
        return np.abs(reflection) ** 2

    def build_stack(self, mode: str, wavelength_index: int, d_air_nm: float) -> tuple[list[complex], list[float]]:
        if mode not in SUPPORTED_MODES:
            raise ValueError(f"不支持的模式: {mode}")
        if d_air_nm < 0.0:
            raise ValueError(f"空气隙厚度必须非负，当前 d_air_nm={d_air_nm}")

        glass_nk = complex(self.n_glass[wavelength_index])
        ito_nk = complex(self.n_ito[wavelength_index])
        niox_nk = complex(self.n_niox[wavelength_index])
        pvk_nk = complex(self.n_pvk[wavelength_index])
        c60_nk = complex(self.n_c60[wavelength_index])
        ag_nk = complex(self.n_ag[wavelength_index])

        if mode == MODE_BASELINE or np.isclose(d_air_nm, 0.0, atol=0.0, rtol=0.0):
            n_list = [glass_nk, ito_nk, niox_nk, pvk_nk, c60_nk, ag_nk]
            d_list = [
                np.inf,
                self.thicknesses.ito_nm,
                self.thicknesses.niox_nm,
                self.thicknesses.pvk_nm,
                self.thicknesses.c60_nm,
                np.inf,
            ]
            return n_list, d_list

        if mode == MODE_CASE_A:
            n_list = [glass_nk, ito_nk, niox_nk, pvk_nk, c60_nk, AIR_INDEX, ag_nk]
            d_list = [
                np.inf,
                self.thicknesses.ito_nm,
                self.thicknesses.niox_nm,
                self.thicknesses.pvk_nm,
                self.thicknesses.c60_nm,
                float(d_air_nm),
                np.inf,
            ]
            return n_list, d_list

        n_list = [glass_nk, ito_nk, niox_nk, pvk_nk, AIR_INDEX, c60_nk, ag_nk]
        d_list = [
            np.inf,
            self.thicknesses.ito_nm,
            self.thicknesses.niox_nm,
            self.thicknesses.pvk_nm,
            float(d_air_nm),
            self.thicknesses.c60_nm,
            np.inf,
        ]
        return n_list, d_list

    def calc_back_reflectance(self, mode: str, d_air_nm: float = 0.0) -> np.ndarray:
        reflectance = np.empty_like(self.wavelength_nm, dtype=float)
        for index, wavelength_nm in enumerate(self.wavelength_nm):
            n_list, d_list = self.build_stack(mode=mode, wavelength_index=index, d_air_nm=d_air_nm)
            result = coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(wavelength_nm))
            reflectance[index] = float(result["R"])
        return reflectance

    def calc_macro_reflectance(self, mode: str, d_air_nm: float = 0.0) -> np.ndarray:
        r_front = self.front_surface_reflectance()
        r_back = self.calc_back_reflectance(mode=mode, d_air_nm=d_air_nm)
        denominator = 1.0 - r_front * r_back
        if np.any(np.isclose(denominator, 0.0)):
            raise ValueError("Air/Glass 与后侧薄膜的强度级联分母接近 0。")
        return r_front + (((1.0 - r_front) ** 2) * r_back) / denominator

    def sweep_air_gap(self, mode: str, d_air_values_nm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        d_air_array = np.asarray(d_air_values_nm, dtype=float)
        if mode == MODE_BASELINE:
            raise ValueError("Baseline 模式不需要做空气隙扫描。")

        baseline_reflectance = self.calc_macro_reflectance(mode=MODE_BASELINE, d_air_nm=0.0)
        reflectance_map = np.empty((d_air_array.size, self.wavelength_nm.size), dtype=float)
        delta_map = np.empty_like(reflectance_map)

        for row_index, d_air_nm in enumerate(d_air_array):
            reflectance = self.calc_macro_reflectance(mode=mode, d_air_nm=float(d_air_nm))
            reflectance_map[row_index] = reflectance
            delta_map[row_index] = reflectance - baseline_reflectance

        return reflectance_map, delta_map
