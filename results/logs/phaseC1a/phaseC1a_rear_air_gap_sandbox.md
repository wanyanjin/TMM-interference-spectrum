# Phase C-1a Rear Air-gap Sandbox

## Inputs

- nominal optical stack: `resources/aligned_full_stack_nk_pvk_v2.csv`
- thickness scan: `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- rear-BEMA scan: `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- front-BEMA scan: `data/processed/phaseB2/phaseB2_front_bema_scan.csv`

## Model Definition

- rear-gap stack: `Glass / ITO / NiOx / SAM / PVK / Air_gap_rear / C60 / Ag / Air`
- rear-gap 是真实空气层，不是 BEMA、不是 mixed layer。
- 本轮不做厚度守恒扣减：`d_PVK = 700 nm`、`d_C60 = 15 nm` 固定，`d_gap_rear` 作为新增分离光程直接插入。

## Scan Range

- scan mode: `A`
- rear-gap main scan: `0–20 nm, 0.5 nm step` plus `25, 30, 40, 50 nm`

## Q1. rear air-gap 的主敏感窗口在哪里？

- transition-window max |Delta R_total|: `9.41%`
- rear-window max |Delta R_total|: `12.83%`
- dominant window: `rear`
- 结论：rear-gap 的主敏感窗口落在 `650–1100 nm`，但最强响应通常先在 transition/rear 交界与后窗内部共同出现；它不像 front-BEMA 那样以前窗为主。

## Q2. rear air-gap 的主要作用更像什么？

- rear peak shift across scan: `28.00 nm`
- rear peak-valley spacing shift across scan: `2.00 nm`
- 结论：rear-gap 不是简单的弱包络微扰；它更像 `非均匀相位重构 + wavelength-dependent shift + 局部 branch-aware 重构` 的混合机制。

## Q3. rear air-gap 与 thickness 的可区分性如何？

- thickness 更接近全局腔长变化与后窗 fringe 系统平移。
- rear-gap 会引入更强的非均匀谱形重构，尤其在过渡区到后窗前缘更明显。
- 结论：rear-gap 与 thickness 具有可区分的第四类机制指纹。

## Q4. rear air-gap 与 rear-only BEMA 的差异是什么？

- rear-BEMA 是 `PVK/C60` intermixing，主效应是弱局部包络/振幅微扰。
- rear-gap 是 `PVK // Air // C60` separation，响应更强、更非线性，也更接近真实剥离的几何分离含义。
- 结论：rear-gap 与 rear-BEMA 不可混淆，前者更像真实界面分离机制。

## Q5. rear air-gap 与 front-only BEMA 的差异是什么？

- front-BEMA 更偏前窗/过渡区背景与斜率扭曲。
- rear-gap 更偏 transition/rear 的相位类与结构类重构。
- 当前已形成 thickness / rear-BEMA / front-BEMA / rear-gap 四方机制框架。

## Q6. 理论 LOD 粗评估

- 1 nm: total exceeds 0.2% = `True`, best window = `rear`
- 2 nm: total exceeds 0.2% = `True`, best window = `rear`
- 3 nm: total exceeds 0.2% = `True`, best window = `rear`
- 5 nm: total exceeds 0.2% = `True`, best window = `rear`
- 10 nm: total exceeds 0.2% = `True`, best window = `rear`
- 结论：rear-gap 的理论检出更适合看 `R_stack`，实验口径则看 `R_total` 的 transition/rear 响应是否稳定超过 `0.2%` 噪声底。

## Uncertainty Spot-check

- max relative spread of rear-window amplitude across ensemble: `0.186`
- robust rear-gap features: `none`
- surrogate-sensitive rear-gap features: `transition-window DeltaR amplitude under rear-gap; absolute R_total at 780 nm under rear-gap`
- 结论：rear-gap 仍可作为独立机制字典使用，但 band-edge 邻域绝对量仍需谨慎。

## Outputs

- scan csv: `data/processed/phaseC1a/phaseC1a_rear_air_gap_scan.csv`
- feature csv: `data/processed/phaseC1a/phaseC1a_rear_air_gap_feature_summary.csv`
- lod csv: `data/processed/phaseC1a/phaseC1a_rear_air_gap_lod_summary.csv`
- robustness csv: `data/processed/phaseC1a/phaseC1a_rear_air_gap_robustness_summary.csv`
- comparison png: `results/figures/phaseC1a/phaseC1a_gap_vs_thickness_vs_rearbema_vs_frontbema.png`

## Recommendation

- 更建议下一步进入 `Phase C-1b front air-gap only`。
- 理由是：rear-gap 已经证明属于与 thickness/BEMA 不同的独立几何机制，下一步最自然的是补齐前界面 gap，再决定是否进入 gap vs BEMA coupled comparison。
