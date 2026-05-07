# CURRENT_TASK.md

## 当前任务

`Phase 09：工具平台架构规范与 core 沙箱骨架`

目标：建立正式工具平台架构文档、升级 `AGENTS.md` 开发规则、明确 core 沙箱与输入 adapter 规则、确定 `PySide6 + pyqtgraph` GUI 技术路线，并新增最小代码骨架与测试骨架。

## 本轮范围

- 新增 `docs/architecture/` 与 `docs/tools/` 文档
- 新增 `src/common/`、`src/domain/`、`src/storage/`、`src/workflows/`、`src/visualization/`、`src/gui/common/` 骨架
- 新增最小 domain / registry / reader protocol / writer protocol
- 新增最小单元测试并运行 `pytest -q`
- 更新 `AGENTS.md`、`CHANGELOG_DIGEST.md`、`docs/PROJECT_STATE.md`、`docs/DATA_FLOW.md`、`docs/KNOWN_ISSUES.md`

不在本轮范围：

- 不实现完整 `reflectance_qc` GUI
- 不实现完整 CSV/H5/Zarr reader
- 不重构旧 `src/scripts/step*.py`
- 不修改 Phase 08 主计算逻辑
- 不重算任何实验结果
- 不修改 `results/slides/phase08_reference_audit/`

## TODO

1. 完成正式工具平台架构文档
2. 追加 AGENTS 规则
3. 建立最小骨架代码
4. 建立最小测试骨架并跑通
5. 更新状态与技术债文档
6. 提交并 push

## 完成状态

- 本轮已明确为独立的 Phase 09 架构治理任务
- 本轮只建立规范与最小骨架，不宣称已实现具体 GUI 工具

## 下一步建议

- 先 formalize 一个最小 `reflectance_qc` workflow
- 再补正式 CSV reader 与 GUI view model
- 最后再进入具体 GUI 业务实现
