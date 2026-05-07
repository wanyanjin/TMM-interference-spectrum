# reflectance_qc GUI（Phase 09C-2）

## 定位
- GUI 提供两种模式：
1. Raw spectra QC（默认主模式）
2. Processed result viewer（历史结果查看）
- GUI 不实现核心反射率计算，只调用 workflow。

## 模式 1：Raw spectra QC（默认）
步骤：
1. Load Sample CSV
2. Load Reference CSV
3. 输入 `Sample exposure ms` 与 `Reference exposure ms`
4. 选择波长范围（Full / 400-750 / 500-700 / Custom）
5. 勾选 `Exposure normalize`（可选）
6. 点击 `Run QC`
7. 查看反射率曲线与 QC 面板
8. 点击 `Open Output Folder` 或 `Export Current View`

运行链路：
`sample/reference raw CSV -> workflow -> processed_reflectance.csv + qc_summary.json + qc_report.md -> GUI 自动加载`

## 模式 2：Processed result viewer
- 可手动加载 `processed_reflectance.csv`
- 可选加载 `qc_summary.json`
- 用于历史结果复盘，不是默认现场入口

## 可视化能力
- 视图：Calculated reflectance / Sample-reference ratio / Sample intensity processed / Reference intensity processed
- 默认 X 范围：500–700 nm
- Y 模式：Robust auto / Full auto / Physical / Manual
- 异常点高亮：`NaN/Inf`、`valid_mask=False`、`R<0`、`R>1.2` 等
- Full-range QC 与 Current-window QC 同时展示

## 导出能力
- `results/gui_exports/reflectance_qc/<run_id>/view_settings.json`
- `results/gui_exports/reflectance_qc/<run_id>/gui_qc_summary.json`
- `results/gui_exports/reflectance_qc/<run_id>/current_view.png`（best effort）

## 已知限制
- 当前不是完整 TMM 拟合 GUI。
- 不支持 H5/Zarr 输入。
- 未实现复杂后台任务进度，仅做最小运行状态提示。
