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
- run_id: `20260509_144837_reflectance_qc_phase09c2_gui`
- inputs: `{'sample_path': 'D:\\onedrive\\Data\\PL\\2026\\0508\\smaple\\processed\\Si-500ms-before-1 2026 五月 08 14_34_07.csv', 'reference_path': 'D:\\onedrive\\Data\\PL\\2026\\0508\\smaple\\processed\\Ag-500ms-after-1 2026 五月 08 14_46_38-1.csv'}`
- outputs: `{'processed_csv': 'D:\\code\\TMM-interference-spectrum\\data\\processed\\phase09\\reflectance_qc\\20260509_144837_reflectance_qc_phase09c2_gui\\processed_reflectance.csv', 'qc_summary_json': 'D:\\code\\TMM-interference-spectrum\\data\\processed\\phase09\\reflectance_qc\\20260509_144837_reflectance_qc_phase09c2_gui\\qc_summary.json', 'qc_report_md': 'D:\\code\\TMM-interference-spectrum\\results\\report\\phase09_reflectance_qc\\20260509_144837_reflectance_qc_phase09c2_gui\\qc_report.md'}`

## 参数

- 波长范围: `500.0` - `700.0` nm
- 是否插值: `False`
- 是否曝光归一化: `True`
- reference_type: `unity`

## QC 结果

- overall_status: `PASS`

## QC Metrics

- `point_count`: 472.0
- `valid_point_count`: 472.0
- `invalid_fraction`: 0.0
- `reference_low_fraction`: 0.0
- `reference_near_saturation_fraction`: 0.0
- `sample_near_saturation_fraction`: 0.0
- `reflectance_lt_minus_0p02_fraction`: 0.0
- `reflectance_gt_1p05_fraction`: 0.0
- `reflectance_gt_1p2_fraction`: 0.0
- `median_reflectance_500_750`: 0.356868454047776
- `reflectance_600nm`: 0.35725498143797024

## 主要风险解释

- 无附加 flags。

## 输出文件路径

- processed_reflectance.csv
- qc_summary.json
- qc_report.md

## 说明

- 本轮只提供最小 CLI + workflow 闭环，不输出 GUI 图像。
- PNG/交互式图查看留给后续 visualization / GUI 阶段。
