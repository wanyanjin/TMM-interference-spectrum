"""Build the Phase 08 HTML slide deck with local frontend assets."""

from __future__ import annotations

import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SLIDE_DIR = PROJECT_ROOT / "results" / "slides" / "phase08_reference_audit"
DECK_HTML = SLIDE_DIR / "phase08_reference_audit_deck.html"
TECH_HTML = SLIDE_DIR / "phase08_reference_audit_technical_report.html"

TRACE_VALUES_JSON = PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison_trace" / "phase08_0429_trace_600nm_values.json"
TRACE_MD = PROJECT_ROOT / "results" / "report" / "phase08_reference_comparison_trace" / "phase08_0429_trace_600nm.md"
MANIFEST_JSON = PROJECT_ROOT / "data" / "processed" / "phase08" / "reference_comparison" / "phase08_0429_dual_reference_manifest_pvk_x01.json"

REFLECTANCE_PNG = PROJECT_ROOT / "results" / "figures" / "phase08" / "reference_comparison" / "phase08_0429_dual_reference_reflectance_exp_vs_tmm_pvk_x01.png"
RESIDUAL_PNG = PROJECT_ROOT / "results" / "figures" / "phase08" / "reference_comparison" / "phase08_0429_residual_pvk_x01.png"
QC_PNG = PROJECT_ROOT / "results" / "figures" / "phase08" / "reference_comparison" / "phase08_0429_ag_bk_qc_pvk_x01.png"


def rel(path: Path) -> str:
    return os.path.relpath(path, SLIDE_DIR).replace(os.sep, "/")


def project_rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


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


