# reflectance-qc

## 功能定位

`reflectance-qc` 是显微反射谱现场 QC 的最小正式 CLI。它读取 sample/reference 光谱，计算 sample/reference ratio 与初步 reflectance，并输出可追溯的 processed CSV、QC summary JSON 与 Markdown report。

## 适用场景

- 现场快速检查显微反射谱是否明显异常
- 在后续 TMM 拟合前做最小数据质量筛查
- 作为未来 GUI 的 workflow/CLI 基础闭环

## 输入格式

- `--sample-csv`：样品光谱 CSV/TXT
- `--reference-csv`：参比光谱 CSV/TXT
- 默认 reader 支持常见两列格式：
  - `wavelength,counts`
  - `Wavelength,Intensity`
  - 无表头两列数值

## 命令示例

```bash
python src/cli/reflectance_qc.py \
  --sample-csv "test_data/phase09/glass-PVK-withoutfliter-20ms 2026 四月 29 14_45_45.csv" \
  --reference-csv "test_data/phase09/glass-Ag-withoutfliter-20ms 2026 四月 29 14_42_25.csv" \
  --sample-exposure-ms 20 \
  --reference-exposure-ms 20 \
  --exposure-normalize \
  --wavelength-range 400-750 \
  --output-tag phase09_real_smoke
```

PowerShell:

```powershell
python src/cli/reflectance_qc.py `
  --sample-csv "test_data/phase09/glass-PVK-withoutfliter-20ms 2026 四月 29 14_45_45.csv" `
  --reference-csv "test_data/phase09/glass-Ag-withoutfliter-20ms 2026 四月 29 14_42_25.csv" `
  --sample-exposure-ms 20 `
  --reference-exposure-ms 20 `
  --exposure-normalize `
  --wavelength-range 400-750 `
  --output-tag phase09_real_smoke
```

## 参数表

| 参数 | 必填 | 说明 |
|---|---|---|
| `--sample-csv` | 是 | 样品光谱路径 |
| `--reference-csv` | 是 | 参比光谱路径 |
| `--sample-exposure-ms` | 否 | 样品曝光时间，配合 `--exposure-normalize` 使用 |
| `--reference-exposure-ms` | 否 | 参比曝光时间，配合 `--exposure-normalize` 使用 |
| `--exposure-normalize` | 否 | 按曝光时间归一化 |
| `--wavelength-range` | 否 | 波长裁剪范围，格式 `min-max` |
| `--output-root` | 否 | 输出根目录，默认项目根目录 |
| `--output-tag` | 否 | 附加到 `run_id` 的标签 |
| `--dry-run` | 否 | 只检查输入并打印计划，不写文件 |

## 输出文件

- `data/processed/phase09/reflectance_qc/<run_id>/processed_reflectance.csv`
- `data/processed/phase09/reflectance_qc/<run_id>/qc_summary.json`
- `results/report/phase09_reflectance_qc/<run_id>/qc_report.md`

## QC 指标

- `point_count`
- `valid_point_count`
- `invalid_fraction`
- `reference_low_fraction`
- `reference_near_saturation_fraction`
- `sample_near_saturation_fraction`
- `reflectance_lt_minus_0p02_fraction`
- `reflectance_gt_1p05_fraction`
- `reflectance_gt_1p2_fraction`
- `median_reflectance_500_750`
- `reflectance_600nm`

## 默认阈值

- `saturation_threshold_counts = 60000`
- `reflectance_warn_upper = 1.05`
- `reflectance_fail_upper = 1.20`
- `reflectance_lower_fail = -0.02`

这些阈值只用于现场 QC 初版，不代表最终物理判定。

## 执行原理

1. `storage/readers` 读取 sample/reference CSV/TXT
2. 转为统一 `SpectrumData`
3. `core.reflectance_qc` 对共同波长范围对齐并按需插值
4. 根据

$$
R_\mathrm{sample}(\lambda)
=
\frac{I_\mathrm{sample}(\lambda)}
{I_\mathrm{reference}(\lambda)}
R_\mathrm{reference}(\lambda)
$$

计算初步 reflectance
5. `storage/writers` 输出 CSV/JSON/Markdown

## 限制

- 当前只支持最小 CSV/TXT reader
- 默认 `reference_reflectance = 1`
- 未实现 dark subtraction
- 未实现多曝光线性检查
- 未实现 Ag->Si 或 glassAg->glass 参比修正
- 未输出 PNG 图

## GUI 调用建议

- 未来 GUI 只调用 `src/workflows/reflectance_qc_workflow.py`
- 不应在 GUI 侧复制 QC 公式、阈值与文件导出逻辑

## 维护记录

- Phase 09B：首次建立最小 workflow + CLI 闭环
