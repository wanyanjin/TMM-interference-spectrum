# Phase B-2 Front-only BEMA Sandbox

## Inputs

- nominal optical stack: `resources/aligned_full_stack_nk_pvk_v2.csv`
- thickness scan: `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- rear-BEMA scan: `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- A-2.1 feature matrix: `data/processed/phaseA2_1/phaseA2_1_feature_robustness_matrix.csv`

## Model Definition

- front-only stack: `Glass / ITO / NiOx / SAM / BEMA_front(NiOx,PVK) / PVK_bulk / C60 / Ag / Air`
- Bruggeman EMA: `50% NiOx + 50% PVK`, fixed `f = 0.50`
- thickness conservation:
  - `d_PVK,bulk = 700 - d_BEMA,front`
  - `d_SAM = 5 nm` fixed
  - `d_NiOx = 45 nm` fixed
  - `d_C60 = 15 nm` fixed

## Scan Range

- d_BEMA,front range: `0-30 nm`
- step: `1 nm`

## Q1. Front-only BEMA 的主敏感窗口在哪里？

- front-window max |Delta R_total|: `2.99%`
- transition-window max |Delta R_total|: `19.26%`
- rear-window max |Delta R_total|: `18.69%`
- dominant window: `transition`
- 结论：front-only BEMA 的主响应更偏 `前窗 + 过渡区`，明显不同于 rear-only BEMA 的后窗主导口径。

## Q2. front-only BEMA 的主要作用更像什么？

- front-window mean shift max: `1.16%`
- transition-window max |Delta R_total|: `19.26%`
- rear-window max |Delta R_total|: `18.69%`
- rear peak shift over full scan: `16.00 nm`
- rear contrast change over full scan: `0.28%`
- 结论：front-only BEMA 更像 `前窗平均背景变化 + 过渡区包络/斜率扭曲`，后窗相位漂移不是主效应。

## Q3. front-only BEMA 与 d_PVK 的可区分性如何？

- max |Delta R_total| under d_PVK scan: `30.37%`
- d_PVK 仍然主要表现为全局微腔光程变化和后窗 fringe 系统平移。
- front-only BEMA 则更局域于 `400-810 nm` 的前窗/过渡区，构成不同于 thickness 的机制指纹。

## Q4. front-only BEMA 与 rear-only BEMA 的差异是什么？

- max |Delta R_total| under rear-only BEMA scan: `0.83%`
- rear-only BEMA 更偏后窗局部包络/振幅微扰。
- front-only BEMA 更偏前窗与过渡区的背景/斜率调制。
- 结论：当前已经形成 thickness / rear-BEMA / front-BEMA 三方可对照的 proxy 字典。

## Q5. R_stack 与 R_total 的差异

- R_stack more sensitive than R_total in front/transition windows: `True`
- 前表面背景会轻微钝化 front-BEMA 的实验可见度，尤其在前窗平均反射背景上。
- 因此 `R_stack` 仍是机制分析首选，`R_total` 用于承接实验观测口径。

## Uncertainty Spot-check

- max relative spread of transition-window amplitude across ensemble: `0.341`
- robust front-BEMA features: `front-window mean DeltaR under front-BEMA`
- surrogate-sensitive front-BEMA features: `transition-window DeltaR amplitude under front-BEMA; rear-window DeltaR amplitude under front-BEMA; absolute R_total at 780 nm under front-BEMA`
- 结论：front-BEMA 的机制类别仍可独立保留，但 band-edge 邻域的绝对反射率量仍需谨慎解释。

## Outputs

- scan csv: `data/processed/phaseB2/phaseB2_front_bema_scan.csv`
- feature csv: `data/processed/phaseB2/phaseB2_front_bema_feature_summary.csv`
- spotcheck csv: `data/processed/phaseB2/phaseB2_front_bema_ensemble_spotcheck.csv`
- robustness csv: `data/processed/phaseB2/phaseB2_front_bema_robustness_summary.csv`
- comparison png: `results/figures/phaseB2/phaseB2_front_vs_rear_vs_thickness_comparison.png`

## Recommendation

- 基于当前三机制框架，更建议下一步进入 `Phase C-1 air-gap only`。
- 理由是：front / rear roughness proxy 与 thickness 已经具备基本正交字典，现在适合补齐另一类几何缺陷机制，再讨论 dual-BEMA 或耦合机制。
