"""Phase 06/07 full-stack microcavity forward-model utilities.

This module consumes the Phase 05c engineered optical-constant table and builds
full-device reflection models on top of a shared thick-glass geometry:

- Baseline: Glass / ITO / NiOx / SAM / PVK / C60 / Ag(100 nm) / Air
- Phase 06 Case A: Glass / ITO / NiOx / SAM / PVK / C60 / Air_Gap / Ag(100 nm) / Air
- Phase 06 Case B: Glass / ITO / NiOx / SAM / PVK / Air_Gap / C60 / Ag(100 nm) / Air
- Phase 07 Front:  Glass / ITO / NiOx / Air_Gap / SAM / PVK / C60 / Ag(100 nm) / Air
- Phase 07 Back:   Glass / ITO / NiOx / SAM / PVK / Air_Gap / C60 / Ag(100 nm) / Air

The PVK column in ``aligned_full_stack_nk.csv`` ultimately traces back to the
Phase 05c stitching workflow, which uses [LIT-0001] for the 450-1000 nm source
window and controlled extrapolation outside that window.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from tmm import coh_tmm


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NK_CSV_PATH = PROJECT_ROOT / "resources" / "aligned_full_stack_nk.csv"
DEFAULT_MATERIAL_DB_PATH = PROJECT_ROOT / "resources" / "materials_master_db.json"

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
SAM_INDEX = 1.5 + 0.0j
ITO_THICKNESS_NM = 100.0
NIOX_THICKNESS_NM = 45.0
SAM_THICKNESS_NM = 5.0
PVK_THICKNESS_NM = 700.0
C60_THICKNESS_NM = 15.0
AG_THICKNESS_NM = 100.0
THICKNESS_TOLERANCE_NM = 1e-6

MODE_BASELINE = "baseline"
MODE_CASE_A = "case_a"
MODE_CASE_B = "case_b"
INTERFACE_FRONT = "front"
INTERFACE_BACK = "back"

SUPPORTED_STACK_MODES = (
    MODE_BASELINE,
    MODE_CASE_A,
    MODE_CASE_B,
    INTERFACE_FRONT,
    INTERFACE_BACK,
)
SUPPORTED_FITTING_INTERFACES = (INTERFACE_FRONT, INTERFACE_BACK)

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
    sam_nm: float
    pvk_nm: float
    c60_nm: float
    ag_nm: float

    def with_overrides(self, **kwargs: float) -> "LayerThicknesses":
        allowed_keys = {
            "ito_thickness_nm": "ito_nm",
            "niox_thickness_nm": "niox_nm",
            "sam_thickness_nm": "sam_nm",
            "pvk_thickness_nm": "pvk_nm",
            "c60_thickness_nm": "c60_nm",
            "ag_thickness_nm": "ag_nm",
        }
        unknown_keys = sorted(set(kwargs) - set(allowed_keys))
        if unknown_keys:
            raise ValueError(f"不支持的厚度覆盖键: {unknown_keys}")

        override_values = {
            field_name: float(getattr(self, field_name))
            for field_name in ("ito_nm", "niox_nm", "sam_nm", "pvk_nm", "c60_nm", "ag_nm")
        }
        for external_key, field_name in allowed_keys.items():
            if external_key in kwargs:
                override_value = float(kwargs[external_key])
                if override_value <= 0.0:
                    raise ValueError(f"{external_key} 必须为正数，当前值 {override_value}")
                override_values[field_name] = override_value

        return LayerThicknesses(**override_values)


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
            raise ValueError("aligned_full_stack_nk.csv 含有 NaN/Inf，无法用于全栈求解。")

        material_db = json.loads(material_db_path.read_text(encoding="utf-8"))
        cls._validate_material_db(material_db)

        thicknesses = LayerThicknesses(
            ito_nm=ITO_THICKNESS_NM,
            niox_nm=NIOX_THICKNESS_NM,
            sam_nm=SAM_THICKNESS_NM,
            pvk_nm=float(pvk_thickness_nm),
            c60_nm=C60_THICKNESS_NM,
            ag_nm=AG_THICKNESS_NM,
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

        # Geometry now follows the Phase 07 stack contract rather than the older
        # materials DB thickness defaults. Keep only presence validation here.

    def _normalize_stack_mode(self, mode: str) -> str:
        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in SUPPORTED_STACK_MODES:
            raise ValueError(f"不支持的模式: {mode}")
        return normalized_mode

    def _normalize_fitting_interface(self, interface_type: str) -> str:
        normalized_type = str(interface_type).strip().lower()
        if normalized_type not in SUPPORTED_FITTING_INTERFACES:
            raise ValueError(
                f"interface_type 必须是 {SUPPORTED_FITTING_INTERFACES} 之一，当前为 {interface_type}"
            )
        return normalized_type

    def _resolve_thicknesses(self, **kwargs: float) -> LayerThicknesses:
        if not kwargs:
            return self.thicknesses
        return self.thicknesses.with_overrides(**kwargs)

    def front_surface_reflectance(self) -> np.ndarray:
        reflection = (AIR_INDEX - self.n_glass) / (AIR_INDEX + self.n_glass)
        return np.abs(reflection) ** 2

    def build_stack(
        self,
        mode: str,
        wavelength_index: int,
        d_air_nm: float,
        thicknesses: LayerThicknesses | None = None,
    ) -> tuple[list[complex], list[float]]:
        normalized_mode = self._normalize_stack_mode(mode)
        if d_air_nm < 0.0:
            raise ValueError(f"空气隙厚度必须非负，当前 d_air_nm={d_air_nm}")

        thickness_state = thicknesses or self.thicknesses
        glass_nk = complex(self.n_glass[wavelength_index])
        ito_nk = complex(self.n_ito[wavelength_index])
        niox_nk = complex(self.n_niox[wavelength_index])
        pvk_nk = complex(self.n_pvk[wavelength_index])
        c60_nk = complex(self.n_c60[wavelength_index])
        ag_nk = complex(self.n_ag[wavelength_index])

        if normalized_mode == MODE_BASELINE or np.isclose(d_air_nm, 0.0, atol=0.0, rtol=0.0):
            n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, pvk_nk, c60_nk, ag_nk, AIR_INDEX]
            d_list = [
                np.inf,
                thickness_state.ito_nm,
                thickness_state.niox_nm,
                thickness_state.sam_nm,
                thickness_state.pvk_nm,
                thickness_state.c60_nm,
                thickness_state.ag_nm,
                np.inf,
            ]
            return n_list, d_list

        if normalized_mode == MODE_CASE_A:
            n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, pvk_nk, c60_nk, AIR_INDEX, ag_nk, AIR_INDEX]
            d_list = [
                np.inf,
                thickness_state.ito_nm,
                thickness_state.niox_nm,
                thickness_state.sam_nm,
                thickness_state.pvk_nm,
                thickness_state.c60_nm,
                float(d_air_nm),
                thickness_state.ag_nm,
                np.inf,
            ]
            return n_list, d_list

        if normalized_mode == INTERFACE_FRONT:
            n_list = [glass_nk, ito_nk, niox_nk, AIR_INDEX, SAM_INDEX, pvk_nk, c60_nk, ag_nk, AIR_INDEX]
            d_list = [
                np.inf,
                thickness_state.ito_nm,
                thickness_state.niox_nm,
                float(d_air_nm),
                thickness_state.sam_nm,
                thickness_state.pvk_nm,
                thickness_state.c60_nm,
                thickness_state.ag_nm,
                np.inf,
            ]
            return n_list, d_list

        n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, pvk_nk, AIR_INDEX, c60_nk, ag_nk, AIR_INDEX]
        d_list = [
            np.inf,
            thickness_state.ito_nm,
            thickness_state.niox_nm,
            thickness_state.sam_nm,
            thickness_state.pvk_nm,
            float(d_air_nm),
            thickness_state.c60_nm,
            thickness_state.ag_nm,
            np.inf,
        ]
        return n_list, d_list

    def calc_back_reflectance(
        self,
        mode: str,
        d_air_nm: float = 0.0,
        thicknesses: LayerThicknesses | None = None,
    ) -> np.ndarray:
        normalized_mode = self._normalize_stack_mode(mode)
        reflectance = np.empty_like(self.wavelength_nm, dtype=float)
        for index, wavelength_nm in enumerate(self.wavelength_nm):
            n_list, d_list = self.build_stack(
                mode=normalized_mode,
                wavelength_index=index,
                d_air_nm=d_air_nm,
                thicknesses=thicknesses,
            )
            result = coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(wavelength_nm))
            reflectance[index] = float(result["R"])
        return reflectance

    def calc_macro_reflectance(
        self,
        mode: str,
        d_air_nm: float = 0.0,
        thicknesses: LayerThicknesses | None = None,
    ) -> np.ndarray:
        normalized_mode = self._normalize_stack_mode(mode)
        r_front = self.front_surface_reflectance()
        r_back = self.calc_back_reflectance(
            mode=normalized_mode,
            d_air_nm=d_air_nm,
            thicknesses=thicknesses,
        )
        denominator = 1.0 - r_front * r_back
        if np.any(np.isclose(denominator, 0.0)):
            raise ValueError("Air/Glass 与后侧薄膜的强度级联分母接近 0。")
        return r_front + (((1.0 - r_front) ** 2) * r_back) / denominator

    def sweep_air_gap(
        self,
        mode: str,
        d_air_values_nm: np.ndarray,
        thicknesses: LayerThicknesses | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        normalized_mode = self._normalize_stack_mode(mode)
        d_air_array = np.asarray(d_air_values_nm, dtype=float)
        if normalized_mode == MODE_BASELINE:
            raise ValueError("Baseline 模式不需要做空气隙扫描。")

        baseline_reflectance = self.calc_macro_reflectance(
            mode=MODE_BASELINE,
            d_air_nm=0.0,
            thicknesses=thicknesses,
        )
        reflectance_map = np.empty((d_air_array.size, self.wavelength_nm.size), dtype=float)
        delta_map = np.empty_like(reflectance_map)

        for row_index, d_air_nm in enumerate(d_air_array):
            reflectance = self.calc_macro_reflectance(
                mode=normalized_mode,
                d_air_nm=float(d_air_nm),
                thicknesses=thicknesses,
            )
            reflectance_map[row_index] = reflectance
            delta_map[row_index] = reflectance - baseline_reflectance

        return reflectance_map, delta_map

    def _validate_query_wavelengths(self, wavelengths_nm: np.ndarray) -> np.ndarray:
        query = np.asarray(wavelengths_nm, dtype=float)
        if query.ndim != 1:
            raise ValueError("wavelengths_nm 必须是一维数组。")
        if query.size == 0:
            raise ValueError("wavelengths_nm 不能为空。")
        if not np.isfinite(query).all():
            raise ValueError("wavelengths_nm 含有 NaN/Inf。")
        if float(np.min(query)) < float(self.wavelength_nm.min()) or float(np.max(query)) > float(self.wavelength_nm.max()):
            raise ValueError(
                "wavelengths_nm 超出支持范围："
                f"[{self.wavelength_nm.min():.1f}, {self.wavelength_nm.max():.1f}] nm"
            )
        return query

    def forward_model_for_fitting(
        self,
        wavelengths_nm: np.ndarray,
        d_air_nm: float,
        interface_type: str = INTERFACE_BACK,
        **kwargs: float,
    ) -> np.ndarray:
        query_wavelengths_nm = self._validate_query_wavelengths(wavelengths_nm)
        normalized_interface = self._normalize_fitting_interface(interface_type)
        thickness_state = self._resolve_thicknesses(**kwargs)

        internal_reflectance = self.calc_macro_reflectance(
            mode=normalized_interface,
            d_air_nm=float(d_air_nm),
            thicknesses=thickness_state,
        )
        if np.array_equal(query_wavelengths_nm, self.wavelength_nm):
            return internal_reflectance.copy()
        return np.interp(query_wavelengths_nm, self.wavelength_nm, internal_reflectance)


@lru_cache(maxsize=1)
def load_default_optical_stack_table() -> OpticalStackTable:
    return OpticalStackTable.from_files(
        nk_csv_path=DEFAULT_NK_CSV_PATH,
        material_db_path=DEFAULT_MATERIAL_DB_PATH,
    )


def forward_model_for_fitting(
    wavelengths_nm: np.ndarray,
    d_air_nm: float,
    interface_type: str = INTERFACE_BACK,
    **kwargs: float,
) -> np.ndarray:
    """Standard real-valued forward interface for future nonlinear fitting."""
    model = load_default_optical_stack_table()
    return model.forward_model_for_fitting(
        wavelengths_nm=wavelengths_nm,
        d_air_nm=d_air_nm,
        interface_type=interface_type,
        **kwargs,
    )
