# CHANGELOG_DIGEST.md

## Phase 09
- 建立工具平台架构文档、core 沙箱规则与最小骨架。

## Phase 09B
- 实现 `reflectance_qc` 最小 CLI + workflow 闭环。

## Phase 09C-1
- 实现 GUI MVP（以 processed 结果查看为主）。

## Phase 09C-2
- 修正 GUI 产品方向：默认改为 Raw sample/reference 一键 QC。
- GUI 通过 `run_reflectance_qc_workflow` 执行计算，禁止 GUI 重写 core 逻辑。
- 保留 processed result viewer 作为辅助模式。
- 新增 `Open Output Folder`，并保持 GUI 导出到受控目录。
