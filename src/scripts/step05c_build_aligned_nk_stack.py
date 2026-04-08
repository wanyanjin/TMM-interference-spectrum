"""Phase 05c aligned full-stack n-k builder.

This script builds a 400-1100 nm aligned optical-constant table for the
materials consumed by the downstream TMM stack. ETL/HTL/interface layers use
measured chart exports plus heuristic long-wave extrapolation. PVK uses the
existing Phase 03/04 middleware above 750 nm and [LIT-0001] digitized data to
backfill the lower band.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESOURCES_DIR = PROJECT_ROOT / "resources"
DOCS_DIR = PROJECT_ROOT / "docs"
JSON_PATH = RESOURCES_DIR / "materials_master_db.json"
PVK_MIDDLEWARE_PATH = PROJECT_ROOT / "data" / "processed" / "CsFAPI_nk_extended.csv"
PVK_DIGITIZED_PATH = RESOURCES_DIR / "digitized" / "phase02_fig3_csfapi_optical_constants_digitized.csv"
AG_PATH = RESOURCES_DIR / "Ag.csv"
OUTPUT_CSV_PATH = RESOURCES_DIR / "aligned_full_stack_nk.csv"
OUTPUT_FIGURE_PATH = DOCS_DIR / "images" / "nk_extrapolation_check.png"

WL_GRID = np.arange(400.0, 1101.0, 1.0, dtype=float)
GLASS_N = 1.515
GLASS_K = 0.0
PVK_LOW_BOUNDARY_NM = 450
PVK_MID_BOUNDARY_NM = 750
SMOOTH_HALF_WINDOW = 2

MATERIAL_SOURCES = {
    "ITO": {
        "json_key": "ITO",
        "glob": "ITO-NK*.csv",
    },
    "NiOx": {
        "json_key": "NIOX",
        "glob": "NIOX-NK*.csv",
    },
    "C60": {
        "json_key": "C60",
        "glob": "C60nk*.csv",
    },
    "SnOx": {
        "json_key": "sno",
        "glob": "SNO-NK*.csv",
    },
}


@dataclass
class MaterialCurve:
    name: str
    n_values: np.ndarray
    k_values: np.ndarray
    measured_mask: np.ndarray
    extrapolated_mask: np.ndarray
    join_nm: int
    k_mode: str
    n_fit_params: tuple[float, float]


def cauchy_model(wavelength_nm: np.ndarray, a_param: float, b_param: float) -> np.ndarray:
    wavelength_um = np.asarray(wavelength_nm, dtype=float) / 1000.0
    return a_param + b_param / (wavelength_um**2)


def wavelength_to_index(wavelength_nm: int) -> int:
    return int(wavelength_nm - int(WL_GRID[0]))


def resolve_resource_path(pattern: str) -> Path:
    matches = sorted(RESOURCES_DIR.glob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected exactly one resources match for pattern '{pattern}', got {len(matches)}.")
    return matches[0]


def get_project_json() -> dict[str, dict]:
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def smooth_join_region(values: np.ndarray, join_nm: int, force_nonnegative: bool = False) -> np.ndarray:
    smoothed = pd.Series(values).rolling(window=5, center=True, min_periods=1).mean().to_numpy(dtype=float)
    output = values.copy()
    join_mask = (WL_GRID >= join_nm - SMOOTH_HALF_WINDOW) & (WL_GRID <= join_nm + SMOOTH_HALF_WINDOW)
    output[join_mask] = smoothed[join_mask]
    if force_nonnegative:
        output = np.maximum(output, 0.0)
    return output


def read_chart_export(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    skiprows = 0
    if raw_lines and raw_lines[0].startswith("sep="):
        skiprows += 1
    if len(raw_lines) > skiprows and raw_lines[skiprows].startswith("NKChart"):
        skiprows += 1

    data = pd.read_csv(path, skiprows=skiprows, usecols=[0, 1, 2, 3])
    wavelength_n = pd.to_numeric(data.iloc[:, 0], errors="coerce").to_numpy(dtype=float)
    refractive_index = pd.to_numeric(data.iloc[:, 1], errors="coerce").to_numpy(dtype=float)
    wavelength_k = pd.to_numeric(data.iloc[:, 2], errors="coerce").to_numpy(dtype=float)
    extinction = pd.to_numeric(data.iloc[:, 3], errors="coerce").to_numpy(dtype=float)

    n_mask = np.isfinite(wavelength_n) & np.isfinite(refractive_index)
    k_mask = np.isfinite(wavelength_k) & np.isfinite(extinction)
    wavelength_n = wavelength_n[n_mask]
    refractive_index = refractive_index[n_mask]
    wavelength_k = wavelength_k[k_mask]
    extinction = extinction[k_mask]

    n_order = np.argsort(wavelength_n)
    k_order = np.argsort(wavelength_k)
    return (
        wavelength_n[n_order],
        refractive_index[n_order],
        wavelength_k[k_order],
        extinction[k_order],
    )


def build_interp(x_values: np.ndarray, y_values: np.ndarray) -> interp1d:
    return interp1d(
        x_values,
        y_values,
        kind="cubic",
        bounds_error=False,
        fill_value=np.nan,
    )


def fit_cauchy_tail(wavelength_nm: np.ndarray, refractive_index: np.ndarray) -> tuple[float, float]:
    tail_mask = wavelength_nm >= (wavelength_nm.max() - 200.0)
    fit_x = wavelength_nm[tail_mask]
    fit_y = refractive_index[tail_mask]
    params, _ = curve_fit(cauchy_model, fit_x, fit_y, p0=(fit_y[-1], 0.05), maxfev=10000)
    return float(params[0]), float(params[1])


def classify_k_tail(wavelength_nm: np.ndarray, extinction: np.ndarray) -> tuple[str, float]:
    tail_mask = wavelength_nm >= (wavelength_nm.max() - 100.0)
    fit_x = wavelength_nm[tail_mask]
    fit_y = extinction[tail_mask]
    slope = float(np.polyfit(fit_x, fit_y, 1)[0])
    tail_k = float(extinction[-1])

    if tail_k < 0.05 and slope <= 0.0:
        return "transparent", slope
    if slope > 0.0:
        return "drude", slope
    return "flat", slope


def extrapolate_k_tail(wavelength_nm: np.ndarray, extinction: np.ndarray, join_nm: int) -> tuple[np.ndarray, str]:
    tail_grid = WL_GRID[WL_GRID >= join_nm]
    tail_value = float(extinction[-1])
    k_mode, slope = classify_k_tail(wavelength_nm, extinction)

    if k_mode == "transparent":
        transition_end = join_nm + 5
        tail_values = np.zeros_like(tail_grid, dtype=float)
        transition_mask = tail_grid <= transition_end
        if np.any(transition_mask):
            tail_values[transition_mask] = np.interp(
                tail_grid[transition_mask],
                [float(join_nm), float(transition_end)],
                [tail_value, 0.0],
            )
        return tail_values, "transparent"

    if k_mode == "drude":
        fit_mask = wavelength_nm >= (wavelength_nm.max() - 150.0)
        fit_x = wavelength_nm[fit_mask]
        fit_y = extinction[fit_mask]

        quadratic = np.poly1d(np.polyfit(fit_x, fit_y, 2))
        tail_values = quadratic(tail_grid)
        tail_values = tail_values + (tail_value - float(tail_values[0]))

        invalid_quadratic = (
            not np.all(np.isfinite(tail_values))
            or float(np.nanmax(tail_values)) > max(5.0 * float(np.nanmax(fit_y)), 1.0)
        )
        if invalid_quadratic:
            linear = np.poly1d(np.polyfit(fit_x, fit_y, 1))
            tail_values = linear(tail_grid)
            tail_values = tail_values + (tail_value - float(tail_values[0]))

        tail_values = np.maximum(tail_values, 0.0)
        tail_values = np.maximum.accumulate(tail_values)
        return tail_values, f"drude(slope={slope:.6e})"

    tail_values = np.full_like(tail_grid, tail_value, dtype=float)
    return tail_values, f"flat(slope={slope:.6e})"


def build_extrapolated_material_curve(material_name: str, json_record: dict, csv_path: Path) -> MaterialCurve:
    wavelength_n, refractive_index, wavelength_k, extinction = read_chart_export(csv_path)
    requires_extrapolation = bool(json_record.get("requires_extrapolation", False))
    join_nm = int(np.ceil(max(wavelength_n.max(), wavelength_k.max())))

    measured_n_interp = build_interp(wavelength_n, refractive_index)
    measured_k_interp = build_interp(wavelength_k, extinction)

    measured_n_mask = (WL_GRID >= 400.0) & (WL_GRID <= np.floor(wavelength_n.max()))
    measured_k_mask = (WL_GRID >= 400.0) & (WL_GRID <= np.floor(wavelength_k.max()))

    n_values = np.full_like(WL_GRID, np.nan, dtype=float)
    k_values = np.full_like(WL_GRID, np.nan, dtype=float)
    n_values[measured_n_mask] = measured_n_interp(WL_GRID[measured_n_mask])
    k_values[measured_k_mask] = measured_k_interp(WL_GRID[measured_k_mask])

    n_fit_params = (float("nan"), float("nan"))
    k_mode = "no_extrapolation"
    extrapolated_mask = WL_GRID >= join_nm

    if requires_extrapolation:
        a_param, b_param = fit_cauchy_tail(wavelength_n, refractive_index)
        n_fit_params = (a_param, b_param)

        n_tail = cauchy_model(WL_GRID[extrapolated_mask], a_param, b_param)
        n_tail += float(refractive_index[-1] - n_tail[0])
        n_values[extrapolated_mask] = n_tail

        k_tail, k_mode = extrapolate_k_tail(wavelength_k, extinction, join_nm)
        k_values[extrapolated_mask] = k_tail

        n_values = smooth_join_region(n_values, join_nm)
        k_values = smooth_join_region(k_values, join_nm, force_nonnegative=True)

        if k_mode.startswith("transparent"):
            k_values[WL_GRID >= (join_nm + 8)] = 0.0
        elif k_mode.startswith("drude"):
            k_values[extrapolated_mask] = np.maximum.accumulate(k_values[extrapolated_mask])
    else:
        extrapolated_mask = np.zeros_like(WL_GRID, dtype=bool)

    if np.any(~np.isfinite(n_values)) or np.any(~np.isfinite(k_values)):
        raise ValueError(f"{material_name} aligned n/k contains invalid values after extrapolation.")

    measured_mask = measured_n_mask & measured_k_mask
    return MaterialCurve(
        name=material_name,
        n_values=n_values,
        k_values=np.maximum(k_values, 0.0),
        measured_mask=measured_mask,
        extrapolated_mask=extrapolated_mask,
        join_nm=join_nm,
        k_mode=k_mode,
        n_fit_params=n_fit_params,
    )


def load_ag_curve() -> tuple[np.ndarray, np.ndarray]:
    data = pd.read_csv(AG_PATH)
    wavelength_nm = pd.to_numeric(data.iloc[:, 0], errors="coerce").to_numpy(dtype=float)
    refractive_index = pd.to_numeric(data.iloc[:, 1], errors="coerce").to_numpy(dtype=float)
    extinction = pd.to_numeric(data.iloc[:, 2], errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(wavelength_nm) & np.isfinite(refractive_index) & np.isfinite(extinction)
    wavelength_nm = wavelength_nm[mask]
    refractive_index = refractive_index[mask]
    extinction = extinction[mask]
    order = np.argsort(wavelength_nm)
    n_values = build_interp(wavelength_nm[order], refractive_index[order])(WL_GRID)
    k_values = build_interp(wavelength_nm[order], extinction[order])(WL_GRID)
    if np.any(~np.isfinite(n_values)) or np.any(~np.isfinite(k_values)):
        raise ValueError("Ag interpolation contains invalid values.")
    return n_values, np.maximum(k_values, 0.0)


def bridge_to_boundary(values: np.ndarray, left_anchor_nm: int, right_anchor_nm: int) -> np.ndarray:
    output = values.copy()
    left_value = float(output[wavelength_to_index(left_anchor_nm)])
    right_value = float(output[wavelength_to_index(right_anchor_nm)])
    bridge_grid = np.arange(left_anchor_nm + 1, right_anchor_nm, dtype=int)
    if bridge_grid.size == 0:
        return output

    bridge_values = np.interp(
        bridge_grid.astype(float),
        [float(left_anchor_nm), float(right_anchor_nm)],
        [left_value, right_value],
    )
    for wavelength_nm, value in zip(bridge_grid, bridge_values):
        output[wavelength_to_index(int(wavelength_nm))] = value
    return output


def load_pvk_curve() -> tuple[np.ndarray, np.ndarray]:
    middleware = pd.read_csv(PVK_MIDDLEWARE_PATH)
    middleware_wl = middleware["Wavelength"].to_numpy(dtype=float)
    middleware_n = middleware["n"].to_numpy(dtype=float)
    middleware_k = middleware["k"].to_numpy(dtype=float)

    digitized = pd.read_csv(PVK_DIGITIZED_PATH)
    pvk_digitized = digitized[digitized["series"] == "ITO/CsFAPI"].copy()  # [LIT-0001]
    pvk_n = pvk_digitized[pvk_digitized["quantity"] == "n"].copy()
    pvk_k = pvk_digitized[pvk_digitized["quantity"] == "kappa"].copy()

    digitized_n_interp = build_interp(
        pvk_n["wavelength_nm"].to_numpy(dtype=float),
        pvk_n["value"].to_numpy(dtype=float),
    )
    digitized_k_interp = build_interp(
        pvk_k["wavelength_nm"].to_numpy(dtype=float),
        pvk_k["value"].to_numpy(dtype=float),
    )
    middleware_n_interp = build_interp(middleware_wl, middleware_n)
    middleware_k_interp = build_interp(middleware_wl, middleware_k)

    n_values = np.full_like(WL_GRID, np.nan, dtype=float)
    k_values = np.full_like(WL_GRID, np.nan, dtype=float)

    upper_mask = WL_GRID >= PVK_MID_BOUNDARY_NM
    middle_mask = (WL_GRID >= PVK_LOW_BOUNDARY_NM) & (WL_GRID < PVK_MID_BOUNDARY_NM)
    low_mask = WL_GRID < PVK_LOW_BOUNDARY_NM

    n_values[upper_mask] = middleware_n_interp(WL_GRID[upper_mask])
    k_values[upper_mask] = middleware_k_interp(WL_GRID[upper_mask])
    n_values[middle_mask] = digitized_n_interp(WL_GRID[middle_mask])
    k_values[middle_mask] = digitized_k_interp(WL_GRID[middle_mask])

    local_n_x = pvk_n["wavelength_nm"].to_numpy(dtype=float)
    local_n_y = pvk_n["value"].to_numpy(dtype=float)
    local_k_x = pvk_k["wavelength_nm"].to_numpy(dtype=float)
    local_k_y = pvk_k["value"].to_numpy(dtype=float)
    n_boundary_mask = (local_n_x >= 450.0) & (local_n_x <= 550.0)
    k_boundary_mask = (local_k_x >= 450.0) & (local_k_x <= 550.0)

    n_params, _ = curve_fit(
        cauchy_model,
        local_n_x[n_boundary_mask],
        local_n_y[n_boundary_mask],
        p0=(2.5, 0.05),
        maxfev=10000,
    )
    k_coeff = np.polyfit(local_k_x[k_boundary_mask], local_k_y[k_boundary_mask], 1)

    n_values[low_mask] = cauchy_model(WL_GRID[low_mask], float(n_params[0]), float(n_params[1]))
    k_values[low_mask] = np.polyval(k_coeff, WL_GRID[low_mask])
    k_values = np.maximum(k_values, 0.0)

    n_values = bridge_to_boundary(n_values, 444, 450)
    k_values = bridge_to_boundary(k_values, 444, 450)
    n_values = bridge_to_boundary(n_values, 744, 750)
    k_values = bridge_to_boundary(k_values, 744, 750)

    n_values = smooth_join_region(n_values, 450)
    k_values = smooth_join_region(k_values, 450, force_nonnegative=True)
    n_values = smooth_join_region(n_values, 750)
    k_values = smooth_join_region(k_values, 750, force_nonnegative=True)

    if np.any(~np.isfinite(n_values)) or np.any(~np.isfinite(k_values)):
        raise ValueError("PVK aligned n/k contains invalid values after source stitching.")

    return n_values, np.maximum(k_values, 0.0)


def build_output_dataframe(curves: dict[str, MaterialCurve], pvk_n: np.ndarray, pvk_k: np.ndarray, ag_n: np.ndarray, ag_k: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Wavelength_nm": WL_GRID.astype(int),
            "n_Glass": np.full_like(WL_GRID, GLASS_N),
            "k_Glass": np.full_like(WL_GRID, GLASS_K),
            "n_ITO": curves["ITO"].n_values,
            "k_ITO": curves["ITO"].k_values,
            "n_NiOx": curves["NiOx"].n_values,
            "k_NiOx": curves["NiOx"].k_values,
            "n_PVK": pvk_n,
            "k_PVK": pvk_k,
            "n_C60": curves["C60"].n_values,
            "k_C60": curves["C60"].k_values,
            "n_SnOx": curves["SnOx"].n_values,
            "k_SnOx": curves["SnOx"].k_values,
            "n_Ag": ag_n,
            "k_Ag": ag_k,
        }
    )


def plot_validation(curves: dict[str, MaterialCurve], output_path: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.8), dpi=300, sharex=True)
    window_mask = (WL_GRID >= 800.0) & (WL_GRID <= 1100.0)

    ito = curves["ITO"]
    c60 = curves["C60"]

    left_axis = axes[0]
    left_axis.plot(
        WL_GRID[window_mask & ito.measured_mask],
        ito.k_values[window_mask & ito.measured_mask],
        color="#1565c0",
        linewidth=2.0,
        label="Measured/interpolated",
    )
    left_axis.plot(
        WL_GRID[window_mask & ito.extrapolated_mask],
        ito.k_values[window_mask & ito.extrapolated_mask],
        color="#ef6c00",
        linewidth=2.0,
        label="Extrapolated",
    )
    left_axis.axvline(ito.join_nm, color="#616161", linestyle="--", linewidth=1.2, label="Join")
    left_axis.set_title("ITO k (800-1100 nm)")
    left_axis.set_xlabel("Wavelength (nm)")
    left_axis.set_ylabel("k")
    left_axis.grid(True, linestyle="--", alpha=0.3)
    left_axis.legend()

    right_axis = axes[1]
    right_axis.plot(
        WL_GRID[window_mask & c60.measured_mask],
        c60.n_values[window_mask & c60.measured_mask],
        color="#2e7d32",
        linewidth=2.0,
        label="Measured/interpolated",
    )
    right_axis.plot(
        WL_GRID[window_mask & c60.extrapolated_mask],
        c60.n_values[window_mask & c60.extrapolated_mask],
        color="#c62828",
        linewidth=2.0,
        label="Extrapolated",
    )
    right_axis.axvline(c60.join_nm, color="#616161", linestyle="--", linewidth=1.2, label="Join")
    right_axis.set_title("C60 n (800-1100 nm)")
    right_axis.set_xlabel("Wavelength (nm)")
    right_axis.set_ylabel("n")
    right_axis.grid(True, linestyle="--", alpha=0.3)
    right_axis.legend()

    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close(figure)


def validate_output(output_df: pd.DataFrame, curves: dict[str, MaterialCurve], pvk_n: np.ndarray, pvk_k: np.ndarray) -> None:
    if len(output_df) != 701:
        raise ValueError(f"Expected 701 aligned rows, got {len(output_df)}.")
    if output_df.isna().any().any():
        raise ValueError("Aligned output contains NaN values.")
    if not np.isfinite(output_df.select_dtypes(include=[np.number]).to_numpy()).all():
        raise ValueError("Aligned output contains non-finite values.")
    if not np.allclose(output_df["n_Glass"].to_numpy(dtype=float), GLASS_N):
        raise ValueError("Glass n column is not constant 1.515.")
    if not np.allclose(output_df["k_Glass"].to_numpy(dtype=float), GLASS_K):
        raise ValueError("Glass k column is not constant 0.")

    ito_tail = output_df.loc[output_df["Wavelength_nm"] >= 900, "k_ITO"].to_numpy(dtype=float)
    if np.any(np.diff(ito_tail) < -1e-8):
        raise ValueError("ITO k tail is not monotonic nondecreasing over 900-1100 nm.")

    for column_name in ["k_C60", "k_SnOx", "k_NiOx", "k_PVK", "k_Ag"]:
        if (output_df[column_name].to_numpy(dtype=float) < -1e-10).any():
            raise ValueError(f"{column_name} contains negative values.")

    if abs(float(pvk_n[wavelength_to_index(749)]) - float(pvk_n[wavelength_to_index(750)])) > 0.2:
        raise ValueError("PVK n discontinuity near 749/750 nm exceeds tolerance.")
    if abs(float(pvk_k[wavelength_to_index(749)]) - float(pvk_k[wavelength_to_index(750)])) > 0.05:
        raise ValueError("PVK k discontinuity near 749/750 nm exceeds tolerance.")
    if abs(float(pvk_n[wavelength_to_index(449)]) - float(pvk_n[wavelength_to_index(450)])) > 0.2:
        raise ValueError("PVK n discontinuity near 449/450 nm exceeds tolerance.")
    if abs(float(pvk_k[wavelength_to_index(449)]) - float(pvk_k[wavelength_to_index(450)])) > 0.05:
        raise ValueError("PVK k discontinuity near 449/450 nm exceeds tolerance.")

    for material_name, curve in curves.items():
        if np.any(~np.isfinite(curve.n_values)) or np.any(~np.isfinite(curve.k_values)):
            raise ValueError(f"{material_name} curve contains invalid values.")


def main() -> None:
    json_data = get_project_json()
    curves: dict[str, MaterialCurve] = {}

    for material_name, config in MATERIAL_SOURCES.items():
        curves[material_name] = build_extrapolated_material_curve(
            material_name=material_name,
            json_record=json_data[config["json_key"]],
            csv_path=resolve_resource_path(config["glob"]),
        )

    ag_n, ag_k = load_ag_curve()
    pvk_n, pvk_k = load_pvk_curve()

    output_df = build_output_dataframe(curves, pvk_n, pvk_k, ag_n, ag_k)
    validate_output(output_df, curves, pvk_n, pvk_k)

    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(OUTPUT_CSV_PATH, index=False)
    plot_validation(curves, OUTPUT_FIGURE_PATH)

    print("Phase 05c aligned n-k stack built successfully.")
    print(f"Output CSV: {OUTPUT_CSV_PATH}")
    print(f"Validation figure: {OUTPUT_FIGURE_PATH}")
    for material_name, curve in curves.items():
        print(
            f"[{material_name}] join={curve.join_nm} nm, "
            f"k_mode={curve.k_mode}, "
            f"n_fit_A={curve.n_fit_params[0]:.6f}, "
            f"n_fit_B={curve.n_fit_params[1]:.6f}"
        )


if __name__ == "__main__":
    main()
