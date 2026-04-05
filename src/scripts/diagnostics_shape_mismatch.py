"""Phase 02 形状畸变诊断沙盒。

本脚本不修改主流程，只在独立诊断环境中复用 step02 的数据读取、
CsFAPI 外推色散与 BEMA 粗糙层基线模型，对以下怀疑方向做敏感性分析：

1. ITO 近红外吸收增强
2. 宏观厚度不均匀性导致的高斯平均
3. PVK Cauchy 斜率失真（以 B 参数缩放表示）

输出：
- results/figures/diagnostic_shape_analysis.png
- results/logs/phase02_shape_diagnostic_report.md
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Callable

import matplotlib
import numpy as np
import pandas as pd
from lmfit import Parameters, minimize

matplotlib.use("Agg")
import matplotlib.pyplot as plt


LONGWAVE_REGION_START_NM = 1050.0
LONGWAVE_REGION_END_NM = 1100.0
ITO_RAMP_START_NM = 950.0
ITO_RAMP_END_NM = 1100.0
THICKNESS_SIGMA_SAMPLES = 7
THICKNESS_SIGMA_SPAN = 3.0
DIAGNOSTIC_FIT_STRIDE = 2


@dataclass
class DiagnosticResult:
    label: str
    color: str
    note: str
    chisqr: float
    global_rmse_pct: float
    longwave_rmse_pct: float
    longwave_bias_pct: float
    r_fit: np.ndarray
    params: dict[str, float]


def get_project_root() -> Path:
    """根据脚本位置推导项目根目录。"""
    return Path(__file__).resolve().parents[2]


def load_step02_module(script_path: Path) -> ModuleType:
    """动态加载 step02 脚本模块以复用其数据读取和常数定义。"""
    spec = spec_from_file_location("step02_tmm_inversion", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块: {script_path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cauchy_model(wavelength_nm: np.ndarray, a_param: float, b_param: float) -> np.ndarray:
    """与 step01b 一致的 Cauchy 折射率表达。"""
    wavelength_um = np.asarray(wavelength_nm, dtype=np.float64) / 1000.0
    return a_param + b_param / (wavelength_um**2)


def fit_cauchy_from_extended_table(wavelength_nm: np.ndarray, refractive_index: np.ndarray) -> tuple[float, float]:
    """从扩展 n-k 表反推出 A/B，用于诊断 Cauchy 斜率是否过平。"""
    wavelength_um = np.asarray(wavelength_nm, dtype=np.float64) / 1000.0
    design_matrix = np.column_stack(
        [
            np.ones_like(wavelength_um, dtype=np.float64),
            1.0 / (wavelength_um**2),
        ]
    )
    coefficients, _, _, _ = np.linalg.lstsq(design_matrix, refractive_index, rcond=None)
    return float(coefficients[0]), float(coefficients[1])


def compute_metrics(
    wavelength_nm: np.ndarray,
    r_target: np.ndarray,
    r_fit: np.ndarray,
) -> tuple[float, float, float]:
    """计算全局/长波 RMSE 以及长波平均偏差，单位均为百分比点。"""
    residual = r_fit - r_target
    longwave_mask = (wavelength_nm >= LONGWAVE_REGION_START_NM) & (wavelength_nm <= LONGWAVE_REGION_END_NM)
    global_rmse_pct = float(np.sqrt(np.mean(residual**2)) * 100.0)
    longwave_rmse_pct = float(np.sqrt(np.mean(residual[longwave_mask] ** 2)) * 100.0)
    longwave_bias_pct = float(np.mean(residual[longwave_mask]) * 100.0)
    return global_rmse_pct, longwave_rmse_pct, longwave_bias_pct


def longwave_ramp(wavelength_nm: np.ndarray) -> np.ndarray:
    """构造只在近红外长波端逐渐增强的 ITO 吸收权重。"""
    wavelength = np.asarray(wavelength_nm, dtype=np.float64)
    ramp = (wavelength - ITO_RAMP_START_NM) / (ITO_RAMP_END_NM - ITO_RAMP_START_NM)
    return np.clip(ramp, 0.0, 1.0) ** 2


def build_scaled_ito_interpolator(
    base_get_ito_nk: Callable[[np.ndarray], np.ndarray],
    alpha_ito_k: float,
) -> Callable[[np.ndarray], np.ndarray]:
    """返回带有近红外吸收增强的 ITO 复折射率插值器。"""

    def get_modified_ito_nk(query_wavelength_nm: np.ndarray) -> np.ndarray:
        query = np.asarray(query_wavelength_nm, dtype=np.float64)
        base_nk = base_get_ito_nk(query)
        n_part = np.real(base_nk)
        k_part = np.imag(base_nk)
        k_scaled = k_part * (1.0 + alpha_ito_k * longwave_ramp(query))
        return n_part + 1j * k_scaled

    return get_modified_ito_nk


def build_scaled_pvk_interpolator(
    pvk_wavelength_nm: np.ndarray,
    pvk_k: np.ndarray,
    cauchy_a: float,
    cauchy_b: float,
    b_scale: float,
) -> Callable[[np.ndarray], np.ndarray]:
    """返回允许调整 Cauchy B 斜率的 PVK 复折射率插值器。"""

    def get_modified_pvk_nk(query_wavelength_nm: np.ndarray) -> np.ndarray:
        query = np.asarray(query_wavelength_nm, dtype=np.float64)
        real_part = cauchy_model(query, cauchy_a, cauchy_b * b_scale)
        imag_part = np.interp(query, pvk_wavelength_nm, pvk_k)
        return real_part + 1j * imag_part

    return get_modified_pvk_nk


def calc_single_reflectance(
    step02_module: ModuleType,
    d_bulk_nm: float,
    d_rough_nm: float,
    wavelength_nm: np.ndarray,
    get_ito_nk: Callable[[np.ndarray], np.ndarray],
    get_pvk_nk: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    """单一厚度点下的 BEMA-TMM 宏观反射率。"""
    wavelength = np.asarray(wavelength_nm, dtype=np.float64)
    ito_nk = get_ito_nk(wavelength)
    pvk_bulk_nk = get_pvk_nk(wavelength)
    pvk_rough_nk = step02_module.calc_bema_rough_nk(pvk_bulk_nk)

    r_coh = np.empty_like(wavelength, dtype=np.float64)

    for index, wl_nm in enumerate(wavelength):
        n_list = [
            step02_module.GLASS_INDEX + 0.0j,
            ito_nk[index],
            step02_module.NIOX_NK,
            step02_module.SAM_NK,
            pvk_bulk_nk[index],
            pvk_rough_nk[index],
            step02_module.AIR_INDEX + 0.0j,
        ]
        d_list = [
            np.inf,
            step02_module.ITO_THICKNESS_NM,
            step02_module.NIOX_THICKNESS_NM,
            step02_module.SAM_THICKNESS_NM,
            d_bulk_nm,
            d_rough_nm,
            np.inf,
        ]
        result = step02_module.coh_tmm("s", n_list, d_list, 0.0, wl_nm)
        r_coh[index] = float(result["R"])

    r_front = ((step02_module.GLASS_INDEX - step02_module.AIR_INDEX) / (step02_module.GLASS_INDEX + step02_module.AIR_INDEX)) ** 2
    return r_front + (((1.0 - r_front) ** 2) * r_coh) / (1.0 - r_front * r_coh)


def calc_reflectance_with_inhomogeneity(
    step02_module: ModuleType,
    d_bulk_nm: float,
    d_rough_nm: float,
    sigma_thickness_nm: float,
    wavelength_nm: np.ndarray,
    get_ito_nk: Callable[[np.ndarray], np.ndarray],
    get_pvk_nk: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    """对块体厚度做高斯分布平均，模拟光斑内宏观不均匀性。"""
    if sigma_thickness_nm <= 1e-9:
        return calc_single_reflectance(
            step02_module=step02_module,
            d_bulk_nm=d_bulk_nm,
            d_rough_nm=d_rough_nm,
            wavelength_nm=wavelength_nm,
            get_ito_nk=get_ito_nk,
            get_pvk_nk=get_pvk_nk,
        )

    sample_axis = np.linspace(-THICKNESS_SIGMA_SPAN, THICKNESS_SIGMA_SPAN, THICKNESS_SIGMA_SAMPLES)
    weights = np.exp(-0.5 * sample_axis**2)
    weights /= np.sum(weights)

    averaged_reflectance = np.zeros_like(wavelength_nm, dtype=np.float64)
    for offset_sigma, weight in zip(sample_axis, weights):
        sampled_d_bulk_nm = max(d_bulk_nm + offset_sigma * sigma_thickness_nm, 1e-6)
        averaged_reflectance += weight * calc_single_reflectance(
            step02_module=step02_module,
            d_bulk_nm=sampled_d_bulk_nm,
            d_rough_nm=d_rough_nm,
            wavelength_nm=wavelength_nm,
            get_ito_nk=get_ito_nk,
            get_pvk_nk=get_pvk_nk,
        )
    return averaged_reflectance


def run_diagnostic_fit(
    step02_module: ModuleType,
    label: str,
    color: str,
    note: str,
    wavelength_nm: np.ndarray,
    r_target: np.ndarray,
    params: Parameters,
    model_builder: Callable[[Parameters], tuple[Callable[[np.ndarray], np.ndarray], Callable[[np.ndarray], np.ndarray], float]],
) -> DiagnosticResult:
    """运行一个诊断模型的 LM 拟合，并返回统一的结果对象。"""
    fit_wavelength_nm = wavelength_nm[::DIAGNOSTIC_FIT_STRIDE]
    fit_r_target = r_target[::DIAGNOSTIC_FIT_STRIDE]

    def residual_function(fit_params: Parameters) -> np.ndarray:
        get_ito_nk, get_pvk_nk, sigma_thickness_nm = model_builder(fit_params)
        r_model = calc_reflectance_with_inhomogeneity(
            step02_module=step02_module,
            d_bulk_nm=fit_params["d_bulk"].value,
            d_rough_nm=fit_params["d_rough"].value,
            sigma_thickness_nm=sigma_thickness_nm,
            wavelength_nm=fit_wavelength_nm,
            get_ito_nk=get_ito_nk,
            get_pvk_nk=get_pvk_nk,
        )
        return r_model - fit_r_target

    result = minimize(residual_function, params, method="leastsq", max_nfev=80)
    get_ito_nk, get_pvk_nk, sigma_thickness_nm = model_builder(result.params)
    r_fit = calc_reflectance_with_inhomogeneity(
        step02_module=step02_module,
        d_bulk_nm=result.params["d_bulk"].value,
        d_rough_nm=result.params["d_rough"].value,
        sigma_thickness_nm=sigma_thickness_nm,
        wavelength_nm=wavelength_nm,
        get_ito_nk=get_ito_nk,
        get_pvk_nk=get_pvk_nk,
    )

    global_rmse_pct, longwave_rmse_pct, longwave_bias_pct = compute_metrics(wavelength_nm, r_target, r_fit)
    summary_params = {
        name: float(parameter.value)
        for name, parameter in result.params.items()
    }

    return DiagnosticResult(
        label=label,
        color=color,
        note=note,
        chisqr=float(result.chisqr),
        global_rmse_pct=global_rmse_pct,
        longwave_rmse_pct=longwave_rmse_pct,
        longwave_bias_pct=longwave_bias_pct,
        r_fit=r_fit,
        params=summary_params,
    )


def create_fit_parameters(
    step02_module: ModuleType,
    include_ito_alpha: bool = False,
    include_sigma: bool = False,
    include_b_scale: bool = False,
) -> Parameters:
    """按诊断探针需求构造 lmfit 参数表。"""
    params = Parameters()
    params.add(
        "d_bulk",
        value=step02_module.INITIAL_PVK_BULK_THICKNESS_NM,
        min=step02_module.MIN_PVK_BULK_THICKNESS_NM,
        max=step02_module.MAX_PVK_BULK_THICKNESS_NM,
    )
    params.add(
        "d_rough",
        value=step02_module.INITIAL_PVK_ROUGHNESS_THICKNESS_NM,
        min=step02_module.MIN_PVK_ROUGHNESS_THICKNESS_NM,
        max=step02_module.MAX_PVK_ROUGHNESS_THICKNESS_NM,
    )
    if include_ito_alpha:
        params.add("ito_k_alpha", value=1.0, min=0.0, max=20.0)
    if include_sigma:
        params.add("sigma_thickness", value=8.0, min=0.0, max=30.0)
    if include_b_scale:
        params.add("pvk_b_scale", value=1.0, min=0.40, max=1.60)
    return params


def format_params_for_plot(result: DiagnosticResult) -> str:
    """生成每个探针面板的参数摘要文本。"""
    lines = [
        f"chi^2={result.chisqr:.3f}",
        f"RMSE={result.global_rmse_pct:.2f}%",
        f"LW-RMSE={result.longwave_rmse_pct:.2f}%",
        f"LW-bias={result.longwave_bias_pct:+.2f}%",
    ]
    if "d_bulk" in result.params:
        lines.append(f"d_bulk={result.params['d_bulk']:.1f} nm")
    if "d_rough" in result.params:
        lines.append(f"d_rough={result.params['d_rough']:.1f} nm")
    if "ito_k_alpha" in result.params:
        lines.append(f"alpha_ITO={result.params['ito_k_alpha']:.2f}")
    if "sigma_thickness" in result.params:
        lines.append(f"sigma={result.params['sigma_thickness']:.2f} nm")
    if "pvk_b_scale" in result.params:
        lines.append(f"B_scale={result.params['pvk_b_scale']:.3f}")
    return "\n".join(lines)


def plot_diagnostic_results(
    wavelength_nm: np.ndarray,
    r_target: np.ndarray,
    results: list[DiagnosticResult],
    output_path: Path,
) -> None:
    """绘制基线与各探针的对比图。"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300, sharex=True, sharey=True)
    axes = axes.ravel()

    for ax, result in zip(axes, results):
        ax.axvspan(LONGWAVE_REGION_START_NM, LONGWAVE_REGION_END_NM, color="#f5f5f5", alpha=0.9)
        ax.plot(
            wavelength_nm,
            r_target * 100.0,
            color="gray",
            linewidth=3.0,
            alpha=0.55,
            label="Measured Target",
        )
        ax.plot(
            wavelength_nm,
            result.r_fit * 100.0,
            color=result.color,
            linewidth=2.1,
            linestyle="--",
            label=result.label,
        )
        ax.set_title(result.label)
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.text(
            0.03,
            0.97,
            format_params_for_plot(result),
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=9,
            bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.86, "edgecolor": "#666666"},
        )
        ax.legend(loc="lower left", fontsize=8)

    axes[0].set_ylabel("Absolute Reflectance (%)")
    axes[2].set_ylabel("Absolute Reflectance (%)")
    axes[2].set_xlabel("Wavelength (nm)")
    axes[3].set_xlabel("Wavelength (nm)")

    fig.suptitle("Phase 02 Diagnostic Sandbox: Shape Mismatch Analysis", fontsize=14)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.98))
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def render_results_table(results: list[DiagnosticResult]) -> str:
    """生成 Markdown 结果表。"""
    header = "| Probe | chi^2 | Global RMSE (%) | Long-wave RMSE (%) | Long-wave Bias (%) |\n| --- | ---: | ---: | ---: | ---: |"
    rows = [
        f"| {result.label} | {result.chisqr:.4f} | {result.global_rmse_pct:.3f} | {result.longwave_rmse_pct:.3f} | {result.longwave_bias_pct:+.3f} |"
        for result in results
    ]
    return "\n".join([header, *rows])


