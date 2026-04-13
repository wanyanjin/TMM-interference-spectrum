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
DEFAULT_CONSTANT_GLASS_INDEX = 1.515 + 0.0j
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
AG_BOUNDARY_FINITE_FILM = "finite_100nm_air_exit"
AG_BOUNDARY_SEMI_INFINITE = "semi_infinite_ag"
SUPPORTED_AG_BOUNDARY_MODES = (
    AG_BOUNDARY_FINITE_FILM,
    AG_BOUNDARY_SEMI_INFINITE,
)
REAR_BEMA_VOLUME_FRACTION = 0.5
FRONT_BEMA_VOLUME_FRACTION = 0.5

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

    def _normalize_ag_boundary_mode(self, ag_boundary_mode: str) -> str:
        normalized_mode = str(ag_boundary_mode).strip().lower()
        if normalized_mode not in SUPPORTED_AG_BOUNDARY_MODES:
            raise ValueError(
                f"ag_boundary_mode 必须是 {SUPPORTED_AG_BOUNDARY_MODES} 之一，当前为 {ag_boundary_mode}"
            )
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

    def front_surface_reflectance_with_glass(self, glass_nk: np.ndarray) -> np.ndarray:
        glass = np.asarray(glass_nk, dtype=np.complex128)
        if glass.shape != self.wavelength_nm.shape:
            raise ValueError("glass_nk 的形状必须与内部波长网格一致。")
        reflection = (AIR_INDEX - glass) / (AIR_INDEX + glass)
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

    def calc_pristine_stack_reflectance(
        self,
        *,
        thicknesses: LayerThicknesses | None = None,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    ) -> np.ndarray:
        thickness_state = thicknesses or self.thicknesses
        normalized_ag_mode = self._normalize_ag_boundary_mode(ag_boundary_mode)
        reflectance = np.empty_like(self.wavelength_nm, dtype=float)
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        for index, wavelength_nm in enumerate(self.wavelength_nm):
            glass_nk = complex(glass_grid[index])
            ito_nk = complex(self.n_ito[index])
            niox_nk = complex(self.n_niox[index])
            pvk_nk = complex(self.n_pvk[index])
            c60_nk = complex(self.n_c60[index])
            ag_nk = complex(self.n_ag[index])

            if normalized_ag_mode == AG_BOUNDARY_FINITE_FILM:
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
            else:
                n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, pvk_nk, c60_nk, ag_nk]
                d_list = [
                    np.inf,
                    thickness_state.ito_nm,
                    thickness_state.niox_nm,
                    thickness_state.sam_nm,
                    thickness_state.pvk_nm,
                    thickness_state.c60_nm,
                    np.inf,
                ]

            result = coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(wavelength_nm))
            reflectance[index] = float(result["R"])
        return reflectance

    def calc_rear_bema_stack_reflectance(
        self,
        *,
        d_bema_rear_nm: float,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    ) -> tuple[np.ndarray, float, float]:
        if d_bema_rear_nm < 0.0:
            raise ValueError(f"d_BEMA,rear 必须非负，当前值 {d_bema_rear_nm}")

        d_pvk_bulk_nm = float(self.thicknesses.pvk_nm - 0.5 * d_bema_rear_nm)
        d_c60_bulk_nm = float(max(0.0, self.thicknesses.c60_nm - 0.5 * d_bema_rear_nm))
        if d_pvk_bulk_nm <= 0.0:
            raise ValueError(
                f"d_BEMA,rear={d_bema_rear_nm} nm 会导致 d_PVK,bulk={d_pvk_bulk_nm} nm，不符合物理约束。"
            )

        normalized_ag_mode = self._normalize_ag_boundary_mode(ag_boundary_mode)
        reflectance = np.empty_like(self.wavelength_nm, dtype=float)
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        for index, wavelength_nm in enumerate(self.wavelength_nm):
            glass_nk = complex(glass_grid[index])
            ito_nk = complex(self.n_ito[index])
            niox_nk = complex(self.n_niox[index])
            pvk_nk = complex(self.n_pvk[index])
            c60_nk = complex(self.n_c60[index])
            ag_nk = complex(self.n_ag[index])
            bema_nk = bruggeman_two_phase_index(
                epsilon_a=pvk_nk**2,
                epsilon_b=c60_nk**2,
                volume_fraction_a=REAR_BEMA_VOLUME_FRACTION,
                seed_index=0.5 * (pvk_nk + c60_nk),
            )

            if normalized_ag_mode == AG_BOUNDARY_FINITE_FILM:
                n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, pvk_nk, bema_nk, c60_nk, ag_nk, AIR_INDEX]
                d_list = [
                    np.inf,
                    self.thicknesses.ito_nm,
                    self.thicknesses.niox_nm,
                    self.thicknesses.sam_nm,
                    d_pvk_bulk_nm,
                    float(d_bema_rear_nm),
                    d_c60_bulk_nm,
                    self.thicknesses.ag_nm,
                    np.inf,
                ]
            else:
                n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, pvk_nk, bema_nk, c60_nk, ag_nk]
                d_list = [
                    np.inf,
                    self.thicknesses.ito_nm,
                    self.thicknesses.niox_nm,
                    self.thicknesses.sam_nm,
                    d_pvk_bulk_nm,
                    float(d_bema_rear_nm),
                    d_c60_bulk_nm,
                    np.inf,
                ]

            result = coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(wavelength_nm))
            reflectance[index] = float(result["R"])

        return reflectance, d_pvk_bulk_nm, d_c60_bulk_nm

    def calc_front_bema_stack_reflectance(
        self,
        *,
        d_bema_front_nm: float,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    ) -> tuple[np.ndarray, float]:
        if d_bema_front_nm < 0.0:
            raise ValueError(f"d_BEMA,front 必须非负，当前值 {d_bema_front_nm}")

        d_pvk_bulk_nm = float(self.thicknesses.pvk_nm - d_bema_front_nm)
        if d_pvk_bulk_nm <= 0.0:
            raise ValueError(
                f"d_BEMA,front={d_bema_front_nm} nm 会导致 d_PVK,bulk={d_pvk_bulk_nm} nm，不符合物理约束。"
            )

        normalized_ag_mode = self._normalize_ag_boundary_mode(ag_boundary_mode)
        reflectance = np.empty_like(self.wavelength_nm, dtype=float)
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        for index, wavelength_nm in enumerate(self.wavelength_nm):
            glass_nk = complex(glass_grid[index])
            ito_nk = complex(self.n_ito[index])
            niox_nk = complex(self.n_niox[index])
            pvk_nk = complex(self.n_pvk[index])
            c60_nk = complex(self.n_c60[index])
            ag_nk = complex(self.n_ag[index])
            # [LIT-0001] anchors the PVK optical constants within the measured window;
            # this BEMA layer is a front-side optical proxy built from NiOx/PVK intermixing.
            bema_nk = bruggeman_two_phase_index(
                epsilon_a=niox_nk**2,
                epsilon_b=pvk_nk**2,
                volume_fraction_a=FRONT_BEMA_VOLUME_FRACTION,
                seed_index=0.5 * (niox_nk + pvk_nk),
            )

            if normalized_ag_mode == AG_BOUNDARY_FINITE_FILM:
                n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, bema_nk, pvk_nk, c60_nk, ag_nk, AIR_INDEX]
                d_list = [
                    np.inf,
                    self.thicknesses.ito_nm,
                    self.thicknesses.niox_nm,
                    self.thicknesses.sam_nm,
                    float(d_bema_front_nm),
                    d_pvk_bulk_nm,
                    self.thicknesses.c60_nm,
                    self.thicknesses.ag_nm,
                    np.inf,
                ]
            else:
                n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, bema_nk, pvk_nk, c60_nk, ag_nk]
                d_list = [
                    np.inf,
                    self.thicknesses.ito_nm,
                    self.thicknesses.niox_nm,
                    self.thicknesses.sam_nm,
                    float(d_bema_front_nm),
                    d_pvk_bulk_nm,
                    self.thicknesses.c60_nm,
                    np.inf,
                ]

            result = coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(wavelength_nm))
            reflectance[index] = float(result["R"])

        return reflectance, d_pvk_bulk_nm

    def calc_rear_air_gap_stack_reflectance(
        self,
        *,
        d_gap_rear_nm: float,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    ) -> np.ndarray:
        if d_gap_rear_nm < 0.0:
            raise ValueError(f"d_gap,rear 必须非负，当前值 {d_gap_rear_nm}")

        normalized_ag_mode = self._normalize_ag_boundary_mode(ag_boundary_mode)
        reflectance = np.empty_like(self.wavelength_nm, dtype=float)
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        for index, wavelength_nm in enumerate(self.wavelength_nm):
            glass_nk = complex(glass_grid[index])
            ito_nk = complex(self.n_ito[index])
            niox_nk = complex(self.n_niox[index])
            pvk_nk = complex(self.n_pvk[index])
            c60_nk = complex(self.n_c60[index])
            ag_nk = complex(self.n_ag[index])

            if normalized_ag_mode == AG_BOUNDARY_FINITE_FILM:
                n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, pvk_nk, AIR_INDEX, c60_nk, ag_nk, AIR_INDEX]
                d_list = [
                    np.inf,
                    self.thicknesses.ito_nm,
                    self.thicknesses.niox_nm,
                    self.thicknesses.sam_nm,
                    self.thicknesses.pvk_nm,
                    float(d_gap_rear_nm),
                    self.thicknesses.c60_nm,
                    self.thicknesses.ag_nm,
                    np.inf,
                ]
            else:
                n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, pvk_nk, AIR_INDEX, c60_nk, ag_nk]
                d_list = [
                    np.inf,
                    self.thicknesses.ito_nm,
                    self.thicknesses.niox_nm,
                    self.thicknesses.sam_nm,
                    self.thicknesses.pvk_nm,
                    float(d_gap_rear_nm),
                    self.thicknesses.c60_nm,
                    np.inf,
                ]

            result = coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(wavelength_nm))
            reflectance[index] = float(result["R"])

        return reflectance

    def calc_front_air_gap_stack_reflectance(
        self,
        *,
        d_gap_front_nm: float,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    ) -> np.ndarray:
        if d_gap_front_nm < 0.0:
            raise ValueError(f"d_gap,front 必须非负，当前值 {d_gap_front_nm}")

        normalized_ag_mode = self._normalize_ag_boundary_mode(ag_boundary_mode)
        reflectance = np.empty_like(self.wavelength_nm, dtype=float)
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        for index, wavelength_nm in enumerate(self.wavelength_nm):
            glass_nk = complex(glass_grid[index])
            ito_nk = complex(self.n_ito[index])
            niox_nk = complex(self.n_niox[index])
            pvk_nk = complex(self.n_pvk[index])
            c60_nk = complex(self.n_c60[index])
            ag_nk = complex(self.n_ag[index])

            if normalized_ag_mode == AG_BOUNDARY_FINITE_FILM:
                n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, AIR_INDEX, pvk_nk, c60_nk, ag_nk, AIR_INDEX]
                d_list = [
                    np.inf,
                    self.thicknesses.ito_nm,
                    self.thicknesses.niox_nm,
                    self.thicknesses.sam_nm,
                    float(d_gap_front_nm),
                    self.thicknesses.pvk_nm,
                    self.thicknesses.c60_nm,
                    self.thicknesses.ag_nm,
                    np.inf,
                ]
            else:
                n_list = [glass_nk, ito_nk, niox_nk, SAM_INDEX, AIR_INDEX, pvk_nk, c60_nk, ag_nk]
                d_list = [
                    np.inf,
                    self.thicknesses.ito_nm,
                    self.thicknesses.niox_nm,
                    self.thicknesses.sam_nm,
                    float(d_gap_front_nm),
                    self.thicknesses.pvk_nm,
                    self.thicknesses.c60_nm,
                    np.inf,
                ]

            result = coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(wavelength_nm))
            reflectance[index] = float(result["R"])

        return reflectance

    def calc_realistic_background_stack_reflectance(
        self,
        *,
        d_pvk_nm: float,
        d_bema_front_nm: float,
        d_bema_rear_nm: float,
        d_gap_front_nm: float,
        d_gap_rear_nm: float,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    ) -> tuple[np.ndarray, dict[str, float]]:
        if d_pvk_nm <= 0.0:
            raise ValueError(f"d_PVK 必须为正数，当前值 {d_pvk_nm}")
        if d_bema_front_nm < 0.0:
            raise ValueError(f"d_BEMA,front 必须非负，当前值 {d_bema_front_nm}")
        if d_bema_rear_nm < 0.0:
            raise ValueError(f"d_BEMA,rear 必须非负，当前值 {d_bema_rear_nm}")
        if d_gap_front_nm < 0.0:
            raise ValueError(f"d_gap,front 必须非负，当前值 {d_gap_front_nm}")
        if d_gap_rear_nm < 0.0:
            raise ValueError(f"d_gap,rear 必须非负，当前值 {d_gap_rear_nm}")

        d_pvk_bulk_nm = float(d_pvk_nm - d_bema_front_nm - 0.5 * d_bema_rear_nm)
        d_c60_bulk_nm = float(max(0.0, self.thicknesses.c60_nm - 0.5 * d_bema_rear_nm))
        if d_pvk_bulk_nm <= 0.0:
            raise ValueError(
                "组合 realistic background 会导致 d_PVK,bulk 非正："
                f"d_PVK={d_pvk_nm}, d_BEMA,front={d_bema_front_nm}, d_BEMA,rear={d_bema_rear_nm}"
            )

        normalized_ag_mode = self._normalize_ag_boundary_mode(ag_boundary_mode)
        reflectance = np.empty_like(self.wavelength_nm, dtype=float)
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        for index, wavelength_nm in enumerate(self.wavelength_nm):
            glass_nk = complex(glass_grid[index])
            ito_nk = complex(self.n_ito[index])
            niox_nk = complex(self.n_niox[index])
            pvk_nk = complex(self.n_pvk[index])
            c60_nk = complex(self.n_c60[index])
            ag_nk = complex(self.n_ag[index])
            bema_front_nk = bruggeman_two_phase_index(
                epsilon_a=niox_nk**2,
                epsilon_b=pvk_nk**2,
                volume_fraction_a=FRONT_BEMA_VOLUME_FRACTION,
                seed_index=0.5 * (niox_nk + pvk_nk),
            )
            bema_rear_nk = bruggeman_two_phase_index(
                epsilon_a=pvk_nk**2,
                epsilon_b=c60_nk**2,
                volume_fraction_a=REAR_BEMA_VOLUME_FRACTION,
                seed_index=0.5 * (pvk_nk + c60_nk),
            )

            layers_nk: list[complex] = [glass_nk, ito_nk, niox_nk, SAM_INDEX]
            layers_d: list[float] = [np.inf, self.thicknesses.ito_nm, self.thicknesses.niox_nm, self.thicknesses.sam_nm]

            if d_gap_front_nm > THICKNESS_TOLERANCE_NM:
                layers_nk.append(AIR_INDEX)
                layers_d.append(float(d_gap_front_nm))
            if d_bema_front_nm > THICKNESS_TOLERANCE_NM:
                layers_nk.append(bema_front_nk)
                layers_d.append(float(d_bema_front_nm))

            layers_nk.append(pvk_nk)
            layers_d.append(d_pvk_bulk_nm)

            if d_bema_rear_nm > THICKNESS_TOLERANCE_NM:
                layers_nk.append(bema_rear_nk)
                layers_d.append(float(d_bema_rear_nm))
            if d_gap_rear_nm > THICKNESS_TOLERANCE_NM:
                layers_nk.append(AIR_INDEX)
                layers_d.append(float(d_gap_rear_nm))
            if d_c60_bulk_nm > THICKNESS_TOLERANCE_NM:
                layers_nk.append(c60_nk)
                layers_d.append(d_c60_bulk_nm)

            if normalized_ag_mode == AG_BOUNDARY_FINITE_FILM:
                layers_nk.extend((ag_nk, AIR_INDEX))
                layers_d.extend((self.thicknesses.ag_nm, np.inf))
            else:
                layers_nk.append(ag_nk)
                layers_d.append(np.inf)

            result = coh_tmm("s", layers_nk, layers_d, th_0=0.0, lam_vac=float(wavelength_nm))
            reflectance[index] = float(result["R"])

        metadata = {
            "d_PVK_input_nm": float(d_pvk_nm),
            "d_BEMA_front_nm": float(d_bema_front_nm),
            "d_BEMA_rear_nm": float(d_bema_rear_nm),
            "d_gap_front_nm": float(d_gap_front_nm),
            "d_gap_rear_nm": float(d_gap_rear_nm),
            "d_PVK_bulk_nm": d_pvk_bulk_nm,
            "d_C60_bulk_nm": d_c60_bulk_nm,
        }
        return reflectance, metadata

    def compute_pristine_baseline_decomposition(
        self,
        wavelengths_nm: np.ndarray | None = None,
        *,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
        **kwargs: float,
    ) -> dict[str, np.ndarray]:
        thickness_state = self._resolve_thicknesses(**kwargs)
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        r_front = self.front_surface_reflectance_with_glass(glass_grid)
        t_front = 1.0 - r_front
        r_stack = self.calc_pristine_stack_reflectance(
            thicknesses=thickness_state,
            use_constant_glass=use_constant_glass,
            constant_glass_nk=constant_glass_nk,
            ag_boundary_mode=ag_boundary_mode,
        )
        denominator = 1.0 - r_front * r_stack
        if np.any(np.isclose(denominator, 0.0)):
            raise ValueError("Pristine baseline 的强度级联分母接近 0。")
        r_total = r_front + (t_front**2) * r_stack / denominator

        if wavelengths_nm is None or np.array_equal(np.asarray(wavelengths_nm, dtype=float), self.wavelength_nm):
            return {
                "Wavelength_nm": self.wavelength_nm.copy(),
                "R_front": r_front,
                "T_front": t_front,
                "R_stack": r_stack,
                "R_total": r_total,
            }

        query_wavelengths_nm = self._validate_query_wavelengths(wavelengths_nm)
        return {
            "Wavelength_nm": query_wavelengths_nm,
            "R_front": np.interp(query_wavelengths_nm, self.wavelength_nm, r_front),
            "T_front": np.interp(query_wavelengths_nm, self.wavelength_nm, t_front),
            "R_stack": np.interp(query_wavelengths_nm, self.wavelength_nm, r_stack),
            "R_total": np.interp(query_wavelengths_nm, self.wavelength_nm, r_total),
        }

    def compute_rear_bema_baseline_decomposition(
        self,
        *,
        d_bema_rear_nm: float,
        wavelengths_nm: np.ndarray | None = None,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    ) -> dict[str, np.ndarray | float]:
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        r_front = self.front_surface_reflectance_with_glass(glass_grid)
        t_front = 1.0 - r_front
        r_stack, d_pvk_bulk_nm, d_c60_bulk_nm = self.calc_rear_bema_stack_reflectance(
            d_bema_rear_nm=d_bema_rear_nm,
            use_constant_glass=use_constant_glass,
            constant_glass_nk=constant_glass_nk,
            ag_boundary_mode=ag_boundary_mode,
        )
        denominator = 1.0 - r_front * r_stack
        if np.any(np.isclose(denominator, 0.0)):
            raise ValueError("Rear-only BEMA baseline 的强度级联分母接近 0。")
        r_total = r_front + (t_front**2) * r_stack / denominator

        if wavelengths_nm is None or np.array_equal(np.asarray(wavelengths_nm, dtype=float), self.wavelength_nm):
            output_wavelength_nm = self.wavelength_nm.copy()
            output_r_front = r_front
            output_t_front = t_front
            output_r_stack = r_stack
            output_r_total = r_total
        else:
            query_wavelengths_nm = self._validate_query_wavelengths(wavelengths_nm)
            output_wavelength_nm = query_wavelengths_nm
            output_r_front = np.interp(query_wavelengths_nm, self.wavelength_nm, r_front)
            output_t_front = np.interp(query_wavelengths_nm, self.wavelength_nm, t_front)
            output_r_stack = np.interp(query_wavelengths_nm, self.wavelength_nm, r_stack)
            output_r_total = np.interp(query_wavelengths_nm, self.wavelength_nm, r_total)

        return {
            "Wavelength_nm": output_wavelength_nm,
            "R_front": output_r_front,
            "T_front": output_t_front,
            "R_stack": output_r_stack,
            "R_total": output_r_total,
            "d_PVK_bulk_nm": d_pvk_bulk_nm,
            "d_C60_bulk_nm": d_c60_bulk_nm,
        }

    def compute_front_bema_baseline_decomposition(
        self,
        *,
        d_bema_front_nm: float,
        wavelengths_nm: np.ndarray | None = None,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    ) -> dict[str, np.ndarray | float]:
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        r_front = self.front_surface_reflectance_with_glass(glass_grid)
        t_front = 1.0 - r_front
        r_stack, d_pvk_bulk_nm = self.calc_front_bema_stack_reflectance(
            d_bema_front_nm=d_bema_front_nm,
            use_constant_glass=use_constant_glass,
            constant_glass_nk=constant_glass_nk,
            ag_boundary_mode=ag_boundary_mode,
        )
        denominator = 1.0 - r_front * r_stack
        if np.any(np.isclose(denominator, 0.0)):
            raise ValueError("Front-only BEMA baseline 的强度级联分母接近 0。")
        r_total = r_front + (t_front**2) * r_stack / denominator

        if wavelengths_nm is None or np.array_equal(np.asarray(wavelengths_nm, dtype=float), self.wavelength_nm):
            output_wavelength_nm = self.wavelength_nm.copy()
            output_r_front = r_front
            output_t_front = t_front
            output_r_stack = r_stack
            output_r_total = r_total
        else:
            query_wavelengths_nm = self._validate_query_wavelengths(wavelengths_nm)
            output_wavelength_nm = query_wavelengths_nm
            output_r_front = np.interp(query_wavelengths_nm, self.wavelength_nm, r_front)
            output_t_front = np.interp(query_wavelengths_nm, self.wavelength_nm, t_front)
            output_r_stack = np.interp(query_wavelengths_nm, self.wavelength_nm, r_stack)
            output_r_total = np.interp(query_wavelengths_nm, self.wavelength_nm, r_total)

        return {
            "Wavelength_nm": output_wavelength_nm,
            "R_front": output_r_front,
            "T_front": output_t_front,
            "R_stack": output_r_stack,
            "R_total": output_r_total,
            "d_PVK_bulk_nm": d_pvk_bulk_nm,
        }

    def compute_rear_air_gap_baseline_decomposition(
        self,
        *,
        d_gap_rear_nm: float,
        wavelengths_nm: np.ndarray | None = None,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    ) -> dict[str, np.ndarray | float]:
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        r_front = self.front_surface_reflectance_with_glass(glass_grid)
        t_front = 1.0 - r_front
        r_stack = self.calc_rear_air_gap_stack_reflectance(
            d_gap_rear_nm=d_gap_rear_nm,
            use_constant_glass=use_constant_glass,
            constant_glass_nk=constant_glass_nk,
            ag_boundary_mode=ag_boundary_mode,
        )
        denominator = 1.0 - r_front * r_stack
        if np.any(np.isclose(denominator, 0.0)):
            raise ValueError("Rear air-gap baseline 的强度级联分母接近 0。")
        r_total = r_front + (t_front**2) * r_stack / denominator

        if wavelengths_nm is None or np.array_equal(np.asarray(wavelengths_nm, dtype=float), self.wavelength_nm):
            output_wavelength_nm = self.wavelength_nm.copy()
            output_r_front = r_front
            output_t_front = t_front
            output_r_stack = r_stack
            output_r_total = r_total
        else:
            query_wavelengths_nm = self._validate_query_wavelengths(wavelengths_nm)
            output_wavelength_nm = query_wavelengths_nm
            output_r_front = np.interp(query_wavelengths_nm, self.wavelength_nm, r_front)
            output_t_front = np.interp(query_wavelengths_nm, self.wavelength_nm, t_front)
            output_r_stack = np.interp(query_wavelengths_nm, self.wavelength_nm, r_stack)
            output_r_total = np.interp(query_wavelengths_nm, self.wavelength_nm, r_total)

        return {
            "Wavelength_nm": output_wavelength_nm,
            "R_front": output_r_front,
            "T_front": output_t_front,
            "R_stack": output_r_stack,
            "R_total": output_r_total,
            "d_gap_rear_nm": float(d_gap_rear_nm),
        }

    def compute_front_air_gap_baseline_decomposition(
        self,
        *,
        d_gap_front_nm: float,
        wavelengths_nm: np.ndarray | None = None,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    ) -> dict[str, np.ndarray | float]:
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        r_front = self.front_surface_reflectance_with_glass(glass_grid)
        t_front = 1.0 - r_front
        r_stack = self.calc_front_air_gap_stack_reflectance(
            d_gap_front_nm=d_gap_front_nm,
            use_constant_glass=use_constant_glass,
            constant_glass_nk=constant_glass_nk,
            ag_boundary_mode=ag_boundary_mode,
        )
        denominator = 1.0 - r_front * r_stack
        if np.any(np.isclose(denominator, 0.0)):
            raise ValueError("Front air-gap baseline 的强度级联分母接近 0。")
        r_total = r_front + (t_front**2) * r_stack / denominator

        if wavelengths_nm is None or np.array_equal(np.asarray(wavelengths_nm, dtype=float), self.wavelength_nm):
            output_wavelength_nm = self.wavelength_nm.copy()
            output_r_front = r_front
            output_t_front = t_front
            output_r_stack = r_stack
            output_r_total = r_total
        else:
            query_wavelengths_nm = self._validate_query_wavelengths(wavelengths_nm)
            output_wavelength_nm = query_wavelengths_nm
            output_r_front = np.interp(query_wavelengths_nm, self.wavelength_nm, r_front)
            output_t_front = np.interp(query_wavelengths_nm, self.wavelength_nm, t_front)
            output_r_stack = np.interp(query_wavelengths_nm, self.wavelength_nm, r_stack)
            output_r_total = np.interp(query_wavelengths_nm, self.wavelength_nm, r_total)

        return {
            "Wavelength_nm": output_wavelength_nm,
            "R_front": output_r_front,
            "T_front": output_t_front,
            "R_stack": output_r_stack,
            "R_total": output_r_total,
            "d_gap_front_nm": float(d_gap_front_nm),
        }

    def compute_realistic_background_baseline_decomposition(
        self,
        *,
        d_pvk_nm: float,
        d_bema_front_nm: float,
        d_bema_rear_nm: float,
        d_gap_front_nm: float,
        d_gap_rear_nm: float,
        wavelengths_nm: np.ndarray | None = None,
        use_constant_glass: bool = True,
        constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
        ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    ) -> dict[str, np.ndarray | float]:
        if use_constant_glass:
            glass_grid = np.full(self.wavelength_nm.shape, complex(constant_glass_nk), dtype=np.complex128)
        else:
            glass_grid = np.asarray(self.n_glass, dtype=np.complex128)

        r_front = self.front_surface_reflectance_with_glass(glass_grid)
        t_front = 1.0 - r_front
        r_stack, metadata = self.calc_realistic_background_stack_reflectance(
            d_pvk_nm=d_pvk_nm,
            d_bema_front_nm=d_bema_front_nm,
            d_bema_rear_nm=d_bema_rear_nm,
            d_gap_front_nm=d_gap_front_nm,
            d_gap_rear_nm=d_gap_rear_nm,
            use_constant_glass=use_constant_glass,
            constant_glass_nk=constant_glass_nk,
            ag_boundary_mode=ag_boundary_mode,
        )
        denominator = 1.0 - r_front * r_stack
        if np.any(np.isclose(denominator, 0.0)):
            raise ValueError("Realistic background baseline 的强度级联分母接近 0。")
        r_total = r_front + (t_front**2) * r_stack / denominator

        if wavelengths_nm is None or np.array_equal(np.asarray(wavelengths_nm, dtype=float), self.wavelength_nm):
            output_wavelength_nm = self.wavelength_nm.copy()
            output_r_front = r_front
            output_t_front = t_front
            output_r_stack = r_stack
            output_r_total = r_total
        else:
            query_wavelengths_nm = self._validate_query_wavelengths(wavelengths_nm)
            output_wavelength_nm = query_wavelengths_nm
            output_r_front = np.interp(query_wavelengths_nm, self.wavelength_nm, r_front)
            output_t_front = np.interp(query_wavelengths_nm, self.wavelength_nm, t_front)
            output_r_stack = np.interp(query_wavelengths_nm, self.wavelength_nm, r_stack)
            output_r_total = np.interp(query_wavelengths_nm, self.wavelength_nm, r_total)

        return {
            "Wavelength_nm": output_wavelength_nm,
            "R_front": output_r_front,
            "T_front": output_t_front,
            "R_stack": output_r_stack,
            "R_total": output_r_total,
            **metadata,
        }

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


