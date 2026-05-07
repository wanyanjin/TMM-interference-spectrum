# Phase 08 0429 Reference Comparison Report

## 1. 原始数据质量
- 本次仅使用 `glass/PVK` 与 `glass/Ag` 两条 CSV，未使用 direct Ag mirror。
- 无 `.spe` 元数据，曝光时间来自文件名推断（`20ms`）。
- 指标计算使用未平滑曲线；若启用平滑，仅用于图示辅助。

## 2. 模型与公式
- 参比模型：`Air / Glass(incoherent) / Ag / Air`
- 样品模型：`Air / Glass(incoherent) / PVK / Air`
- 实验反射率：`R_exp = (I_pvk/t_pvk)/(I_ag/t_ag) * R_TMM_glass_ag`

## 3. 结果摘要
- `best_d_PVK_nm = 483.000`
- `diagnostic_scale_a_fixed = -2.109841`
- `diagnostic_offset_b_fixed = 5.837685e-01`
- `diagnostic_scale_a_best_d = -0.222002`
- `diagnostic_offset_b_best_d = 3.521836e-01`

## 4. 主结论范围
- 主结论仅基于 `400.0-750.0 nm` 且 strict mask。
- `750.0-931.443 nm` 仅作为扩展 QC。

## 5. 关键图
- /Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/figures/phase08/reference_comparison/phase08_0429_reflectance_exp_vs_tmm.png
- /Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/figures/phase08/reference_comparison/phase08_0429_residual.png
- /Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/figures/phase08/reference_comparison/phase08_0429_thickness_scan.png

## 6. 指标表

```text
               Band  Wavelength_Min_nm  Wavelength_Max_nm  Point_Count_Strict  Model      MAE     RMSE  Mean_Bias  Max_Abs_Error  Pearson_Correlation
            450_500              450.0            500.000                  58  fixed 0.202397 0.210238   0.202397       0.478154            -0.833379
            450_500              450.0            500.000                  58 best_d 0.202399 0.210240   0.202399       0.478156            -0.833405
            500_650              500.0            650.000                 354  fixed 0.151650 0.155170   0.151650       0.217080            -0.804747
            500_650              500.0            650.000                 354 best_d 0.152571 0.156575   0.152571       0.229728            -0.859701
            650_750              650.0            750.000                 237  fixed 0.269655 0.271308   0.269655       0.315988            -0.808379
            650_750              650.0            750.000                 237 best_d 0.245695 0.246734   0.245695       0.272862             0.541433
    400_750_primary              400.0            750.000                 648  fixed 0.199250 0.209663   0.199250       0.478154            -0.758381
    400_750_primary              400.0            750.000                 648 best_d 0.190971 0.198829   0.190971       0.478156            -0.083581
750_931_extended_qc              750.0            931.443                 344  fixed 0.178905 0.226556   0.168916       0.442288            -0.666240
750_931_extended_qc              750.0            931.443                 344 best_d 0.208052 0.233585   0.207036       0.387693            -0.020687
```

## 7. 诊断解释
- 若 `a` 明显偏离 1 或 `b` 明显偏离 0，应优先排查参比口径/收光几何/背景项。
- 本节诊断不替代物理模型判断。