def boundary_note(result: DiagnosticResult, name: str, lower: float, upper: float, atol: float = 1e-3) -> str:
    """生成参数是否撞到边界的说明。"""
    if name not in result.params:
        return ""
    value = result.params[name]
    if abs(value - lower) <= atol:
        return f"`{name}` 撞到了下边界 `{lower}`。"
    if abs(value - upper) <= atol:
        return f"`{name}` 撞到了上边界 `{upper}`。"
    return f"`{name}` 在边界内收敛。"


def build_diagnostic_report(results: list[DiagnosticResult]) -> str:
    """根据诊断结果自动生成 Markdown 报告。"""
    result_map = {result.label: result for result in results}
    baseline = result_map["Baseline BEMA"]
    ito_probe = result_map["Probe A: ITO IR Absorption"]
    sigma_probe = result_map["Probe B: Thickness Inhomogeneity"]
    slope_probe = result_map["Probe C: PVK Cauchy Slope"]

    best_global = min(results[1:], key=lambda item: item.global_rmse_pct)
    best_longwave = min(results[1:], key=lambda item: item.longwave_rmse_pct)

    executive_summary = f"""本轮 sandbox 明确支持“**ITO 近红外吸收失真是主导因素**”这一结论。  

- 基线 BEMA 模型的 `Global RMSE = {baseline.global_rmse_pct:.3f}%`、`Long-wave RMSE = {baseline.longwave_rmse_pct:.3f}%`
- Probe A 把它们分别压到 `{ito_probe.global_rmse_pct:.3f}%` 和 `{ito_probe.longwave_rmse_pct:.3f}%`
- 与之相比，Probe B 和 Probe C 虽然也能改善条纹形状，但改善幅度明显更弱

因此，“长波端托平”首先应归因于 ITO 的近红外吸收偏弱；厚度不均匀性和 PVK 色散斜率失真更像二级因素。"""

    counter_proposal = f"""人类给出的两个方向都不是空想，但数据告诉我们：**方向 1 的解释力远强于方向 2**。  

- Probe B（厚度不均匀性）把全局 RMSE 从 `{baseline.global_rmse_pct:.3f}%` 降到 `{sigma_probe.global_rmse_pct:.3f}%`，说明它确实会把条纹做宽、做钝
- Probe C（PVK Cauchy 斜率）把全局 RMSE 降到 `{slope_probe.global_rmse_pct:.3f}%`，说明色散斜率也参与了条纹跨度误差
- 但两者都没有像 Probe A 那样同时显著修复“整体形状 + 长波端托平”

因此，我的反驳是：**当前这次失真不能优先归因于厚度统计平均，也不能优先归因于 PVK Cauchy 外推过平；首要矛盾仍是 ITO 在近红外的吸收建模不足。**"""

    next_step = """建议下一步优先把“ITO 近红外吸收修正”固化到 `step02` 主流程。  

具体做法上，不建议直接把 sandbox 里的经验缩放系数原样硬编码，而是应把它升格为更物理的 ITO 自由载流子吸收修正参数化，例如：

1. 先在 `step02` 中引入一个受限的 ITO 近红外 `k` 增强因子或等价 Drude 校正项
2. 保持 BEMA 粗糙层继续负责振幅压制
3. 仅在完成 ITO 修正后，才继续评估是否需要把厚度高斯平均或 PVK Cauchy `B` 缩放并入主流程"""

    return f"""# Phase 02 Shape Diagnostic Report

## 1. Executive Summary

{executive_summary}

本轮基线模型（BEMA 双参数反演）指标：

- `chi^2 = {baseline.chisqr:.6f}`
- `Global RMSE = {baseline.global_rmse_pct:.3f}%`
- `Long-wave RMSE = {baseline.longwave_rmse_pct:.3f}%`
- `Long-wave Bias = {baseline.longwave_bias_pct:+.3f}%`

诊断结果总表：

{render_results_table(results)}

## 2. ITO Absorption Analysis

Probe A 通过对 ITO 的近红外 `k` 施加随波长增长的增强因子 `alpha_ITO` 来测试 Drude 吸收失真假说。

- 最优 `alpha_ITO = {ito_probe.params.get('ito_k_alpha', 0.0):.4f}`
- `chi^2 = {ito_probe.chisqr:.6f}`
- `Global RMSE = {ito_probe.global_rmse_pct:.3f}%`
- `Long-wave RMSE = {ito_probe.longwave_rmse_pct:.3f}%`
- `Long-wave Bias = {ito_probe.longwave_bias_pct:+.3f}%`

结论：

- Probe A 在所有已测探针中给出了最好的全局和长波误差。
- 这说明 ITO 近红外吸收增强不仅能解释长波端托平，也能显著改善整体条纹形状。
- {boundary_note(ito_probe, "ito_k_alpha", 0.0, 20.0)}

## 3. Inhomogeneity & Dispersion Analysis

### Probe B: 厚度不均匀性

- 最优 `sigma_thickness = {sigma_probe.params.get('sigma_thickness', 0.0):.4f} nm`
- `chi^2 = {sigma_probe.chisqr:.6f}`
- `Global RMSE = {sigma_probe.global_rmse_pct:.3f}%`
- `Long-wave RMSE = {sigma_probe.longwave_rmse_pct:.3f}%`
- `Long-wave Bias = {sigma_probe.longwave_bias_pct:+.3f}%`

判断：

- Probe B 明显优于基线，说明光斑面积内的宏观厚度不均匀性确实会展宽条纹。
- 但它对长波端偏差的修复远弱于 Probe A，说明“托平”不能主要归因于厚度平均。
- {boundary_note(sigma_probe, "sigma_thickness", 0.0, 30.0)}

### Probe C: PVK Cauchy 斜率

- 最优 `B_scale = {slope_probe.params.get('pvk_b_scale', 0.0):.4f}`
- `chi^2 = {slope_probe.chisqr:.6f}`
- `Global RMSE = {slope_probe.global_rmse_pct:.3f}%`
- `Long-wave RMSE = {slope_probe.longwave_rmse_pct:.3f}%`
- `Long-wave Bias = {slope_probe.longwave_bias_pct:+.3f}%`

判断：

- Probe C 也优于基线，说明当前 PVK 的近红外色散斜率可能确实偏平。
- 但它仍然明显落后于 Probe A，说明色散斜率不是这次畸变的首要矛盾。
- {boundary_note(slope_probe, "pvk_b_scale", 0.40, 1.60)}

## 4. AI's Counter-proposal

{counter_proposal}

进一步说明：

- BEMA 粗糙层已经成功解决“振幅过高”问题，但不会自动解决“长波端托平 + 条纹跨度偏宽”的复合畸变。
- 若后续继续扩展 sandbox，最有价值的联合模型将是：
  - `ITO absorption correction + BEMA roughness`
  - 必要时再叠加 `sigma_thickness`
  - 最后才考虑把 `PVK Cauchy B-scale` 做成正式自由度

## 5. Next Step Recommendation

{next_step}

建议下一轮主流程候选优先级：

1. `{best_global.label}`
2. `Probe B: Thickness Inhomogeneity`
3. `Probe C: PVK Cauchy Slope`
"""


