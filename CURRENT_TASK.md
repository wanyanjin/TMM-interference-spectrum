# CURRENT_TASK.md

## 当前任务

`Phase 08：参比几何验证与治理规范收敛`

目标：实现 `glass/PVK` 与 `glass/Ag` 参比校准/TMM 对比 CLI 最小闭环，并完成文档与测试同步。

## 本轮范围

- 新增 `src/core/reference_comparison.py`
- 新增 `src/cli/reference_comparison.py`
- 新增最小测试：列识别、公式、mask、TMM smoke、CLI dry-run
- 更新 `docs/CLI_INDEX.md` 与 `docs/cli/reference_comparison.md`
- 产出 `phase08/reference_comparison` 数据表、图表、日志、报告

不在本轮范围：

- 不修改 TMM/HDR/Phase 07 业务代码
- 不修改材料 `n-k` 表
- 不迁移原始数据或历史结果目录
- 不引入新依赖

## TODO

1. 完成 CLI 计算链与严格 mask 输出
2. 生成主波段（400-750 nm）与扩展 QC（750-931.443 nm）指标
3. 完成最小测试并记录结果
4. 仅暂存本任务文件，提交并 push：`[Phase 08] 新增glassAg参比校准与TMM对比CLI`

## 阻塞与注意事项

- 工作区存在无关未提交改动（`docs/PROJECT_STATE.md`、`src/scripts/stepD2b_explain_feature_pipeline.py`、`results/report/...`），本轮不得纳入提交。
- `test_data/0429` 无 `.spe`，曝光时间仅来自文件名推断，必须在 manifest/report 标注。

## 立即下一步

- 完成 CLI dry-run 与 full-run 验证
- 复核主结论仅基于 400-750 nm strict mask
- 输出提交前文件清单、指标摘要与关键图路径
