# CURRENT_TASK.md

## 当前任务

`Phase 08：参比几何验证与治理规范收敛`

目标：完善项目治理规范，为下一步 `glass/PVK` 与 `glass/Ag`、`Ag mirror` 两类参比反射率比较任务做准备。

## 本轮范围

- 重构 `AGENTS.md`（稳定规则与红线）
- 新增 `CHANGELOG_DIGEST.md`
- 新增 `docs/DATA_FLOW.md`
- 新增 `docs/KNOWN_ISSUES.md`
- 新增 `docs/phases/phase_governance_refactor.md`

不在本轮范围：

- 不修改 TMM/HDR/Phase 07 业务代码
- 不修改材料 `n-k` 表
- 不迁移原始数据或历史结果目录
- 不引入新依赖

## TODO

1. 完成治理文档新增与重构
2. 检查历史条目证据边界，证据不足内容移入“待核对”
3. 仅暂存治理文档，隔离无关未提交改动
4. 提交并 push：`[Phase 08] 完善项目治理规范并准备参比比较流程`

## 阻塞与注意事项

- 工作区存在无关未提交改动（`docs/PROJECT_STATE.md`、`src/scripts/stepD2b_explain_feature_pipeline.py`、`results/report/...`），本轮不得纳入提交。
- `results/report/` 为当前实际目录名；本轮只在规范中声明现状，不做目录改名。

## 立即下一步

开始执行文档一致性检查，生成提交候选文件清单并展示 `git status --short` 与 `git diff --stat`。

