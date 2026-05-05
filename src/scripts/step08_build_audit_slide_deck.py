"""Build Phase 08 reflectance calibration and TMM audit HTML slide deck."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import json
import math
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIGURE_DIR = PROJECT_ROOT / "results" / "figures" / "phase08" / "reference_comparison_deck"
SLIDE_DIR = PROJECT_ROOT / "results" / "slides" / "phase08_reference_audit"

CALIBRATED_CSV = PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison" / "phase08_0429_dual_reference_calibrated_reflectance_pvk_x01.csv"
THEORY_CSV = PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison" / "phase08_0429_dual_reference_tmm_theory_curves_pvk_x01.csv"
MANIFEST_JSON = PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison" / "phase08_0429_dual_reference_manifest_pvk_x01.json"
DUAL_REPORT_MD = PROJECT_ROOT / "results" / "report" / "phase08_reference_comparison" / "phase08_0429_dual_reference_report_pvk_x01.md"
TRACE_MD = PROJECT_ROOT / "results" / "report" / "phase08_reference_comparison_trace" / "phase08_0429_trace_600nm.md"

EXISTING_REFLECTANCE_PNG = PROJECT_ROOT / "results" / "figures" / "phase08" / "reference_comparison" / "phase08_0429_dual_reference_reflectance_exp_vs_tmm_pvk_x01.png"
EXISTING_RESIDUAL_PNG = PROJECT_ROOT / "results" / "figures" / "phase08" / "reference_comparison" / "phase08_0429_residual_pvk_x01.png"
EXISTING_AG_BK_QC_PNG = PROJECT_ROOT / "results" / "figures" / "phase08" / "reference_comparison" / "phase08_0429_ag_bk_qc_pvk_x01.png"

DECK_HTML = SLIDE_DIR / "phase08_reference_audit_deck.html"
TECH_REPORT_HTML = SLIDE_DIR / "phase08_reference_audit_technical_report.html"

TARGET_WAVELENGTH_NM = 600.0
TOL = 1e-9


@dataclass(frozen=True)
class TraceStatus:
    item: str
    status: str
    note: str


@dataclass(frozen=True)
class AuditContext:
    calibrated: pd.DataFrame
    theory: pd.DataFrame
    manifest: dict
    report_md: str
    trace_md: str
    row_600: pd.Series
    theory_row_600: pd.Series
    lambda_used_nm: float
    trace_statuses: list[TraceStatus]
    trace_summary_values: dict[str, float]


def relpath(target: Path, start: Path) -> str:
    return os.path.relpath(target, start).replace(os.sep, "/")


def html_relpath(target: Path) -> str:
    return relpath(target, SLIDE_DIR)


def load_context() -> AuditContext:
    calibrated = pd.read_csv(CALIBRATED_CSV)
    theory = pd.read_csv(THEORY_CSV)
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    report_md = DUAL_REPORT_MD.read_text(encoding="utf-8")
    trace_md = TRACE_MD.read_text(encoding="utf-8")

    idx = int((calibrated["Wavelength_nm"] - TARGET_WAVELENGTH_NM).abs().argmin())
    row_600 = calibrated.iloc[idx]
    theory_row_600 = theory.iloc[idx]
    lambda_used_nm = float(row_600["Wavelength_nm"])

    statuses = parse_trace_statuses(trace_md)
    summary_values = parse_trace_summary_values(trace_md)
    ctx = AuditContext(
        calibrated=calibrated,
        theory=theory,
        manifest=manifest,
        report_md=report_md,
        trace_md=trace_md,
        row_600=row_600,
        theory_row_600=theory_row_600,
        lambda_used_nm=lambda_used_nm,
        trace_statuses=statuses,
        trace_summary_values=summary_values,
    )
    assert_consistency(ctx)
    return ctx


def parse_trace_statuses(text: str) -> list[TraceStatus]:
    statuses: list[TraceStatus] = []
    in_table = False
    for line in text.splitlines():
        if line.strip() == "## 0.1 审计状态表":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if in_table and line.startswith("|") and "---" not in line:
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) == 3 and parts[0] != "检查项":
                statuses.append(TraceStatus(parts[0], parts[1], parts[2]))
    return statuses


def parse_trace_summary_values(text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    patterns = {
        "R_Exp_GlassPVK_by_GlassAg": r"glass/Ag = ([0-9.]+)",
        "R_Exp_GlassPVK_by_AgMirror": r"Ag mirror = ([0-9.]+)",
        "R_TMM_GlassPVK_Fixed": r"R_TMM_GlassPVK_Fixed = ([0-9.]+)",
        "lambda_used_nm": r"最近数据点 `([0-9.]+) nm`",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if not match:
            raise ValueError(f"无法从 trace 报告中提取 {key}")
        values[key] = float(match.group(1))
    return values


def assert_consistency(ctx: AuditContext) -> None:
    row = ctx.row_600
    checks = {
        "R_Exp_GlassPVK_by_GlassAg": float(row["R_Exp_GlassPVK_by_GlassAg"]),
        "R_Exp_GlassPVK_by_AgMirror": float(row["R_Exp_GlassPVK_by_AgMirror"]),
        "R_TMM_GlassPVK_Fixed": float(row["R_TMM_GlassPVK_Fixed"]),
        "lambda_used_nm": ctx.lambda_used_nm,
    }
    for key, value in checks.items():
        if abs(value - ctx.trace_summary_values[key]) > TOL:
            raise ValueError(f"trace 与 CSV/JSON 不一致: {key}: {value} vs {ctx.trace_summary_values[key]}")
    if abs(float(row["R_TMM_GlassPVK_Fixed"]) - float(ctx.theory_row_600["R_TMM_GlassPVK_Fixed"])) > TOL:
        raise ValueError("calibrated/theory 在 600 nm 的 R_TMM_GlassPVK_Fixed 不一致")


def ensure_dirs() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    SLIDE_DIR.mkdir(parents=True, exist_ok=True)


def write_svg(path: Path, width: int, height: int, content: str) -> None:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
        f'<rect width="{width}" height="{height}" fill="white"/>'
        f"{content}</svg>"
    )
    path.write_text(svg, encoding="utf-8")


def svg_text(x: float, y: float, text: str, size: int = 24, weight: str = "400", anchor: str = "start", fill: str = "#111827") -> str:
    lines = escape(text).split("\n")
    parts = []
    for i, line in enumerate(lines):
        dy = i * (size + 6)
        parts.append(
            f'<text x="{x}" y="{y + dy}" font-family="Arial, DejaVu Sans, Helvetica, sans-serif" '
            f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{line}</text>'
        )
    return "".join(parts)


def render_formula_card(path: Path, latex: str, label: str) -> None:
    fig = plt.figure(figsize=(7.2, 2.0), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_facecolor("white")
    ax.text(0.03, 0.82, label, fontsize=13, fontweight="bold", ha="left", va="center")
    ax.text(0.03, 0.35, f"${latex}$", fontsize=20, ha="left", va="center")
    fig.savefig(path, format="svg", facecolor="white")
    plt.close(fig)


def make_stack_svg(path: Path, title: str, labels: list[str], fills: list[str]) -> None:
    width, height = 1200, 800
    content = [svg_text(70, 80, title, size=34, weight="700")]
    x = 160
    y = 260
    layer_w = 200
    h = 260
    for i, (label, fill) in enumerate(zip(labels, fills)):
        content.append(
            f'<rect x="{x + i * layer_w}" y="{y}" width="{layer_w}" height="{h}" fill="{fill}" stroke="#334155" stroke-width="3" rx="8"/>'
        )
        content.append(svg_text(x + i * layer_w + layer_w / 2, y + h / 2, label, size=28, weight="700", anchor="middle"))
    write_svg(path, width, height, "".join(content))


def make_flow_svg(path: Path, title: str, boxes: list[str]) -> None:
    width, height = 1200, 800
    content = [svg_text(70, 80, title, size=34, weight="700")]
    box_w, box_h = 230, 120
    y = 320
    gap = 50
    start_x = 70
    palette = ["#dbeafe", "#e0f2fe", "#ede9fe", "#fef3c7", "#dcfce7"]
    for i, label in enumerate(boxes):
        x = start_x + i * (box_w + gap)
        fill = palette[i % len(palette)]
        content.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="18" fill="{fill}" stroke="#334155" stroke-width="3"/>')
        content.append(svg_text(x + box_w / 2, y + 52, label, size=23, weight="700", anchor="middle"))
        if i < len(boxes) - 1:
            x1 = x + box_w
            x2 = x + box_w + gap - 10
            content.append(f'<line x1="{x1}" y1="{y + box_h/2}" x2="{x2}" y2="{y + box_h/2}" stroke="#334155" stroke-width="5"/>')
            content.append(f'<polygon points="{x2},{y + box_h/2} {x2-18},{y + box_h/2 - 10} {x2-18},{y + box_h/2 + 10}" fill="#334155"/>')
    write_svg(path, width, height, "".join(content))


def make_microscope_geometry_svg(path: Path) -> None:
    width, height = 1200, 800
    content = [svg_text(70, 80, "显微反射测量几何", size=34, weight="700")]
    content.append(f'<rect x="180" y="210" width="840" height="330" fill="#f8fafc" stroke="#64748b" stroke-width="4" rx="16"/>')
    content.append(f'<rect x="260" y="320" width="680" height="60" fill="#cbd5e1" stroke="#334155" stroke-width="3"/>')
    content.append(svg_text(600, 357, "Glass substrate", size=26, weight="700", anchor="middle"))
    content.append(f'<rect x="260" y="290" width="680" height="28" fill="#fde68a" stroke="#334155" stroke-width="2"/>')
    content.append(svg_text(600, 311, "PVK film", size=24, weight="700", anchor="middle"))
    content.append(f'<rect x="450" y="570" width="300" height="90" rx="16" fill="#dbeafe" stroke="#1d4ed8" stroke-width="3"/>')
    content.append(svg_text(600, 612, "4X Objective\nNA = 0.1", size=24, weight="700", anchor="middle"))
    content.append(f'<line x1="600" y1="570" x2="600" y2="380" stroke="#2563eb" stroke-width="6"/>')
    content.append(f'<polygon points="600,380 586,404 614,404" fill="#2563eb"/>')
    content.append(svg_text(640, 465, "glass-side incidence", size=24, weight="700", fill="#1d4ed8"))
    content.append(svg_text(240, 170, "IX73 / IX3-RFAL / inverted microscope", size=24, weight="700"))
    write_svg(path, width, height, "".join(content))


def make_incoherent_cascade_svg(path: Path) -> None:
    width, height = 1200, 800
    content = [svg_text(70, 80, "厚玻璃非相干级联", size=34, weight="700")]
    content.append(f'<rect x="110" y="260" width="280" height="180" rx="16" fill="#dbeafe" stroke="#334155" stroke-width="3"/>')
    content.append(svg_text(250, 335, "Front interface\nAir / Glass\nR_front", size=28, weight="700", anchor="middle"))
    content.append(f'<rect x="470" y="260" width="310" height="180" rx="16" fill="#fef3c7" stroke="#334155" stroke-width="3"/>')
    content.append(svg_text(625, 335, "Rear coherent stack\nGlass / PVK / Air\nR_stack", size=28, weight="700", anchor="middle"))
    content.append(f'<rect x="860" y="260" width="240" height="180" rx="16" fill="#dcfce7" stroke="#334155" stroke-width="3"/>')
    content.append(svg_text(980, 335, "R_total", size=32, weight="700", anchor="middle"))
    content.append(f'<line x1="390" y1="350" x2="460" y2="350" stroke="#334155" stroke-width="5"/>')
    content.append(f'<polygon points="460,350 442,338 442,362" fill="#334155"/>')
    content.append(f'<line x1="780" y1="350" x2="850" y2="350" stroke="#334155" stroke-width="5"/>')
    content.append(f'<polygon points="850,350 832,338 832,362" fill="#334155"/>')
    content.append(svg_text(120, 560, "R_total = R_front + (1-R_front)^2 R_stack / (1-R_front R_stack)", size=24, weight="700"))
    write_svg(path, width, height, "".join(content))


def make_trace_cards_svg(path: Path, ctx: AuditContext) -> None:
    row = ctx.row_600
    man = ctx.manifest
    values = [
        ("λ used (nm)", f"{ctx.lambda_used_nm:.6f}"),
        ("PVK counts/ms", f"{row['Glass_PVK_CountsPerMs']:.3f}"),
        ("glass/Ag counts/ms", f"{row['Glass_Ag_CountsPerMs']:.3f}"),
        ("Ag mirror counts/ms", f"{row['Ag_Mirror_Corrected_CountsPerMs']:.3f}"),
        ("ratio by glass/Ag", f"{row['Glass_PVK_CountsPerMs']/row['Glass_Ag_CountsPerMs']:.6f}"),
        ("ratio by Ag mirror", f"{row['Glass_PVK_CountsPerMs']/row['Ag_Mirror_Corrected_CountsPerMs']:.6f}"),
        ("R_exp by glass/Ag", f"{row['R_Exp_GlassPVK_by_GlassAg']:.6f}"),
        ("R_exp by Ag mirror", f"{row['R_Exp_GlassPVK_by_AgMirror']:.6f}"),
        ("R_TMM fixed", f"{row['R_TMM_GlassPVK_Fixed']:.6f}"),
        ("Ag frames used", "2–100 (99 frames)"),
        ("Ag frame dropped", "1"),
        ("BK frames", "1–100 mean"),
    ]
    width, height = 1200, 800
    content = [svg_text(70, 70, "600 nm 单点 trace 数值卡片", size=34, weight="700")]
    card_w, card_h = 250, 120
    cols = 4
    for i, (label, value) in enumerate(values):
        row_i, col_i = divmod(i, cols)
        x = 70 + col_i * 280
        y = 140 + row_i * 160
        content.append(f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="16" fill="#f8fafc" stroke="#334155" stroke-width="3"/>')
        content.append(svg_text(x + 125, y + 42, label, size=22, weight="700", anchor="middle"))
        content.append(svg_text(x + 125, y + 86, value, size=26, weight="700", anchor="middle", fill="#1d4ed8"))
    content.append(svg_text(70, 720, f"best_d_PVK = {man['best_d_PVK_nm']:.0f} nm; 反射率单位统一为 0–1", size=24, weight="700"))
    write_svg(path, width, height, "".join(content))


def make_risk_map_svg(path: Path) -> None:
    width, height = 1200, 800
    content = [svg_text(70, 70, "风险来源地图", size=34, weight="700")]
    content.append(f'<line x1="600" y1="160" x2="600" y2="700" stroke="#334155" stroke-width="4"/>')
    content.append(f'<line x1="140" y1="430" x2="1060" y2="430" stroke="#334155" stroke-width="4"/>')
    boxes = [
        (220, 240, "实验链路", "背景、ROI、参比切换、现场 QC", "#fee2e2"),
        (720, 240, "n,k", "PVK / Ag 适用性与 envelope", "#fef3c7"),
        (220, 520, "模型边界", "specular-only / incoherent 假设", "#e0f2fe"),
        (720, 520, "显微收光", "NA、散射、空间平均", "#dcfce7"),
    ]
    for x, y, title, body, fill in boxes:
        content.append(f'<rect x="{x}" y="{y}" width="260" height="120" rx="18" fill="{fill}" stroke="#334155" stroke-width="3"/>')
        content.append(svg_text(x + 130, y + 38, title, size=26, weight="700", anchor="middle"))
        content.append(svg_text(x + 130, y + 78, body, size=20, weight="400", anchor="middle"))
    content.append(svg_text(90, 420, "较低可控性", size=20, weight="700"))
    content.append(svg_text(980, 420, "较高可控性", size=20, weight="700"))
    content.append(svg_text(610, 130, "较低证据", size=20, weight="700", anchor="middle"))
    content.append(svg_text(610, 740, "较高证据", size=20, weight="700", anchor="middle"))
    write_svg(path, width, height, "".join(content))


def make_qc_flow_svg(path: Path) -> None:
    make_flow_svg(
        path,
        "下一步闭环路线",
        ["nk_audit", "nk_envelope", "glass only", "标准片", "现场 QC"],
    )


def extract_metric(report_md: str, label: str) -> str | None:
    match = re.search(rf"{re.escape(label)}\s*=\s*([^\n]+)", report_md)
    return match.group(1).strip() if match else None


def slide(title: str, body: str, index: int) -> str:
    return f'<section class="slide" data-index="{index}"><div class="slide-inner"><h1>{escape(title)}</h1>{body}</div></section>'


def img_tag(path: Path, alt: str, cls: str = "hero-image") -> str:
    return f'<img class="{cls}" src="{html_relpath(path)}" alt="{escape(alt)}"/>'


def build_deck_html(ctx: AuditContext, assets: dict[str, Path]) -> str:
    row = ctx.row_600
    man = ctx.manifest
    residual_gag = float(row["R_Exp_GlassPVK_by_GlassAg"] - row["R_TMM_GlassPVK_Fixed"])
    residual_ag = float(row["R_Exp_GlassPVK_by_AgMirror"] - row["R_TMM_GlassPVK_Fixed"])
    status_pass = [s for s in ctx.trace_statuses if s.status == "PASS"]
    status_warning = [s for s in ctx.trace_statuses if s.status == "WARNING"]
    slides = []
    slides.append(slide("Phase 08 反射率校准与 TMM 审计", f"""
        <div class="two-col">
          <div>
            <p class="lead">目标：解释显微反射率如何从原始光谱与参比得到，并说明为何当前实验反射率高于 TMM 理论值。</p>
            <ul>
              <li>数据集：0429</li>
              <li>当前 audited 结果集：<code>pvk_x01</code></li>
              <li>单点审计波长：<code>{ctx.lambda_used_nm:.6f} nm</code></li>
            </ul>
          </div>
          <div>{img_tag(assets["microscope_geometry"], "显微几何", "side-image")}</div>
        </div>
    """, 1))
    slides.append(slide("研究问题：显微反射谱能否得到可 TMM 建模的反射率？", """
        <div class="content-block">
          <p class="lead">核心矛盾：在 600 nm 附近，实验反射率约为理论值的 2 倍。</p>
          <ul>
            <li>实验链：<code>glass/PVK → counts/ms → ratio × R_ref → R_exp</code></li>
            <li>理论链：<code>n,k + layer stack + incoherent glass cascade → R_TMM</code></li>
            <li>本轮不是重新拟合，而是把这两条链完整讲清楚。</li>
          </ul>
        </div>
    """, 2))
    slides.append(slide("实验光路和样品几何", f"""
        <div class="content-block">{img_tag(assets["microscope_geometry"], "显微几何")}</div>
        <ul>
          <li>平台：IX73 / IX3-RFAL / 4X objective / NA 0.1</li>
          <li>倒置显微镜，从玻璃侧入射并收光</li>
          <li>当前建模对象：<code>Air / Glass / PVK / Air</code></li>
        </ul>
    """, 3))
    slides.append(slide("原始光谱和参比对象", f"""
        <div class="two-col">
          <div>{img_tag(EXISTING_AG_BK_QC_PNG, "Ag/BK QC")}</div>
          <div>
            <div class="mini-stack-grid">
              {img_tag(assets["stack_glass_pvk_air"], "sample stack", "mini-stack")}
              {img_tag(assets["stack_glass_ag"], "glass ag stack", "mini-stack")}
              {img_tag(assets["stack_air_ag_air"], "ag mirror stack", "mini-stack")}
            </div>
            <ul>
              <li><code>glass/PVK</code>：样品光谱</li>
              <li><code>glass/Ag</code>：同光路参比</li>
              <li><code>Ag mirror + bk</code>：直接银镜参比；第 1 帧过曝，后 99 帧可用</li>
            </ul>
          </div>
        </div>
    """, 4))
    slides.append(slide("实验反射率校准公式", f"""
        <div class="two-col">
          <div>{img_tag(assets["formula_reflectance_calibration"], "reflectance formula", "formula-image")}</div>
          <div>{img_tag(assets["reflectance_calibration_flow"], "calibration flow", "formula-image")}</div>
        </div>
        <ul>
          <li>先把 sample / reference 都转成 counts/ms</li>
          <li>再做比值，最后乘以参比反射率</li>
          <li>反射率单位统一为 <code>0–1</code></li>
        </ul>
    """, 5))
    slides.append(slide("glass/Ag 和 Ag mirror 两条参比链", f"""
        <div class="two-col">
          <div>
            {img_tag(assets["stack_glass_ag"], "glass ag", "side-image")}
            <p class="note"><code>R_ref = R_TMM_GlassAg</code></p>
          </div>
          <div>
            {img_tag(assets["stack_air_ag_air"], "ag mirror", "side-image")}
            <p class="note"><code>R_ref = R_TMM_AgMirror</code></p>
          </div>
        </div>
        <ul>
          <li>两条参比链共享同一份样品 counts</li>
          <li>参比结构和理论反射率不同，不能混用</li>
        </ul>
    """, 6))
    slides.append(slide("TMM 输入：nk 与层结构", f"""
        <div class="two-col">
          <div>
            <ul>
              <li>nk 来源：<code>{escape(Path(man['nk_csv']).name)}</code></li>
              <li>wavelength used range：<code>{man['wavelength_min_nm_used']:.3f}–{man['wavelength_max_nm_used']:.3f} nm</code></li>
              <li>PVK fixed thickness：<code>{man['d_pvk_fixed_nm_assumption']:.0f} nm</code></li>
              <li>best d：<code>{man['best_d_PVK_nm']:.0f} nm</code></li>
            </ul>
          </div>
          <div>
            {img_tag(assets["stack_glass_pvk_air"], "stack", "mini-stack")}
            {img_tag(assets["tmm_flow"], "tmm flow", "mini-stack")}
          </div>
        </div>
        <p class="note"><code>n + ik</code> 决定 Fresnel 系数、相位项和吸收强度。</p>
    """, 7))
    slides.append(slide("TMM 后侧相干栈：Glass / PVK / Air", f"""
        <div class="two-col">
          <div>{img_tag(assets["formula_coherent_stack"], "coherent formula", "formula-image")}</div>
          <div>{img_tag(assets["stack_glass_pvk_air"], "glass pvk air", "formula-image")}</div>
        </div>
        <ul>
          <li>后侧薄膜栈是相干问题，不能把界面反射率直接相加</li>
          <li>相位项 <code>δ</code> 控制条纹位置和干涉强弱</li>
        </ul>
    """, 8))
    slides.append(slide("厚玻璃非相干级联", f"""
        <div class="two-col">
          <div>{img_tag(assets["formula_incoherent_cascade"], "incoherent formula", "formula-image")}</div>
          <div>{img_tag(assets["incoherent_cascade"], "incoherent cascade", "formula-image")}</div>
        </div>
        <p class="note">前表面 <code>Air/Glass</code> 与后侧相干栈之间采用非相干级联，当前审计已证明该公式与 CSV 一致。</p>
    """, 9))
    slides.append(slide("600 nm 单点 trace：从 counts 到 R_exp", f"""
        <div class="two-col">
          <div>{img_tag(assets["trace_cards"], "trace cards", "hero-image")}</div>
          <div class="number-panel">
            <div class="big-number">R_exp by glass/Ag<br><span>{row['R_Exp_GlassPVK_by_GlassAg']:.6f}</span></div>
            <div class="big-number">R_exp by Ag mirror<br><span>{row['R_Exp_GlassPVK_by_AgMirror']:.6f}</span></div>
          </div>
        </div>
    """, 10))
    slides.append(slide("600 nm 单点 trace：从 Fresnel / TMM 到 R_TMM", f"""
        <div class="two-col">
          <div>{img_tag(assets["trace_cards"], "trace cards", "hero-image")}</div>
          <div class="number-panel">
            <div class="big-number">R_TMM GlassPVK fixed<br><span>{row['R_TMM_GlassPVK_Fixed']:.6f}</span></div>
            <div class="big-number">R_TMM GlassAg<br><span>{row['R_TMM_GlassAg']:.6f}</span></div>
            <div class="big-number">R_TMM AgMirror<br><span>{row['R_TMM_AgMirror']:.6f}</span></div>
          </div>
        </div>
    """, 11))
    slides.append(slide("实验 vs TMM 曲线对比", f"""
        <div class="content-block">{img_tag(EXISTING_REFLECTANCE_PNG, "reflectance compare")}</div>
        <p class="note">主图只看 500–750 nm；实验两条链与 TMM fixed / bestD 颜色和线型保持一致。</p>
    """, 12))
    slides.append(slide("残差与核心矛盾", f"""
        <div class="two-col">
          <div>{img_tag(EXISTING_RESIDUAL_PNG, "residual")}</div>
          <div>
            <ul>
              <li>600 nm residual by glass/Ag: <code>{residual_gag:.6f}</code></li>
              <li>600 nm residual by Ag mirror: <code>{residual_ag:.6f}</code></li>
              <li>best d from manifest: <code>{man['best_d_PVK_nm']:.0f} nm</code></li>
            </ul>
            <p class="lead">核心矛盾不是公式不自洽，而是实验反射率显著高于理论值。</p>
          </div>
        </div>
    """, 13))
    slides.append(slide("审计结论：证明了什么，没有证明什么", f"""
        <div class="two-col">
          <div>
            <h2>已证明</h2>
            <ul>{''.join(f'<li>{escape(s.item)}</li>' for s in status_pass)}</ul>
          </div>
          <div>
            <h2>未证明 / 需警惕</h2>
            <ul>{''.join(f'<li>{escape(s.note)}</li>' for s in status_warning)}</ul>
          </div>
        </div>
    """, 14))
    slides.append(slide("风险来源地图", f"""
        <div class="content-block">{img_tag(assets["risk_map"], "risk map")}</div>
    """, 15))
    slides.append(slide("下一步：闭环路线", f"""
        <div class="content-block">{img_tag(assets["next_qc_flow"], "next step flow")}</div>
        <ul>
          <li><code>nk_audit</code>：逐项审查 PVK / Ag 光学常数来源与适用性</li>
          <li><code>nk_envelope</code>：构建可解释的 nk 不确定范围</li>
          <li><code>glass only</code> + 标准片 + 现场 QC：补实验闭环</li>
        </ul>
    """, 16))

    toc = "".join(f'<button class="toc-btn" data-target="{i}">{i}</button>' for i in range(1, 17))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Phase 08 反射率校准与 TMM 审计</title>
  <style>
    :root {{
      --bg: #ffffff; --fg: #0f172a; --muted: #475569; --accent: #2563eb; --accent2: #d97706;
      --border: #cbd5e1; --panel: #f8fafc;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, "DejaVu Sans", Helvetica, sans-serif; background: #e5e7eb; color: var(--fg); }}
    .deck {{ width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; }}
    .slide {{ width: 1440px; height: 960px; background: var(--bg); display: none; border-radius: 18px; box-shadow: 0 18px 60px rgba(15,23,42,.18); overflow: hidden; position: relative; }}
    .slide.active {{ display: block; }}
    .slide-inner {{ padding: 56px 70px 90px 70px; height: 100%; }}
    h1 {{ font-size: 40px; margin: 0 0 18px 0; }}
    h2 {{ font-size: 28px; margin: 0 0 12px 0; }}
    p, li {{ font-size: 24px; line-height: 1.45; color: var(--fg); }}
    .lead {{ font-size: 28px; font-weight: 700; color: var(--fg); }}
    .note {{ color: var(--muted); font-size: 20px; }}
    code {{ background: #eff6ff; padding: 2px 6px; border-radius: 6px; font-size: .92em; }}
    ul {{ margin-top: 14px; }}
    .two-col {{ display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 28px; align-items: start; }}
    .hero-image, .side-image, .formula-image, .content-block img {{ width: 100%; max-height: 720px; object-fit: contain; border: 1px solid var(--border); border-radius: 14px; background: white; }}
    .content-block {{ width: 100%; }}
    .mini-stack-grid {{ display: grid; grid-template-columns: 1fr; gap: 14px; margin-bottom: 16px; }}
    .mini-stack {{ width: 100%; max-height: 170px; object-fit: contain; border: 1px solid var(--border); border-radius: 12px; }}
    .number-panel {{ display: grid; gap: 18px; }}
    .big-number {{ background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 20px; font-size: 24px; font-weight: 700; }}
    .big-number span {{ display: block; margin-top: 8px; font-size: 36px; color: var(--accent); }}
    .toolbar {{ position: fixed; left: 50%; transform: translateX(-50%); bottom: 18px; background: rgba(15,23,42,.92); color: white; padding: 10px 16px; border-radius: 999px; display: flex; gap: 12px; align-items: center; z-index: 30; }}
    .toolbar button, .toc-btn {{ border: none; background: #1e293b; color: white; border-radius: 999px; cursor: pointer; }}
    .toolbar button {{ padding: 8px 14px; font-size: 16px; }}
    .pager {{ min-width: 78px; text-align: center; font-weight: 700; }}
    .toc {{ position: fixed; top: 18px; right: 18px; width: 260px; background: rgba(255,255,255,.96); border: 1px solid var(--border); border-radius: 16px; padding: 16px; z-index: 25; }}
    .toc h3 {{ margin: 0 0 12px 0; font-size: 18px; }}
    .toc-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }}
    .toc-btn {{ padding: 8px 0; font-size: 14px; }}
  </style>
</head>
<body>
  <div class="toc"><h3>Slides</h3><div class="toc-grid">{toc}</div></div>
  <div class="deck">{''.join(slides)}</div>
  <div class="toolbar">
    <button id="prevBtn">← Prev</button>
    <div class="pager"><span id="pageNow">1</span> / <span id="pageTotal">16</span></div>
    <button id="nextBtn">Next →</button>
  </div>
  <script>
    const slides = Array.from(document.querySelectorAll('.slide'));
    const total = slides.length;
    const pageNow = document.getElementById('pageNow');
    const pageTotal = document.getElementById('pageTotal');
    pageTotal.textContent = total;
    let current = 0;
    function show(index) {{
      current = Math.max(0, Math.min(total - 1, index));
      slides.forEach((s, i) => s.classList.toggle('active', i === current));
      pageNow.textContent = String(current + 1);
    }}
    document.getElementById('prevBtn').onclick = () => show(current - 1);
    document.getElementById('nextBtn').onclick = () => show(current + 1);
    document.querySelectorAll('.toc-btn').forEach(btn => btn.onclick = () => show(Number(btn.dataset.target) - 1));
    document.addEventListener('keydown', (e) => {{
      if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') show(current + 1);
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') show(current - 1);
    }});
    show(0);
  </script>
</body>
</html>"""


