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

---

## 6. CLI 工具层数据流

标准方向：

```text
raw / processed input
  -> CLI 参数解析与输入验证
  -> core / workflow / storage
  -> data/processed 标准中间产物
  -> results/figures QA 图
  -> results/logs 或 results/report 摘要
  -> manifest-like summary
```

约束：

- CLI 不应绕开 `data/processed` 中间层直接做隐式内存串联。
- CLI 不应绕开 `results/figures`、`results/logs`、`results/report` 的结果目录规范。
- CLI 应将关键运行元信息写入 manifest 或 manifest-like summary，保证后续可追溯。

### 6.1 Phase 08 `reference-comparison` 实例

`test_data/0429/glass-PVK*.csv + glass-Ag*.csv`
-> `src/cli/reference_comparison.py` 参数解析与输入校验
-> `src/core/reference_comparison.py`（mask、TMM、厚度扫描、诊断）
-> `data/processed/phase08/reference_comparison/*.csv + manifest.json`
-> `results/figures/phase08/reference_comparison/*.png`
-> `results/logs/phase08/reference_comparison/*.md`
-> `results/report/phase08_reference_comparison/*.md`

### 6.2 Phase 08 dual-reference 实例（Ag + bk）

`test_data/0429/Ag-withoutfliter-20ms*.csv + bk-20ms*.csv`
-> `src/core/reference_comparison.py` 多帧读取（Frame/Wavelength/Pixel/Counts）
-> 按 `Pixel_Index` 对齐背景并扣除（Ag 使用帧 2-100，排除过曝第 1 帧）
-> 产出 `phase08_0429_ag_mirror_background_corrected.csv` 与 frame QC
-> 与 `glass-PVK*.csv + glass-Ag*.csv` 共同进入 dual-reference 对比
-> `phase08_0429_dual_reference_calibrated_reflectance.csv`
-> `phase08_0429_dual_reference_manifest.json`
-> `phase08_0429_dual_reference_report.md`

### 6.3 Phase 08 文献 `x=0.1` 替代 PVK 光学常数实例

`resources/1-s2.0-S0927024818304446-mmc1.docx`
-> `src/core/literature_x01_nk.py` 提取 `Table S3` 中 `FA0.9Cs0.1PbI3` 的 `Photon Energy / ε1 / ε2`
-> `resources/digitized/lit_x01_csfapi_epsilon_table_s3.csv`
-> `eps -> n/k` 转换
-> `resources/digitized/lit_x01_csfapi_nk_table_s3.csv`
-> 替换 `resources/aligned_full_stack_nk.csv` 中 `n_PVK/k_PVK`
-> `resources/aligned_full_stack_nk_phase08_x01.csv`
-> `src/cli/reference_comparison.py --nk-csv ... --output-tag pvk_x01`
-> `phase08_0429_dual_reference_*_pvk_x01.*`
-> `phase08_0429_dual_reference_pvk_source_comparison.png/.md`
