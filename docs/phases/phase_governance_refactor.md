# phase_governance_refactor.md

## Phase 标识

`Phase 08：参比几何验证与治理规范收敛`

## 目的

为下一步 `glass/PVK` 与 `glass/Ag`、`Ag mirror` 两类参比反射率比较任务提供稳定治理层，降低多机协作与多阶段迭代中的上下文漂移风险。

## 本次改动范围

1. 重构 `AGENTS.md` 为稳定宪法（规则、红线、执行纪律）
2. 新增 `CURRENT_TASK.md`（当前活动记忆）
3. 新增 `CHANGELOG_DIGEST.md`（可证实历史摘要）
4. 新增 `docs/DATA_FLOW.md`（数据链路与 I/O 合约）
5. 新增 `docs/KNOWN_ISSUES.md`（结构债务与科学风险）

## 明确不改动项

1. 不修改 TMM 计算逻辑
2. 不修改 HDR 标定逻辑
3. 不修改 Phase 07 双窗反演逻辑
4. 不修改材料 `n-k` 数据表
5. 不迁移原始/历史结果数据
6. 不引入新依赖

## 历史证据策略

- `CHANGELOG_DIGEST.md` 仅写可由 `git log`、已跟踪文件、`docs/PROJECT_STATE.md`、仓库现有结果目录证实的条目。
- 证据不足或语义不确定内容转入 `docs/KNOWN_ISSUES.md` 的“待核对”区。

## 验证方式

1. `git diff --stat`
2. `git status --short`
3. 展示拟提交文件清单，确认仅包含治理文档
4. 确认未纳入无关未提交改动（脚本、report 资产、`.DS_Store`、`__pycache__`）

