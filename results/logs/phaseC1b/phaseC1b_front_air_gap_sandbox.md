# Phase C-1b Front Air-gap Sandbox

## Inputs

- nominal optical stack: `resources/aligned_full_stack_nk_pvk_v2.csv`
- thickness scan: `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- front-BEMA scan: `data/processed/phaseB2/phaseB2_front_bema_scan.csv`
- rear-gap scan: `data/processed/phaseC1a/phaseC1a_rear_air_gap_scan.csv`

## Model Definition

- front-gap stack: `Glass / ITO / NiOx / SAM / Air_gap_front / PVK / C60 / Ag / Air`
- front-gap 是真实空气层，不是 BEMA、不是 mixed layer。
- 本轮不做厚度守恒扣减：`d_SAM = 5 nm`、`d_PVK = 700 nm`、`d_C60 = 15 nm` 固定，`d_gap_front` 作为新增分离光程直接插入。

## Scan Range

- scan mode: `A`
- front-gap main scan: `0–20 nm, 0.5 nm step` plus `25, 30, 40, 50 nm`

## Q1. front air-gap 的主敏感窗口在哪里？

- front-window max |mean Delta R_total|: `5.06%`
- transition-window max |Delta R_total|: `14.09%`
- rear-window max |Delta R_total|: `17.23%`
- dominant window: `rear`
- 结论：front-gap 的主敏感窗口落在前窗到过渡区，但它会比 front-BEMA 更强地牵动后窗次级结构。

## Q2. front air-gap 的主要作用更像什么？

- rear peak shift across scan: `24.00 nm`
- rear peak-valley spacing shift across scan: `8.00 nm`
- 结论：front-gap 不是单纯背景变化，而是 `前窗背景变化 + 过渡区强扭曲 + 后窗次级 wavelength-dependent shift` 的混合机制。

## Q3. front air-gap 与 front-only BEMA 的可区分性如何？

- front-BEMA 更像平滑 transition-layer / intermixing proxy。
- front-gap 更强、更非线性，也更接近真实分离层；尤其在过渡区与 band-edge 邻域更容易出现强化重构。
- 结论：front-gap 与 front-BEMA 可区分，不应混为一类机制。

## Q4. front air-gap 与 rear-gap 的差异是什么？

- rear-gap 更偏 transition/rear 的相位类重构与后窗红移。
- front-gap 更偏 front/transition，但仍会牵动 rear-window 的次级结构。
- 结论：front-gap / rear-gap 已形成前后界面分离机制的成对字典。

## Q5. front air-gap 与 thickness 的差异是什么？

- thickness 仍然更接近全局腔长变化。
- front-gap 更局部、更偏前侧边界条件重构，不等价于简单的 `d_PVK` 相位平移。
- 结论：front-gap 与 thickness 足够正交。

## Q6. 理论 LOD 粗评估

- 1 nm: total exceeds 0.2% = `True`, best window = `front`
- 2 nm: total exceeds 0.2% = `True`, best window = `front`
- 3 nm: total exceeds 0.2% = `True`, best window = `front`
- 5 nm: total exceeds 0.2% = `True`, best window = `front`
- 10 nm: total exceeds 0.2% = `True`, best window = `front`
- 结论：front-gap 的理论检出更适合优先看 `R_stack`，实验上则看前窗平均背景与过渡区包络是否稳定超过 `0.2%`。

## Uncertainty Spot-check

- max relative spread of transition amplitude across ensemble: `0.708`
- robust front-gap features: `front-window mean DeltaR_total under front-gap; rear-window DeltaR amplitude under front-gap`
- surrogate-sensitive front-gap features: `transition-window DeltaR amplitude under front-gap; absolute R_total at 780 nm under front-gap`
- 结论：front-gap 仍可作为独立机制字典使用，但 band-edge 邻域绝对量仍需谨慎。

## Outputs

- scan csv: `data/processed/phaseC1b/phaseC1b_front_air_gap_scan.csv`
- feature csv: `data/processed/phaseC1b/phaseC1b_front_air_gap_feature_summary.csv`
- lod csv: `data/processed/phaseC1b/phaseC1b_front_air_gap_lod_summary.csv`
- robustness csv: `data/processed/phaseC1b/phaseC1b_front_air_gap_robustness_summary.csv`
- comparison png: `results/figures/phaseC1b/phaseC1b_frontgap_vs_frontbema_vs_reargap_vs_thickness.png`

## Recommendation

- 更建议下一步进入 `Phase C-2 gap vs BEMA coupled comparison`。
- 理由是：front-gap / rear-gap 与 front-BEMA / rear-BEMA 四条独立字典已基本齐备，下一步最自然的是比较 separation vs intermixing 的耦合/混淆边界。
