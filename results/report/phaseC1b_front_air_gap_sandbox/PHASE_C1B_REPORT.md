# Phase C-1b Report

## 1. 为什么 C-1b 是当前自然下一步

- rear-gap 已经确认为独立于 thickness / BEMA 的第四类机制。
- 本阶段补齐 front-gap，建立前/后界面真实分离缺陷的成对对照。

## 2. 模型定义

- front-gap stack: `Glass / ITO / NiOx / SAM / Air_gap_front / PVK / C60 / Ag / Air`。
- 本轮不做厚度守恒扣减，因为 front-gap 被定义为新增几何分离层，而不是从 SAM/PVK 中挖出的过渡层。
- front-BEMA 是 transition-layer optical proxy；front-gap 是 real separation，两者是不同物理。

## 3. 输入数据来源

- nominal `PVK surrogate v2`。
- PVK ensemble 的 `nominal / more_absorptive / less_absorptive` 三成员。
- 已有 thickness / rear-BEMA / front-BEMA / rear-gap 结果。

## 4. 关键结果

- front-gap 最敏感的窗口位于前窗到过渡区，但会比 front-BEMA 更强地牵动后窗次级结构。
- 它既不同于 thickness 的全局腔长变化，也不同于 rear-gap 的后窗主导型相位重构。
- 因此 front-gap 可以作为第五类独立机制字典。

## 5. 理论 LOD 粗评估

- 在 `Delta R_noise ≈ 0.2%` 假设下，本轮已对 `1 / 2 / 3 / 5 / 10 nm` 给出 coarse detectability 评估。
- 最值得关注的是前窗平均背景变化与过渡区包络重构，而不是单看 band-edge 点值。

## 6. 不确定性 spot-check 结果

- 稳健特征：`front-window mean DeltaR_total under front-gap; rear-window DeltaR amplitude under front-gap`
- 敏感特征：`transition-window DeltaR amplitude under front-gap; absolute R_total at 780 nm under front-gap`
- front-gap 的机制类别仍稳健，但 band-edge 邻域绝对 `R_total` 仍需谨慎解释。

## 7. 物理结论

- front-gap 已形成第五类独立机制字典。
- 就当前 specular TMM 而言，它比 front-BEMA 更接近真正关心的前界面分离缺陷。

## 8. 风险与限制

- 当前仍是 specular TMM，不含散射。
- 只做了 front-gap，不含 dual-gap。
- 不含 gap+BEMA 联合机制。
- band-edge 邻域绝对 `R_total` 仍需谨慎解释。

## 9. 下一步建议

- 更建议下一步进入 `Phase C-2 gap vs BEMA coupled comparison`。
- 理由是：当前 separation 与 intermixing 的前/后界面字典已经齐备，下一步最自然的是比较两类机制的混淆边界与可分性。