def main() -> int:
    values = json.loads(TRACE_VALUES_JSON.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    trace_md = TRACE_MD.read_text(encoding="utf-8")

    c = values["counts"]
    fresnel = values["fresnel"]
    stack = values["coherent_stack"]["glass_pvk"]["fixed"]
    cascade = values["incoherent_cascade"]["glass_pvk_fixed"]
    row = values["experimental_reflectance"]
    ag_diag = values["ag_mirror_multiframe_trace"]

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
        <p class="slide-subtitle">本 deck 只重构展示层，继续读取现有 <span class="en">pvk_x01</span> 结果，不改主计算链。</p>
        <div class="deck-grid-2">
          <div class="card soft">
            <h2 class="card-title">本轮目标</h2>
            <ul class="bullet-list">
              <li>把反射率校准与 TMM 计算链讲清楚。</li>
              <li>把公式改成可投影的数学排版，而不是嵌入旧大图。</li>
              <li>加入本地视觉 QA，系统检查 overflow 与页面比例问题。</li>
            </ul>
          </div>
          <div class="card soft">
            <h2 class="card-title">当前边界</h2>
            <ul class="bullet-list">
              <li>数据集：0429</li>
              <li>结果集：<span class="en">pvk_x01</span></li>
              <li>单点审计波长：<span class="en">{values["lambda_used_nm"]:.6f} nm</span></li>
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
              <div class="formula-label">主公式</div>
              <div>$$R_{{\\mathrm{{total}}}} = R_{{\\mathrm{{front}}}} + \\frac{{(1-R_{{\\mathrm{{front}}}})^2 R_{{\\mathrm{{stack}}}}}}{{1-R_{{\\mathrm{{front}}}}R_{{\\mathrm{{stack}}}}}}$$</div>
            </div>
            <div class="card formula-card">
              <div class="formula-label">数字代入</div>
              <div>$$R_{{\\mathrm{{total}}}} = {fresnel["air_glass"]["R"]:.6f} + \\frac{{(1-{fresnel["air_glass"]["R"]:.6f})^2 \\times {stack["R_stack_by_formula"]:.6f}}}{{1-{fresnel["air_glass"]["R"]:.6f}\\times {stack["R_stack_by_formula"]:.6f}}}$$</div>
            </div>
            <div class="card formula-card">
              <div class="formula-label">结果</div>
              <div>$$R_{{\\mathrm{{TMM,GlassPVK,Fixed}}}} = {cascade["R_total"]:.6f}$$</div>
            </div>
          </div>
          <div class="stack-col">
            <div class="card diagram-card">
              <div class="mermaid">
flowchart LR
  A["Air / Glass front surface<br/>R_front = {fresnel["air_glass"]["R"]:.6f}"] --> B["1 mm glass<br/>treated as incoherent spacer"]
  B --> C["Glass / PVK / Air coherent stack<br/>R_stack = {stack["R_stack_by_formula"]:.6f}"]
  C --> D["Total reflectance<br/>R_total = {cascade["R_total"]:.6f}"]
              </div>
              <div class="diagram-caption">前表面只贡献 Fresnel 强度，后侧薄膜条纹在 <span class="en">R_stack</span> 中处理。</div>
            </div>
            <div class="card">
              <h2 class="card-title">术语解释</h2>
              <ul class="bullet-list">
                <li><span class="en">R_front</span>：<span class="en">Air/Glass</span> 前表面 Fresnel 反射率。</li>
                <li><span class="en">R_stack</span>：<span class="en">Glass/PVK/Air</span> 后侧薄膜栈的相干反射率。</li>
                <li>当前页解决的是“公式只有一行、解释不够”的问题。</li>
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
        <h1 class="slide-title">TMM Calculation Flow</h1>
        <p class="slide-subtitle">把原来偏小且右侧有截断风险的图改成横向大卡片，每步都说清楚输入与物理含义。</p>
        <div class="step-flow">
          <div class="step-box blue"><div class="step-index">01</div><div class="step-name">nk table</div><div class="step-note">读取对齐后的 Glass、PVK、Ag 光学常数表，并锁定同一波长采样。</div></div>
          <div class="step-box cyan"><div class="step-index">02</div><div class="step-name">complex n(λ)+ik(λ)</div><div class="step-note">把每种材料写成复折射率，显式保留吸收项，而不是只看 n。</div></div>
          <div class="step-box purple"><div class="step-index">03</div><div class="step-name">coherent stack</div><div class="step-note">在 Glass/PVK/Air 后侧薄膜栈中计算相位延迟与振幅叠加。</div></div>
          <div class="step-box gold"><div class="step-index">04</div><div class="step-name">front-surface Fresnel</div><div class="step-note">单独求 Air/Glass 前表面 Fresnel 反射，保持与薄膜干涉层分离。</div></div>
          <div class="step-box green"><div class="step-index">05</div><div class="step-name">incoherent cascade</div><div class="step-note">把 1 mm 玻璃当作非相干隔离层，用强度级联组合前后两部分。</div></div>
          <div class="step-box blue"><div class="step-index">06</div><div class="step-name">R_TMM(λ)</div><div class="step-note">输出可与实验反射率逐点对比的理论曲线。</div></div>
        </div>
      </section>

      <section data-qa-watch="slide-5">
        <h1 class="slide-title">Risk Source Map</h1>
        <p class="slide-subtitle">保留四象限逻辑，但统一块尺寸、字号和二级说明，补出当前优先事项。</p>
        <div class="quad-grid">
          <div class="card risk-box" style="background:#fef2f2"><h3>实验链路</h3><div class="risk-note">低证据 / 低可控性</div><ul><li>背景扣除与 ROI 语义</li><li>glass/Ag 与 Ag mirror 切换一致性</li><li>现场标准片与重复性 QC</li></ul></div>
          <div class="card risk-box" style="background:#fffaeb"><h3>n,k 适用性</h3><div class="risk-note">低证据 / 高可控性</div><ul><li>PVK 文献常数是否代表当前样品</li><li>Ag 常数与实际镜面状态的偏离</li><li>需要 envelope 而不是单点信任</li></ul></div>
          <div class="card risk-box" style="background:#eff8ff"><h3>模型边界</h3><div class="risk-note">高证据 / 低可控性</div><ul><li>specular-only 假设</li><li>厚玻璃非相干近似</li><li>显微场景是否可直接等价于理想平面波</li></ul></div>
          <div class="card risk-box" style="background:#ecfdf3"><h3>显微收光</h3><div class="risk-note">高证据 / 高可控性</div><ul><li>NA 与空间平均</li><li>散射与非镜面贡献</li><li>objective / alignment 对实测值的放大效应</li></ul></div>
        </div>
        <div class="risk-summary"><strong>当前优先事项：</strong>先做 <span class="en">n,k audit + envelope</span>，并补 <span class="en">glass only / standard wafer / field QC</span>，不要把“公式自洽”误判为“物理链路已闭环”。</div>
      </section>

      <section data-qa-watch="slide-6">
        <h1 class="slide-title">Key Curves</h1>
        <p class="slide-subtitle">这两页继续复用现有 Phase 08 图，不回写主结果，只提高讲解入口质量。</p>
        <div class="deck-grid-2">
          <div class="card"><img class="hero-image" src="{rel(REFLECTANCE_PNG)}" alt="reflectance compare" /></div>
          <div class="card"><img class="hero-image" src="{rel(RESIDUAL_PNG)}" alt="residual compare" /></div>
        </div>
      </section>

      <section data-qa-watch="slide-7">
        <h1 class="slide-title">Ag/BK QA Context</h1>
        <div class="deck-grid-2">
          <div class="card"><img class="hero-image" src="{rel(QC_PNG)}" alt="Ag BK QC" /></div>
          <div class="card soft">
            <h2 class="card-title">审计约束</h2>
            <ul class="bullet-list">
              <li>Ag 第 1 帧显式 dropped。</li>
              <li>Ag 使用 frame 2–100 求均值。</li>
              <li>BK 使用 frame 1–100 求均值。</li>
              <li>曝光时间仍来自文件名推断，需要在汇报中保留该边界。</li>
            </ul>
          </div>
        </div>
      </section>

      <section data-qa-watch="slide-8">
        <h1 class="slide-title">Technical Report Boundary</h1>
        <div class="deck-grid-2">
          <div class="card soft">
            <h2 class="card-title">Slide deck 负责“讲”</h2>
            <ul class="bullet-list">
              <li>一页一个主问题。</li>
              <li>优先显示公式链、数值链和风险优先级。</li>
              <li>压缩次要证据，不把页面塞成技术报告。</li>
            </ul>
          </div>
          <div class="card soft">
            <h2 class="card-title">Technical report 负责“查”</h2>
            <ul class="bullet-list">
              <li>保留输入路径、审计状态表和更多上下文。</li>
              <li>继续共用同一组 Phase 08 数据事实。</li>
              <li>不与 deck 混用同一种信息密度。</li>
            </ul>
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
  <link rel="stylesheet" href="assets/theme.css" />
  <style>
    body {{ padding: 40px; background: #f3f5f9; }}
    main {{ max-width: 1200px; margin: 0 auto; background: #fff; border-radius: 20px; padding: 40px; box-shadow: 0 18px 48px rgba(16,24,40,.12); }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #d0d5dd; padding: 10px 12px; text-align: left; font-size: 15px; }}
    th {{ background: #f8fafc; }}
    img {{ width: 100%; border: 1px solid #d0d5dd; border-radius: 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
  </style>
</head>
<body>
  <main>
    <h1 class="slide-title">Phase 08 Technical Report</h1>
    <p class="slide-subtitle">本页保留技术查阅密度；slide deck 负责讲解，不与 technical report 混排。</p>
    <h2 class="card-title">输入路径</h2>
    <table>
      <tr><th>项</th><th>路径</th></tr>
      <tr><td>trace values</td><td><code>{project_rel(TRACE_VALUES_JSON)}</code></td></tr>
      <tr><td>trace markdown</td><td><code>{project_rel(TRACE_MD)}</code></td></tr>
      <tr><td>manifest</td><td><code>{project_rel(MANIFEST_JSON)}</code></td></tr>
      <tr><td>reflectance figure</td><td><code>{project_rel(REFLECTANCE_PNG)}</code></td></tr>
      <tr><td>residual figure</td><td><code>{project_rel(RESIDUAL_PNG)}</code></td></tr>
    </table>
    <h2 class="card-title">600 nm 核心值</h2>
    <table>
      <tr><th>quantity</th><th>value</th></tr>
      <tr><td>lambda_used_nm</td><td>{values["lambda_used_nm"]:.12f}</td></tr>
      <tr><td>counts_ratio_glassAg</td><td>{row["counts_ratio_glassAg"]:.12f}</td></tr>
      <tr><td>counts_ratio_AgMirror</td><td>{row["counts_ratio_AgMirror"]:.12f}</td></tr>
      <tr><td>R_Exp_GlassPVK_by_GlassAg</td><td>{row["R_Exp_GlassPVK_by_GlassAg"]:.12f}</td></tr>
      <tr><td>R_Exp_GlassPVK_by_AgMirror</td><td>{row["R_Exp_GlassPVK_by_AgMirror"]:.12f}</td></tr>
      <tr><td>R_TMM_GlassPVK_Fixed</td><td>{row["R_TMM_GlassPVK_Fixed"]:.12f}</td></tr>
    </table>
    <h2 class="card-title">关键图</h2>
    <div class="grid">
      <img src="{rel(REFLECTANCE_PNG)}" alt="reflectance compare" />
      <img src="{rel(RESIDUAL_PNG)}" alt="residual compare" />
    </div>
    <h2 class="card-title">Trace 边界</h2>
    <pre style="white-space:pre-wrap; font: 14px/1.5 Menlo, monospace; color:#344054;">{trace_md[:2400]}</pre>
  </main>
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
