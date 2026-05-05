# CLI: reference-comparison

状态：`active`（支持 `single_reference` / `dual_reference`）

## 1. 功能定位

在 `glass/Ag` 或 `Ag mirror` 参比口径下，完成 `glass/PVK` 实验反射率重建，并与 TMM 理论曲线做 fixed/best-d 对比和诊断。

## 2. 适用场景

- 同光路 `glass/PVK` vs `glass/Ag` 参比校准可行性评估
- `Ag mirror + bk` 多帧校准后与 `glass/Ag` 双参比并列诊断
- Phase 08 参比几何验证与流程收敛

## 3. 入口命令

Single-reference：

```bash
python src/cli/reference_comparison.py \
  --sample-csv "test_data/0429/glass-PVK-withoutfliter-20ms 2026 四月 29 14_45_45.csv" \
  --reference-csv "test_data/0429/glass-Ag-withoutfliter-20ms 2026 四月 29 14_42_25.csv"
```

Dual-reference：

```bash
python src/cli/reference_comparison.py \
  --sample-csv "test_data/0429/glass-PVK-withoutfliter-20ms 2026 四月 29 14_45_45.csv" \
  --reference-csv "test_data/0429/glass-Ag-withoutfliter-20ms 2026 四月 29 14_42_25.csv" \
  --comparison-mode dual_reference \
  --ag-mirror-csv "test_data/0429/Ag-withoutfliter-20ms 2026 四月 29 15_14_48.csv" \
  --background-csv "test_data/0429/bk-20ms 2026 四月 29 15_31_12.csv"
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
- `--comparison-mode`: `single_reference` 或 `dual_reference`
- `--ag-mirror-csv`: direct Ag mirror 多帧 CSV（dual 模式必填）
- `--background-csv`: 背景多帧 CSV（dual 模式必填）
- `--drop-ag-frames`: 需排除的 Ag 帧，默认 `1`
- `--ag-background-align`: 背景对齐方式，首版仅 `pixel`
- `--ag-reference-model`: Ag mirror 理论模型，首版仅 `air_ag_air`
- `--reference-type`: 首版仅支持 `glass_ag`
- `--nk-csv`: 光学常数表，默认 `resources/aligned_full_stack_nk.csv`
- `--primary-range`: 主分析波段，默认 `400-750`
- `--extended-qc-range`: 扩展 QC 波段，默认 `750-931.443`
- `--review-range`: 主审查图 x 轴范围，默认 `500-750`
- `--d-ag-nm`: Ag 厚度假设，默认 `100`
- `--d-pvk-fixed-nm`: fixed PVK 厚度假设，默认 `700`
- `--d-pvk-scan-min/max/step`: PVK 单参数扫描范围，默认 `400/1000/1`
- `--output-root`: 输出根目录，默认项目根目录
- `--smooth-for-plot`: 图示辅助平滑开关（默认关闭）
- `--smooth-window`, `--smooth-polyorder`: 平滑参数（仅图示）
- `--dry-run`: 只做输入检查和运行计划，不写结果

## 5. 输入文件要求

- 单谱 CSV 必须可识别波长列与强度列（兼容 `Wavelength` / `Intensity`）
- dual 模式下 Ag/bk 多帧 CSV 列约定：
  - 第 2 列：`Frame_Index`
  - 第 3 列：`Wavelength_nm`
  - 第 5 列：`Pixel_Index`
  - 第 6 列：`Counts`
- sample/reference 波长网格必须一致
- 本版不依赖 `.spe`；曝光时间若无元数据则来自文件名推断并写入 manifest

## 6. 输出文件

输出目录：

- `data/processed/phase08/reference_comparison/`
- `results/figures/phase08/reference_comparison/`
- `results/logs/phase08/reference_comparison/`
- `results/report/phase08_reference_comparison/`

关键文件：

- `phase08_0429_input_inventory.csv`（single）
- `phase08_0429_calibrated_reflectance.csv`（single）
- `phase08_0429_manifest.json`（single）
- `phase08_0429_dual_reference_calibrated_reflectance.csv`（dual）
- `phase08_0429_dual_reference_error_metrics.csv`（dual）
- `phase08_0429_dual_reference_manifest.json`（dual）
- `phase08_0429_ag_mirror_background_corrected.csv`（dual）
- `phase08_0429_ag_mirror_frame_qc.csv`（dual）
- `phase08_0429_dual_reference_report.md`（dual）

## 7. 执行原理

- `glass/Ag` 校准：
  - `R_exp_by_glassAg = (I_pvk/t_pvk)/(I_glassAg/t_glassAg) * R_TMM_glassAg`
- `Ag mirror` 校准：
  - `R_exp_by_AgMirror = (I_pvk/t_pvk)/(I_AgMirror_corr/t_AgMirror) * R_TMM_AgMirror`
- 参比模型：
  - `R_TMM_glassAg`: `Air / Glass(incoherent) / Ag / Air`
  - `R_TMM_AgMirror`: `Air / Ag / Air`
- 样品模型：
  - `R_TMM_glassPVK`: `Air / Glass(incoherent) / PVK / Air`
- 厚度拟合：
  - 仅释放 `d_PVK`，扫描 `400-1000 nm`

## 8. 调用核心接口

- `src/core/reference_comparison.py`：
  - 单谱读取、mask 构建、TMM 曲线、厚度扫描、诊断
  - 多帧 Ag/bk 读取、按 pixel 背景扣除、Ag frame QC

## 9. 数据流方向

single：
`sample/reference csv -> CLI 参数解析与输入校验 -> core 计算 -> data/processed -> figures/logs/report -> manifest`

dual：
`Ag multi-frame + bk multi-frame -> pixel 对齐背景扣除 -> Ag mirror corrected spectrum -> dual reference comparison -> data/processed -> figures/logs/report -> manifest`

## 10. 校验与错误行为

- `reference_type` 非 `glass_ag`：报错
- `comparison_mode=dual_reference` 但缺少 `ag-mirror-csv` 或 `background-csv`：报错
- 单谱波长网格不一致：报错
- Ag 与 bk 的 `Pixel_Index` 集合不一致：报错
- 主波段 strict mask 有效点不足：报错
- 诊断 `a/b` 仅用于系统误差判断，不作为物理结论

## 11. GUI 调用建议

- GUI 仅做参数输入、任务触发、结果展示
- 业务计算统一调用 CLI/核心模块，不在 GUI 复制物理公式
- 图示规范：
  - `Ag mirror` 与 `glass/Ag` 使用不同颜色实线
  - TMM 理论曲线使用灰色虚线

## 12. 版本与维护记录

- `v1`（Phase 08）：`glass/Ag` 参比最小闭环
- `v1.1`（Phase 08）：支持 `Ag mirror + bk` 多帧校准与 dual-reference 对比
- 已知限制：不含粗糙层/角度平均/多参数拟合
