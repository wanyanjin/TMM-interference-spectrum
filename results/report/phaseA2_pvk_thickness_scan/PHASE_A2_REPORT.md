# Phase A-2 Report

## 1. 阶段目标

本阶段的目标是：在 `Phase A-1.2` 已修复 PVK seam artifact 的前提下，扫描 `d_PVK` 对 pristine baseline 的调制规律，建立“厚度-条纹相位-谱形”关系图谱。

本轮并不涉及：

- 实验拟合
- 缺陷层引入
- BEMA 调制
- air gap 调制

本阶段只改变一个变量：`d_PVK`。

## 2. 输入数据来源

本阶段使用的关键输入包括：

- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `src/scripts/stepA1_pristine_baseline.py`
- `src/scripts/stepA2_pvk_thickness_scan.py`

固定几何口径为：

- `Glass (1 mm, incoherent)`
- `ITO = 100 nm`
- `NiOx = 45 nm`
- `SAM = 5 nm`
- `PVK = variable`
- `C60 = 15 nm`
- `Ag = 100 nm finite film + semi-infinite Air exit`
- `normal incidence`

## 3. 扫描设置

- 扫描范围：`d_PVK = 500–900 nm`
- 实际步长：`5 nm`
- 厚度采样点数：`81`
- 参考厚度：`700 nm`

本目录同步保存的核心资产包括：

- `phaseA2_pvk_thickness_scan.csv`
- `phaseA2_pvk_feature_summary.csv`
- `phaseA2_key_metrics.csv`
- `phaseA2_R_stack_heatmap.png`
- `phaseA2_R_total_heatmap.png`
- `phaseA2_deltaR_stack_vs_700nm_heatmap.png`
- `phaseA2_deltaR_total_vs_700nm_heatmap.png`
- `phaseA2_peak_valley_tracking.png`
- `phaseA2_selected_thickness_curves.png`

## 4. 方法概述

### 4.1 基本计算对象

对每一个 `d_PVK`，都重新计算：

- `R_stack(λ)`：后侧薄膜堆栈相干反射
- `R_total(λ)`：厚玻璃前表面与后侧 stack 级联后的总反射率

同时相对于 `700 nm` 参考厚度构造：

- `Delta_R_stack_vs_700nm`
- `Delta_R_total_vs_700nm`

### 4.2 特征提取

在 `810–1100 nm` 后窗内，提取：

- 主峰位置
- 主谷位置
- 峰谷间距
- 代表波长点的 `R_stack / R_total`

这里的 peak/valley tracking 是工程摘要指标，目的是建立厚度-谱形关系的第一版图谱，而不是做严格的模式标号。

## 5. 关键结果

### 5.1 后窗是厚度主敏感窗口

厚度灵敏度最强的波长集中在后窗长波端：

- rear-window `R_stack` 最敏感波长：`1100, 1099, 1098 nm`
- rear-window `R_total` 最敏感波长：`1100, 1099, 1098 nm`

对应的最大标准差为：

- rear-window `max std(R_stack) = 11.59%`
- rear-window `max std(R_total) = 11.29%`

相比之下，前窗的最大标准差只有：

- front-window `max std(R_stack) = 0.57%`
- front-window `max std(R_total) = 0.52%`

这说明厚度变化主要通过后窗微腔结构放大，而前窗只表现出弱响应。

### 5.2 后窗对厚度高度敏感，但不是单一模态全范围严格单调

从热力图和 tracking 图可以看到：

- 后窗 fringe 会随 `d_PVK` 明显漂移
- 局部区间中峰位/谷位存在清晰近线性漂移
- 但若把整个 `500–900 nm` 范围压缩为单一“主峰/主谷”轨迹，则会因为不同 fringe 模式交替占优而出现 mode switching

因此，更准确的结论是：

- 后窗对 `d_PVK` 具有强系统灵敏度
- 存在可辨识的局部近线性区间
- 但不能把它简单概括为“整个扫描范围里单一主峰全程严格单调”

### 5.3 `R_stack` 比 `R_total` 更适合作为理论灵敏度对象

本轮结果显示：

- rear-window `max std(R_stack) > max std(R_total)`
- 前表面固定 `R_front` 背景会略微钝化 `R_total` 的厚度敏感性

因此：

- `R_stack` 更适合做纯理论灵敏度分析
- `R_total` 仍然是更接近实验可见量的观测对象

### 5.4 厚度变化的谱形指纹

本轮扫描表明，`d_PVK` 的主导效应是：

- 后窗 fringe 的整体相位漂移
- 峰谷位置系统移动
- 峰谷间距随厚度变化而演化

这类特征更像“全局光程变化”，而不是界面局部缺陷。

## 6. 对后续缺陷建模的意义

本阶段给出了一条很重要的判别线：

- 若一个谱形变化主要表现为后窗 fringe 整体平移，更像 `d_PVK`
- 若变化更像局部振幅异常、局部背景抬升、特定窗口畸变，则更可能来自界面缺陷，例如 roughness、BEMA 或 air gap

这并不意味着厚度与缺陷完全正交，但至少说明：

- `d_PVK` 是“全局微腔光程”变量
- 缺陷调制更可能是“局部界面扰动”变量

因此，`Phase A-2` 为后续区分“厚度变化”和“界面缺陷”提供了理论参照图谱。

## 7. 风险与边界

当前仍需明确以下边界：

- 本轮扫描建立在 `PVK surrogate v2` 上，不等于 band-edge 真值已锁定
- 还没有把 surrogate 不确定性传播到 thickness scan 结论
- 还没有引入玻璃色散敏感性
- peak/valley tracking 使用的是工程定义，不应替代更系统的 fringe mode 标号

因此，本阶段得到的是一套可靠的“第一版厚度灵敏度地图”，而不是最终完备的厚度反演字典。

## 8. 本阶段结论

`Phase A-2` 证明了：

- 在修复后的 pristine baseline 上，`d_PVK` 对后窗 fringe 具有强烈且系统的调制作用
- 厚度响应主要集中在 `810–1100 nm` 后窗
- `R_stack` 的理论敏感性略强于 `R_total`
- 厚度变化的主特征是 fringe 相位漂移，而不是局部缺陷式的振幅畸变

因此，本阶段已经建立起后续缺陷模型比较所需的“厚度参考图谱”。

## 9. 下一步建议

建议下一步优先进入：

1. `PVK uncertainty ensemble`

理由是：

- 当前 thickness scan 的主趋势已经清楚
- 但这些趋势仍依赖 `PVK surrogate v2`
- 先量化 surrogate 不确定性对 thickness scan 的传播范围，再继续 `BEMA only` 或 `air gap only`，会更利于后续判断哪些特征真正稳健

在 uncertainty envelope 明确之后，再进入：

2. `BEMA only`
3. `air gap only`

会更容易区分“厚度引起的全局 fringe 相位变化”和“界面缺陷引起的局部谱形扭曲”。
