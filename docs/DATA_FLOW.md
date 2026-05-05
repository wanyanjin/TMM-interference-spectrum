# DATA_FLOW.md

本文档描述当前仓库中可证实的数据链路与 I/O 合约，重点覆盖绝对反射率、HDR、TMM 拟合输入与输出。

---

## 1. 数据层分工

- `data/raw/`：规范目标中的原始数据层（当前仓库尚未完全落地）
- `test_data/`：当前主要本地测试夹具与部分历史原始样本入口
- `data/processed/`：标准中间数据层（跨脚本共享）
- `results/figures/`：图表结果
- `results/logs/`：日志与摘要
- `results/report/`：汇报层精选资产

---

## 2. 基础链路（绝对反射率 -> 反演）

### 2.1 Phase 01 标定链

- 脚本：`src/scripts/step01_absolute_calibration.py`
- 典型输入：
  - `test_data/sample.csv`
  - `test_data/Ag-mirro.csv`
  - `resources/GCC-1022系列xlsx.xlsx`
- 典型输出：
  - `data/processed/target_reflectance.csv`
  - `results/figures/absolute_reflectance_interference.png`

### 2.2 Phase 02 外推与反演链

- 脚本：
  - `src/scripts/step01b_cauchy_extrapolation.py`
  - `src/scripts/step02_tmm_inversion.py`
- 关键中间件：
  - `data/processed/CsFAPI_nk_extended.csv`
- 关键资源：
  - `resources/ITO_20 Ohm_105 nm_e1e2.mat`
- 典型输出：
  - `results/figures/tmm_inversion_result.png`

---

## 3. HDR 与双窗拟合链路

### 3.1 HDR 绝对标定（Phase 06）

- 核心模块：`src/core/hdr_absolute_calibration.py`
- 入口脚本：
  - `src/scripts/step06_single_sample_hdr_absolute_calibration.py`
  - `src/scripts/step06_batch_hdr_calibration.py`
- 典型输出：
  - `data/processed/phase06_batch/*_curve_table.csv`
  - `data/processed/phase06_batch/phase06_batch_summary.csv`
  - `results/figures/phase06_batch/*_QA_plot.png`

### 3.2 双窗联合反演（Phase 07）

- 核心模块：`src/core/phase07_dual_window.py`
- 入口脚本：`src/scripts/step07_dual_window_inversion.py`
- 支持输入：
  - 原始多曝光 `*-cor.csv + .spe`（若存在）
  - `*_hdr_curves.csv`（已处理入口）
- 关键中间层：
  - `data/processed/phase07/fit_inputs/*_fit_input.csv`
  - `data/processed/phase07/phase07_source_manifest.csv`
- 结果层：
  - `data/processed/phase07/phase07_fit_summary.csv`
  - `data/processed/phase07/fit_results/*_fit_curve.csv`
  - `results/figures/phase07/*.png`
  - `results/logs/phase07/*_optimizer_log.md`

---

## 4. 理论重建与专题扫描链路

### 4.1 固定参数理论前向（Phase 08）

- 脚本：`src/scripts/step08_theoretical_tmm_modeling.py`
- 输入：
  - `data/processed/phase07/phase07_fit_summary.csv`
  - `data/processed/phase07/fit_inputs/*_fit_input.csv`
- 输出：
  - `data/processed/phase08/*`
  - `results/figures/phase08/*`
  - `results/logs/phase08/*`

### 4.2 Phase A-D 专题脚本链

- 脚本族：
  - `stepA*`、`stepB*`、`stepC*`、`stepD*`
- 输出主要落在：
  - `data/processed/phaseA*` 到 `phaseD*`
  - `results/figures/phaseA*` 到 `phaseD*`
  - `results/logs/phaseA*` 到 `phaseD*`
  - `results/report/phase*`

---

## 5. I/O 合约最低要求

每个脚本应至少明确：

- 输入文件路径
- 输出文件路径
- 依赖资源文件
- 前序中间产物
- 运行后产物清单

跨脚本共享数据必须优先落在 `data/processed/`，禁止仅依赖会话状态。

