# CURRENT_TASK.md

## 当前任务

`Phase 08：参比几何验证与治理规范收敛`

目标：已完成文献 `FA0.9Cs0.1PbI3` (`x=0.1`) 介电函数表提取、Phase 08 专用 PVK `n/k` 替代表生成，以及与当前 PVK 来源在 `glass/Ag` / `Ag mirror` 双参比链路下的并排比较；当前待审查结果并决定是否继续把该来源用于后续诊断。

## 本轮范围

- 提取 `Table S3 x=0.1` 的 `ε1/ε2` 并生成 `n/k`
- 生成 `resources/aligned_full_stack_nk_phase08_x01.csv`
- 用 `current_pvk` 与 `pvk_x01` 两套 `nk` 完成双参比重算
- 输出 `phase08_0429_dual_reference_pvk_source_comparison.png/.md/.csv`
- 新增单波长 trace 审计脚本，展开 600 nm 附近的 counts / TMM / 级联全过程
- 同步更新文献地图、CLI 文档、数据流与历史摘要

不在本轮范围：

- 不修改 TMM/HDR/Phase 07 业务代码
- 不全局替换其他 Phase 的默认 PVK `n-k` 表
- 不迁移原始数据或历史结果目录
- 不引入新依赖

## TODO

1. 审查 `phase08_0429_trace_600nm.md`，确认手写公式与 CSV/TMM 一致性
2. 判断实验-理论偏差主要来自公式链路还是实验/参比链路
3. 仅暂存本任务文件，提交并 push：`[Phase 08] 新增单波长反射率链路审计脚本`

## 阻塞与注意事项

- 工作区存在无关未提交改动（`docs/PROJECT_STATE.md`、`src/scripts/stepD2b_explain_feature_pipeline.py`、`results/report/...`），本轮不得纳入提交。
- `test_data/0429` 无 `.spe`，曝光时间仅来自文件名推断，必须在 manifest/report 标注。
- `Table S3` 在 docx 中以固定宽度字符串出现，提取时必须避免把 `x=0.2` 段落混入 `x=0.1`。
- 不得覆盖当前未带 tag 的 Phase 08 结果；新运行必须使用 `--output-tag`。

## 立即下一步

- 运行 `step08_single_wavelength_trace.py --target-wavelength-nm 600 --output-tag 600nm`
- 审查 trace JSON/Markdown 中的公式展开与一致性检查
- 输出审计报告路径、JSON 路径、发现的问题与 commit 信息
