# CURRENT_TASK.md

## 当前任务

`Phase 08：参比几何验证与治理规范收敛`

目标：建立报告与可视化规范，重生成 Phase 08 单波长 trace 报告，并为下一步 `nk_audit` / `nk_envelope` 做准备。

## 本轮范围

- 新增项目级报告与绘图规范文档
- 在稳定宪法中补充简短交付红线
- 重构单波长 trace 报告模板，不改主计算逻辑
- 重生成 `600 nm` trace Markdown/JSON 并保持数值不变

不在本轮范围：

- 不修改 TMM / HDR / Phase 07 业务代码
- 不批量重绘历史图
- 不迁移原始数据或历史结果目录
- 不引入新依赖

## TODO

1. 新增 `docs/REPORTING_AND_FIGURE_STYLE.md`
2. 重生成 `phase08_0429_trace_600nm.md`，改为 LaTeX 公式、状态表和表格化结果
3. 为下一步 `nk_audit` 与 `nk_envelope` 保留清晰的 trace 报告模板

## 阻塞与注意事项

- 工作区存在无关未提交改动（`docs/PROJECT_STATE.md`、`src/scripts/stepD2b_explain_feature_pipeline.py`、`results/report/...`），本轮不得纳入提交。
- `test_data/0429` 无 `.spe`，曝光时间仅来自文件名推断，必须在 trace 报告中保留该约束。
- 新报告不得使用绝对路径，不得把长帧列表直接塞进主文。

## 立即下一步

- 建立报告与可视化规范
- 重生成 `600 nm` 单波长 trace 报告
- 下一步准备 `nk_audit` 与 `nk_envelope`，验证 PVK / Ag `n,k` 数据的适用性
