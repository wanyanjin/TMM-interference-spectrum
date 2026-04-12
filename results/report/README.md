# Report Asset Index

`results/report/` 是本项目的长期汇报资产层，用于沉淀每个关键阶段最值得展示和复盘的精选结果。这里保留的是适合组会、阶段总结和对外沟通的资产，而不是全部中间文件。

## Directory Index

### `phaseA1_2_pvk_surrogate_and_pristine/`

- 主题：`PVK surrogate v2` 重建、`~750 nm` seam 修复、pristine baseline rerun
- 主要内容：
  - 修复后的全栈 `n-k` 表
  - v1/v2 局部对照图和 pristine baseline 对照图
  - seam、平滑性、fringe 保真度的关键指标表
  - 可直接用于汇报的阶段总结文档 `PHASE_A1_2_REPORT.md`

### `phaseA2_pvk_thickness_scan/`

- 主题：基于 `PVK surrogate v2` 的 `d_PVK` 厚度扫描
- 主要内容：
  - 厚度扫描主表与特征汇总表
  - `R_stack / R_total / ΔR` 热力图
  - 后窗 peak/valley tracking 与代表厚度曲线
  - 可直接用于汇报的阶段总结文档 `PHASE_A2_REPORT.md`

## Usage Rule

- 标准分析输出仍以 `data/processed/`、`results/figures/`、`results/logs/` 为准。
- `results/report/` 只存放精选资产，不替代原始结果层。
- 每个阶段目录至少应包含：
  - 关键图表
  - 关键 CSV / 数据表
  - 一份详细 Markdown 报告
  - 必要时的 manifest / README / 指标摘要
- 新阶段完成后，必须同步更新本索引。

### `phaseB1_rear_bema_sandbox/`

- 主题：rear-only `PVK/C60` Bruggeman 粗糙层前向模拟
- 主要内容：
  - rear-BEMA 扫描主表与特征汇总表
  - `R / ΔR` 热力图、代表曲线、peak/valley tracking
  - rear-BEMA 与 `d_PVK` 指纹的正交对照图
  - 可直接用于汇报的阶段总结文档 `PHASE_B1_REPORT.md`

### `phaseA2_1_pvk_uncertainty_ensemble/`

- 主题：`PVK surrogate v2` 的 band-edge uncertainty ensemble 及其对 thickness / rear-BEMA 机制的传播
- 主要内容：
  - ensemble manifest 与局部 `n/k/eps` 对照
  - thickness 与 rear-BEMA 的 ensemble robustness summary
  - “robust features vs surrogate-sensitive features” 总结矩阵
  - 可直接用于汇报的阶段总结文档 `PHASE_A2_1_REPORT.md`

### `phaseB2_front_bema_sandbox/`

- 主题：front-only `NiOx/PVK` proxy BEMA 前向模拟
- 主要内容：
  - front-BEMA 主扫描表与特征汇总表
  - 前窗/过渡区重点图、热力图与代表曲线
  - front vs rear vs thickness 的正交对照图
  - uncertainty spot-check 与阶段总结文档 `PHASE_B2_REPORT.md`
