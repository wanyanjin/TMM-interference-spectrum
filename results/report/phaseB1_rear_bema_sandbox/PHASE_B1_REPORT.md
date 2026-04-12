# Phase B-1 Report

## 1. 阶段目标

- `Phase A-2` 已建立 `d_PVK` 的厚度指纹，因此本阶段把 rear-only BEMA 作为独立机制单独拆出。
- 目标是回答：`PVK/C60` 后界面 50/50 solid-solid intermixing 是否表现出不同于 thickness 的独立光谱指纹。

## 2. 模型定义

- rear-only stack: `Glass / ITO / NiOx / SAM / PVK_bulk / BEMA(PVK,C60) / C60_bulk / Ag / Air`
- Bruggeman EMA: 固定 `50% PVK + 50% C60`，不扫描体积分数。
- 厚度守恒规则：
  - `d_PVK,bulk = 700 - 0.5 * d_BEMA,rear`
  - `d_C60,bulk = max(0, 15 - 0.5 * d_BEMA,rear)`
- 本阶段不引入前界面粗糙、不引入 air gap、不做实验拟合。

## 3. 输入数据来源

- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseA2/phaseA2_pvk_feature_summary.csv`
- `src/core/full_stack_microcavity.py`
- `src/scripts/stepB1_rear_bema_sandbox.py`

## 4. 关键结果

- rear-only BEMA 最敏感的窗口仍然是后窗 `810–1100 nm`。
- 它的主效应更像 `fringe 振幅/对比度衰减 + 包络畸变`，只伴随次级相位漂移。
- 与 `d_PVK` 相比，rear-only BEMA 更不像全局腔长变化，而更像局部后界面混合导致的后窗形貌扭曲。
- `R_stack` 的机制灵敏度仍略高于 `R_total`，说明固定前表面背景会轻微钝化观测强度。

## 5. 物理结论

- rear-only BEMA 可以作为一类独立于 thickness 的后界面粗糙指纹保留。
- 它与 `d_PVK` 不是完全正交，但在 Delta R 形态上具有足够明确的可区分趋势。
- 因此 rear-only BEMA 值得进入下一步更系统的缺陷机制字典构建。

## 6. 风险与限制

- 当前只做了 solid-solid rear BEMA，没有涉及 void 或 air gap。
- 还没有做 front-side proxy BEMA，因此当前只回答“后界面粗糙”的独立指纹。
- 大 `d_BEMA,rear` 区间会同时导致 `C60_bulk` 明显变薄，因此 `20-30 nm` 更像极限测试区间。
- 仍未把 `PVK surrogate v2` 的 band-edge 不确定性传播到本轮结果。

## 7. 下一步建议

- 更建议下一步先进入 `Phase A-2.1: PVK uncertainty ensemble`。
- 理由是：rear-BEMA 与 d_PVK 已经显示出可区分趋势，但这些趋势仍建立在当前 surrogate 上；先量化 surrogate 不确定性，再进入 `Phase B-2: front-only BEMA`，有利于避免把材料尾部不确定性误读为界面机制差异。
