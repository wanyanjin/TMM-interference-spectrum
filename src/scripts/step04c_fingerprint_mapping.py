"""Phase 04c 前向差分指纹映射与保零归一化相位对齐。

本脚本放弃对 bad-20-2 的高维逆向绝对拟合，转而执行一个更稳健的正向验证：
1. 读取 good-21 / bad-20-2 原始光谱并复用 step01 标定链得到平滑绝对反射率
2. 对 good-21 执行标准六参数拟合，作为“完美无损器件”的物理底盘
3. 在 L1/L2/L3 三个候选界面分别注入固定 40 nm 空气隙，生成理论差分指纹
4. 对实验差分与理论差分分别做保零归一化，只比较波峰/波谷/过零点相位

其中 PVK 色散继续复用 step01b 产出的 CsFAPI 外推 n-k 中间件 [LIT-0001]。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import step04a_air_gap_diagnostic as step04a
import step04b_air_gap_localization as step04b


PHASE_NAME = "Phase 04c"
GOOD_SAMPLE_NAME = "good-21"
BAD_SAMPLE_NAME = "bad-20-2"
FIXED_AIR_GAP_NM = 40.0
EPSILON = 1e-12


@dataclass
class FingerprintCurve:
    location_key: str
    label: str
    delta_r: np.ndarray
    normalized_delta_r: np.ndarray


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_reference_excel(resources_dir: Path) -> Path:
    """Resolve mirror-reference Excel path robustly against filename encoding variants."""
    candidates = sorted(resources_dir.glob("GCC-1022*.xlsx"))
    if not candidates:
        raise FileNotFoundError(f"未在 {resources_dir} 下找到 GCC-1022*.xlsx 参考文件。")
    return candidates[0]


def normalize_zero_preserving(delta_r: np.ndarray) -> np.ndarray:
    max_abs = float(np.max(np.abs(delta_r)))
    if max_abs <= EPSILON:
        raise ValueError("差分曲线最大绝对值过小，无法做保零归一化。")
    return delta_r / max_abs


def evaluate_alignment_score(exp_norm: np.ndarray, theory_norm: np.ndarray) -> float:
    """使用归一化均方误差评价相位形状对齐程度，数值越小越好。"""
    residual = np.asarray(theory_norm, dtype=float) - np.asarray(exp_norm, dtype=float)
    return float(np.sqrt(np.mean(residual**2)))


def compute_theoretical_fingerprint(
    wavelength_nm: np.ndarray,
    good_six_fit: step04a.FitSummary,
    get_ito_nk,
    get_pvk_nk,
    location_key: str,
) -> FingerprintCurve:
    reflected_with_gap = step04b.calc_macro_reflectance_with_localized_air_gap(
        location_key=location_key,
        d_bulk_nm=good_six_fit.d_bulk_nm,
        d_rough_nm=good_six_fit.d_rough_nm,
        d_air_nm=FIXED_AIR_GAP_NM,
        ito_alpha=good_six_fit.ito_alpha,
        sigma_thickness_nm=good_six_fit.sigma_thickness_nm,
        pvk_b_scale=good_six_fit.pvk_b_scale,
        niox_k=good_six_fit.niox_k,
        wavelength_nm=wavelength_nm,
        get_ito_nk=get_ito_nk,
        get_pvk_nk=get_pvk_nk,
    )
    delta_r = reflected_with_gap - good_six_fit.reflectance_fit
    return FingerprintCurve(
        location_key=location_key,
        label=step04b.LOCATION_LABELS[location_key],
        delta_r=delta_r,
        normalized_delta_r=normalize_zero_preserving(delta_r),
    )


def plot_phase04c_panel(
    wavelength_nm: np.ndarray,
    experimental_delta_r: np.ndarray,
    normalized_experimental_delta_r: np.ndarray,
    theoretical_curves: list[FingerprintCurve],
    best_curve: FingerprintCurve,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 5.6), dpi=320)
    ax_left, ax_right = axes

    color_map = {
        step04b.LOCATION_L1: "#546e7a",
        step04b.LOCATION_L2: "#ef6c00",
        step04b.LOCATION_L3: "#1565c0",
    }

    ax_left.axhline(0.0, color="black", linewidth=1.1, linestyle="--")
    for curve in theoretical_curves:
        ax_left.plot(
            wavelength_nm,
            curve.delta_r * 100.0,
            color=color_map[curve.location_key],
            linewidth=2.2,
            label=f"{curve.label}, d_air = {FIXED_AIR_GAP_NM:.0f} nm",
        )
    ax_left.set_title("Theoretical Orthogonality")
    ax_left.set_xlabel("Wavelength (nm)")
    ax_left.set_ylabel("Delta R Theory (%)")
    ax_left.grid(True, linestyle="--", alpha=0.35)
    ax_left.legend(fontsize=9)

    ax_right.axhline(0.0, color="black", linewidth=1.1, linestyle="--")
    ax_right.plot(
        wavelength_nm,
        normalized_experimental_delta_r,
        color="#6a1b9a",
        linewidth=2.4,
        label="Norm Delta R Exp",
    )
    for curve in theoretical_curves:
        line_width = 2.6 if curve.location_key == best_curve.location_key else 1.9
        alpha = 1.0 if curve.location_key == best_curve.location_key else 0.78
        ax_right.plot(
            wavelength_nm,
            curve.normalized_delta_r,
            color=color_map[curve.location_key],
            linewidth=line_width,
            alpha=alpha,
            linestyle="--",
            label=f"{curve.label} Norm Theory",
        )
    ax_right.set_title(f"Morphological Phase Alignment: best = {best_curve.label}")
    ax_right.set_xlabel("Wavelength (nm)")
    ax_right.set_ylabel("Normalized Delta R")
    ax_right.grid(True, linestyle="--", alpha=0.35)
    ax_right.legend(fontsize=8.8)

    for axis in axes:
        axis.set_xlim(float(wavelength_nm.min()), float(wavelength_nm.max()))

    fig.tight_layout()
    fig.savefig(output_path, dpi=320, bbox_inches="tight")
    plt.close(fig)


def build_summary_text(
    good_six_fit: step04a.FitSummary,
    experimental_delta_r: np.ndarray,
    normalized_experimental_delta_r: np.ndarray,
    theoretical_curves: list[FingerprintCurve],
    best_curve: FingerprintCurve,
) -> str:
    lines = [
        f"# {PHASE_NAME} Forward Differential Fingerprint Mapping",
        "",
        "## Baseline",
        "",
        f"- Good reference: `{GOOD_SAMPLE_NAME}`",
        f"- Experimental defect sample: `{BAD_SAMPLE_NAME}`",
        f"- Fixed theoretical air gap: `{FIXED_AIR_GAP_NM:.1f} nm`",
        f"- good-21 6p chi-square: `{good_six_fit.chisqr:.6f}`",
        f"- good-21 baseline parameters: `d_bulk={good_six_fit.d_bulk_nm:.3f} nm`, `d_rough={good_six_fit.d_rough_nm:.3f} nm`, `sigma={good_six_fit.sigma_thickness_nm:.3f} nm`, `ito_alpha={good_six_fit.ito_alpha:.6f}`, `pvk_b_scale={good_six_fit.pvk_b_scale:.6f}`, `niox_k={good_six_fit.niox_k:.6f}`",
        "",
        "## Experimental Delta",
        "",
        f"- max(|Delta_R_exp|) = `{np.max(np.abs(experimental_delta_r)) * 100.0:.3f}%`",
        f"- normalized range = `[{np.min(normalized_experimental_delta_r):+.3f}, {np.max(normalized_experimental_delta_r):+.3f}]`",
        "",
        "## Theoretical Fingerprint Alignment",
        "",
    ]
    for curve in theoretical_curves:
        score = evaluate_alignment_score(normalized_experimental_delta_r, curve.normalized_delta_r)
        lines.append(
            f"- {curve.label}: max(|Delta_R|) = `{np.max(np.abs(curve.delta_r)) * 100.0:.3f}%`, normalized RMSE = `{score:.6f}`"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- Best phase alignment: `{best_curve.label}`",
            "- Interpretation: Phase 04c uses zero-preserving normalization to remove area-fraction amplitude ambiguity and compares only fingerprint morphology.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    project_root = get_project_root()
    good_csv = project_root / "test_data" / "good-21.csv"
    bad_csv = project_root / "test_data" / "bad-20-2.csv"
    mirror_csv = project_root / "test_data" / "Ag-mirro.csv"
    reference_excel = resolve_reference_excel(project_root / "resources")

    processed_dir = project_root / "data" / "processed" / "phase04c"
    figure_path = project_root / "results" / "figures" / "phase04c_fingerprint_mapping.png"
    log_path = project_root / "results" / "logs" / "phase04c_fingerprint_mapping.md"
    processed_dir.mkdir(parents=True, exist_ok=True)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    mirror_wavelength_raw, mirror_signal_raw = step04a.step01.load_csv_spectrum(mirror_csv)
    mirror_wavelength_nm, mirror_signal = step04a.step01.crop_spectrum(mirror_wavelength_raw, mirror_signal_raw)
    excel_wavelength_raw, excel_reflectance_raw = step04a.step01.load_excel_reference(reference_excel)
    excel_wavelength_nm, excel_reflectance = step04a.step01.crop_spectrum(excel_wavelength_raw, excel_reflectance_raw)

    good_spectrum = step04a.calibrate_sample(
        sample_name=GOOD_SAMPLE_NAME,
        sample_csv=good_csv,
        mirror_wavelength_nm=mirror_wavelength_nm,
        mirror_signal_raw=mirror_signal,
        excel_wavelength_nm=excel_wavelength_nm,
        excel_reflectance=excel_reflectance,
    )
    bad_spectrum = step04a.calibrate_sample(
        sample_name=BAD_SAMPLE_NAME,
        sample_csv=bad_csv,
        mirror_wavelength_nm=mirror_wavelength_nm,
        mirror_signal_raw=mirror_signal,
        excel_wavelength_nm=excel_wavelength_nm,
        excel_reflectance=excel_reflectance,
    )

    if good_spectrum.wavelength_nm.size != bad_spectrum.wavelength_nm.size or not np.allclose(
        good_spectrum.wavelength_nm,
        bad_spectrum.wavelength_nm,
        atol=1e-12,
        rtol=0.0,
    ):
        raise ValueError("good-21 / bad-20-2 的波长网格不一致。")

    step04a.export_calibrated_csv(good_spectrum, processed_dir / "good-21_calibrated.csv")
    step04a.export_calibrated_csv(bad_spectrum, processed_dir / "bad-20-2_calibrated.csv")

    get_ito_nk, get_pvk_nk = step04a.build_material_interpolators(project_root)
    good_six_fit = step04a.fit_six_parameter_model(
        label="good-21 6-parameter fit",
        wavelength_nm=good_spectrum.wavelength_nm,
        r_target=good_spectrum.reflectance_smooth,
        get_ito_nk=get_ito_nk,
        get_pvk_nk=get_pvk_nk,
    )

    experimental_delta_r = bad_spectrum.reflectance_smooth - good_spectrum.reflectance_smooth
    normalized_experimental_delta_r = normalize_zero_preserving(experimental_delta_r)

    theoretical_curves = [
        compute_theoretical_fingerprint(
            wavelength_nm=good_spectrum.wavelength_nm,
            good_six_fit=good_six_fit,
            get_ito_nk=get_ito_nk,
            get_pvk_nk=get_pvk_nk,
            location_key=location_key,
        )
        for location_key in [step04b.LOCATION_L1, step04b.LOCATION_L2, step04b.LOCATION_L3]
    ]

    best_curve = min(
        theoretical_curves,
        key=lambda curve: evaluate_alignment_score(normalized_experimental_delta_r, curve.normalized_delta_r),
    )

    plot_phase04c_panel(
        wavelength_nm=good_spectrum.wavelength_nm,
        experimental_delta_r=experimental_delta_r,
        normalized_experimental_delta_r=normalized_experimental_delta_r,
        theoretical_curves=theoretical_curves,
        best_curve=best_curve,
        output_path=figure_path,
    )
    log_path.write_text(
        build_summary_text(
            good_six_fit=good_six_fit,
            experimental_delta_r=experimental_delta_r,
            normalized_experimental_delta_r=normalized_experimental_delta_r,
            theoretical_curves=theoretical_curves,
            best_curve=best_curve,
        ),
        encoding="utf-8",
    )

    print(f"{PHASE_NAME} fingerprint mapping complete.")
    print(f"Figure: {figure_path}")
    print(f"Log: {log_path}")
    print(f"Good 6p chi-square: {good_six_fit.chisqr:.6f}")
    print(f"Best phase-aligned interface: {best_curve.label}")
    for curve in theoretical_curves:
        score = evaluate_alignment_score(normalized_experimental_delta_r, curve.normalized_delta_r)
        print(
            f"{curve.label}: max(|Delta_R|) = {np.max(np.abs(curve.delta_r)) * 100.0:.6f}%, "
            f"normalized RMSE = {score:.6f}"
        )


if __name__ == "__main__":
    main()