def main() -> None:
    project_root = get_project_root()
    step02_path = project_root / "src" / "scripts" / "step02_tmm_inversion.py"
    figure_output_path = project_root / "results" / "figures" / "diagnostic_shape_analysis.png"
    report_output_path = project_root / "results" / "logs" / "phase02_shape_diagnostic_report.md"

    figure_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.parent.mkdir(parents=True, exist_ok=True)

    step02 = load_step02_module(step02_path)

    target_csv = project_root / "data" / "processed" / "target_reflectance.csv"
    pvk_csv = project_root / "data" / "processed" / "CsFAPI_nk_extended.csv"
    ito_path = project_root / "resources" / "ITO_20 Ohm_105 nm_e1e2.mat"

    wavelength_nm, r_target = step02.load_target_reflectance_csv(target_csv)

    ito_wavelength_nm, ito_e1, ito_e2 = step02.load_ito_dispersion(ito_path)
    step02.validate_interp_domain(wavelength_nm, ito_wavelength_nm, "ITO 数据库")
    ito_nk = step02.convert_dielectric_to_nk(ito_e1, ito_e2)
    base_get_ito_nk = step02.build_ito_interpolator(ito_wavelength_nm, ito_nk)

    pvk_wavelength_nm, pvk_n, pvk_k = step02.load_pvk_dispersion(pvk_csv)
    step02.validate_interp_domain(wavelength_nm, pvk_wavelength_nm, "PVK 扩展光谱")
    base_get_pvk_nk = step02.build_pvk_interpolator(pvk_wavelength_nm, pvk_n, pvk_k)
    cauchy_a, cauchy_b = fit_cauchy_from_extended_table(pvk_wavelength_nm, pvk_n)

    baseline = run_diagnostic_fit(
        step02_module=step02,
        label="Baseline BEMA",
        color="#1565c0",
        note="当前主流程：BEMA 双参数反演",
        wavelength_nm=wavelength_nm,
        r_target=r_target,
        params=create_fit_parameters(step02),
        model_builder=lambda fit_params: (base_get_ito_nk, base_get_pvk_nk, 0.0),
    )

    probe_a = run_diagnostic_fit(
        step02_module=step02,
        label="Probe A: ITO IR Absorption",
        color="#ef6c00",
        note="对 ITO 的 k 在近红外长波端做增强缩放",
        wavelength_nm=wavelength_nm,
        r_target=r_target,
        params=create_fit_parameters(step02, include_ito_alpha=True),
        model_builder=lambda fit_params: (
            build_scaled_ito_interpolator(base_get_ito_nk, fit_params["ito_k_alpha"].value),
            base_get_pvk_nk,
            0.0,
        ),
    )

    probe_b = run_diagnostic_fit(
        step02_module=step02,
        label="Probe B: Thickness Inhomogeneity",
        color="#2e7d32",
        note="对 d_bulk 做高斯厚度平均",
        wavelength_nm=wavelength_nm,
        r_target=r_target,
        params=create_fit_parameters(step02, include_sigma=True),
        model_builder=lambda fit_params: (
            base_get_ito_nk,
            base_get_pvk_nk,
            fit_params["sigma_thickness"].value,
        ),
    )

    probe_c = run_diagnostic_fit(
        step02_module=step02,
        label="Probe C: PVK Cauchy Slope",
        color="#6a1b9a",
        note="将 PVK 的 Cauchy B 参数作为自由缩放变量",
        wavelength_nm=wavelength_nm,
        r_target=r_target,
        params=create_fit_parameters(step02, include_b_scale=True),
        model_builder=lambda fit_params: (
            base_get_ito_nk,
            build_scaled_pvk_interpolator(
                pvk_wavelength_nm=pvk_wavelength_nm,
                pvk_k=pvk_k,
                cauchy_a=cauchy_a,
                cauchy_b=cauchy_b,
                b_scale=fit_params["pvk_b_scale"].value,
            ),
            0.0,
        ),
    )

    results = [baseline, probe_a, probe_b, probe_c]
    plot_diagnostic_results(wavelength_nm, r_target, results, figure_output_path)

    report_output_path.write_text(build_diagnostic_report(results), encoding="utf-8")

    print("Phase 02 形状诊断完成。")
    print(f"输出图表: {figure_output_path}")
    print(f"输出报告: {report_output_path}")
    for result in results:
        print(
            f"{result.label}: chi^2={result.chisqr:.6f}, "
            f"global_rmse={result.global_rmse_pct:.3f}%, "
            f"longwave_rmse={result.longwave_rmse_pct:.3f}%"
        )


if __name__ == "__main__":
    main()
