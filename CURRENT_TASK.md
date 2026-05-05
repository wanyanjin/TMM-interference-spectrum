# CURRENT_TASK.md

## 当前任务

`Phase 08：参比几何验证与治理规范收敛`

目标：实现 `Ag mirror + bk` 校准与 `glass/Ag` 双参比 `glass/PVK` 反射率/TMM 对比 CLI，并完成文档与测试同步。

## 本轮范围

- 扩展 `src/core/reference_comparison.py`：Ag/bk 多帧读取、pixel 对齐背景扣除、双参比输出
- 扩展 `src/cli/reference_comparison.py`：dual-reference 参数与图表/报告
- 扩展测试：多帧列识别、Ag 帧过滤、pixel 对齐、dual dry-run
- 更新 `docs/CLI_INDEX.md`、`docs/cli/reference_comparison.md`、`docs/DATA_FLOW.md`
- 产出 dual-reference 数据表、图表、日志、报告

不在本轮范围：

- 不修改 TMM/HDR/Phase 07 业务代码
- 不修改材料 `n-k` 表
- 不迁移原始数据或历史结果目录
- 不引入新依赖

## TODO

1. 完成 Ag/bk 校准并输出 Ag mirror 单谱与 frame QC
2. 完成 dual-reference 反射率/TMM 对比并输出报告
3. 完成扩展测试并记录结果
4. 仅暂存本任务文件，提交并 push：`[Phase 08] 新增Ag镜与glassAg双参比对比CLI`

## 阻塞与注意事项

- 工作区存在无关未提交改动（`docs/PROJECT_STATE.md`、`src/scripts/stepD2b_explain_feature_pipeline.py`、`results/report/...`），本轮不得纳入提交。
- `test_data/0429` 无 `.spe`，曝光时间仅来自文件名推断，必须在 manifest/report 标注。
- Ag 与 bk 第三列波长不一致，必须按第五列 pixel 对齐，不能按波长直接相减。

## 立即下一步

- 完成 dual-reference dry-run 与 full-run 验证
- 复核主审查图范围 500-750 nm 且 y 轴自适应
- 输出提交前文件清单、指标摘要与关键图路径
