"""Phase 08 manual TMM theory audit for single-wavelength reflectance."""

from __future__ import annotations

from pathlib import Path
import json
import math
import sys

import numpy as np
import pandas as pd
from tmm import coh_tmm


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core import reference_comparison as rc  # noqa: E402


TRACE_JSON = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase08"
    / "reference_comparison_trace"
    / "phase08_0429_trace_600nm_values.json"
)
MANIFEST_JSON = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase08"
    / "reference_comparison"
    / "phase08_0429_dual_reference_manifest_pvk_x01.json"
)
NK_CSV = PROJECT_ROOT / "resources" / "aligned_full_stack_nk_phase08_x01.csv"
AUDIT_JSON = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase08"
    / "reference_comparison"
    / "phase08_0429_theory_tmm_manual_audit_pvk_x01.json"
)
AUDIT_MD = (
    PROJECT_ROOT
    / "results"
    / "report"
    / "phase08_reference_comparison_trace"
    / "phase08_0429_theory_tmm_manual_audit_pvk_x01.md"
)
ABS_TOL = 1e-8
AIR = 1.0 + 0.0j
GLASS_THICKNESS_NOTE = "1 mm glass treated as incoherent spacer; current implementation uses P≈1."


def complex_payload(value: complex) -> dict[str, float]:
    phase_rad = float(np.angle(value))
    return {
        "real": float(np.real(value)),
        "imag": float(np.imag(value)),
        "abs": float(np.abs(value)),
        "phase_rad": phase_rad,
        "phase_deg": float(np.degrees(phase_rad)),
    }


def slim_complex(value: complex) -> dict[str, float]:
    return {
        "real": float(np.real(value)),
        "imag": float(np.imag(value)),
    }


def fmt(value: float) -> str:
    return f"{float(value):.12f}"


def fmt_complex(value: dict[str, float]) -> str:
    return f"{value['real']:.12f} + {value['imag']:.12f}i"


def diff_payload(manual: float, reference: float) -> dict[str, float | bool]:
    abs_diff = abs(float(manual) - float(reference))
    if abs(reference) < 1e-15:
        rel_diff = math.inf if abs_diff > 0 else 0.0
    else:
        rel_diff = abs_diff / abs(reference)
    return {
        "abs_diff": float(abs_diff),
        "rel_diff": float(rel_diff),
        "pass": abs_diff <= ABS_TOL,
    }


def fresnel_r(n0: complex, n1: complex) -> complex:
    return (n0 - n1) / (n0 + n1)


def fresnel_t(n0: complex, n1: complex) -> complex:
    return 2.0 * n0 / (n0 + n1)


def power_transmittance(n0: complex, n1: complex, t01: complex) -> float:
    return float((np.real(n1) / np.real(n0)) * abs(t01) ** 2)


def single_layer_manual(n0: complex, n1: complex, n2: complex, d1_nm: float, wavelength_nm: float) -> dict[str, object]:
    r01 = fresnel_r(n0, n1)
    r12 = fresnel_r(n1, n2)
    delta = 2.0 * np.pi * n1 * d1_nm / wavelength_nm
    exp_2i_delta = np.exp(2.0j * delta)
    exp_minus_2i_delta = np.exp(-2.0j * delta)
    r_stack = (r01 + r12 * exp_2i_delta) / (1.0 + r01 * r12 * exp_2i_delta)
    r_stack_minus = (r01 + r12 * exp_minus_2i_delta) / (1.0 + r01 * r12 * exp_minus_2i_delta)
    R_stack = float(abs(r_stack) ** 2)
    coh = coh_tmm("s", [n0, n1, n2], [np.inf, float(d1_nm), np.inf], 0.0, float(wavelength_nm))
    R_tmm = float(coh["R"])
    return {
        "r01": r01,
        "r12": r12,
        "delta": delta,
        "exp_2i_delta": exp_2i_delta,
        "exp_minus_2i_delta": exp_minus_2i_delta,
        "r_stack": r_stack,
        "r_stack_minus": r_stack_minus,
        "R_stack": R_stack,
        "R_tmm": R_tmm,
        "comparison": diff_payload(R_stack, R_tmm),
    }


