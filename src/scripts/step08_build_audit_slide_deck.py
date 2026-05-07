"""Build the Phase 08 HTML slide deck with manual TMM audit content."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SLIDE_DIR = PROJECT_ROOT / "results" / "slides" / "phase08_reference_audit"
DECK_HTML = SLIDE_DIR / "phase08_reference_audit_deck.html"
TECH_HTML = SLIDE_DIR / "phase08_reference_audit_technical_report.html"

TRACE_VALUES_JSON = PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison_trace" / "phase08_0429_trace_600nm_values.json"
TRACE_MD = PROJECT_ROOT / "results" / "report" / "phase08_reference_comparison_trace" / "phase08_0429_trace_600nm.md"
AUDIT_JSON = PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison" / "phase08_0429_theory_tmm_manual_audit_pvk_x01.json"
AUDIT_MD = PROJECT_ROOT / "results" / "report" / "phase08_reference_comparison_trace" / "phase08_0429_theory_tmm_manual_audit_pvk_x01.md"
MANIFEST_JSON = PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison" / "phase08_0429_dual_reference_manifest_pvk_x01.json"

REFLECTANCE_PNG = PROJECT_ROOT / "results" / "figures" / "phase08" / "reference_comparison" / "phase08_0429_dual_reference_reflectance_exp_vs_tmm_pvk_x01.png"
RESIDUAL_PNG = PROJECT_ROOT / "results" / "figures" / "phase08" / "reference_comparison" / "phase08_0429_residual_pvk_x01.png"
QC_PNG = PROJECT_ROOT / "results" / "figures" / "phase08" / "reference_comparison" / "phase08_0429_ag_bk_qc_pvk_x01.png"
VALUE_LOCATOR_REFLECTANCE_SVG = SLIDE_DIR / "assets" / "value_locator_reflectance.svg"
VALUE_LOCATOR_NK_SVG = SLIDE_DIR / "assets" / "value_locator_nk.svg"


def rel(path: Path) -> str:
    return os.path.relpath(path, SLIDE_DIR).replace(os.sep, "/")


def project_rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return reader.fieldnames or [], rows


def float_or_none(value: str) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def svg_line_plot(
    path: Path,
    title: str,
    x_values: list[float],
    series: list[dict[str, object]],
    x_marker: float,
    note: str,
    y_min: float | None = None,
    y_max: float | None = None,
) -> None:
    width, height = 900, 384
    margin = {"l": 74, "r": 64, "t": 64, "b": 62}
    plot_w = width - margin["l"] - margin["r"]
    plot_h = height - margin["t"] - margin["b"]
    finite_values = [y for item in series for y in item["y_values"] if y is not None]
    ymin = y_min if y_min is not None else min(finite_values)
    ymax = y_max if y_max is not None else max(finite_values)
    if ymax == ymin:
        ymax = ymin + 1.0
    x0, x1 = min(x_values), max(x_values)

    def sx(x: float) -> float:
        return margin["l"] + (x - x0) / (x1 - x0) * plot_w

    def sy(y: float) -> float:
        return margin["t"] + (1 - (y - ymin) / (ymax - ymin)) * plot_h

    grid = []
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        yv = ymin + (ymax - ymin) * frac
        y = sy(yv)
        grid.append(f'<line x1="{margin["l"]}" y1="{y:.2f}" x2="{width - margin["r"]}" y2="{y:.2f}" stroke="#e4e7ec" stroke-width="1"/>')
        grid.append(f'<text x="{margin["l"] - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="13" fill="#475467">{yv:.3f}</text>')

    paths = []
    labels = []
    for idx, item in enumerate(series):
        points = []
        last = None
        for x, y in zip(x_values, item["y_values"]):
            if y is None:
                if points:
                    paths.append(f'<polyline fill="none" stroke="{item["color"]}" stroke-width="3" points="{" ".join(points)}"/>')
                    points = []
                continue
            p = f"{sx(x):.2f},{sy(y):.2f}"
            points.append(p)
            last = (x, y)
        if points:
            paths.append(f'<polyline fill="none" stroke="{item["color"]}" stroke-width="3" points="{" ".join(points)}"/>')
        if last is not None:
            label_x = min(max(sx(last[0]) - 12, margin["l"] + 72), width - margin["r"] + 8)
            label_y = min(max(sy(last[1]) - 10 - idx * 18, margin["t"] + 14), height - margin["b"] - 8)
            labels.append(
                f'<text x="{label_x:.2f}" y="{label_y:.2f}" text-anchor="end" font-size="14" font-weight="700" fill="{item["color"]}">{item["label"]}</text>'
            )

    x_line = sx(x_marker)
    marker = [
        f'<line x1="{x_line:.2f}" y1="{margin["t"]}" x2="{x_line:.2f}" y2="{height - margin["b"]}" stroke="#344054" stroke-dasharray="8 6" stroke-width="2.5"/>',
        f'<text x="{x_line + 8:.2f}" y="{margin["t"] + 16:.2f}" font-size="14" font-weight="700" fill="#344054">λ = {x_marker:.3f} nm</text>',
    ]
    x_ticks = []
    for tick in [400, 500, 600, 700, 800, 900]:
        if x0 <= tick <= x1:
            x = sx(float(tick))
            x_ticks.append(f'<line x1="{x:.2f}" y1="{height - margin["b"]}" x2="{x:.2f}" y2="{height - margin["b"] + 6}" stroke="#98a2b3" stroke-width="1"/>')
            x_ticks.append(f'<text x="{x:.2f}" y="{height - margin["b"] + 24}" text-anchor="middle" font-size="13" fill="#475467">{tick}</text>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#ffffff"/>
  <text x="{margin["l"]}" y="28" font-size="24" font-weight="700" fill="#101828">{title}</text>
  {''.join(grid)}
  <line x1="{margin["l"]}" y1="{height - margin["b"]}" x2="{width - margin["r"]}" y2="{height - margin["b"]}" stroke="#98a2b3" stroke-width="1.5"/>
  <line x1="{margin["l"]}" y1="{margin["t"]}" x2="{margin["l"]}" y2="{height - margin["b"]}" stroke="#98a2b3" stroke-width="1.5"/>
  {''.join(x_ticks)}
  {''.join(paths)}
  {''.join(labels)}
  {''.join(marker)}
  <text x="{margin["l"]}" y="{height - 12}" font-size="14" fill="#475467">{note}</text>
</svg>"""
    path.write_text(svg, encoding="utf-8")


