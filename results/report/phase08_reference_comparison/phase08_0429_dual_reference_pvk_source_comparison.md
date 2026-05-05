# Phase 08 x=0.1 Literature PVK Source Comparison

## 1. 数据来源
- 文献补充材料：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/resources/1-s2.0-S0927024818304446-mmc1.docx`
- 采用 `Table S3` 中 `FA0.9Cs0.1PbI3` 的 `Photon Energy / ε1 / ε2` 数据。
- 提取行数：`695`
- 文献波长覆盖：`210.613-1687.321 nm`

## 2. 生成文件
- epsilon 表：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/resources/digitized/lit_x01_csfapi_epsilon_table_s3.csv`
- nk 表：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/resources/digitized/lit_x01_csfapi_nk_table_s3.csv`
- Phase08 专用 aligned nk：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/resources/aligned_full_stack_nk_phase08_x01.csv`
- 对比图：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/figures/phase08/reference_comparison/phase08_0429_dual_reference_pvk_source_comparison.png`
- 当前 PVK 单独图：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/figures/phase08/reference_comparison/phase08_0429_dual_reference_pvk_source_current_pvk.png`
- x=0.1 单独图：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/figures/phase08/reference_comparison/phase08_0429_dual_reference_pvk_source_pvk_x01.png`
- 对比指标：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/data/processed/phase08/reference_comparison/phase08_0429_dual_reference_pvk_source_comparison_metrics.csv`

## 3. 运行口径
- 基线 nk：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/resources/aligned_full_stack_nk.csv`
- x=0.1 nk：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/resources/aligned_full_stack_nk_phase08_x01.csv`
- 双参比保持一致：`glass/Ag` 与 `Ag mirror + bk`。
- 主审查波段：`500-750 nm`；指标主体仍保留 CLI 的 primary 定义与 thickness scan。

## 4. 400-750 nm primary 指标摘录

```text
 PVK_Source            Band  Wavelength_Min_nm  Wavelength_Max_nm  Point_Count_Strict  Model      MAE     RMSE  Mean_Bias  Max_Abs_Error  Pearson_Correlation
current_pvk 400_750_primary              400.0              750.0                 648  fixed 0.199250 0.209663   0.199250       0.478154            -0.758381
current_pvk 400_750_primary              400.0              750.0                 648 best_d 0.190971 0.198829   0.190971       0.478156            -0.083581
    pvk_x01 400_750_primary              400.0              750.0                 648  fixed 0.190440 0.198299   0.190440       0.477111            -0.414810
    pvk_x01 400_750_primary              400.0              750.0                 648 best_d 0.186525 0.193156   0.186525       0.477110             0.121115
```

## 5. 关键结论入口
- 基线 dual 报告：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/report/phase08_reference_comparison/phase08_0429_dual_reference_report_current_pvk.md`
- x=0.1 dual 报告：`/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/report/phase08_reference_comparison/phase08_0429_dual_reference_report_pvk_x01.md`
- 本报告只做当前 PVK 来源与文献 x=0.1 来源的并排对照，不替代各自单独 manifest/report。