def build_technical_report_html(ctx: AuditContext, assets: dict[str, Path]) -> str:
    row = ctx.row_600
    man = ctx.manifest
    statuses = "".join(
        f"<tr><td>{escape(s.item)}</td><td>{escape(s.status)}</td><td>{escape(s.note)}</td></tr>"
        for s in ctx.trace_statuses
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Phase 08 Technical Report</title>
  <style>
    body {{ font-family: Arial, "DejaVu Sans", Helvetica, sans-serif; margin: 0; background: white; color: #0f172a; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 40px 48px 80px; }}
    h1 {{ font-size: 38px; margin-bottom: 8px; }}
    h2 {{ font-size: 28px; margin-top: 38px; }}
    p, li, td, th {{ font-size: 18px; line-height: 1.5; }}
    img {{ max-width: 100%; border: 1px solid #cbd5e1; border-radius: 12px; background: white; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 22px; align-items: start; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; }}
    th {{ background: #f8fafc; }}
    code {{ background: #eff6ff; padding: 2px 6px; border-radius: 6px; }}
    .note {{ color: #475569; }}
  </style>
</head>
<body>
<main>
  <h1>Phase 08 反射率校准与 TMM 审计 Technical Report</h1>
  <p class="note">当前主审计对象：<code>pvk_x01</code>。本页补充 slide deck，用于组会前阅读，不替代主 deck。</p>

  <h2>1. 输入与版本</h2>
  <table>
    <tr><th>项</th><th>值</th></tr>
    <tr><td>calibrated csv</td><td><code>{escape(CALIBRATED_CSV.relative_to(PROJECT_ROOT).as_posix())}</code></td></tr>
    <tr><td>theory csv</td><td><code>{escape(THEORY_CSV.relative_to(PROJECT_ROOT).as_posix())}</code></td></tr>
    <tr><td>manifest</td><td><code>{escape(MANIFEST_JSON.relative_to(PROJECT_ROOT).as_posix())}</code></td></tr>
    <tr><td>trace report</td><td><code>{escape(TRACE_MD.relative_to(PROJECT_ROOT).as_posix())}</code></td></tr>
    <tr><td>nk source</td><td><code>{escape(Path(man['nk_csv']).relative_to(PROJECT_ROOT).as_posix())}</code></td></tr>
  </table>

  <h2>2. 600 nm 单点关键值</h2>
  <table>
    <tr><th>quantity</th><th>value</th></tr>
    <tr><td>lambda_used_nm</td><td>{ctx.lambda_used_nm:.12f}</td></tr>
    <tr><td>R_Exp_GlassPVK_by_GlassAg</td><td>{row['R_Exp_GlassPVK_by_GlassAg']:.12f}</td></tr>
    <tr><td>R_Exp_GlassPVK_by_AgMirror</td><td>{row['R_Exp_GlassPVK_by_AgMirror']:.12f}</td></tr>
    <tr><td>R_TMM_GlassPVK_Fixed</td><td>{row['R_TMM_GlassPVK_Fixed']:.12f}</td></tr>
    <tr><td>R_TMM_GlassAg</td><td>{row['R_TMM_GlassAg']:.12f}</td></tr>
    <tr><td>R_TMM_AgMirror</td><td>{row['R_TMM_AgMirror']:.12f}</td></tr>
    <tr><td>counts_ratio_glassAg</td><td>{row['Glass_PVK_CountsPerMs']/row['Glass_Ag_CountsPerMs']:.12f}</td></tr>
    <tr><td>counts_ratio_AgMirror</td><td>{row['Glass_PVK_CountsPerMs']/row['Ag_Mirror_Corrected_CountsPerMs']:.12f}</td></tr>
    <tr><td>best_d_PVK_nm</td><td>{man['best_d_PVK_nm']:.0f}</td></tr>
  </table>

  <h2>3. 审计状态</h2>
  <table>
    <tr><th>检查项</th><th>状态</th><th>说明</th></tr>
    {statuses}
  </table>

  <h2>4. 主要图示</h2>
  <div class="grid">
    <div><img src="{html_relpath(EXISTING_REFLECTANCE_PNG)}" alt="reflectance compare"/></div>
    <div><img src="{html_relpath(EXISTING_RESIDUAL_PNG)}" alt="residual"/></div>
    <div><img src="{html_relpath(EXISTING_AG_BK_QC_PNG)}" alt="ag bk qc"/></div>
    <div><img src="{html_relpath(assets['trace_cards'])}" alt="trace cards"/></div>
  </div>

  <h2>5. 解释</h2>
  <ul>
    <li>本轮 deck 不重算反射率或 TMM，只读取现有 <code>pvk_x01</code> 结果集。</li>
    <li>600 nm 单点 trace 已证明：公式实现、单层相干解析式、厚玻璃非相干级联与当前 CSV 输出自洽。</li>
    <li>当前实验反射率仍显著高于理论值，说明剩余矛盾更可能落在实验链路、nk 适用性、显微收光和 specular-only 假设边界。</li>
  </ul>
</main>
</body>
</html>"""


def generate_assets(ctx: AuditContext) -> dict[str, Path]:
    assets = {
        "formula_reflectance_calibration": FIGURE_DIR / "formula_reflectance_calibration.svg",
        "formula_coherent_stack": FIGURE_DIR / "formula_coherent_stack.svg",
        "formula_incoherent_cascade": FIGURE_DIR / "formula_incoherent_cascade.svg",
        "microscope_geometry": FIGURE_DIR / "microscope_geometry.svg",
        "stack_glass_pvk_air": FIGURE_DIR / "stack_glass_pvk_air.svg",
        "stack_glass_ag": FIGURE_DIR / "stack_glass_ag.svg",
        "stack_air_ag_air": FIGURE_DIR / "stack_air_ag_air.svg",
        "reflectance_calibration_flow": FIGURE_DIR / "reflectance_calibration_flow.svg",
        "tmm_flow": FIGURE_DIR / "tmm_flow.svg",
        "incoherent_cascade": FIGURE_DIR / "incoherent_cascade.svg",
        "trace_cards": FIGURE_DIR / "trace_600nm_cards.svg",
        "risk_map": FIGURE_DIR / "risk_map.svg",
        "next_qc_flow": FIGURE_DIR / "next_step_qc_flow.svg",
    }
    render_formula_card(assets["formula_reflectance_calibration"], r"R_{\mathrm{exp}}=\frac{I_{\mathrm{sample}}/t_{\mathrm{sample}}}{I_{\mathrm{ref}}/t_{\mathrm{ref}}}\times R_{\mathrm{ref}}", "Reflectance calibration")
    render_formula_card(assets["formula_coherent_stack"], r"r_{\mathrm{total}}=\frac{r_{01}+r_{12}\exp(2i\delta)}{1+r_{01}r_{12}\exp(2i\delta)}", "Coherent stack")
    render_formula_card(assets["formula_incoherent_cascade"], r"R_{\mathrm{total}}=R_{\mathrm{front}}+\frac{(1-R_{\mathrm{front}})^2R_{\mathrm{stack}}}{1-R_{\mathrm{front}}R_{\mathrm{stack}}}", "Incoherent cascade")
    make_microscope_geometry_svg(assets["microscope_geometry"])
    make_stack_svg(assets["stack_glass_pvk_air"], "Sample stack: Air / Glass / PVK / Air", ["Air", "Glass", "PVK", "Air"], ["#e2e8f0", "#cbd5e1", "#fde68a", "#e2e8f0"])
    make_stack_svg(assets["stack_glass_ag"], "Reference stack: Air / Glass / Ag / Air", ["Air", "Glass", "Ag", "Air"], ["#e2e8f0", "#cbd5e1", "#d1d5db", "#e2e8f0"])
    make_stack_svg(assets["stack_air_ag_air"], "Reference stack: Air / Ag / Air", ["Air", "Ag", "Air"], ["#e2e8f0", "#d1d5db", "#e2e8f0"])
    make_flow_svg(assets["reflectance_calibration_flow"], "反射率校准流程", ["counts", "counts/ms", "ratio", "× R_ref", "R_exp"])
    make_flow_svg(assets["tmm_flow"], "TMM 计算流程", ["nk", "Fresnel", "coherent stack", "incoherent cascade", "R_TMM"])
    make_incoherent_cascade_svg(assets["incoherent_cascade"])
    make_trace_cards_svg(assets["trace_cards"], ctx)
    make_risk_map_svg(assets["risk_map"])
    make_qc_flow_svg(assets["next_qc_flow"])
    return assets


def validate_html_outputs() -> None:
    for path in [DECK_HTML, TECH_REPORT_HTML]:
        text = path.read_text(encoding="utf-8")
        if "/Users/luxin/" in text:
            raise ValueError(f"{path.name} 包含绝对路径")
        if "http://" in text or "https://" in text:
            raise ValueError(f"{path.name} 包含外部依赖")


def main() -> int:
    ensure_dirs()
    ctx = load_context()
    assets = generate_assets(ctx)
    DECK_HTML.write_text(build_deck_html(ctx, assets), encoding="utf-8")
    TECH_REPORT_HTML.write_text(build_technical_report_html(ctx, assets), encoding="utf-8")
    validate_html_outputs()
    print(f"deck: {DECK_HTML.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"technical_report: {TECH_REPORT_HTML.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"lambda_used_nm: {ctx.lambda_used_nm:.12f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
