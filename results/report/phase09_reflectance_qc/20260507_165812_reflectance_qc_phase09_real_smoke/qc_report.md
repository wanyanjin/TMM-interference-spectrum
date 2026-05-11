# Reflectance QC Report

## 计算公式

$$
R_\mathrm{sample}(\lambda)
=
\frac{I_\mathrm{sample}(\lambda)}{I_\mathrm{reference}(\lambda)}
R_\mathrm{reference}(\lambda)
$$

## 输入文件

- tool_name: `reflectance_qc`
- run_id: `20260507_165812_reflectance_qc_phase09_real_smoke`
- inputs: `{'sample_path': 'test_data\\phase09\\glass-PVK-withoutfliter-20ms 2026 四月 29 14_45_45.csv', 'reference_path': 'test_data\\phase09\\glass-Ag-withoutfliter-20ms 2026 四月 29 14_42_25.csv'}`
- outputs: `{'processed_csv': 'D:\\code\\TMM-interference-spectrum\\data\\processed\\phase09\\reflectance_qc\\20260507_165812_reflectance_qc_phase09_real_smoke\\processed_reflectance.csv', 'qc_summary_json': 'D:\\code\\TMM-interference-spectrum\\data\\processed\\phase09\\reflectance_qc\\20260507_165812_reflectance_qc_phase09_real_smoke\\qc_summary.json', 'qc_report_md': 'D:\\code\\TMM-interference-spectrum\\results\\report\\phase09_reflectance_qc\\20260507_165812_reflectance_qc_phase09_real_smoke\\qc_report.md'}`

## 参数

- 波长范围: `400.0` - `750.0` nm
- 是否插值: `False`
- 是否曝光归一化: `True`
- reference_type: `unity`

## QC 结果

- overall_status: `FAIL`

## QC Metrics

- `point_count`: 824.0
- `valid_point_count`: 815.0
- `invalid_fraction`: 0.01092233009708743
- `reference_low_fraction`: 0.0
- `reference_near_saturation_fraction`: 0.0
- `sample_near_saturation_fraction`: 0.0
- `reflectance_lt_minus_0p02_fraction`: 0.0036407766990291263
- `reflectance_gt_1p05_fraction`: 0.043689320388349516
- `reflectance_gt_1p2_fraction`: 0.02912621359223301
- `median_reflectance_500_750`: 0.31754984362091976
- `reflectance_600nm`: 0.29584330991630753

## 主要风险解释

- `FAIL` `reflectance_gt_1p2`: More than 1% of points exceed reflectance 1.20
- `WARN` `reflectance_gt_1p05`: More than 1% of points exceed reflectance 1.05

## 输出文件路径

- processed_reflectance.csv
- qc_summary.json
- qc_report.md

## 说明

- 本轮只提供最小 CLI + workflow 闭环，不输出 GUI 图像。
- PNG/交互式图查看留给后续 visualization / GUI 阶段。
