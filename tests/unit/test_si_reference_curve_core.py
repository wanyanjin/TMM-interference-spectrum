from __future__ import annotations

import numpy as np

from src.core.si_reference_curve import fresnel_air_si_reflectance


def test_fresnel_air_si_reflectance_matches_manual_formula() -> None:
    n_si = np.array([3.9])
    k_si = np.array([0.02])
    got = fresnel_air_si_reflectance(n_si, k_si)[0]
    n_tilde = 3.9 + 0.02j
    expected = abs((1 - n_tilde) / (1 + n_tilde)) ** 2
    assert np.isclose(got, expected)
