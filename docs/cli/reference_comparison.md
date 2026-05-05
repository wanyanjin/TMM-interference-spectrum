# CLI: reference-comparison

状态：`active`

## 1. 功能定位

在 `glass/Ag` 参比口径下，完成 `glass/PVK` 实验反射率重建，并与 TMM 理论曲线做 fixed/best-d 对比和诊断。

## 2. 适用场景

- 同光路 `glass/PVK` vs `glass/Ag` 参比校准可行性评估
- Phase 08 参比几何验证
- 后续 GUI 调用前的可追溯 CLI 基线

## 3. 入口命令

```bash
python src/cli/reference_comparison.py \
  --sample-csv "test_data/0429/glass-PVK-withoutfliter-20ms 2026 四月 29 14_45_45.csv" \
  --reference-csv "test_data/0429/glass-Ag-withoutfliter-20ms 2026 四月 29 14_42_25.csv"
```

Dry-run：

```bash
python src/cli/reference_comparison.py \
  --sample-csv "<sample.csv>" \
  --reference-csv "<reference.csv>" \
  --dry-run
```

## 4. 参数说明

- `--sample-csv`: `glass/PVK` 测量 CSV（必填）
- `--reference-csv`: `glass/Ag` 参比 CSV（必填）
- `--reference-type`: 第一版仅支持 `glass_ag`
- `--nk-csv`: 光学常数表，默认 `resources/aligned_full_stack_nk.csv`
- `--primary-range`: 主分析波段，默认 `400-750`
- `--extended-qc-range`: 扩展 QC 波段，默认 `750-931.443`
- `--d-ag-nm`: Ag 厚度假设，默认 `100`
- `--d-pvk-fixed-nm`: fixed PVK 厚度假设，默认 `700`
- `--d-pvk-scan-min/max/step`: PVK 单参数扫描范围，默认 `400/1000/1`
- `--output-root`: 输出根目录，默认项目根目录
- `--smooth-for-plot`: 图示辅助平滑开关（默认关闭）
- `--smooth-window`, `--smooth-polyorder`: 平滑参数（仅图示）
- `--dry-run`: 只做输入检查和运行计划，不写结果

## 5. 输入文件要求

- CSV 必须可识别波长列与强度列（默认兼容 `Wavelength` / `Intensity`）
- sample/reference 波长网格必须一致
- 本版不依赖 `.spe`；曝光时间若无元数据则来自文件名推断并写入 manifest

## 6. 输出文件

输出目录：

- `data/processed/phase08/reference_comparison/`
- `results/figures/phase08/reference_comparison/`
- `results/logs/phase08/reference_comparison/`
- `results/report/phase08_reference_comparison/`

关键文件：

- `phase08_0429_input_inventory.csv`
- `phase08_0429_calibrated_reflectance.csv`
- `phase08_0429_tmm_theory_curves.csv`
- `phase08_0429_error_metrics.csv`
- `phase08_0429_thickness_scan_cost.csv`
- `phase08_0429_manifest.json`
- `phase08_0429_reference_comparison_report.md`

## 7. 执行原理

- 实验反射率：
  - `R_exp = (I_pvk/t_pvk)/(I_ag/t_ag) * R_TMM_glass_ag`
- 参比理论模型：
  - `Air / Glass(incoherent) / Ag / Air`
- 样品理论模型：
  - `Air / Glass(incoherent) / PVK / Air`
- 厚度拟合：
  - 仅释放 `d_PVK`，扫描 `400-1000 nm`
- 诊断：
  - 对 fixed 与 best-d 各自拟合 `R_exp ≈ a * R_TMM + b`

## 8. 调用的核心接口

- `src/core/reference_comparison.py`
  - 数据读取与列识别
  - mask 构建（loose/strict）
  - TMM 曲线计算
  - 厚度扫描
  - 诊断 scale/offset
  - 数据表与 manifest 输出

## 9. 数据流方向

`sample/reference csv -> CLI 参数解析与输入校验 -> core 计算 -> data/processed -> figures/logs/report -> manifest`

## 10. 校验与错误行为

- `reference_type` 非 `glass_ag`：直接报错
- 波长网格不一致：报错终止
- 主波段 strict mask 有效点不足：报错终止
- 测量波段超出 `nk` 覆盖：报错终止
- 诊断提示：
  - `a` 偏离 1 或 `b` 偏离 0 仅说明系统误差风险，非物理结论

## 11. GUI 调用建议

- GUI 仅做参数输入、任务触发、结果展示
- 业务计算统一调用 CLI/核心模块，不在 GUI 复制物理公式

## 12. 示例

默认执行：

```bash
python src/cli/reference_comparison.py \
  --sample-csv "test_data/0429/glass-PVK-withoutfliter-20ms 2026 四月 29 14_45_45.csv" \
  --reference-csv "test_data/0429/glass-Ag-withoutfliter-20ms 2026 四月 29 14_42_25.csv" \
  --primary-range "400-750" \
  --extended-qc-range "750-931.443"
```

## 13. 版本与维护记录

- `v1`（Phase 08）：首版上线，支持 `glass/Ag` 参比最小闭环。
- 已知限制：不支持 direct Ag mirror 口径、不含粗糙层/角度平均/多参数拟合。

