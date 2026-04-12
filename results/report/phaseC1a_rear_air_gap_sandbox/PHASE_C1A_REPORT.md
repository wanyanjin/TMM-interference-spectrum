# Phase C-1a Report

## 1. 为什么 C-1a 是当前重点

- thickness / rear-BEMA / front-BEMA 三类非空隙机制已经建立。
- 本阶段要补入真实界面分离机制，而 rear-gap 是与隐性剥离最直接相关的最小 specular 模型。

## 2. 模型定义

- rear-gap stack: `Glass / ITO / NiOx / SAM / PVK / Air_gap_rear / C60 / Ag / Air`。
- 本轮不做厚度守恒扣减，因为 air gap 被定义为新增几何分离层，而不是从 PVK/C60 中挖出的过渡层。
- rear-BEMA 是 intermixing；rear-gap 是 separation，两者是不同物理。

## 3. 输入数据来源

- nominal `PVK surrogate v2`。
- PVK ensemble 的 `nominal / more_absorptive / less_absorptive` 三成员。
- 已有 thickness / rear-BEMA / front-BEMA 字典结果。

## 4. 关键结果

- rear-gap 最敏感的窗口位于 transition 到 rear 的联合区段，而不是前窗。
- 它比 rear-BEMA 更强、更非线性，也比 thickness 更不像全局平移。
- 因此 rear-gap 可以作为与 thickness / rear-BEMA / front-BEMA 并列的第四类机制字典。

## 5. 理论 LOD 粗评估

- 在 `Delta R_noise ≈ 0.2%` 假设下，本轮已对 `1 / 2 / 3 / 5 / 10 nm` 给出粗评估。
- 最值得重点关注的是 low-gap 区域在 transition/rear 的响应，以及 `R_stack` 中更清晰的机制信号。

## 6. 不确定性 spot-check 结果

- 稳健特征：`none`
- 敏感特征：`transition-window DeltaR amplitude under rear-gap; absolute R_total at 780 nm under rear-gap`
- rear-gap 的机制类别仍稳健，但 band-edge 邻域绝对 `R_total` 仍需谨慎解释。

## 7. 物理结论

- rear-gap 已形成第四类独立机制字典。
- 就当前 specular TMM 而言，它比 rear-BEMA 更接近真正关心的界面剥离机制。

## 8. 风险与限制

- 当前仍是 specular TMM，不含散射。
- 只做了 rear-gap，不含 front-gap。
- 不含 dual-gap / gap+BEMA 联合机制。
- band-edge 邻域绝对 `R_total` 仍需谨慎解释。

## 9. 下一步建议

- 更建议下一步进入 `Phase C-1b front air-gap only`。
- 理由是：当前最需要补齐 front/rear 对照，再决定是否进入 coupled comparison。
