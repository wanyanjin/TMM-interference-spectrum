# CURRENT_TASK.md

## 当前任务
`Phase 09C-2：reflectance_qc GUI 原始光谱一键 QC 整改`

## 本轮目标
- 将 GUI 从 processed-only viewer 改为默认 Raw spectra QC。
- 让 GUI 通过 `run_reflectance_qc_workflow` 执行一键计算。
- 保留 processed viewer 作为辅助模式。

## 完成状态
- 已改为双模式：Raw spectra QC（默认）+ Processed result viewer。
- Raw 模式可输入 sample/reference、曝光、波段并触发 workflow。
- workflow 成功后 GUI 自动加载 `processed_reflectance.csv` 与 `qc_summary.json`。
- 增加 `Open Output Folder`（Windows）。

## 待办
1. 在依赖完整环境复跑 CLI smoke 与 GUI smoke。
2. 清理并提交 Phase 09C-2 相关文件。