def render_trace_step(tag: str, cls: str, title: str, body: str) -> str:
    return f"""
    <div class="trace-step" data-qa-watch="{tag}">
      <div class="trace-step-tag {cls}">{tag}</div>
      <div class="trace-step-body">
        <div class="trace-step-title">{title}</div>
        {body}
      </div>
    </div>
    """


def chip(value: bool) -> str:
    cls = "pass" if value else "fail"
    label = "PASS" if value else "FAIL"
    return f'<span class="status-chip {cls}">{label}</span>'


def fmt_complex(parts: dict[str, float], digits: int = 6) -> str:
    return f"{parts['real']:.{digits}f} + {parts['imag']:.{digits}f}i"


def fmt_float(value: float, digits: int = 6) -> str:
    return f"{float(value):.{digits}f}"


def table_html(headers: list[str], rows: list[list[str]], table_class: str = "audit-table") -> str:
    thead = "".join(f"<th>{item}</th>" for item in headers)
    tbody = []
    for row in rows:
        tbody.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    return f'<table class="{table_class}"><thead><tr>{thead}</tr></thead><tbody>{"".join(tbody)}</tbody></table>'


def main() -> int:
    values = json.loads(TRACE_VALUES_JSON.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    trace_md = TRACE_MD.read_text(encoding="utf-8")
    audit_md = AUDIT_MD.read_text(encoding="utf-8")

    c = values["counts"]
    fresnel = values["fresnel"]
    row = values["experimental_reflectance"]
    ag_diag = values["ag_mirror_multiframe_trace"]
    lambda_used = float(values["lambda_used_nm"])

    gp = audit["glass_pvk_air"]
    front = audit["air_glass_front"]
    total = audit["glass_pvk_total"]
    gag = audit["glass_ag"]
    mirror = audit["ag_mirror"]
    sanity = audit["sanity_checks"]["exp_minus_2i_delta_result"]

    _, reflectance_rows = read_csv_rows(
        PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison" / "phase08_0429_dual_reference_calibrated_reflectance_pvk_x01.csv"
    )
    _, nk_rows = read_csv_rows(PROJECT_ROOT / "resources" / "aligned_full_stack_nk_phase08_x01.csv")

    reflectance_x = [float(r["\ufeffWavelength_nm"]) for r in reflectance_rows]
    reflectance_gag = [float_or_none(r["R_Exp_GlassPVK_by_GlassAg"]) for r in reflectance_rows]
    reflectance_tmm = [float_or_none(r["R_TMM_GlassPVK_Fixed"]) for r in reflectance_rows]
    nk_x = [float(r["\ufeffWavelength_nm"]) for r in nk_rows]
    pvk_n = [float_or_none(r["n_PVK"]) for r in nk_rows]
    pvk_k = [float_or_none(r["k_PVK"]) for r in nk_rows]
    ag_k = [float_or_none(r["k_Ag"]) for r in nk_rows]

    svg_line_plot(
        VALUE_LOCATOR_REFLECTANCE_SVG,
        "Reflectance source window",
        reflectance_x,
        [
            {"label": "Exp by glass/Ag", "color": "#2f6fed", "y_values": reflectance_gag},
            {"label": "TMM fixed", "color": "#047857", "y_values": reflectance_tmm},
        ],
        lambda_used,
        "在实验曲线与 TMM 曲线上用同一根虚线标出单点 trace 的取值波长。",
        y_min=0.0,
        y_max=0.5,
    )
    svg_line_plot(
        VALUE_LOCATOR_NK_SVG,
        "n,k source window",
        nk_x,
        [
            {"label": "PVK n", "color": "#7c3aed", "y_values": pvk_n},
            {"label": "PVK k", "color": "#d97706", "y_values": pvk_k},
            {"label": "Ag k", "color": "#ef4444", "y_values": ag_k},
        ],
        lambda_used,
        "同一波长虚线同时穿过 n,k 数据表对应位置，说明数值代入来自当前 Phase 08 材料表。",
    )

    glassag_steps = "".join(
        [
            render_trace_step("1", "glassag", "通用公式", "<div>$R_{\\mathrm{exp}}^{\\mathrm{glass/Ag}} = \\frac{I_{\\mathrm{PVK}}/t_{\\mathrm{PVK}}}{I_{\\mathrm{glass/Ag}}/t_{\\mathrm{glass/Ag}}} \\cdot R_{\\mathrm{TMM}}^{\\mathrm{glass/Ag}}$</div>"),
            render_trace_step("2", "glassag", "数值代入", f"<div>$= \\frac{{{c['Glass_PVK_Counts']:.3f}/20}}{{{c['Glass_Ag_Counts']:.3f}/20}} \\cdot {row['R_TMM_GlassAg']:.6f}$</div>"),
            render_trace_step("3", "glassag", "counts ratio", f"<div>$\\frac{{I_{{\\mathrm{{PVK}}}}/t}}{{I_{{\\mathrm{{glass/Ag}}}}/t}} = {row['counts_ratio_glassAg']:.6f}$</div>"),
            render_trace_step("4", "glassag", "乘以 R_TMM_GlassAg", f"<div>${row['counts_ratio_glassAg']:.6f} \\times {row['R_TMM_GlassAg']:.6f}$</div>"),
            render_trace_step("5", "glassag", "得到 R_exp_by_glassAg", f"<div>$R_{{\\mathrm{{exp}}}}^{{\\mathrm{{glass/Ag}}}} = {row['R_Exp_GlassPVK_by_GlassAg']:.6f}$</div>"),
        ]
    )
    agmirror_steps = "".join(
        [
            render_trace_step("1", "agmirror", "通用公式", "<div>$R_{\\mathrm{exp}}^{\\mathrm{Ag\\ mirror}} = \\frac{I_{\\mathrm{PVK}}/t_{\\mathrm{PVK}}}{I_{\\mathrm{Ag\\ mirror,corr}}/t_{\\mathrm{Ag\\ mirror}}} \\cdot R_{\\mathrm{TMM}}^{\\mathrm{Ag\\ mirror}}$</div>"),
            render_trace_step("2", "agmirror", "数值代入", f"<div>$= \\frac{{{c['Glass_PVK_Counts']:.3f}/20}}{{{c['Ag_Mirror_Corrected_Counts']:.3f}/20}} \\cdot {row['R_TMM_AgMirror']:.6f}$</div>"),
            render_trace_step("3", "agmirror", "counts ratio", f"<div>$\\frac{{I_{{\\mathrm{{PVK}}}}/t}}{{I_{{\\mathrm{{Ag\\ mirror,corr}}}}/t}} = {row['counts_ratio_AgMirror']:.6f}$</div>"),
            render_trace_step("4", "agmirror", "乘以 R_TMM_AgMirror", f"<div>${row['counts_ratio_AgMirror']:.6f} \\times {row['R_TMM_AgMirror']:.6f}$</div>"),
            render_trace_step("5", "agmirror", "得到 R_exp_by_AgMirror", f"<div>$R_{{\\mathrm{{exp}}}}^{{\\mathrm{{Ag\\ mirror}}}} = {row['R_Exp_GlassPVK_by_AgMirror']:.6f}$</div>"),
        ]
    )

    slide_d_table = table_html(
        ["quantity", "value"],
        [
            ["R_stack_manual", fmt_float(gp["R_stack_manual"], 12)],
            ["R_stack_tmm", fmt_float(gp["R_stack_tmm"], 12)],
            ["abs_diff", f"{gp['abs_diff']:.3e}"],
            ["rel_diff", f"{gp['rel_diff']:.3e}"],
            ["result", chip(gp["pass"])],
        ],
    )
    slide_f_table = table_html(
        ["case", "manual", "tmm", "csv", "abs_diff", "result"],
        [
            [
                "glass/Ag stack",
                fmt_float(gag["R_stack_manual"], 12),
                fmt_float(gag["R_stack_tmm"], 12),
                "—",
                f"{gag['stack_abs_diff']:.3e}",
                chip(gag["stack_pass"]),
            ],
            [
                "glass/Ag total",
                fmt_float(gag["R_total_manual"], 12),
                "—",
                fmt_float(gag["R_TMM_GlassAg_csv"], 12),
                f"{gag['abs_diff']:.3e}",
                chip(gag["pass"]),
            ],
            [
                "Ag mirror",
                fmt_float(mirror["R_manual"], 12),
                fmt_float(mirror["R_tmm"], 12),
                fmt_float(mirror["R_TMM_AgMirror_csv"], 12),
                f"{mirror['abs_diff']:.3e}",
                chip(mirror["pass"]),
            ],
        ],
        "audit-table compact",
    )

    deck = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Phase 08 反射率校准与 TMM 审计</title>
  <link rel="stylesheet" href="../../../node_modules/reveal.js/dist/reveal.css" />
  <link rel="stylesheet" href="../../../node_modules/katex/dist/katex.min.css" />
  <link rel="stylesheet" href="assets/theme.css" />
</head>
<body>
  <div class="reveal">
    <div class="slides">
      <section data-qa-watch="slide-1">
        <h1 class="slide-title">Phase 08 反射率校准与 TMM 审计</h1>
        <p class="slide-subtitle">本 deck 继续读取现有 <span class="en">pvk_x01</span> 结果；新增的理论审计章节只证明公式与实现自洽，不改核心主计算链。</p>
        <div class="deck-grid-2">
          <div class="card soft">
            <h2 class="card-title">本轮目标</h2>
            <ul class="bullet-list">
              <li>保留实验反射率校准链。</li>
              <li>新增手写公式审计，证明理论反射率不是黑箱输出。</li>
              <li>让 slide deck 与 technical report 共同消费同一份审计 JSON。</li>
            </ul>
          </div>
          <div class="card soft">
            <h2 class="card-title">当前边界</h2>
            <ul class="bullet-list">
              <li>数据集：0429</li>
              <li>结果集：<span class="en">pvk_x01</span></li>
              <li>审计波长：<span class="en">{lambda_used:.12f} nm</span></li>
              <li>不重算 <span class="en">src/core/reference_comparison.py</span> 主结果。</li>
            </ul>
          </div>
        </div>
        <div class="metric-strip">
          <div class="metric-card"><div class="metric-label">R_exp by glass/Ag</div><div class="metric-value" style="color:var(--color-glassag)">{row["R_Exp_GlassPVK_by_GlassAg"]:.6f}</div></div>
          <div class="metric-card"><div class="metric-label">R_exp by Ag mirror</div><div class="metric-value" style="color:var(--color-agmirror)">{row["R_Exp_GlassPVK_by_AgMirror"]:.6f}</div></div>
          <div class="metric-card"><div class="metric-label">R_TMM GlassPVK fixed</div><div class="metric-value" style="color:var(--color-tmm-fixed)">{row["R_TMM_GlassPVK_Fixed"]:.6f}</div></div>
        </div>
      </section>

      <section data-qa-watch="slide-2">
        <h1 class="slide-title">Incoherent Cascade</h1>
        <p class="slide-subtitle">厚玻璃前表面与后侧相干薄膜栈之间采用强度级联，而不是整体相干求和。</p>
        <div class="deck-grid-2">
          <div class="stack-col">
            <div class="card formula-card">
              <div class="formula-label">当前简化式</div>
              <div>$$R_{{\\mathrm{{total}}}} = R_{{\\mathrm{{front}}}} + \\frac{{(1-R_{{\\mathrm{{front}}}})^2 R_{{\\mathrm{{stack}}}}}}{{1-R_{{\\mathrm{{front}}}}R_{{\\mathrm{{stack}}}}}}$$</div>
            </div>
            <div class="card formula-card">
              <div class="formula-label">数字代入</div>
              <div>$$R_{{\\mathrm{{total}}}} = {front["R_front"]:.6f} + \\frac{{(1-{front["R_front"]:.6f})^2 \\times {gp["R_stack_manual"]:.6f}}}{{1-{front["R_front"]:.6f}\\times {gp["R_stack_manual"]:.6f}}}$$</div>
            </div>
            <div class="card formula-card">
              <div class="formula-label">结果</div>
              <div>$$R_{{\\mathrm{{TMM,GlassPVK,Fixed}}}} = {total["R_total_simplified_formula"]:.6f}$$</div>
            </div>
          </div>
          <div class="stack-col">
            <div class="card diagram-card">
              <div class="cascade-diagram">
                <div class="cascade-node">
                  <div class="cascade-node-title">Air / Glass</div>
                  <div class="cascade-node-note">前表面 Fresnel</div>
                  <div class="cascade-node-note">R_front = {front["R_front"]:.6f}</div>
                </div>
                <div class="arrow">→</div>
                <div class="cascade-node mid">
                  <div class="cascade-node-title">1 mm glass</div>
                  <div class="cascade-node-note">非相干隔离层</div>
                  <div class="cascade-node-note">P ≈ 1</div>
                </div>
                <div class="arrow">→</div>
                <div class="cascade-node end">
                  <div class="cascade-node-title">Glass / PVK / Air</div>
                  <div class="cascade-node-note">后侧相干薄膜栈</div>
                  <div class="cascade-node-note">R_stack = {gp["R_stack_manual"]:.6f}</div>
                </div>
              </div>
              <div class="diagram-caption">前表面贡献 Fresnel 强度，后侧薄膜条纹在 <span class="en">R_stack</span> 中处理。</div>
            </div>
            <div class="card">
              <h2 class="card-title">术语解释</h2>
              <ul class="bullet-list compact-list">
                <li><span class="en">R_front</span>：<span class="en">Air/Glass</span> 前表面 Fresnel 反射率。</li>
                <li><span class="en">R_stack</span>：<span class="en">Glass/PVK/Air</span> 后侧薄膜栈的相干反射率。</li>
                <li><span class="en">P</span>：厚玻璃单程传播强度保留因子；当前实现取 <span class="en">P≈1</span>。</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section data-qa-watch="slide-3">
        <h1 class="slide-title">600 nm Trace: Counts to R_exp</h1>
        <p class="slide-subtitle">左右两列分别展开 <span class="en">glass/Ag</span> 与 <span class="en">Ag mirror</span> 参比链，强调“公式 + 数字代入 + 结果”。</p>
        <div class="deck-grid-2">
          <div class="trace-col">
            <div class="card">
              <h2 class="card-title">glass/Ag chain</h2>
              <div class="trace-chain">
                {glassag_steps}
              </div>
            </div>
          </div>
          <div class="trace-col">
            <div class="card">
              <h2 class="card-title">Ag mirror chain</h2>
              <div class="trace-chain">
                {agmirror_steps}
              </div>
            </div>
          </div>
        </div>
        <div class="metric-strip">
          <div class="metric-card"><div class="metric-label">R_TMM_GlassPVK_Fixed</div><div class="metric-value" style="color:var(--color-tmm-fixed)">{row["R_TMM_GlassPVK_Fixed"]:.6f}</div></div>
          <div class="metric-card"><div class="metric-label">Ag frame dropped / used</div><div class="metric-value">{ag_diag["Ag_frames_dropped"][0]} / {ag_diag["Ag_used_frame_count"]}</div></div>
          <div class="metric-card"><div class="metric-label">BK frames</div><div class="metric-value">{ag_diag["BK_used_frame_count"]}</div></div>
        </div>
      </section>

      <section data-qa-watch="slide-4">
        <h1 class="slide-title">Why Audit Theoretical TMM?</h1>
        <p class="slide-subtitle">实验反射率显著高于理论值，因此必须先确认理论反射率链路不是公式或库调用错误。</p>
        <div class="deck-grid-3">
          <div class="card audit-pillar">
            <div class="pillar-index">01</div>
            <h2 class="card-title">手写单层公式</h2>
            <p class="body-text">把 <span class="en">Glass / PVK / Air</span> 与 <span class="en">Glass / Ag / Air</span> 的振幅反射式完整写开，显式展示 <span class="en">r01</span>、<span class="en">r12</span>、<span class="en">delta</span> 与 <span class="en">exp(2i delta)</span>。</p>
          </div>
          <div class="card audit-pillar">
            <div class="pillar-index">02</div>
            <h2 class="card-title">Python tmm.coh_tmm</h2>
            <p class="body-text">用同一层序、同一厚度、同一波长、同一 <span class="en">s polarization</span> 做独立计算，排除“手写式推导错了”的风险。</p>
          </div>
          <div class="card audit-pillar">
            <div class="pillar-index">03</div>
            <h2 class="card-title">当前 CSV 输出</h2>
            <p class="body-text">再与当前 Phase 08 理论 CSV 对比，确认 slide 中展示的理论值和现有主链输出一致，不存在二次抄写误差。</p>
          </div>
        </div>
        <div class="callout-row">
          <div class="callout-card">结论标准：所有关键比较以 <span class="en">abs_diff ≤ 1e-8</span> 为 PASS。</div>
          <div class="callout-card">审计范围：证明“公式与实现自洽”，不证明“nk 与实验语义已经完全正确”。</div>
        </div>
      </section>

      <section data-qa-watch="slide-5">
        <h1 class="slide-title">Glass / PVK / Air Manual Coherent Formula</h1>
        <p class="slide-subtitle">主公式固定采用 Steven Byrnes / python <span class="en">tmm</span> convention：<span class="en">exp(-iωt)</span>、前进方向 <span class="en">+z</span>、展示用 <span class="en">s polarization</span>。</p>
        <div class="deck-grid-2">
          <div class="stack-col">
            <div class="card formula-card tall">
              <div class="formula-label">interface amplitudes</div>
              <div>$$r_{{01}} = \\frac{{N_0-N_1}}{{N_0+N_1}}, \\qquad r_{{12}} = \\frac{{N_1-N_2}}{{N_1+N_2}}$$</div>
            </div>
            <div class="card formula-card tall">
              <div class="formula-label">phase</div>
              <div>$$\\delta = \\frac{{2\\pi N_1 d_1}}{{\\lambda}}$$</div>
            </div>
            <div class="card formula-card tall">
              <div class="formula-label">main formula</div>
              <div>$$r_{{\\mathrm{{stack}}}} = \\frac{{r_{{01}} + r_{{12}} e^{{2 i \\delta}}}}{{1 + r_{{01}} r_{{12}} e^{{2 i \\delta}}}}, \\qquad R_{{\\mathrm{{stack}}}} = |r_{{\\mathrm{{stack}}}}|^2$$</div>
            </div>
          </div>
          <div class="stack-col">
            <div class="card diagram-card">
              <div class="layer-stack">
                <div class="layer-box glass">Glass<br/><span>incident semi-infinite medium</span></div>
                <div class="layer-box pvk">PVK<br/><span>d = {audit["d_pvk_nm"]:.2f} nm</span></div>
                <div class="layer-box air">Air<br/><span>N = 1 + 0i</span></div>
              </div>
              <div class="diagram-caption">这一页只处理后侧相干薄膜栈，不把厚玻璃前表面混进相位项。</div>
            </div>
            <div class="card">
              <h2 class="card-title">600 nm 处材料复折射率</h2>
              <div class="mini-metric-grid">
                <div class="mini-metric"><span>N_glass</span><strong>{fmt_complex(audit["N_glass"])}</strong></div>
                <div class="mini-metric"><span>N_pvk</span><strong>{fmt_complex(audit["N_pvk"])}</strong></div>
                <div class="mini-metric"><span>N_air</span><strong>1.000000 + 0.000000i</strong></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section data-qa-watch="slide-6">
        <h1 class="slide-title">600 nm Numerical Substitution</h1>
        <p class="slide-subtitle">这里展示的是“公式 + 数字代入 + 结果”，并显式标出真实取值波长 <span class="en">{lambda_used:.12f} nm</span>，不是强行代到精确 <span class="en">600.000 nm</span>。</p>
        <div class="deck-grid-2">
          <div class="stack-col">
            <div class="card formula-card">
              <div class="formula-label">numerical chain</div>
              <div>$$N_0 = {audit["N_glass"]["real"]:.6f} + {audit["N_glass"]["imag"]:.6f}i, \\quad N_1 = {audit["N_pvk"]["real"]:.6f} + {audit["N_pvk"]["imag"]:.6f}i$$</div>
              <div>$$r_{{01}} = {gp["r01"]["real"]:.6f} + {gp["r01"]["imag"]:.6f}i, \\quad r_{{12}} = {gp["r12"]["real"]:.6f} + {gp["r12"]["imag"]:.6f}i$$</div>
              <div>$$\\delta = {gp["delta"]["real"]:.6f} + {gp["delta"]["imag"]:.6f}i, \\quad e^{{2 i\\delta}} = {gp["exp_2i_delta"]["real"]:.6f} + {gp["exp_2i_delta"]["imag"]:.6f}i$$</div>
              <div>$$r_{{\\mathrm{{stack}}}} = {gp["r_stack_manual"]["real"]:.6f} + {gp["r_stack_manual"]["imag"]:.6f}i$$</div>
              <div>$$R_{{\\mathrm{{stack}}}} = {gp["R_stack_manual"]:.12f}$$</div>
            </div>
            <div class="card">
              <h2 class="card-title">核心数值</h2>
              <div class="mini-metric-grid">
                <div class="mini-metric"><span>lambda_used_nm</span><strong>{lambda_used:.12f}</strong></div>
                <div class="mini-metric"><span>d_PVK</span><strong>{audit["d_pvk_nm"]:.3f} nm</strong></div>
                <div class="mini-metric"><span>R_stack_manual</span><strong>{gp["R_stack_manual"]:.12f}</strong></div>
              </div>
            </div>
          </div>
          <div class="stack-col">
            <div class="card source-card">
              <h2 class="card-title">取值来源：反射率曲线</h2>
              <img src="assets/value_locator_reflectance.svg" alt="reflectance locator" />
              <div class="source-caption">单点审计波长和实验 / 理论曲线使用同一根虚线标出。</div>
            </div>
            <div class="card source-card">
              <h2 class="card-title">取值来源：n,k 材料表</h2>
              <img src="assets/value_locator_nk.svg" alt="nk locator" />
              <div class="source-caption">材料表上的同一波长定位说明代入来源是可追溯的，不是手工挑值。</div>
            </div>
          </div>
        </div>
      </section>

      <section data-qa-watch="slide-7">
        <h1 class="slide-title">Manual Formula vs tmm.coh_tmm</h1>
        <p class="slide-subtitle">主公式采用 <span class="en">exp(+2i delta)</span>；<span class="en">exp(-2i delta)</span> 只保留为 convention sanity check，不作为主物理逻辑。</p>
        <div class="deck-grid-2">
          <div class="card table-card">
            <h2 class="card-title">Glass / PVK / Air consistency check</h2>
            {slide_d_table}
          </div>
          <div class="stack-col">
            <div class="card formula-card tall">
              <div class="formula-label">sanity check only</div>
              <div>$$R_{{\\mathrm{{stack}}}}^{{e^{{-2i\\delta}}}} = {sanity["R_stack"]:.12f}$$</div>
            </div>
            <div class="card">
              <h2 class="card-title">说明</h2>
              <ul class="bullet-list compact-list">
                <li>主公式与 <span class="en">tmm.coh_tmm</span> 在当前口径下通过 <span class="en">{chip(gp["pass"])}</span>。</li>
                <li><span class="en">exp(-2i delta)</span> 分支被保留，只是为了避免符号 convention 被误写成“自动择优”。</li>
                <li>当前报告明确采用 Byrnes / <span class="en">tmm</span> convention。</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section data-qa-watch="slide-8">
        <h1 class="slide-title">Thick Glass Incoherent Cascade</h1>
        <p class="slide-subtitle">先写通用式，再说明当前 Phase 08 为何可以退化到现有实现里的简化式。</p>
        <div class="deck-grid-2">
          <div class="stack-col">
            <div class="card formula-card tall">
              <div class="formula-label">general formula</div>
              <div>$$R_{{\\mathrm{{total}}}} = R_{{01}} + \\frac{{T_{{01}} T_{{10}} P^2 R_{{\\mathrm{{stack}}}}}}{{1 - R_{{10}} P^2 R_{{\\mathrm{{stack}}}}}}$$</div>
            </div>
            <div class="card formula-card tall">
              <div class="formula-label">current simplification</div>
              <div>$$R_{{\\mathrm{{total}}}} = R_{{\\mathrm{{front}}}} + \\frac{{(1-R_{{\\mathrm{{front}}}})^2 R_{{\\mathrm{{stack}}}}}}{{1-R_{{\\mathrm{{front}}}}R_{{\\mathrm{{stack}}}}}}$$</div>
            </div>
            <div class="card">
              <h2 class="card-title">简化条件</h2>
              <ul class="bullet-list compact-list">
                <li><span class="en">Glass k ≈ 0</span></li>
                <li><span class="en">P ≈ 1</span></li>
                <li><span class="en">R01 = R10 = R_front</span></li>
                <li><span class="en">T01 · T10 = (1 - R_front)^2</span></li>
              </ul>
            </div>
          </div>
          <div class="stack-col">
            <div class="card table-card">
              <h2 class="card-title">Numerical substitution</h2>
              {table_html(
                  ["quantity", "value"],
                  [
                      ["R_front", fmt_float(front["R_front"], 12)],
                      ["R_stack", fmt_float(gp["R_stack_manual"], 12)],
                      ["T01", fmt_float(front["T01"], 12)],
                      ["T10", fmt_float(front["T10"], 12)],
                      ["P", fmt_float(front["P"], 12)],
                      ["R_total_general", fmt_float(total["R_total_general_formula"], 12)],
                      ["R_total_simplified", fmt_float(total["R_total_simplified_formula"], 12)],
                      ["R_TMM_GlassPVK_Fixed_csv", fmt_float(total["R_TMM_GlassPVK_Fixed_csv"], 12)],
                      ["abs_diff", f"{total['abs_diff']:.3e}"],
                      ["result", chip(total["pass"])],
                  ],
              )}
            </div>
          </div>
        </div>
      </section>

      <section data-qa-watch="slide-9">
        <h1 class="slide-title">Reference Theory Audit</h1>
        <p class="slide-subtitle">同一口径继续审计 <span class="en">glass/Ag</span> 与 <span class="en">Ag mirror</span> 理论参比链，确认不是某一个 reference 独自“失真”。</p>
        <div class="stack-col">
          <div class="card table-card">
            {slide_f_table}
          </div>
          <div class="callout-row">
            <div class="callout-card">理论计算链路在当前模型假设下自洽。</div>
            <div class="callout-card">实验-理论差异更可能来自 <span class="en">nk</span> 适用性、显微收光/散射、参比有效响应或 <span class="en">specular-only</span> 假设边界。</div>
          </div>
          <div class="card soft">
            <h2 class="card-title">Ag mirror caveat</h2>
            <p class="body-text">{mirror["caveat"]}</p>
          </div>
        </div>
      </section>

      <section data-qa-watch="slide-10">
        <h1 class="slide-title">TMM Calculation Flow</h1>
        <p class="slide-subtitle">上半页讲计算流程，下半页说明单点 trace 的数值到底从哪条曲线、哪张材料表取来。</p>
        <div class="flow-slide-grid">
          <div class="step-flow">
            <div class="step-box blue"><div class="step-index">01</div><div class="step-name">nk table</div><div class="step-note">读取对齐后的 Glass、PVK、Ag 光学常数表，并锁定同一波长采样。</div></div>
            <div class="step-box cyan"><div class="step-index">02</div><div class="step-name">complex n(λ)+ik(λ)</div><div class="step-note">把每种材料写成复折射率，显式保留吸收项，而不是只看 n。</div></div>
            <div class="step-box purple"><div class="step-index">03</div><div class="step-name">coherent stack</div><div class="step-note">在 Glass/PVK/Air 后侧薄膜栈中计算相位延迟与振幅叠加。</div></div>
            <div class="step-box gold"><div class="step-index">04</div><div class="step-name">front-surface Fresnel</div><div class="step-note">单独求 Air/Glass 前表面 Fresnel 反射，保持与薄膜干涉层分离。</div></div>
            <div class="step-box green"><div class="step-index">05</div><div class="step-name">incoherent cascade</div><div class="step-note">把 1 mm 玻璃当作非相干隔离层，用强度级联组合前后两部分。</div></div>
            <div class="step-box blue"><div class="step-index">06</div><div class="step-name">R_TMM(λ)</div><div class="step-note">输出可与实验反射率逐点对比的理论曲线。</div></div>
          </div>
          <div class="source-grid">
            <div class="card source-card">
              <h2 class="card-title">取值来源：反射率曲线</h2>
              <img src="assets/value_locator_reflectance.svg" alt="reflectance locator" />
              <div class="source-caption">虚线固定在 <span class="en">{lambda_used:.3f} nm</span>，对应单点 trace 中使用的最近数据点。</div>
            </div>
            <div class="card source-card">
              <h2 class="card-title">取值来源：n,k 材料表</h2>
              <img src="assets/value_locator_nk.svg" alt="nk locator" />
              <div class="source-caption">同一根虚线在材料表上也落到相同波长，保证代入的 <span class="en">PVK n,k</span> 与反射率 trace 来自同一数据口径。</div>
            </div>
          </div>
        </div>
      </section>

      <section data-qa-watch="slide-11">
        <h1 class="slide-title">Risk Source Map</h1>
        <p class="slide-subtitle">公式链已经过审计，但这不等于实验-理论差异已经被定位到单一原因。</p>
        <div class="quad-grid">
          <div class="card risk-box" style="background:#fef2f2"><h3>实验链路</h3><div class="risk-note">低证据 / 低可控性</div><ul><li>背景扣除与 ROI 语义</li><li>glass/Ag 与 Ag mirror 切换一致性</li><li>现场标准片与重复性 QC</li></ul></div>
          <div class="card risk-box" style="background:#fffaeb"><h3>n,k 适用性</h3><div class="risk-note">低证据 / 高可控性</div><ul><li>PVK 文献常数是否代表当前样品</li><li>Ag 常数与实际镜面状态的偏离</li><li>需要 envelope 而不是单点信任</li></ul></div>
          <div class="card risk-box" style="background:#eff8ff"><h3>模型边界</h3><div class="risk-note">高证据 / 低可控性</div><ul><li>specular-only 假设</li><li>厚玻璃非相干近似</li><li>显微场景是否可直接等价于理想平面波</li></ul></div>
          <div class="card risk-box" style="background:#ecfdf3"><h3>显微收光</h3><div class="risk-note">高证据 / 高可控性</div><ul><li>NA 与空间平均</li><li>散射与非镜面贡献</li><li>objective / alignment 对实测值的放大效应</li></ul></div>
        </div>
        <div class="risk-summary"><strong>当前优先事项：</strong>先做 <span class="en">n,k audit + envelope</span>，并补 <span class="en">glass only / standard wafer / field QC</span>，不要把“公式自洽”误判为“物理链路已闭环”。</div>
      </section>

      <section data-qa-watch="slide-12">
        <h1 class="slide-title">Key Curves and QA Boundary</h1>
        <p class="slide-subtitle">保留现有全谱结果图，同时说明 technical report 承担更高信息密度的查阅角色。</p>
        <div class="deck-grid-2">
          <div class="stack-col">
            <div class="card"><img class="hero-image" src="{rel(REFLECTANCE_PNG)}" alt="reflectance compare" /></div>
            <div class="card"><img class="hero-image hero-image-small" src="{rel(QC_PNG)}" alt="Ag BK QC" /></div>
          </div>
          <div class="stack-col">
            <div class="card"><img class="hero-image" src="{rel(RESIDUAL_PNG)}" alt="residual compare" /></div>
            <div class="card soft">
              <h2 class="card-title">Technical report 负责“查”</h2>
              <ul class="bullet-list compact-list">
                <li>保留 convention、完整公式、差值表与 caveat。</li>
                <li>消费同一份理论审计 JSON 与 markdown，不手填数字。</li>
                <li>与 deck 明确分工：deck 讲主结论，report 查证据。</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
  <script src="../../../node_modules/reveal.js/dist/reveal.js"></script>
  <script src="../../../node_modules/katex/dist/katex.min.js"></script>
  <script src="../../../node_modules/katex/dist/contrib/auto-render.min.js"></script>
  <script src="../../../node_modules/mermaid/dist/mermaid.min.js"></script>
  <script src="assets/qa-watchdog.js"></script>
  <script src="assets/deck.js"></script>
</body>
</html>
"""

    tech = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Phase 08 Technical Report</title>
  <link rel="stylesheet" href="../../../node_modules/katex/dist/katex.min.css" />
  <link rel="stylesheet" href="assets/theme.css" />
  <style>
    body {{ padding: 40px; background: #f3f5f9; }}
    main {{ max-width: 1280px; margin: 0 auto; background: #fff; border-radius: 20px; padding: 40px; box-shadow: 0 18px 48px rgba(16,24,40,.12); }}
    section {{ margin-bottom: 34px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #d0d5dd; padding: 10px 12px; text-align: left; font-size: 15px; vertical-align: top; }}
    th {{ background: #f8fafc; }}
    img {{ width: 100%; border: 1px solid #d0d5dd; border-radius: 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    .codeblock {{ white-space: pre-wrap; font: 14px/1.5 Menlo, monospace; color:#344054; background:#f8fafc; border:1px solid #d0d5dd; border-radius:12px; padding:16px; }}
    .tag {{ display:inline-block; padding:4px 10px; border-radius:999px; font:600 12px/1.2 Inter, Arial, sans-serif; color:#fff; background:#047857; }}
  </style>
</head>
<body>
  <main>
    <h1 class="slide-title">Phase 08 Technical Report</h1>
    <p class="slide-subtitle">这份 technical report 负责查证据；HTML slide deck 负责讲主问题。两者共用同一套 Phase 08 审计数据事实。</p>

    <section>
      <h2 class="card-title">输入路径</h2>
      <table>
        <tr><th>项</th><th>路径</th></tr>
        <tr><td>trace values</td><td><code>{project_rel(TRACE_VALUES_JSON)}</code></td></tr>
        <tr><td>theory audit json</td><td><code>{project_rel(AUDIT_JSON)}</code></td></tr>
        <tr><td>trace markdown</td><td><code>{project_rel(TRACE_MD)}</code></td></tr>
        <tr><td>theory audit markdown</td><td><code>{project_rel(AUDIT_MD)}</code></td></tr>
        <tr><td>manifest</td><td><code>{project_rel(MANIFEST_JSON)}</code></td></tr>
        <tr><td>reflectance figure</td><td><code>{project_rel(REFLECTANCE_PNG)}</code></td></tr>
        <tr><td>residual figure</td><td><code>{project_rel(RESIDUAL_PNG)}</code></td></tr>
      </table>
    </section>

    <section>
      <h2 class="card-title">TMM theoretical reflectance manual audit</h2>
      <p class="body-text">采用 Steven Byrnes / python <span class="en">tmm</span> convention：<span class="en">exp(-iωt)</span>、前进方向 <span class="en">+z</span>、法向入射下展示 <span class="en">s polarization</span>。当前入射半无限介质非吸收，因此可写 <span class="en">R = |r|²</span>。</p>
      <table>
        <tr><th>quantity</th><th>value</th></tr>
        <tr><td>lambda_used_nm</td><td>{lambda_used:.12f}</td></tr>
        <tr><td>N_glass</td><td>{fmt_complex(audit["N_glass"], 12)}</td></tr>
        <tr><td>N_pvk</td><td>{fmt_complex(audit["N_pvk"], 12)}</td></tr>
        <tr><td>N_ag</td><td>{fmt_complex(audit["N_ag"], 12)}</td></tr>
        <tr><td>d_pvk_nm</td><td>{audit["d_pvk_nm"]:.12f}</td></tr>
        <tr><td>d_ag_nm</td><td>{audit["d_ag_nm"]:.12f}</td></tr>
      </table>
    </section>

    <section>
      <h2 class="card-title">Glass / PVK / Air coherent formula</h2>
      <div class="codeblock">r01 = (N0 - N1) / (N0 + N1)
r12 = (N1 - N2) / (N1 + N2)
delta = 2π N1 d1 / lambda
r_stack = (r01 + r12 * exp(2i * delta)) / (1 + r01 * r12 * exp(2i * delta))
R_stack = |r_stack|²</div>
      <table>
        <tr><th>quantity</th><th>value</th></tr>
        <tr><td>r01</td><td>{fmt_complex(gp["r01"], 12)}</td></tr>
        <tr><td>r12</td><td>{fmt_complex(gp["r12"], 12)}</td></tr>
        <tr><td>delta</td><td>{fmt_complex(gp["delta"], 12)}</td></tr>
        <tr><td>exp(2i delta)</td><td>{fmt_complex(gp["exp_2i_delta"], 12)}</td></tr>
        <tr><td>r_stack_manual</td><td>{fmt_complex(gp["r_stack_manual"], 12)}</td></tr>
        <tr><td>R_stack_manual</td><td>{gp["R_stack_manual"]:.12f}</td></tr>
        <tr><td>R_stack_tmm</td><td>{gp["R_stack_tmm"]:.12f}</td></tr>
        <tr><td>abs_diff</td><td>{gp["abs_diff"]:.3e} <span class="tag">{"PASS" if gp["pass"] else "FAIL"}</span></td></tr>
      </table>
    </section>

    <section>
      <h2 class="card-title">Incoherent cascade audit</h2>
      <div class="codeblock">R_total = R01 + (T01 * T10 * P² * R_stack) / (1 - R10 * P² * R_stack)

Current simplification:
R_total = R_front + ((1 - R_front)² * R_stack) / (1 - R_front * R_stack)</div>
      <table>
        <tr><th>quantity</th><th>value</th></tr>
        <tr><td>R_front</td><td>{front["R_front"]:.12f}</td></tr>
        <tr><td>T01</td><td>{front["T01"]:.12f}</td></tr>
        <tr><td>T10</td><td>{front["T10"]:.12f}</td></tr>
        <tr><td>P</td><td>{front["P"]:.12f}</td></tr>
        <tr><td>R_total_general_formula</td><td>{total["R_total_general_formula"]:.12f}</td></tr>
        <tr><td>R_total_simplified_formula</td><td>{total["R_total_simplified_formula"]:.12f}</td></tr>
        <tr><td>R_TMM_GlassPVK_Fixed_csv</td><td>{total["R_TMM_GlassPVK_Fixed_csv"]:.12f}</td></tr>
        <tr><td>abs_diff</td><td>{total["abs_diff"]:.3e} <span class="tag">{"PASS" if total["pass"] else "FAIL"}</span></td></tr>
      </table>
    </section>

    <section>
      <h2 class="card-title">glass/Ag and Ag mirror audit</h2>
      {slide_f_table}
      <p class="body-text">Ag mirror caveat: {mirror["caveat"]}</p>
    </section>

    <section>
      <h2 class="card-title">Value source locator</h2>
      <div class="grid">
        <img src="assets/value_locator_reflectance.svg" alt="reflectance locator" />
        <img src="assets/value_locator_nk.svg" alt="nk locator" />
      </div>
    </section>

    <section>
      <h2 class="card-title">Key figures</h2>
      <div class="grid">
        <img src="{rel(REFLECTANCE_PNG)}" alt="reflectance compare" />
        <img src="{rel(RESIDUAL_PNG)}" alt="residual compare" />
      </div>
    </section>

    <section>
      <h2 class="card-title">Audit boundary</h2>
      <ul class="bullet-list compact-list">
        <li>本审计证明当前手写公式、<span class="en">tmm.coh_tmm()</span> 与现有 CSV 在当前模型假设下自洽。</li>
        <li>本审计不证明 <span class="en">nk</span> 数据一定代表真实样品，也不证明显微实验一定等价于理想 <span class="en">specular reflectance</span>。</li>
        <li><span class="en">exp(-2i delta)</span> 结果只作为 convention sanity check，不进入主物理逻辑。</li>
      </ul>
    </section>

    <section>
      <h2 class="card-title">Appendix excerpts</h2>
      <div class="grid">
        <div class="codeblock">{trace_md[:2200]}</div>
        <div class="codeblock">{audit_md[:2200]}</div>
      </div>
    </section>
  </main>
  <script src="../../../node_modules/katex/dist/katex.min.js"></script>
  <script src="../../../node_modules/katex/dist/contrib/auto-render.min.js"></script>
  <script>
    renderMathInElement(document.body, {{
      delimiters: [
        {{left: "$$", right: "$$", display: true}},
        {{left: "$", right: "$", display: false}}
      ]
    }});
  </script>
</body>
</html>
"""

    DECK_HTML.write_text(deck, encoding="utf-8")
    TECH_HTML.write_text(tech, encoding="utf-8")
    print(project_rel(DECK_HTML))
    print(project_rel(TECH_HTML))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
