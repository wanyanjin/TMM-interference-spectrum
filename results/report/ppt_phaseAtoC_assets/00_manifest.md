# Phase A→C PPT Asset Manifest

## 整体主线

1. 先用完整器件结构 TMM 建立实验可见量 `R_total` 的理论 baseline。
2. 然后逐个只引入一个因素，比较其对 `R_total` 的影响。
3. 最终形成五类单因素机制字典：
   - thickness
   - rear-BEMA
   - front-BEMA
   - rear-gap
   - front-gap

## 页面对照

### 01 Baseline
- 主图：`01_baseline/main_figure.png`
- 次图：`01_baseline/secondary_figure.png`
- 建议讲法：先固定完整器件、固定观测量 `R_total`，为后续所有单因素比较建立统一参考。

### 02 Thickness
- 主图：`02_thickness/main_figure.png`
- 次图：`02_thickness/secondary_figure.png`
- 建议讲法：强调 `d_PVK` 主导后窗 fringe 的全局相位/峰谷位置漂移，本质是全局 cavity length change。

### 03 Rear-BEMA
- 主图：`03_rear_bema/main_figure.png`
- 次图：`03_rear_bema/secondary_figure.png`
- 建议讲法：强调 rear-BEMA 主要改变后窗局部包络/振幅，不像 thickness 那样做整体 fringe 平移。

### 04 Front-BEMA
- 主图：`04_front_bema/main_figure.png`
- 次图：`04_front_bema/secondary_figure.png`
- 建议讲法：强调 front-BEMA 主要作用在 front + transition，是 transition-layer / intermixing proxy，不是 real gap。

### 05 Rear-gap
- 主图：`05_rear_gap/main_figure.png`
- 次图：`05_rear_gap/secondary_figure.png`
- 建议讲法：强调 rear-gap 是真实 rear-interface separation，表现为 transition + rear 的相位类重构和非线性响应。

### 06 Front-gap
- 主图：`06_front_gap/main_figure.png`
- 次图：`06_front_gap/secondary_figure.png`
- 建议讲法：强调 front-gap 主要作用在 front → transition，但会次级牵动 rear-window，且比 front-BEMA 更强、更非线性。

### 07 Summary
- 主图：`07_summary/main_figure.png`
- 次图：`07_summary/secondary_figure.png`
- 建议讲法：用矩阵收束五类机制，重点不是信号大小，而是窗口分布和谱形特征差异。

### Appendix: PVK surrogate fix
- 主图：`appendix_pvk_surrogate_fix/main_figure.png`
- 次图：`appendix_pvk_surrogate_fix/secondary_figure.png`
- 建议讲法：只在附录中解释 `749/750 nm` seam fix，说明正文结论建立在已修复的 surrogate 上。
