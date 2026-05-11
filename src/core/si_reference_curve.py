from __future__ import annotations

import numpy as np
from tmm import coh_tmm

from domain.si_reference import SiReferenceCurveResult


def fresnel_air_si_reflectance(n_si: np.ndarray, k_si: np.ndarray) -> np.ndarray:
    n_tilde = n_si + 1j * k_si
    r = (1.0 - n_tilde) / (1.0 + n_tilde)
    return np.abs(r) ** 2


def compute_air_sio2_si_reflectance(
    wavelength_nm: np.ndarray, n_si: np.ndarray, k_si: np.ndarray, oxide_thickness_nm: float, n_sio2: float
) -> np.ndarray:
    out = np.zeros_like(wavelength_nm, dtype=float)
    for i, wl in enumerate(wavelength_nm):
        n_list = [1.0 + 0.0j, complex(n_sio2, 0.0), complex(n_si[i], k_si[i])]
        d_list = [np.inf, float(oxide_thickness_nm), np.inf]
        out[i] = float(coh_tmm("s", n_list, d_list, th_0=0.0, lam_vac=float(wl))["R"])
    return out


def build_si_reference_curve(
    wavelength_nm: np.ndarray,
    n_si: np.ndarray,
    k_si: np.ndarray,
    oxide_nm: list[float],
    n_sio2: float,
) -> SiReferenceCurveResult:
    r_air_si = fresnel_air_si_reflectance(n_si, k_si)
    oxide_curves: dict[str, np.ndarray] = {}
    for t_nm in oxide_nm:
        key = f"R_air_sio2_{int(t_nm)}nm_si"
        if t_nm == 0:
            oxide_curves[key] = r_air_si.copy()
        else:
            oxide_curves[key] = compute_air_sio2_si_reflectance(wavelength_nm, n_si, k_si, t_nm, n_sio2)
    return SiReferenceCurveResult(
        wavelength_nm=wavelength_nm,
        n_si=n_si,
        k_si=k_si,
        r_air_si=r_air_si,
        oxide_curves=oxide_curves,
        metadata={},
    )
