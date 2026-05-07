# Phase 08 0429 Reference Comparison Report

## 1. 原始数据质量
- 本次使用 `glass/PVK` 与 `glass/Ag`，并在 dual 模式引入 direct Ag mirror + bk 多帧校准。
- 无 `.spe` 元数据，曝光时间来自文件名推断（`20ms`）。
- 指标计算使用未平滑曲线；若启用平滑，仅用于图示辅助。

## 2. 模型与公式
- 参比模型（glass/Ag）：`Air / Glass(incoherent) / Ag / Air`
- 参比模型（Ag mirror）：`Air / Ag / Air`
- 样品模型：`Air / Glass(incoherent) / PVK / Air`
- 实验反射率：`R_exp = (I_pvk/t_pvk)/(I_ag/t_ag) * R_TMM_glass_ag`

## 3. 结果摘要
- `best_d_PVK_nm = 458.000`
- `diagnostic_scale_a_fixed = -2.111595`
- `diagnostic_offset_b_fixed = 6.025901e-01`
- `diagnostic_scale_a_best_d = 0.635082`
- `diagnostic_offset_b_best_d = 2.362893e-01`

## 4. 主结论范围
- 主结论仅基于 `400.0-750.0 nm` 且 strict mask。
- `750.0-931.443 nm` 仅作为扩展 QC。

## 5. 关键图
- /Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/figures/phase08/reference_comparison/phase08_0429_dual_reference_reflectance_exp_vs_tmm_pvk_x01.png
- /Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/figures/phase08/reference_comparison/phase08_0429_residual_pvk_x01.png
- /Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/figures/phase08/reference_comparison/phase08_0429_thickness_scan_pvk_x01.png
- /Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/figures/phase08/reference_comparison/phase08_0429_ag_bk_qc_pvk_x01.png

## 6. 指标表

```text
               Band  Wavelength_Min_nm  Wavelength_Max_nm  Point_Count_Strict  Model      MAE     RMSE  Mean_Bias  Max_Abs_Error  Pearson_Correlation
            450_500              450.0            500.000                  58  fixed 0.201619 0.209421   0.201619       0.477111            -0.861296
            450_500              450.0            500.000                  58 best_d 0.201617 0.209419   0.201617       0.477110            -0.861283
            500_650              500.0            650.000                 354  fixed 0.150371 0.153560   0.150371       0.211711            -0.814801
            500_650              500.0            650.000                 354 best_d 0.150677 0.153913   0.150677       0.210784            -0.809350
            650_750              650.0            750.000                 237  fixed 0.247642 0.248495   0.247642       0.282790             0.073738
            650_750              650.0            750.000                 237 best_d 0.236479 0.236815   0.236479       0.258806             0.830393
    400_750_primary              400.0            750.000                 648  fixed 0.190440 0.198299   0.190440       0.477111            -0.414810
    400_750_primary              400.0            750.000                 648 best_d 0.186525 0.193156   0.186525       0.477110             0.121115
750_931_extended_qc              750.0            931.443                 344  fixed 0.268734 0.282819   0.268734       0.468010            -0.050472
750_931_extended_qc              750.0            931.443                 344 best_d 0.253904 0.264576   0.253904       0.396132             0.697697
```

## 7. 诊断解释
- 若 `a` 明显偏离 1 或 `b` 明显偏离 0，应优先排查参比口径/收光几何/背景项。
- 本节诊断不替代物理模型判断。
