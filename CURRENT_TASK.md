# CURRENT_TASK.md

## 当前任务

`Phase 08：参比几何验证与治理规范收敛`

目标：已完成文献 `FA0.9Cs0.1PbI3` (`x=0.1`) 介电函数表提取、Phase 08 专用 PVK `n/k` 替代表生成，以及与当前 PVK 来源在 `glass/Ag` / `Ag mirror` 双参比链路下的并排比较；当前待审查结果并决定是否继续把该来源用于后续诊断。

## 本轮范围

- 提取 `Table S3 x=0.1` 的 `ε1/ε2` 并生成 `n/k`
- 生成 `resources/aligned_full_stack_nk_phase08_x01.csv`
- 用 `current_pvk` 与 `pvk_x01` 两套 `nk` 完成双参比重算
- 输出 `phase08_0429_dual_reference_pvk_source_comparison.png/.md/.csv`
- 同步更新文献地图、CLI 文档、数据流与历史摘要

不在本轮范围：

- 不修改 TMM/HDR/Phase 07 业务代码
- 不全局替换其他 Phase 的默认 PVK `n-k` 表
- 不迁移原始数据或历史结果目录
- 不引入新依赖

## TODO

1. 复核 `current_pvk` vs `pvk_x01` 的 primary 指标与图形差异
2. 判断是否需要继续引入更贴近样品的 PVK/FA-Cs 组分或几何诊断
3. 仅暂存本任务文件，提交并 push：`[Phase 08] 引入x=0.1文献PVK光学常数并重算双参比对比`

## 阻塞与注意事项

- 工作区存在无关未提交改动（`docs/PROJECT_STATE.md`、`src/scripts/stepD2b_explain_feature_pipeline.py`、`results/report/...`），本轮不得纳入提交。
- `test_data/0429` 无 `.spe`，曝光时间仅来自文件名推断，必须在 manifest/report 标注。
- `Table S3` 在 docx 中以固定宽度字符串出现，提取时必须避免把 `x=0.2` 段落混入 `x=0.1`。
- 不得覆盖当前未带 tag 的 Phase 08 结果；新运行必须使用 `--output-tag`。

## 立即下一步

- 审查 `phase08_0429_dual_reference_pvk_source_comparison.png`
- 对照 `phase08_0429_dual_reference_pvk_source_comparison_metrics.csv` 判断 x=0.1 是否优于当前 PVK surrogate
- 输出提交前文件清单、关键图、比较报告路径与 commit 信息
