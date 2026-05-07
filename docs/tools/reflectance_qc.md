# reflectance_qc

## 工具定位

`reflectance_qc` 是 Phase 09B 落地的第一个正式小工具，用于显微反射谱 sample/reference 现场 QC。

## 适用场景

- 快速检查一次采谱结果是否存在明显异常
- 在进入更昂贵的建模、反演、报告流程前做初筛
- 为后续 GUI 提供稳定 workflow / CLI 基础

## 状态

- 当前状态：`experimental`
- Phase：`Phase 09B`

## 输入

- sample 光谱 CSV/TXT
- reference 光谱 CSV/TXT
- 可选曝光时间
- 可选波长裁剪范围

## 输出

- `processed_reflectance.csv`
- `qc_summary.json`
- `qc_report.md`

## 核心数据模型

- `domain.spectrum.SpectrumData`
- `domain.reflectance.ReflectanceQCConfig`
- `domain.reflectance.ReflectanceQCResult`
- `domain.qc.QCSummary`
- `domain.run_manifest.ToolRunManifest`

## core 接口

- `core.reflectance_qc.align_spectra_to_common_grid(...)`
- `core.reflectance_qc.compute_reflectance_qc(...)`

## workflow 接口

- `workflows.reflectance_qc_workflow.ReflectanceQCWorkflowConfig`
- `workflows.reflectance_qc_workflow.run_reflectance_qc_workflow(...)`

## CLI 入口

- `python src/cli/reflectance_qc.py ...`

## GUI 入口

- 本轮不实现 GUI
- 下一轮可在 `src/gui/reflectance_qc/` 上层调用 workflow

## 测试要求

- CSV reader 单元测试
- core QC 单元测试
- workflow 集成测试
- CLI 集成测试
- 真实 `test_data/phase09` smoke test

## 文档要求

- `docs/cli/reflectance_qc.md`
- `docs/tools/reflectance_qc.md`
- `docs/tools/TOOL_REGISTRY.md`
- `docs/CLI_INDEX.md`

## 已知限制

- 只支持最小 CSV/TXT adapter
- 未实现 H5/Zarr
- 未实现 GUI
- 未实现 dark subtraction
- 默认 reference reflectance 为 unity

## 验收标准

- CLI 可运行
- workflow 输出完整 CSV/JSON/Markdown
- 核心逻辑在 `core`，文件读写只在 `storage`
- 真实测试数据 smoke 可完成一轮输出