def load_inputs() -> tuple[dict, dict, pd.DataFrame]:
    trace = json.loads(TRACE_JSON.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    nk_df = pd.read_csv(NK_CSV)
    return trace, manifest, nk_df


def interp_complex(nk_df: pd.DataFrame, wavelength_nm: float, n_col: str, k_col: str) -> complex:
    wavelength_base = nk_df["Wavelength_nm"].to_numpy(dtype=float)
    return rc.interpolate_complex(
        wavelength_query_nm=np.array([wavelength_nm], dtype=float),
        wavelength_base_nm=wavelength_base,
        real_base=nk_df[n_col].to_numpy(dtype=float),
        imag_base=nk_df[k_col].to_numpy(dtype=float),
    )[0]


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return lines


def build_audit() -> dict[str, object]:
    trace, manifest, nk_df = load_inputs()
    lambda_used_nm = float(trace["lambda_used_nm"])
    d_pvk_nm = float(trace["coherent_stack"]["glass_pvk"]["fixed"]["d1_nm"])
    d_ag_nm = float(manifest.get("d_ag_nm_assumption", 100.0))

    n_glass = interp_complex(nk_df, lambda_used_nm, "n_Glass", "k_Glass")
    n_pvk = interp_complex(nk_df, lambda_used_nm, "n_PVK", "k_PVK")
    n_ag = interp_complex(nk_df, lambda_used_nm, "n_Ag", "k_Ag")

    glass_pvk = single_layer_manual(n_glass, n_pvk, AIR, d_pvk_nm, lambda_used_nm)
    glass_ag = single_layer_manual(n_glass, n_ag, AIR, d_ag_nm, lambda_used_nm)
    ag_mirror = single_layer_manual(AIR, n_ag, AIR, d_ag_nm, lambda_used_nm)

    r_front = fresnel_r(AIR, n_glass)
    r_back = fresnel_r(n_glass, AIR)
    R01 = float(abs(r_front) ** 2)
    R10 = float(abs(r_back) ** 2)
    t01 = fresnel_t(AIR, n_glass)
    t10 = fresnel_t(n_glass, AIR)
    T01 = power_transmittance(AIR, n_glass, t01)
    T10 = power_transmittance(n_glass, AIR, t10)
    P = 1.0

    total_general_pvk = R01 + (T01 * T10 * (P**2) * glass_pvk["R_stack"]) / (1.0 - R10 * (P**2) * glass_pvk["R_stack"])
    total_simplified_pvk = R01 + (((1.0 - R01) ** 2) * glass_pvk["R_stack"]) / (1.0 - R01 * glass_pvk["R_stack"])
    total_general_glassag = R01 + (T01 * T10 * (P**2) * glass_ag["R_stack"]) / (1.0 - R10 * (P**2) * glass_ag["R_stack"])
    total_simplified_glassag = R01 + (((1.0 - R01) ** 2) * glass_ag["R_stack"]) / (1.0 - R01 * glass_ag["R_stack"])

    csv_pvk = float(trace["csv_comparison"]["R_TMM_GlassPVK_Fixed_theory_csv"]["reference"])
    csv_glassag = float(trace["csv_comparison"]["R_TMM_GlassAg_theory_csv"]["reference"])
    csv_agmirror = float(trace["csv_comparison"]["R_TMM_AgMirror_theory_csv"]["reference"])

    pvk_total_cmp = diff_payload(total_simplified_pvk, csv_pvk)
    glassag_total_cmp = diff_payload(total_simplified_glassag, csv_glassag)
    agmirror_cmp = diff_payload(ag_mirror["R_stack"], csv_agmirror)

    return {
        "meta": {
            "phase": "Phase 08",
            "sample_tag": "pvk_x01",
            "convention": {
                "time_factor": "exp(-iωt)",
                "forward_direction": "+z",
                "polarization": "s",
                "reflectance_rule": "R = |r|^2 for current non-absorbing incident medium",
                "note": "Main formula follows Steven Byrnes / python-tmm convention; exp(-2i delta) branch is only a sanity check.",
            },
            "source_trace_json": str(TRACE_JSON.relative_to(PROJECT_ROOT).as_posix()),
            "source_manifest_json": str(MANIFEST_JSON.relative_to(PROJECT_ROOT).as_posix()),
            "source_nk_csv": str(NK_CSV.relative_to(PROJECT_ROOT).as_posix()),
            "abs_tolerance": ABS_TOL,
        },
        "lambda_used_nm": lambda_used_nm,
        "N_glass": complex_payload(n_glass),
        "N_pvk": complex_payload(n_pvk),
        "N_ag": complex_payload(n_ag),
        "d_pvk_nm": d_pvk_nm,
        "d_ag_nm": d_ag_nm,
        "glass_pvk_air": {
            "structure": "Glass / PVK / Air",
            "r01": complex_payload(glass_pvk["r01"]),
            "r12": complex_payload(glass_pvk["r12"]),
            "delta": complex_payload(glass_pvk["delta"]),
            "exp_2i_delta": complex_payload(glass_pvk["exp_2i_delta"]),
            "r_stack_manual": complex_payload(glass_pvk["r_stack"]),
            "R_stack_manual": glass_pvk["R_stack"],
            "R_stack_tmm": glass_pvk["R_tmm"],
            **glass_pvk["comparison"],
        },
        "air_glass_front": {
            "structure": "Air / Glass",
            "r_front": complex_payload(r_front),
            "R_front": R01,
            "R10": R10,
            "T01": T01,
            "T10": T10,
            "P": P,
            "note": GLASS_THICKNESS_NOTE,
        },
        "glass_pvk_total": {
            "structure": "Air / Glass(thick incoherent) / PVK / Air",
            "R_total_general_formula": total_general_pvk,
            "R_total_simplified_formula": total_simplified_pvk,
            "R_TMM_GlassPVK_Fixed_csv": csv_pvk,
            **pvk_total_cmp,
        },
        "glass_ag": {
            "structure": "Air / Glass(thick incoherent) / Ag / Air",
            "R_stack_manual": glass_ag["R_stack"],
            "R_stack_tmm": glass_ag["R_tmm"],
            "R_total_general_formula": total_general_glassag,
            "R_total_manual": total_simplified_glassag,
            "R_TMM_GlassAg_csv": csv_glassag,
            "stack_abs_diff": glass_ag["comparison"]["abs_diff"],
            "stack_rel_diff": glass_ag["comparison"]["rel_diff"],
            "stack_pass": glass_ag["comparison"]["pass"],
            **glassag_total_cmp,
        },
        "ag_mirror": {
            "structure": "Air / Ag / Air",
            "R_manual": ag_mirror["R_stack"],
            "R_tmm": ag_mirror["R_tmm"],
            "R_TMM_AgMirror_csv": csv_agmirror,
            **agmirror_cmp,
            "caveat": "This only audits consistency with the current model; whether the physical Ag mirror is equivalent to Air / 100 nm Ag / Air still needs sample-level confirmation.",
        },
        "sanity_checks": {
            "exp_minus_2i_delta_result": {
                "r_stack": complex_payload(glass_pvk["r_stack_minus"]),
                "R_stack": float(abs(glass_pvk["r_stack_minus"]) ** 2),
                **diff_payload(float(abs(glass_pvk["r_stack_minus"]) ** 2), glass_pvk["R_tmm"]),
            },
            "note": "exp(-2i delta) is retained only as a convention sanity check; exp(+2i delta) is the report’s primary formula.",
        },
        "json_complex_real_imag_only": {
            "N_glass": slim_complex(n_glass),
            "N_pvk": slim_complex(n_pvk),
            "N_ag": slim_complex(n_ag),
        },
    }


def render_markdown(audit: dict[str, object]) -> str:
    gp = audit["glass_pvk_air"]
    front = audit["air_glass_front"]
    total = audit["glass_pvk_total"]
    gag = audit["glass_ag"]
    mirror = audit["ag_mirror"]
    sanity = audit["sanity_checks"]["exp_minus_2i_delta_result"]

    lines = [
        "# Phase 08 TMM Theoretical Reflectance Manual Audit",
        "",
        "## 1. Convention",
        "- 时间因子：`exp(-iωt)`",
        "- 前进方向：`+z`",
        "- 统一使用 `s polarization` 展示",
        "- 当前入射半无限介质非吸收，因此 `R = |r|²`",
        f"- 目标波长使用 trace 最近点：`lambda_used_nm = {fmt(audit['lambda_used_nm'])}`",
        "",
        "## 2. Glass / PVK / Air coherent stack",
        "$$r_{01}=\\frac{N_0-N_1}{N_0+N_1},\\qquad r_{12}=\\frac{N_1-N_2}{N_1+N_2}$$",
        "$$\\delta = \\frac{2\\pi N_1 d_1}{\\lambda}$$",
        "$$r_{\\mathrm{stack}} = \\frac{r_{01}+r_{12}e^{2 i \\delta}}{1+r_{01}r_{12}e^{2 i \\delta}},\\qquad R_{\\mathrm{stack}}=|r_{\\mathrm{stack}}|^2$$",
        "",
    ]
    lines.extend(
        markdown_table(
            ["quantity", "value"],
            [
                ["N_glass", fmt_complex(audit["N_glass"])],
                ["N_pvk", fmt_complex(audit["N_pvk"])],
                ["N_air", "1.000000000000 + 0.000000000000i"],
                ["d_pvk_nm", fmt(audit["d_pvk_nm"])],
                ["r01", fmt_complex(gp["r01"])],
                ["r12", fmt_complex(gp["r12"])],
                ["delta", fmt_complex(gp["delta"])],
                ["exp(2i delta)", fmt_complex(gp["exp_2i_delta"])],
                ["r_stack_manual", fmt_complex(gp["r_stack_manual"])],
                ["R_stack_manual", fmt(gp["R_stack_manual"])],
                ["R_stack_tmm", fmt(gp["R_stack_tmm"])],
                ["abs_diff", f"{gp['abs_diff']:.3e}"],
                ["PASS", gp["pass"]],
            ],
        )
    )
    lines.extend(
        [
            "",
            "## 3. Thick-glass incoherent cascade",
            "$$R_{\\mathrm{total}} = R_{01} + \\frac{T_{01}T_{10}P^2R_{\\mathrm{stack}}}{1-R_{10}P^2R_{\\mathrm{stack}}}$$",
            "当前简化条件：`Glass k≈0`，`P≈1`，`R01=R10=R_front`，`T01 T10=(1-R_front)^2`",
            "$$R_{\\mathrm{total}} = R_{\\mathrm{front}} + \\frac{(1-R_{\\mathrm{front}})^2 R_{\\mathrm{stack}}}{1-R_{\\mathrm{front}}R_{\\mathrm{stack}}}$$",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["quantity", "value"],
            [
                ["R_front", fmt(front["R_front"])],
                ["R_stack", fmt(gp["R_stack_manual"])],
                ["T01", fmt(front["T01"])],
                ["T10", fmt(front["T10"])],
                ["P", fmt(front["P"])],
                ["R_total_general_formula", fmt(total["R_total_general_formula"])],
                ["R_total_simplified_formula", fmt(total["R_total_simplified_formula"])],
                ["R_TMM_GlassPVK_Fixed_csv", fmt(total["R_TMM_GlassPVK_Fixed_csv"])],
                ["abs_diff", f"{total['abs_diff']:.3e}"],
                ["PASS", total["pass"]],
            ],
        )
    )
    lines.extend(["", "## 4. Reference theory audit"])
    lines.extend(
        markdown_table(
            ["case", "manual", "tmm", "csv", "abs_diff", "PASS"],
            [
                [
                    "glass/Ag stack",
                    fmt(gag["R_stack_manual"]),
                    fmt(gag["R_stack_tmm"]),
                    "—",
                    f"{gag['stack_abs_diff']:.3e}",
                    gag["stack_pass"],
                ],
                [
                    "glass/Ag total",
                    fmt(gag["R_total_manual"]),
                    "—",
                    fmt(gag["R_TMM_GlassAg_csv"]),
                    f"{gag['abs_diff']:.3e}",
                    gag["pass"],
                ],
                [
                    "Ag mirror",
                    fmt(mirror["R_manual"]),
                    fmt(mirror["R_tmm"]),
                    fmt(mirror["R_TMM_AgMirror_csv"]),
                    f"{mirror['abs_diff']:.3e}",
                    mirror["pass"],
                ],
            ],
        )
    )
    lines.extend(
        [
            "",
            "## 5. Convention sanity check",
            "下表仅用于说明 `exp(-2i delta)` 没被当成主物理逻辑。",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["quantity", "value"],
            [
                ["R_stack_by_exp(-2i delta)", fmt(sanity["R_stack"])],
                ["abs_diff_vs_tmm", f"{sanity['abs_diff']:.3e}"],
                ["PASS", sanity["pass"]],
            ],
        )
    )
    lines.extend(
        [
            "",
            "## 6. Conclusion boundary",
            "- 本审计证明当前手写公式、`tmm.coh_tmm()` 与现有 CSV 在当前模型假设下自洽。",
            "- 本审计不证明 `n,k` 数据一定代表真实样品，也不证明显微测量一定等于理想 specular reflectance。",
            f"- Ag mirror caveat：{mirror['caveat']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    audit = build_audit()
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_MD.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    AUDIT_MD.write_text(render_markdown(audit), encoding="utf-8")
    print(AUDIT_JSON.relative_to(PROJECT_ROOT).as_posix())
    print(AUDIT_MD.relative_to(PROJECT_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
