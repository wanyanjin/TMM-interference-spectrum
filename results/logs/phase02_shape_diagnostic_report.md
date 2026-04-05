# Phase 02 Shape Diagnostic Report

## 1. Executive Summary

本轮 sandbox 明确支持“**ITO 近红外吸收失真是主导因素**”这一结论。  

- 基线 BEMA 模型的 `Global RMSE = 3.589%`、`Long-wave RMSE = 5.736%`
- Probe A 把它们分别压到 `1.045%` 和 `0.600%`
- 与之相比，Probe B 和 Probe C 虽然也能改善条纹形状，但改善幅度明显更弱

因此，“长波端托平”首先应归因于 ITO 的近红外吸收偏弱；厚度不均匀性和 PVK 色散斜率失真更像二级因素。

本轮基线模型（BEMA 双参数反演）指标：

- `chi^2 = 0.391721`
- `Global RMSE = 3.589%`
- `Long-wave RMSE = 5.736%`
- `Long-wave Bias = -4.486%`

诊断结果总表：

| Probe | chi^2 | Global RMSE (%) | Long-wave RMSE (%) | Long-wave Bias (%) |
| --- | ---: | ---: | ---: | ---: |
| Baseline BEMA | 0.3917 | 3.589 | 5.736 | -4.486 |
| Probe A: ITO IR Absorption | 0.0332 | 1.045 | 0.600 | -0.215 |
| Probe B: Thickness Inhomogeneity | 0.1216 | 1.996 | 3.362 | -2.454 |
| Probe C: PVK Cauchy Slope | 0.1573 | 2.271 | 3.940 | -2.609 |

## 2. ITO Absorption Analysis

Probe A 通过对 ITO 的近红外 `k` 施加随波长增长的增强因子 `alpha_ITO` 来测试 Drude 吸收失真假说。

- 最优 `alpha_ITO = 15.2497`
- `chi^2 = 0.033248`
- `Global RMSE = 1.045%`
- `Long-wave RMSE = 0.600%`
- `Long-wave Bias = -0.215%`

结论：

- Probe A 在所有已测探针中给出了最好的全局和长波误差。
- 这说明 ITO 近红外吸收增强不仅能解释长波端托平，也能显著改善整体条纹形状。
- `ito_k_alpha` 在边界内收敛。

## 3. Inhomogeneity & Dispersion Analysis

### Probe B: 厚度不均匀性

- 最优 `sigma_thickness = 30.0000 nm`
- `chi^2 = 0.121572`
- `Global RMSE = 1.996%`
- `Long-wave RMSE = 3.362%`
- `Long-wave Bias = -2.454%`

判断：

- Probe B 明显优于基线，说明光斑面积内的宏观厚度不均匀性确实会展宽条纹。
- 但它对长波端偏差的修复远弱于 Probe A，说明“托平”不能主要归因于厚度平均。
- `sigma_thickness` 撞到了上边界 `30.0`。

### Probe C: PVK Cauchy 斜率

- 最优 `B_scale = 0.4000`
- `chi^2 = 0.157274`
- `Global RMSE = 2.271%`
- `Long-wave RMSE = 3.940%`
- `Long-wave Bias = -2.609%`

判断：

- Probe C 也优于基线，说明当前 PVK 的近红外色散斜率可能确实偏平。
- 但它仍然明显落后于 Probe A，说明色散斜率不是这次畸变的首要矛盾。
- `pvk_b_scale` 撞到了下边界 `0.4`。

## 4. AI's Counter-proposal

人类给出的两个方向都不是空想，但数据告诉我们：**方向 1 的解释力远强于方向 2**。  

- Probe B（厚度不均匀性）把全局 RMSE 从 `3.589%` 降到 `1.996%`，说明它确实会把条纹做宽、做钝
- Probe C（PVK Cauchy 斜率）把全局 RMSE 降到 `2.271%`，说明色散斜率也参与了条纹跨度误差
- 但两者都没有像 Probe A 那样同时显著修复“整体形状 + 长波端托平”

因此，我的反驳是：**当前这次失真不能优先归因于厚度统计平均，也不能优先归因于 PVK Cauchy 外推过平；首要矛盾仍是 ITO 在近红外的吸收建模不足。**

进一步说明：

- BEMA 粗糙层已经成功解决“振幅过高”问题，但不会自动解决“长波端托平 + 条纹跨度偏宽”的复合畸变。
- 若后续继续扩展 sandbox，最有价值的联合模型将是：
  - `ITO absorption correction + BEMA roughness`
  - 必要时再叠加 `sigma_thickness`
  - 最后才考虑把 `PVK Cauchy B-scale` 做成正式自由度

## 5. Next Step Recommendation

建议下一步优先把“ITO 近红外吸收修正”固化到 `step02` 主流程。  

具体做法上，不建议直接把 sandbox 里的经验缩放系数原样硬编码，而是应把它升格为更物理的 ITO 自由载流子吸收修正参数化，例如：

1. 先在 `step02` 中引入一个受限的 ITO 近红外 `k` 增强因子或等价 Drude 校正项
2. 保持 BEMA 粗糙层继续负责振幅压制
3. 仅在完成 ITO 修正后，才继续评估是否需要把厚度高斯平均或 PVK Cauchy `B` 缩放并入主流程

建议下一轮主流程候选优先级：

1. `Probe A: ITO IR Absorption`
2. `Probe B: Thickness Inhomogeneity`
3. `Probe C: PVK Cauchy Slope`
