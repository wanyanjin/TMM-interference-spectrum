# CURRENT_TASK.md

## 当前任务

`Phase 08：强化根目录生成物路径治理规则`

目标：建立项目级“根目录零污染”约束，清理现有 pytest 临时/缓存目录，补强 `.gitignore`，并把正式产物、临时产物与测试夹具的路径分流规则写入记忆文档与数据流文档。

## 本轮范围

- 更新 `AGENTS.md`，新增生成物路径治理与根目录零污染规则
- 更新 `.gitignore`，覆盖 pytest/cache/tmp/debug/export 产物
- 清理根目录现有 `.pytest-tmp*` 与 `pytest-cache-files-*`
- 必要时补充 `docs/DATA_FLOW.md`、`docs/PROJECT_STATE.md`、`CHANGELOG_DIGEST.md`
- 检查测试与脚本是否仍会默认写入根目录
- 完成后执行 `git status --short`、测试、提交并 push

不在本轮范围：

- 不改业务物理模型
- 不做 GUI / CLI 新功能
- 不迁移既有正式结果目录结构，除非发现根目录污染必须回收

## TODO

1. 完成文档与 `.gitignore` 更新
2. 清理现有根目录缓存/临时目录
3. 复查测试与脚本的输出路径约定
4. 跑验证并提交 push

## 完成状态

- 当前任务聚焦于仓库治理与输出路径约束，不涉及模型与算法变更
- 以 root zero pollution 为检查重点
- 目前已完成规则与忽略项更新，并清掉部分根目录生成物；剩余少量 `.pytest-tmp` / `pytest-cache-files-*` 目录受 Windows ACL 限制，仍需后续在具备权限的环境中继续清理

## 下一步建议

- 若后续新增工具生成新的产物类型，先登记目录再实现输出
- 保持测试、CLI、GUI、workflow 默认输出到受控目录，不得落根目录
