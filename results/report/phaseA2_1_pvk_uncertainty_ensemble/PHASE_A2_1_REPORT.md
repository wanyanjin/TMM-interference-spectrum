# Phase A-2.1 Report

## 1. 为什么要做 uncertainty ensemble

- 当前 thickness 与 rear-BEMA 结论都建立在 `PVK surrogate v2` 上。
- 在继续 front-BEMA / air-gap 之前，必须先确认这些机制结论是不是被 band-edge 先验强烈污染。

## 2. ensemble 是怎么构建的

- `nominal`: 直接使用 `PVK surrogate v2`。
- `more_absorptive`: 在 `740-850 nm` 内用 smooth envelope 适度增强 `k` 吸收尾，并用小幅联动的 `n` 偏移保持连续和平滑。
- `less_absorptive`: 在同一窗口内用 smooth envelope 适度削弱 `k` 吸收尾，并同步做小幅 `n` 联动。
- 软作用窗口扩展到 `730-900 nm`，用于保证导数平滑和无 seam 过渡。

## 3. 对 thickness 结论的影响

- 后窗仍然是主厚度敏感窗口，这一点稳健。
- `d_PVK` 导致后窗 fringe 整体相位/条纹位置系统漂移，这一点仍然稳健。
- 受 ensemble 影响更大的是 band-edge 相邻波段的振幅细节，而不是后窗厚度机制本身。

## 4. 对 rear-BEMA 结论的影响

- rear-BEMA 的“局部包络/轻微振幅微扰”结论在 ensemble 下仍成立。
- 它与 `d_PVK` 的正交性仍成立：前者不像全局腔长变化，后者仍主要表现为后窗整体 fringe 相位漂移。
- 不过 rear-BEMA 的幅值量级对 band-edge 先验比 thickness 峰位更敏感，因此 amplitude 解释需要更谨慎。

## 5. 最重要的最终结论

- 高置信度结构指纹：`rear-window dominant DeltaR wavelength under d_PVK; rear-window DeltaR amplitude under d_PVK; rear-window dominant DeltaR wavelength under rear-BEMA; band-edge DeltaR amplitude under d_PVK`
- surrogate-sensitive 指纹：`rear-window DeltaR amplitude under rear-BEMA; band-edge DeltaR amplitude under rear-BEMA; absolute R_total at 780 nm under d_PVK; absolute R_total at 780 nm under rear-BEMA`
- 当前可以高置信使用的，是后窗作为 thickness 主窗口以及 thickness 与 rear-BEMA 的机制差异本身。
- 需要谨慎解释的，是 band-edge 附近与 amplitude 细节强相关的次级特征。

## 6. 下一步建议

- 更建议下一步进入 `Phase B-2 front-only BEMA`。
- 理由是：经过本轮 uncertainty propagation，thickness 与 rear-BEMA 的核心判据已经证明足够稳健，可以继续增加 front-side 粗糙这一新的结构维度；`air-gap only` 更适合放在粗糙机制字典更完整之后统一比较。