def _choose_passive_root(effective_epsilon: np.ndarray, seed_index: np.ndarray | complex) -> np.ndarray:
    root_positive = np.sqrt(effective_epsilon)
    root_negative = -root_positive
    candidate = np.where(np.imag(root_positive) >= 0.0, root_positive, root_negative)
    seed = np.asarray(seed_index, dtype=np.complex128)
    if seed.shape == ():
        seed = np.full(candidate.shape, complex(seed), dtype=np.complex128)
    alternate = np.where(candidate == root_positive, root_negative, root_positive)
    use_alternate = np.abs(alternate - seed) < np.abs(candidate - seed)
    return np.where(use_alternate, alternate, candidate)


def bruggeman_two_phase_index(
    *,
    epsilon_a: np.ndarray | complex,
    epsilon_b: np.ndarray | complex,
    volume_fraction_a: float = REAR_BEMA_VOLUME_FRACTION,
    seed_index: np.ndarray | complex | None = None,
) -> np.ndarray:
    fraction = float(volume_fraction_a)
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"Bruggeman 体积分数必须在 [0, 1]，当前为 {fraction}")

    epsilon_a_array = np.asarray(epsilon_a, dtype=np.complex128)
    epsilon_b_array = np.asarray(epsilon_b, dtype=np.complex128)
    if epsilon_a_array.shape != epsilon_b_array.shape:
        raise ValueError("epsilon_a 与 epsilon_b 的形状必须一致。")

    linear_term = ((3.0 * fraction - 1.0) * epsilon_a_array) + ((2.0 - 3.0 * fraction) * epsilon_b_array)
    discriminant = linear_term**2 + 8.0 * epsilon_a_array * epsilon_b_array
    epsilon_eff = 0.25 * (linear_term + np.sqrt(discriminant))
    if seed_index is None:
        seed = 0.5 * (np.sqrt(epsilon_a_array) + np.sqrt(epsilon_b_array))
    else:
        seed = np.asarray(seed_index, dtype=np.complex128)
    return _choose_passive_root(effective_epsilon=epsilon_eff, seed_index=seed)


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


