# CURRENT_TASK.md

## 当前任务

`Phase 09B：reflectance_qc 最小 workflow + CLI 闭环`

目标：在 Phase 09 架构骨架上实现第一个正式小工具 `reflectance_qc` 的最小非 GUI 闭环：CSV/TXT 读取、`SpectrumData` 转换、core QC 计算、workflow 编排、CLI 入口，以及 processed CSV、summary JSON、Markdown report 输出。

## 本轮范围

- 新增 `reflectance_qc` domain/core/storage/workflow/cli 最小实现
- 新增 CSV/TXT reader 与 QC writer
- 新增 `reflectance_qc` 单元测试与集成测试
- 使用 `test_data/phase09` 进行一次真实 smoke test
- 更新 CLI 文档、工具文档、状态与技术债文档

不在本轮范围：

- 不实现 GUI
- 不实现 H5/Zarr reader
- 不做 TMM 拟合
- 不做 Ag->Si 或 glassAg->glass 参比修正
- 不迁移旧脚本
- 不修改 Phase 08 主计算逻辑与结果

## TODO

1. 完成 `reflectance_qc` 最小实现
2. 建立 reader/core/workflow/cli 测试
3. 完成真实测试数据 smoke
4. 更新文档与 registry
5. 提交并 push

## 完成状态

- 本轮已明确为独立的 Phase 09B 工具闭环任务
- 本轮只实现最小非 GUI 闭环，不宣称已实现正式 GUI 或复杂参比物理修正

## 下一步建议

- 补充真实参比反射率模型与更严格的 reference conversion
- 增加 H5/Zarr/LightField reader adapter
- 再进入 PySide6 + pyqtgraph GUI 实现
