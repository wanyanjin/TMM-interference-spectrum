# Phase B-1 Rear-only BEMA Sandbox

## Inputs

- optical stack: `resources/aligned_full_stack_nk_pvk_v2.csv`
- pristine baseline: `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- Phase A-2 scan: `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- Phase A-2 feature summary: `data/processed/phaseA2/phaseA2_pvk_feature_summary.csv`

## Model Definition

- rear-only stack: `Glass / ITO / NiOx / SAM / PVK_bulk / BEMA(PVK,C60) / C60_bulk / Ag / Air`
- Bruggeman EMA: `50% PVK + 50% C60`, fixed `f = 0.50`
- thickness conservation:
  - `d_PVK,bulk = 700 - 0.5 * d_BEMA,rear`
  - `d_C60,bulk = max(0, 15 - 0.5 * d_BEMA,rear)`

## Scan Range

- d_BEMA,rear range: `0-30 nm`
- step: `1 nm`

## Q1. Rear-only BEMA 的主要作用更像什么？

- rear peak shift from 0 to 30 nm: `1.00 nm`
- rear peak-valley contrast change in R_total (30 nm vs pristine): `0.12%`
- rear peak-valley spacing change: `0.00 nm`
- 结论：rear-only BEMA 的主效应是 `局部包络重塑 + 轻微振幅变化`，相位漂移非常弱；它不像 d_PVK 那样以全局腔长变化为主导。
- amplitude-dominated verdict: `True`

## Q2. rear-only BEMA 的主敏感窗口在哪里？

- front-window max |Delta R_stack|: `0.03%`
- transition-window max |Delta R_stack|: `0.86%`
- rear-window max |Delta R_stack|: `0.85%`
- front-window max |Delta R_total|: `0.03%`
- transition-window max |Delta R_total|: `0.83%`
- rear-window max |Delta R_total|: `0.82%`
- most sensitive window: `transition/rear boundary`
- 结论：rear-only BEMA 的主响应集中在 `650-1100 nm` 的 transition/rear 区间，尤其是后窗前缘到后窗内部；它不像 d_PVK 那样表现为更纯粹的全局峰位平移。

## Q3. rear-only BEMA 与 d_PVK 的可区分性如何？

- Phase A-2 rear-window max |Delta R_total| level: `30.37%`
- d_PVK 的主指纹是后窗 fringe 的整体相位漂移和峰谷系统移动。
- rear-only BEMA 的主指纹是后窗 fringe 振幅衰减、对比度下降和局部包络重塑。
- 从 `phaseB1_bema_vs_pvk_deltaR_comparison.png` 可以看到，两者虽然都主要作用于后窗，但 Delta R 的形状并不等价，具有可区分的正交趋势。

## Q4. R_stack 与 R_total 的差异

- rear-window max |Delta R_stack| > max |Delta R_total|: `True`
- 前表面固定背景会轻微钝化 rear-BEMA 在总反射率中的观测灵敏度。
- 因此 `R_stack` 仍是更适合机制分析的理论对象，`R_total` 负责承接实验可见量。

## Q5. C60 守恒约束是否引入额外影响？

- minimum d_C60,bulk in scan: `0.00 nm`
- number of scan points with d_C60,bulk = 0: `1`
- 在 `0-30 nm` 扫描范围内，`d_C60,bulk` 由 `15 nm` 递减到 `0 nm`，这会让大 BEMA 厚度区间同时带入明显的 C60 变薄效应。
- 这不是本轮模型错误，而是厚度守恒本身的一部分；因此 `20-30 nm` 区间应理解为“强 rear intermixing + C60 severely thinned”的联合极限，而不是纯几何粗糙宽化。

## Outputs

- scan csv: `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- feature summary csv: `data/processed/phaseB1/phaseB1_rear_bema_feature_summary.csv`
- R_stack heatmap: `results/figures/phaseB1/phaseB1_R_stack_heatmap.png`
- R_total heatmap: `results/figures/phaseB1/phaseB1_R_total_heatmap.png`
- Delta R_stack heatmap: `results/figures/phaseB1/phaseB1_deltaR_stack_heatmap.png`
- Delta R_total heatmap: `results/figures/phaseB1/phaseB1_deltaR_total_heatmap.png`
- selected curves: `results/figures/phaseB1/phaseB1_selected_bema_curves.png`
- tracking: `results/figures/phaseB1/phaseB1_peak_valley_tracking.png`
- contrast trend: `results/figures/phaseB1/phaseB1_contrast_vs_bema.png`
- BEMA vs d_PVK comparison: `results/figures/phaseB1/phaseB1_bema_vs_pvk_deltaR_comparison.png`

## Recommendation

- rear-only BEMA 已经显示出与 d_PVK 不同的机制指纹，因此值得作为独立后界面粗糙机制继续保留。
- 下一步更建议先进入 `Phase A-2.1: PVK uncertainty ensemble`，先量化 band-edge surrogate 不确定性对 thickness 与 rear-BEMA 结论的传播，再做 `Phase B-2: front-only BEMA` 会更稳妥。