def compute_pristine_baseline_decomposition(
    wavelengths_nm: np.ndarray | None = None,
    *,
    use_constant_glass: bool = True,
    constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
    ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
    **kwargs: float,
) -> dict[str, np.ndarray]:
    """Pristine baseline decomposition for Phase A-1 without any defect modulation."""
    model = load_default_optical_stack_table()
    return model.compute_pristine_baseline_decomposition(
        wavelengths_nm=wavelengths_nm,
        use_constant_glass=use_constant_glass,
        constant_glass_nk=constant_glass_nk,
        ag_boundary_mode=ag_boundary_mode,
        **kwargs,
    )


def compute_realistic_background_baseline_decomposition(
    *,
    d_pvk_nm: float,
    d_bema_front_nm: float,
    d_bema_rear_nm: float,
    d_gap_front_nm: float,
    d_gap_rear_nm: float,
    wavelengths_nm: np.ndarray | None = None,
    use_constant_glass: bool = True,
    constant_glass_nk: complex = DEFAULT_CONSTANT_GLASS_INDEX,
    ag_boundary_mode: str = AG_BOUNDARY_FINITE_FILM,
) -> dict[str, np.ndarray | float]:
    """Combined realistic-background baseline for Phase D-1 discrimination."""
    model = load_default_optical_stack_table()
    return model.compute_realistic_background_baseline_decomposition(
        d_pvk_nm=d_pvk_nm,
        d_bema_front_nm=d_bema_front_nm,
        d_bema_rear_nm=d_bema_rear_nm,
        d_gap_front_nm=d_gap_front_nm,
        d_gap_rear_nm=d_gap_rear_nm,
        wavelengths_nm=wavelengths_nm,
        use_constant_glass=use_constant_glass,
        constant_glass_nk=constant_glass_nk,
        ag_boundary_mode=ag_boundary_mode,
    )
