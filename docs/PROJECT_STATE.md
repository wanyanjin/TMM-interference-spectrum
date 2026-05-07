# PROJECT_STATE.md

## Current Snapshot
- Date: 2026-05-07
- Phase: Phase 09C-2
- Focus: `reflectance_qc` GUI 从结果查看器整改为原始光谱一键 QC 工具。

## reflectance_qc 当前能力
- CLI: `src/cli/reflectance_qc.py`
- Workflow: `src/workflows/reflectance_qc_workflow.py`
- Core: `src/core/reflectance_qc.py`
- GUI: `src/gui/reflectance_qc/app.py`

## GUI 当前模式
1. Raw spectra QC（默认）
  - 输入 sample/reference raw CSV
  - 配置曝光与波段
  - 调用 workflow
  - 自动加载 workflow 输出并展示
2. Processed result viewer（辅助）
  - 加载历史 `processed_reflectance.csv` / `qc_summary.json`

## 输出路径
- Workflow 输出：
  - `data/processed/phase09/reflectance_qc/<run_id>/`
  - `results/report/phase09_reflectance_qc/<run_id>/`
- GUI 导出：
  - `results/gui_exports/reflectance_qc/<run_id>/`

## 已知边界
- GUI 不做 TMM 拟合，不改写 core 反射率计算。
- 仍仅支持 CSV/TXT reader，不支持 H5/Zarr。
