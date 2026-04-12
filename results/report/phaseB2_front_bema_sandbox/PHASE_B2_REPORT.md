# Phase B-2 Report

## 1. 阶段目标

- `thickness` 与 `rear-BEMA` 机制字典已经建立，因此本阶段补齐 front-side roughness proxy。
- 目标是确认 front-only BEMA 是否主要作用于前窗/过渡区，并与 thickness、rear-BEMA 保持可区分指纹。

## 2. 模型定义

- front-only stack: `Glass / ITO / NiOx / SAM / BEMA_front(NiOx,PVK) / PVK_bulk / C60 / Ag / Air`。
- 采用 `NiOx/PVK` proxy 的原因是：本轮关注的是前侧形貌在 PVK 底界面的等效光学投影，而不是把 `SAM` 厚度本身当作粗糙自由度。
- Bruggeman EMA 固定为 `50% NiOx + 50% PVK`。
- `SAM = 5 nm` 固定不变；守恒规则只作用在 PVK：`d_PVK,bulk = 700 - d_BEMA,front`。

## 3. 输入数据来源

- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_{nominal,more_absorptive,less_absorptive}.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- `data/processed/phaseA2_1/phaseA2_1_feature_robustness_matrix.csv`

## 4. 关键结果

- front-only BEMA 的主敏感窗口偏向前窗 `400–650 nm` 与过渡区 `650–810 nm`。
- 它更像前窗背景变化与过渡区包络/斜率扭曲，而不是后窗 fringe 的主相位机制。
- 因此它与 `d_PVK` 的全局腔长变化、以及 rear-only BEMA 的后窗局部包络微扰，均保持可区分性。

## 5. 不确定性 spot-check 结果

- 稳健结论：`front-window mean DeltaR under front-BEMA`
- 受 surrogate 影响较大的特征：`transition-window DeltaR amplitude under front-BEMA; rear-window DeltaR amplitude under front-BEMA; absolute R_total at 780 nm under front-BEMA`
- band-edge 邻域绝对 `R_total` 仍需谨慎解释，但 front-BEMA 的机制类别判断可以保留。

## 6. 物理结论

- front-only BEMA 可以作为独立于 thickness / rear-BEMA 的前界面 roughness proxy 使用。
- 当前已经形成 thickness / rear-BEMA / front-BEMA 三方对照框架，为后续引入 air-gap 提供更清晰的参照系。

## 7. 风险与限制

- 当前是 front-side optical proxy，不是完整化学界面模型。
- 还没有涉及 air gap / void，也没有 dual-BEMA。
- `band-edge` 邻域绝对 `R_total` 仍会受到 PVK surrogate 先验影响。

## 8. 下一步建议

- 更建议下一步进入 `Phase C-1 air-gap only`。
- 理由是：三套 roughness/thickness proxy 已经齐备，下一步最自然的是补充另一类几何缺陷机制，并在统一框架下比较其正交性。
