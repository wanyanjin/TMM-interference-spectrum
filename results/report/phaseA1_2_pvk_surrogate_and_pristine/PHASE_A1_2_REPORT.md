# Phase A-1.2 Report

## 1. 阶段背景

`Phase A-1` 的 pristine baseline 在 `~750 nm` 附近暴露出明显的台阶式突变。上一轮 `Phase A-1.1` 审计已经确认：

- `R_front` 平滑，不是台阶来源
- Ag 终端边界不是主导因子
- 代码实现路径没有发现 off-by-one、边界切换或绘图采样伪影
- 主因是 PVK `n-k` 在 `749/750 nm` 的 seam，被完整微腔结构显著放大

因此，本阶段的任务不是继续做缺陷模拟或实验拟合，而是先修复材料 surrogate，再重跑 pristine baseline，为后续厚度扫描和缺陷调制建立可靠零缺陷参考谱。

## 2. 输入与数据来源

本阶段实际使用的输入文件如下：

- `resources/aligned_full_stack_nk.csv`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
- `data/processed/phaseA1_seam_audit/pvk_seam_local_audit.csv`
- `data/processed/phaseA1_seam_audit/pvk_source_comparison.csv`
- `src/scripts/step05c_build_aligned_nk_stack.py`
- `src/scripts/stepA1_pristine_baseline.py`
- `src/scripts/stepA1_2_build_pvk_surrogate_v2.py`
- `src/scripts/stepA1_2_rerun_pristine_with_pvk_v2.py`

本目录同步保存的关键资产包括：

- `aligned_full_stack_nk_pvk_v2.csv`
- `phaseA1_2_pristine_baseline.csv`
- `pvk_v2_candidate_metrics.csv`
- `pvk_v1_v2_local_comparison.csv`
- 局部 `n-k / eps / derivative` QA 图
- pristine v1/v2 对照图
- `phaseA1_2_key_metrics.csv`

## 3. 方法概述

本轮并没有在反射率层直接做平滑，而是在材料 `n-k` 层重建 `PVK surrogate v2`。

### 3.1 transition zone 选择

- 比较了 `744–760 nm`、`740–770 nm`、`740–780 nm` 三个候选过渡带
- 最终选定主推荐版本：`740–780 nm`

### 3.2 bridge / blend 策略

本轮采用：

- `smoothstep blend inside transition zone`
- `cosine-tail k decay`
- `relaxed n target toward extended trend`

具体含义是：

- 左侧继续以 pre-seam 的 v1 PVK 吸收尾为锚点
- 右侧只保留 long-wave `n` 趋势作为远端参考
- `k` 在带边区逐步衰减，而不是从 `750 nm` 开始硬切换到 `0`
- 修复对象是 `n(λ)`、`k(λ)` 以及由此导出的 `eps1/eps2` 连续性，而不是把 `R_total` 后处理成“看上去更平”

## 4. 关键结果

### 4.1 seam 步长对比

- `ΔR_stack(749->750)`: `+0.113042 -> +0.001713`
- `ΔR_total(749->750)`: `+0.107011 -> +0.001580`
- `Δn(749->750)`: `+0.009820 -> +0.001408`
- `Δk(749->750)`: `-0.021517 -> -0.006187`
- `Δeps2(749->750)`: `-0.112429 -> -0.030895`

### 4.2 平滑性指标

在 `740–780 nm` 窗口内：

- `max(|dn/dλ|)`: `0.017367 -> 0.003422`
- `max(|dk/dλ|)`: `0.035862 -> 0.009411`
- `max(|Δ²n|)`: `0.008678 -> 0.000379`
- `max(|Δ²k|)`: `0.018793 -> 0.000756`

### 4.3 后窗保真度

在 `810–1100 nm`：

- `R_total fringe RMSE = 0.000000`
- `R_total fringe correlation = 1.000000`
- mean peak/valley shift `= 0.000 nm`

这些结果说明本轮修复主要是局部 band-edge repair，而不是通过全谱扭曲换取表面平滑。

## 5. 对 TMM Baseline 的影响

本阶段最关键的结论是：

- `750 nm` 附近的原始台阶已经从明显跳变压低为连续但较陡的 band-edge 过渡
- 修复影响主要局限在 `740–800 nm`
- 后窗 `810–1100 nm` fringe 基本保持不变

因此，修复后的 pristine baseline 已经可以继续承担“零缺陷参考谱”的角色，而不会把工程 seam 误当成物理结构特征。

## 6. 物理解释与边界

需要明确限定这一步的物理含义：

- 当前 `PVK surrogate v2` 仍然是 surrogate，不是实验直接确认的真值
- 本阶段解决的是 `PVK n-k` seam artifact，而不是关闭了所有材料不确定性
- 本轮没有做完整 Kramers-Kronig 重建，也没有重新反演 band-edge 介电函数参数
- 因此，后续仍需要通过 `PVK uncertainty ensemble` 传播 band-edge surrogate 的不确定性

换句话说，本阶段解决的是“先把明显非物理的接缝修掉”，而不是“已经得到最终可信的 PVK 真值模型”。

## 7. 本阶段结论

`Phase A-1.2` 是继续推进 TMM 理论主线的必要前置条件。原因在于：

- 如果不先修掉 `749/750 nm` seam，后续厚度扫描和缺陷建模都会把工程伪影误识别为谱学特征
- 修复后，baseline 已恢复为“局部 band-edge 过渡 + 稳定后窗微腔 fringe”的结构
- 因此现在可以在不被 seam 污染的前提下，继续分析 `d_PVK` 对谱形的真实调制规律

## 8. 下一步工作

建议按以下顺序推进：

1. `Phase A-2: d_PVK thickness scan`
2. `PVK uncertainty ensemble`

第 1 步用于建立厚度-条纹相位-谱形图谱，第 2 步用于评估 surrogate 不确定性会如何传播到这些结论。
