# PROJECT_STATE.md

本文件用于持续同步 `TMM-interference-spectrum` 项目的当前状态，是后续 AI Agent 和架构师恢复上下文的首要入口。

## 1. Current Snapshot

- 更新时间：2026-04-10
- 当前判断 Phase：`Phase 06`
- 阶段定义：`单样本 Bit-Agnostic HDR 拼接与银镜绝对反射率校准 Dry Run，验证重复求均值 + HDR 融合 + 厂家银镜校准链路`
- 当前可用能力：
  - 已有 `step01_absolute_calibration.py`，可将样品与银镜原始计数转换为绝对反射率
  - 已有 `step01b_cauchy_extrapolation.py`，可基于 [LIT-0001] 的 `ITO/CsFAPI` 数字化折射率曲线生成 `750-1100 nm` 的 CsFAPI 扩展 `n-k` 中间件
  - 已有 `step02_tmm_inversion.py`，可读取目标反射率、ITO 色散和 CsFAPI 扩展 `n-k` 中间件，执行包含 50/50 BEMA 粗糙度、ITO 色散吸收补偿、宏观厚度不均匀性高斯平均、PVK 色散斜率扰动与 NiOx 寄生吸收的六参数 `d_bulk + d_rough + ito_alpha + sigma_thickness + pvk_b_scale + niox_k` 联合反演
  - 已有 `step03_batch_fit_samples.py`，可对 OneDrive 原始样品目录中的多位置 CSV 做统一绝对反射率校准、六参数批量拟合、单样品图导出和汇总表生成
  - 已有 `step03_forward_simulation.py`，可固化 Phase 03 六参数最优基线，在 `850-1500 nm` 波段前向预测 `SAM/PVK` 界面空气隙对绝对反射率 `R` 与差分反射率 `ΔR` 的影响
  - 已有 `step04a_air_gap_diagnostic.py`，可基于 `test_data/good-21.csv` 与 `test_data/bad-23.csv` 完成绝对反射率标定、6 参数/7 参数对比拟合、差分指纹比对与空气隙收敛诊断
  - 已有 `step04b_air_gap_localization.py`，可基于 `test_data/good-21.csv` 与 `test_data/bad-20-2.csv` 完成空气隙空间定位对比与材料参数弛豫诊断
  - 已新增 `src/core/hdr_absolute_calibration.py`，可扫描 OneDrive 测试目录、从 `.spe` 元数据提取曝光时间、对重复采集做均值提纯、执行 Bit-Agnostic Cross-fade HDR 融合，并导出绝对反射率 QA 图/表
  - 已新增 `step06_single_sample_hdr_absolute_calibration.py`，可对 `DEVICE-1-withAg` 与对应 `Ag_mirro` 组执行单样本 HDR Dry Run，输出到系统临时目录
  - 已有 `diagnostics_shape_mismatch.py`，可在独立沙盒中对 ITO 近红外吸收、厚度不均匀性和 PVK 色散斜率做形状畸变诊断
  - 已有 `step02_digitize_fapi_optical_constants.py`，可从 `LIT-0001` 的 Fig. 2 原图数字化提取 FAPI 的 `n/κ` 曲线并输出 QA 图
  - 已有 `step02_digitize_csfapi_optical_constants.py`，可从 `LIT-0001` 的 Fig. 3 原图数字化提取 CsFAPI 的 `n/κ` 曲线并输出 QA 图
  - 已有 `step05_parse_ellipsometry_markdown.py`，可从 `resources/n-kdata/*/full.md` 解析椭偏报告并构建 `materials_master_db.json`
  - 已有 `step05b_verify_against_pdf.py`，可用原始 PDF 交叉验证材料数据库中的厚度、RMSE、波段范围与模型完整性
  - 已有 `step05c_build_aligned_nk_stack.py`，可生成 `400-1100 nm / 1 nm` 的全栈对齐 `n-k` 表 `aligned_full_stack_nk.csv`
  - 已有 `src/core/full_stack_microcavity.py`，可基于 `aligned_full_stack_nk.csv` 构建 `Baseline / Case A / Case B / Front / Back` 五类全器件微腔堆栈，并暴露 `forward_model_for_fitting()` 作为后续 LM 目标函数入口
  - 已有 `step06_dual_mode_microcavity_sandbox.py`，可扫描 `d_air = 0-50 nm`，输出双模式 `R / ΔR` 指纹字典、40 nm 对比图和 2D 雷达热力图
  - 已有 `step07_orthogonal_radar_and_baseline.py`，可输出 pristine 全谱三分区基准图、Front/Back 正交雷达图与 `Phase 07` 指纹字典
  - 已产出标准中间文件 `data/processed/target_reflectance.csv` 与 `data/processed/CsFAPI_nk_extended.csv`
  - 已完成 Phase 02 形状畸变诊断，当前证据指向：ITO 近红外吸收失真是长波端托平与整体形状失配的主导因素
  - 已完成 Phase 04 空气隙前向预测，当前基线下 `d_air = 2 nm` 与 `5 nm` 的 `max(|ΔR|)` 分别约为 `0.538%` 与 `1.347%`，均高于 `0.2%` 典型噪声线
  - 已完成 Phase 04a 空气隙诊断沙盒：在 `bad-23` 上加入 `d_air` 后，`chi-square` 由 `0.03197` 降至 `0.01619`，`d_air` 收敛到约 `39.9 nm`，但仍未低于 `0.01`
  - 已完成 Phase 04b 空气隙空间定位：对 `bad-20-2` 的 L1/L2/L3 三个 7 参数模型中，L3 (`SAM/PVK`) 的 `chi-square` 最低，但材料参数锁死时仍未优于 6 参数基线；释放材料参数后 `chi-square` 可进一步降至 `0.01932`
  - 已完成 Phase 06 单样本 HDR Dry Run：对 `DEVICE-1-withAg` 的 `150 ms / 2000 ms` 三重复和 `Ag_mirro` 的 `500 us / 10 ms` 单重复完成均值提纯、HDR 融合和绝对校准
  - 已确认当前实测窗口仅覆盖 `498.934-1055.460 nm`，未外推到 `400-498.934 nm` 或 `1055.460-1100 nm`
  - 已确认 `850-1055 nm` 区间的样品与银镜都几乎完全信任长曝光，因此近红外区并非本次 HDR 拼接主战场
  - 已明确暴露银镜短曝光异常：按 `.spe` 元数据的真实曝光时间归一化后，`Ag_mirro-500us` 相对 `Ag_mirro-10ms` 的 `Counts/ms` 比值中位数约为 `12.28`
- 当前未完成内容：
  - 尚未把历史目录完全迁移到 `AGENTS.md` 规定的新结构
  - 尚未形成规范化的 Phase 日志、资源索引和结构化结果台账
  - 尚未把 Phase 06 的单样本 HDR 逻辑扩展到批量样品或规范化 `data/raw/` 目录

## 2. Current Directory Tree

以下目录树基于当前仓库实际状态整理，仅保留关键层级和关键文件。

```text
TMM-interference-spectrum/
├── AGENTS.md
├── requirements.txt
├── docs/
│   ├── LITERATURE_MAP.md
│   └── PROJECT_STATE.md
├── src/
│   ├── core/
│   │   └── hdr_absolute_calibration.py
│   └── scripts/
│       ├── diagnostics_shape_mismatch.py
│       ├── step01_absolute_calibration.py
│       ├── step01b_cauchy_extrapolation.py
│       ├── step02_digitize_csfapi_optical_constants.py
│       ├── step02_digitize_fapi_optical_constants.py
│       ├── step02_tmm_inversion.py
│       ├── step03_batch_fit_samples.py
│       ├── step03_forward_simulation.py
│       ├── step04a_air_gap_diagnostic.py
│       ├── step04b_air_gap_localization.py
│       └── step06_single_sample_hdr_absolute_calibration.py
├── data/
│   └── processed/
│       ├── CsFAPI_nk_extended.csv
│       ├── phase03_batch_fit/
│       ├── phase04a/
│       ├── phase04b/
│       ├── phase04c/
│       ├── phase06/
│       ├── phase07/
│       └── target_reflectance.csv
├── resources/
│   ├── digitized/
│   │   ├── phase02_fig2_fapi_optical_constants_digitized.csv
│   │   └── phase02_fig3_csfapi_optical_constants_digitized.csv
│   ├── n-kdata/
│   ├── aligned_full_stack_nk.csv
│   ├── materials_master_db.json
│   ├── GCC-1022系列xlsx.xlsx
│   ├── ITO_20 Ohm_105 nm_e1e2.mat
│   ├── CsFAPI_TL_parameters_and_formulas.md
│   └── MinerU-0.13.1-arm64.dmg
├── results/
│   ├── figures/
│   │   ├── absolute_reflectance_interference.png
│   │   ├── cauchy_extrapolation_check.png
│   │   ├── diagnostic_shape_analysis.png
│   │   ├── phase03_batch_fit/
│   │   ├── phase02_fig2_fapi_optical_constants_digitized.png
│   │   ├── phase02_fig2_fapi_optical_constants_overlay.png
│   │   ├── phase02_fig3_csfapi_optical_constants_digitized.png
│   │   ├── phase02_fig3a_csfapi_optical_constants_overlay.png
│   │   ├── phase02_fig3b_csfapi_optical_constants_overlay.png
│   │   ├── phase04_air_gap_prediction.png
│   │   ├── phase04a_air_gap_diagnostic.png
│   │   ├── phase04b_localization.png
│   │   ├── phase04c_fingerprint_mapping.png
│   │   ├── phase06_dual_mode_delta_r_40nm_850_1100.png
│   │   ├── phase06_dual_mode_radar_map.png
│   │   ├── phase07_baseline_3zones.png
│   │   ├── phase07_orthogonal_radar.png
│   │   └── tmm_inversion_result.png
│   └── logs/
│       ├── phase03_batch_fit/
│       ├── phase04c_fingerprint_mapping.md
│       ├── phase04a_air_gap_diagnostic.md
│       ├── phase04b_localization.md
│       ├── phase06_dual_mode_microcavity_sandbox.md
│       ├── phase07_orthogonal_radar_diagnostic.md
│       ├── phase02_shape_diagnostic_report.md
│       ├── phase02_fig2_fapi_digitization_notes.md
│       └── phase02_fig3_csfapi_digitization_notes.md
├── test_data/
│   ├── sample.csv
│   ├── glass-1mm.csv
│   └── Ag-mirro.csv
└── reference/
    └── Khan.../...
```

## 3. Structure Compliance Notes

当前仓库与项目级 `AGENTS.md` 规范相比，存在以下结构偏差：

- `test_data/` 仍然承担原始测量数据目录职责，后续应迁移或重命名到 `data/raw/`
- `reference/` 目前存放论文拆解结果，按新规范更适合逐步并入 `resources/references/`
- `src/core/` 已开始建立，但 `step01/step02/step04` 的大量复用逻辑仍散落在 `src/scripts/`
- 项目根已有 `requirements.txt`，但仍缺正式 `README.md`

这些偏差当前不会阻断现有流程，但属于后续需要收敛的结构债务。

## 4. Script SOP

### 4.1 `step01_absolute_calibration.py`

- 文件位置：`src/scripts/step01_absolute_calibration.py`
- 主要职责：将样品和银镜测量计数转换为 `850-1100 nm` 波段的绝对反射率，并输出图表和标准中间 CSV

输入：
- `test_data/sample.csv`
  - 样品测量光谱
  - 约定曝光时间：100 ms
- `test_data/Ag-mirro.csv`
  - 银镜测量光谱
  - 约定曝光时间：25 ms
- `resources/GCC-1022系列xlsx.xlsx`
  - 厂家提供的银镜绝对反射率基准

核心处理流程：
- 自动识别 CSV 的波长列和强度列
- 截取 `850-1100 nm` 目标波段
- 对银镜信号按曝光时间做归一化
- 将厂家银镜基准插值到样品波长网格
- 计算绝对反射率：
  - `R_abs = (S_sample / S_mirror_norm) * R_mirror_ref`
- 对反射率曲线做 Savitzky-Golay 平滑

输出：
- `data/processed/target_reflectance.csv`
  - 关键列约定至少包含：
    - `Wavelength`
    - `R_smooth`
- `results/figures/absolute_reflectance_interference.png`

### 4.2 `step01b_cauchy_extrapolation.py`

- 文件位置：`src/scripts/step01b_cauchy_extrapolation.py`
- 主要职责：从 [LIT-0001] Fig. 3 的数字化 `ITO/CsFAPI` 折射率曲线中提取透明区，用 Cauchy 模型外推到 `1100 nm`，生成 step02 可直接消费的标准 `n-k` 中间件

输入：
- `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
  - [LIT-0001] Fig. 3 的数字化光学常数数据
  - 本步骤只使用 `series = ITO/CsFAPI` 且 `quantity = n` 的数据

当前模型假设：
- 只截取 `750-1000 nm` 的近红外透明区拟合 Cauchy 模型
- Cauchy 模型写作 `n(lambda) = A + B / (lambda_um^2)`
- 为保证数值稳定性，拟合时使用 `lambda_um = wavelength_nm / 1000`
- `750-1100 nm` 内统一强制 `k = 0`
- `1000-1100 nm` 为超出 [LIT-0001] 原始测量窗口的解析外推区

输出：
- `data/processed/CsFAPI_nk_extended.csv`
  - 列约定：
    - `Wavelength`
    - `n`
    - `k`
- `results/figures/cauchy_extrapolation_check.png`

### 4.3 `step02_tmm_inversion.py`

- 文件位置：`src/scripts/step02_tmm_inversion.py`
- 主要职责：读取 `step01` 输出的目标反射率、ITO 色散和 `step01b` 生成的 CsFAPI 扩展 `n-k` 中间件，执行包含 BEMA 表面粗糙度修正、ITO 色散吸收补偿、宏观厚度不均匀性高斯平均、PVK 色散斜率扰动与 NiOx 寄生吸收的六参数联合反演

输入：
- `data/processed/target_reflectance.csv`
  - 来自 `step01`
- `data/processed/CsFAPI_nk_extended.csv`
  - 来自 `step01b`
  - 用作 PVK 层在 `850-1100 nm` 的复折射率输入
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`
  - ITO 介电函数数据库
  - 脚本兼容两类情况：
    - MATLAB 可读 MAT
    - 实际为三列表格文本

当前模型假设：
- 波段：`850-1100 nm`
- 入射角：`0` 度
- 玻璃前表面按非相干处理
- 后侧薄膜堆栈按相干 TMM 处理
- ITO 厚度固定：`105 nm`
- NiOx 厚度固定：`20 nm`
- SAM 厚度固定：`2 nm`
- PVK 块体厚度 `d_bulk` 搜索范围：`400-500 nm`
- PVK 表面粗糙层厚度 `d_rough` 搜索范围：`0-100 nm`
- ITO 色散吸收参数 `ito_alpha` 搜索范围：`0.0-30.0`
- 宏观厚度不均匀性参数 `sigma_thickness` 搜索范围：`0.0-60.0 nm`
- PVK 色散斜率缩放参数 `pvk_b_scale` 搜索范围：`0.1-3.0`
- NiOx 近红外寄生吸收参数 `niox_k` 搜索范围：`0.0-0.5`
- PVK 采用 `step01b` 生成的 CsFAPI 扩展 `n-k` 中间件，并通过线性插值映射到目标波长网格
- 粗糙层采用 `50% PVK + 50% Air` 的 Bruggeman EMA 有效介质模型
- ITO 在进入 TMM 之前，锁定实部 `n` 不变，仅对虚部 `k` 施加锚定在 `850-1100 nm` 的二次增长色散吸收缩放
- 当 `sigma_thickness >= 0.1 nm` 时，对 `d_bulk` 在 `[-3σ, +3σ]` 上做 9 点离散高斯加权平均，以模拟光斑尺度内的宏观厚度不均匀性
- PVK 色散扰动以 `1000 nm` 为折射率锚点，仅对 `n(λ)-n(1000 nm)` 的变化量施加 `pvk_b_scale` 缩放
- NiOx 层在主流程中由固定实部 `2.1` 和可拟合虚部 `niox_k` 构成
- 相干层堆栈为：`Glass -> ITO -> NiOx -> SAM -> PVK_Bulk -> PVK_Roughness -> Air`

核心处理流程：
- 读取目标绝对反射率
- 读取 `step01b` 生成的 CsFAPI 扩展 `n-k` 表
- 解析 ITO 的 `e1/e2` 数据并转为 `n + ik`
- 构建 ITO 复折射率插值器
- 根据 `ito_alpha` 对 ITO 的消光系数 `k` 做长波增强的色散吸收放大
- 构建 PVK 复折射率插值器
- 根据 `pvk_b_scale` 扰动 PVK 的近红外色散斜率
- 根据扰动后的块体 PVK 复介电常数计算 50/50 BEMA 粗糙层复折射率
- 动态构建 `2.1 + i*niox_k` 的 NiOx 复折射率
- 计算宏观反射率：
  - 玻璃前表面菲涅尔反射
  - 玻璃后方包含粗糙层的薄膜堆栈相干 TMM
  - 若 `sigma_thickness` 非零，则对多个 `d_bulk` 采样点做高斯加权平均
  - 再按非相干强度级联公式合成总反射率
- 使用 `lmfit` 的 `leastsq` 做六参数联合反演
- 输出最佳拟合图

输出：
- `results/figures/tmm_inversion_result.png`
- 终端打印：
  - 拟合厚度
  - `chi-square`
  - 优化状态

### 4.4 `step02_digitize_fapi_optical_constants.py`

- 文件位置：`src/scripts/step02_digitize_fapi_optical_constants.py`
- 主要职责：从 `LIT-0001` 的 Fig. 2 原图中提取 FAPI 的折射率 `n` 与消光系数 `κ` 两个子图数据，并输出单一 CSV 与 QA 图

输出：
- `resources/digitized/phase02_fig2_fapi_optical_constants_digitized.csv`
- `results/figures/phase02_fig2_fapi_optical_constants_digitized.png`
- `results/figures/phase02_fig2_fapi_optical_constants_overlay.png`
- `results/logs/phase02_fig2_fapi_digitization_notes.md`

### 4.5 `step03_batch_fit_samples.py`

- 文件位置：`src/scripts/step03_batch_fit_samples.py`
- 主要职责：对 OneDrive 原始样品目录中的多位置 CSV 逐文件执行绝对反射率校准、六参数拟合、单样品图导出和汇总表生成

输入：
- `/Users/luxin/Library/CloudStorage/OneDrive-共享的库-onedrive/Data/PL/2026/0403/cor/data-0403/*.csv`
- `test_data/Ag-mirro.csv`
- `resources/GCC-1022系列xlsx.xlsx`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`
- `data/processed/CsFAPI_nk_extended.csv`

输出：
- `results/figures/phase03_batch_fit/*.png`
- `data/processed/phase03_batch_fit/*.csv`
- `results/logs/phase03_batch_fit/phase03_batch_fit_summary.csv`
- `results/logs/phase03_batch_fit/phase03_batch_fit_pivot.csv`
- `/Users/luxin/Library/CloudStorage/OneDrive-共享的库-onedrive/Data/PL/2026/0403/cor/data-0403/batch-fit-results/...`

### 4.6 `step02_digitize_csfapi_optical_constants.py`

- 文件位置：`src/scripts/step02_digitize_csfapi_optical_constants.py`
- 主要职责：从 `LIT-0001` 的 Fig. 3 原图中提取 CsFAPI 的折射率 `n` 与消光系数 `κ` 两个子图数据，并输出单一 CSV 与 QA 图

输出：
- `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
- `results/figures/phase02_fig3_csfapi_optical_constants_digitized.png`
- `results/figures/phase02_fig3a_csfapi_optical_constants_overlay.png`
- `results/figures/phase02_fig3b_csfapi_optical_constants_overlay.png`
- `results/logs/phase02_fig3_csfapi_digitization_notes.md`

### 4.7 `step03_forward_simulation.py`

- 文件位置：`src/scripts/step03_forward_simulation.py`
- 主要职责：固化 Phase 03 六参数最优基线，在 `850-1500 nm` 波段前向扫描 `SAM/PVK` 界面空气隙引入后的绝对反射率 `R` 与差分反射率 `ΔR`

输入：
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`

固化参数：
- `d_bulk_base = 700.0 nm`
- `d_rough = 31.337 nm`
- `ito_alpha = 13.313`
- `sigma_thickness = 22.761 nm`
- `pvk_b_scale = 1.626`
- `niox_k = 0.455`

核心处理流程：
- 复用 `step02_tmm_inversion.py` 的 ITO 数据读取、介电常数转 `n+k`、ITO 长波吸收补偿、BEMA 粗糙层与厚玻璃非相干合成逻辑
- 对 `data/processed/CsFAPI_nk_extended.csv` 先做 `<=1100 nm` 的表格插值
- 对 `1100-1500 nm` 的 PVK 尾部折射率，在 `1050-1100 nm` 真实表格上拟合 `n(lambda)=A+B/lambda_um^2` 的 Cauchy 模型，并强制 `k = 0`
- 保持 `sigma_thickness` 的 `9` 点高斯厚度平均
- 将相干层堆栈升级为：
  - `Glass -> ITO -> NiOx -> SAM -> Air_Gap -> PVK_Bulk -> PVK_Roughness -> Air`
- 扫描 `d_air = [0, 2, 5, 10, 50, 100] nm`
- 以 `d_air = 0` 为基线计算 `ΔR = R_dair - R_0`

输出：
- `results/figures/phase04_air_gap_prediction.png`
- 终端摘要：
  - `PVK >1100 nm` 外推是否成功
  - `Cauchy A/B` 参数
  - `d_air = 2 nm` 与 `5 nm` 的 `max(|ΔR|)`
  - 是否高于 `0.2%` 噪声阈值

### 4.8 `step04a_air_gap_diagnostic.py`

- 文件位置：`src/scripts/step04a_air_gap_diagnostic.py`
- 主要职责：对 `test_data/good-21.csv` 与 `test_data/bad-23.csv` 做代表性绝对反射率标定、6 参数/7 参数拟合对比与空气隙差分指纹诊断

输入：
- `test_data/good-21.csv`
- `test_data/bad-23.csv`
- `test_data/Ag-mirro.csv`
- `resources/GCC-1022系列xlsx.xlsx`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`

核心处理流程：
- 先复用 `step01_absolute_calibration.py` 将 `good-21` 与 `bad-23` 原始计数转换为 `850-1100 nm` 的 `Measured Smooth`
- 对 `good-21` 运行完整六参数拟合，提取 `ito_alpha`、`pvk_b_scale`、`niox_k` 作为 bad 样品 7 参数诊断中的锁定材料参数
- 对 `bad-23` 先运行六参数基线拟合，再运行仅放开 `d_bulk`、`d_rough`、`sigma_thickness`、`d_air` 的七参数局部优化
- 空气隙位置显式固定为 `SAM -> Air_Gap -> PVK`
- 输出 `ΔR_exp = R_bad - R_good` 与 `ΔR_theory = R_bad_7p_fit - R_good_6p_fit` 的差分指纹对比
- 检查 `d_air` 是否卡在下界/初值，以及 `chi-square` 是否改善到 `0.01` 以下

输出：
- `data/processed/phase04a/good-21_calibrated.csv`
- `data/processed/phase04a/bad-23_calibrated.csv`
- `results/figures/phase04a_air_gap_diagnostic.png`
- `results/logs/phase04a_air_gap_diagnostic.md`

### 4.9 `step04b_air_gap_localization.py`

- 文件位置：`src/scripts/step04b_air_gap_localization.py`
- 主要职责：对 `test_data/bad-20-2.csv` 执行空气隙空间定位反证测试，并在最佳位置上释放材料参数做进一步弛豫

输入：
- `test_data/good-21.csv`
- `test_data/bad-20-2.csv`
- `test_data/Ag-mirro.csv`
- `resources/GCC-1022系列xlsx.xlsx`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`

核心处理流程：
- 先复用 04a 的标定链生成 `good-21` 与 `bad-20-2` 的 `Measured Smooth`
- 对 `good-21` 运行六参数拟合，提取 `base_ito_alpha`、`base_pvk_b_scale` 与 `base_niox_k`
- 对 `bad-20-2` 的 7 参数模型分别测试三种空气隙位置：
  - `L1: Glass -> Air_Gap -> ITO`
  - `L2: ITO -> Air_Gap -> NiOx`
  - `L3: SAM -> Air_Gap -> PVK`
- 在材料参数锁定到 `good-21` 的前提下比较 L1/L2/L3 的 `chi-square` 与 `d_air`
- 选取最佳位置后，再释放 `ito_alpha`、`pvk_b_scale` 与 `niox_k`，并把三者边界限制在 `good-21` 基准值的 `±15%`

输出：
- `data/processed/phase04b/good-21_calibrated.csv`
- `data/processed/phase04b/bad-20-2_calibrated.csv`
- `results/figures/phase04b_localization.png`
- `results/logs/phase04b_localization.md`

### 4.10 `src/core/hdr_absolute_calibration.py`

- 文件位置：`src/core/hdr_absolute_calibration.py`
- 主要职责：为 Phase 06 提供可复用的 HDR 绝对校准公共逻辑，避免将路径扫描、`.spe` 曝光时间解析、重复求均值和 HDR 拼接散落在脚本层

输入：
- OneDrive 原始目录中的 `-cor.csv / -cor.spe`
- `resources/GCC-1022系列xlsx.xlsx`

核心处理流程：
- 按前缀和曝光标签扫描目标组，禁止硬编码包含中文时间戳的完整文件名
- 从 `.spe` XML 元数据优先读取 `ExposureTime`、背景参考路径和 `FramesToStore`
- 将同曝光重复采集在 `Counts` 级别求算术平均，形成 `Mean_Counts`
- 按 `Counts / ms` 归一化得到 `N_long` 与 `N_short`
- 基于长曝光 `Cmax` 构造 `TH_lower = 0.75 * Cmax` 与 `TH_upper = 0.90 * Cmax`
- 对长曝光计数执行线性 `W_long` 权重融合，生成 `HDR(Counts/ms)`
- 读取银镜理论反射率表并插值到目标波长网格
- 输出绝对反射率曲线、HDR QA 图、最大相邻点跳变和一致性统计

### 4.11 `step06_single_sample_hdr_absolute_calibration.py`

- 文件位置：`src/scripts/step06_single_sample_hdr_absolute_calibration.py`
- 主要职责：对 `DEVICE-1-withAg` 的单样本组执行 Bit-Agnostic HDR Dry Run，并将图表与摘要输出到系统临时目录

输入：
- `D:\onedrive\Data\PL\2026\0409\cor\DEVICE-1-withAg-150ms-{1,2,3}*.csv`
- `D:\onedrive\Data\PL\2026\0409\cor\DEVICE-1-withAg-2000ms-{1,2,3}*.csv`
- `D:\onedrive\Data\PL\2026\0409\cor\Ag_mirro-500us-1*.csv`
- `D:\onedrive\Data\PL\2026\0409\cor\Ag_mirro-10ms-1*.csv`
- `resources/GCC-1022系列xlsx.xlsx`

输出：
- `%TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_hdr_diagnostic.png`
- `%TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_absolute_reflectance.png`
- `%TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_curve_table.csv`
- `%TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_summary.md`

### 4.12 `diagnostics_shape_mismatch.py`

- 文件位置：`src/scripts/diagnostics_shape_mismatch.py`
- 主要职责：在不修改主流程的前提下，复用 `step02` 的数据读取和 BEMA 基线模型，对条纹形状畸变的物理来源做诊断

输入：
- `data/processed/target_reflectance.csv`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/ITO_20 Ohm_105 nm_e1e2.mat`

核心诊断探针：
- Probe A：对 ITO 的近红外 `k` 施加长波增强缩放，测试 Drude 吸收失真假说
- Probe B：对 `d_bulk` 做高斯厚度平均，测试光斑内宏观厚度不均匀性
- Probe C：放开 PVK 的 Cauchy `B` 参数缩放，测试近红外色散斜率是否过平

输出：
- `results/figures/diagnostic_shape_analysis.png`
- `results/logs/phase02_shape_diagnostic_report.md`

### 4.11 `step06_dual_mode_microcavity_sandbox.py`

- 文件位置：`src/scripts/step06_dual_mode_microcavity_sandbox.py`
- 主要职责：直接消费 `Phase 05c` 的 `aligned_full_stack_nk.csv`，在全器件几何下构建 `Baseline / Case A / Case B` 双模式微腔缺陷指纹字典

输入：
- `resources/aligned_full_stack_nk.csv`
- `resources/materials_master_db.json`
- `src/core/full_stack_microcavity.py`

核心处理流程：
- 校验 `aligned_full_stack_nk.csv` 是否满足 `400-1100 nm / 1 nm` 的完整网格和固定列约定
- 校验 `materials_master_db.json` 中的 `ITO / NIOX / C60` 厚度是否与 `Phase 06` 口径一致
- 在厚玻璃前表面采用 `Air -> Glass` 非相干反射级联，在玻璃后侧薄膜堆栈采用相干 TMM
- 构建三种层序：
  - `Baseline: Glass -> ITO -> NiOx -> PVK -> C60 -> Ag`
  - `Case A: Glass -> ITO -> NiOx -> PVK -> C60 -> Air_Gap -> Ag`
  - `Case B: Glass -> ITO -> NiOx -> PVK -> Air_Gap -> C60 -> Ag`
- 对 `d_air = 0-50 nm` 做逐 nm 扫描，输出 `R(lambda)` 和 `ΔR(lambda) = R(d_air) - R(0)`
- 生成 `d_air = 40 nm` 的双模式长波差分对比图，以及 `Case A / Case B` 双 panel 雷达热力图

输出：
- `data/processed/phase06/phase06_dual_mode_fingerprint_dictionary.csv`
- `results/figures/phase06_dual_mode_delta_r_40nm_850_1100.png`
- `results/figures/phase06_dual_mode_radar_map.png`
- `results/logs/phase06_dual_mode_microcavity_sandbox.md`

### 4.12 `step07_orthogonal_radar_and_baseline.py`

- 文件位置：`src/scripts/step07_orthogonal_radar_and_baseline.py`
- 主要职责：在 `Phase 06` 全栈读表框架上，构建 pristine 全谱三分区基准图与 `front/back` 正交界面探伤雷达

输入：
- `resources/aligned_full_stack_nk.csv`
- `resources/materials_master_db.json`
- `src/core/full_stack_microcavity.py`

核心处理流程：
- 通过 `forward_model_for_fitting(wavelengths_nm, d_air_nm, interface_type)` 暴露标准纯实数前向接口，作为后续 LM 目标函数插槽
- 用 `d_air = 0 nm` 生成 pristine 全谱绝对反射率基准，并按 `400-650 / 650-810 / 810-1100 nm` 三分区绘制背景隔离图
- 对 `front (NiOx/PVK)` 与 `back (PVK/C60)` 分别执行 `d_air = 0-50 nm` 扫描，输出共享色标的双 panel `ΔR` 雷达图
- 生成 `Phase 07` 指纹字典与分区诊断日志，并显式比较 Zone 1 下前后界面信号强弱

输出：
- `data/processed/phase07/phase07_orthogonal_fingerprint_dictionary.csv`
- `results/figures/phase07_baseline_3zones.png`
- `results/figures/phase07_orthogonal_radar.png`
- `results/logs/phase07_orthogonal_radar_diagnostic.md`

## 5. Data Flow

当前项目主数据流如下：

```text
test_data/sample.csv
test_data/Ag-mirro.csv
resources/GCC-1022系列xlsx.xlsx
    -> step01_absolute_calibration.py
    -> data/processed/target_reflectance.csv

resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv
    -> step01b_cauchy_extrapolation.py
    -> data/processed/CsFAPI_nk_extended.csv
    -> results/figures/cauchy_extrapolation_check.png

D:\onedrive\Data\PL\2026\0409\cor\DEVICE-1-withAg-150ms-{1,2,3}*.csv
D:\onedrive\Data\PL\2026\0409\cor\DEVICE-1-withAg-2000ms-{1,2,3}*.csv
D:\onedrive\Data\PL\2026\0409\cor\Ag_mirro-500us-1*.csv
D:\onedrive\Data\PL\2026\0409\cor\Ag_mirro-10ms-1*.csv
resources/GCC-1022系列xlsx.xlsx
    -> step06_single_sample_hdr_absolute_calibration.py
    -> src/core/hdr_absolute_calibration.py (扫描文件 -> 读取 .spe 曝光元数据 -> 同曝光重复求均值 -> Bit-Agnostic HDR 融合 -> 银镜理论反射率插值 -> 绝对反射率 QA)
    -> %TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_*.png
    -> %TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_curve_table.csv
    -> %TEMP%/tmm_phase06_dry_run_*/phase06_device1_withag_summary.md

data/processed/target_reflectance.csv
data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> step02_tmm_inversion.py (CsFAPI 扩展 n-k -> ITO 色散吸收补偿 -> PVK 色散斜率扰动 -> NiOx 寄生吸收 -> BEMA 粗糙层修正 -> 宏观厚度高斯平均 -> 六参数反演)
    -> results/figures/tmm_inversion_result.png

/Users/luxin/Library/CloudStorage/OneDrive-共享的库-onedrive/Data/PL/2026/0403/cor/data-0403/*.csv
test_data/Ag-mirro.csv
resources/GCC-1022系列xlsx.xlsx
resources/ITO_20 Ohm_105 nm_e1e2.mat
data/processed/CsFAPI_nk_extended.csv
    -> step03_batch_fit_samples.py (绝对反射率校准 -> 六参数逐文件拟合 -> 单样品图 / 曲线 CSV / 汇总表)
    -> results/figures/phase03_batch_fit/*.png
    -> data/processed/phase03_batch_fit/*.csv
    -> results/logs/phase03_batch_fit/*.csv
    -> OneDrive batch-fit-results/*

data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> step03_forward_simulation.py (Phase 03 六参数基线固化 -> 1050-1100 nm Cauchy 尾段拟合 -> 1100-1500 nm PVK 尾部外推 -> Air_Gap 扫描 -> ΔR 阈值判别)
    -> results/figures/phase04_air_gap_prediction.png

test_data/good-21.csv
test_data/bad-23.csv
test_data/Ag-mirro.csv
resources/GCC-1022系列xlsx.xlsx
data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> step04a_air_gap_diagnostic.py (代表谱绝对标定 -> good 六参数参考拟合 -> bad 六参数基线拟合 -> SAM/PVK 空气隙七参数诊断拟合 -> ΔR 指纹比对)
    -> data/processed/phase04a/*_calibrated.csv
    -> results/figures/phase04a_air_gap_diagnostic.png
    -> results/logs/phase04a_air_gap_diagnostic.md

test_data/good-21.csv
test_data/bad-20-2.csv
test_data/Ag-mirro.csv
resources/GCC-1022系列xlsx.xlsx
data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> step04b_air_gap_localization.py (代表谱绝对标定 -> good 六参数基准提取 -> L1/L2/L3 空气隙空间定位 -> 最优位置材料参数弛豫)
    -> data/processed/phase04b/*_calibrated.csv
    -> results/figures/phase04b_localization.png
    -> results/logs/phase04b_localization.md

data/processed/target_reflectance.csv
data/processed/CsFAPI_nk_extended.csv
resources/ITO_20 Ohm_105 nm_e1e2.mat
    -> diagnostics_shape_mismatch.py
    -> results/figures/diagnostic_shape_analysis.png
    -> results/logs/phase02_shape_diagnostic_report.md

reference/Khan.../images/b3c499f799...
    -> step02_digitize_fapi_optical_constants.py
    -> resources/digitized/phase02_fig2_fapi_optical_constants_digitized.csv

reference/Khan.../images/4ad6d508...
reference/Khan.../images/885e29d3...
    -> step02_digitize_csfapi_optical_constants.py
    -> resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv

resources/n-kdata/*/full.md
    -> step05_parse_ellipsometry_markdown.py
    -> resources/materials_master_db.json

resources/n-kdata/*.pdf
resources/materials_master_db.json
    -> step05b_verify_against_pdf.py
    -> resources/materials_master_db.json

resources/materials_master_db.json
resources/ITO-NK值.csv
resources/NIOX-NK值.csv
resources/C60nk值.csv
resources/SNO-NK值.csv
data/processed/CsFAPI_nk_extended.csv
resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv
resources/Ag.csv
    -> step05c_build_aligned_nk_stack.py
    -> resources/aligned_full_stack_nk.csv

resources/aligned_full_stack_nk.csv
resources/materials_master_db.json
    -> step06_dual_mode_microcavity_sandbox.py (全器件读表 -> Baseline/Case A/Case B 堆栈构建 -> d_air 扫描 -> 双模式 ΔR 字典 / 对比图 / 雷达图)
    -> data/processed/phase06/phase06_dual_mode_fingerprint_dictionary.csv
    -> results/figures/phase06_dual_mode_delta_r_40nm_850_1100.png
    -> results/figures/phase06_dual_mode_radar_map.png
    -> results/logs/phase06_dual_mode_microcavity_sandbox.md

resources/aligned_full_stack_nk.csv
resources/materials_master_db.json
    -> step07_orthogonal_radar_and_baseline.py (LM 友好前向接口 -> pristine 全谱基准图 -> front/back 正交雷达 -> 分区诊断)
    -> data/processed/phase07/phase07_orthogonal_fingerprint_dictionary.csv
    -> results/figures/phase07_baseline_3zones.png
    -> results/figures/phase07_orthogonal_radar.png
    -> results/logs/phase07_orthogonal_radar_diagnostic.md
```

可按 SOP 理解为：

1. `step01` 负责把原始计数校准成可用于物理建模的绝对反射率
2. `step01b` 把 [LIT-0001] 数字化 CsFAPI 曲线转换成标准近红外 `n-k` 中间件
3. `step02` 在消费标准 `n-k` 中间件后，先对 ITO 的消光系数 `k` 做锚定 `850-1100 nm` 的色散吸收补偿，再对 PVK 斜率和 NiOx 吸收做微调，通过 50/50 BEMA 将 PVK-Air 表面粗糙度折算为有效介质层，并对 `d_bulk` 做高斯厚度平均
4. `step03_forward_simulation.py` 继承上述基线，并通过 `Air_Gap` 缺陷层把反演引擎扩展为“前向预测雷达”，直接输出隐性剥离在 `850-1500 nm` 的 `R / ΔR` 可检测性图
5. `step04a_air_gap_diagnostic.py` 进一步把代表性原始谱拉回到单样品诊断闭环，用 `good-21` 作为参考样本、在 `bad-23` 上显式检验 `SAM/PVK` 空气隙假设
6. `step04b_air_gap_localization.py` 则进一步把假设从“是否有空气隙”推进到“空气隙最可能位于哪个界面，以及材料参数是否也必须发生漂移”
7. `step05` / `step05b` / `step05c` 进一步把材料报告解析、PDF 校验和全栈 `n-k` 对齐表建立为长期可复用的数据层
8. `step06_dual_mode_microcavity_sandbox.py` 则在不再引入拟合自由度的前提下，把全栈材料表直接转为双模式微腔缺陷字典，用于后续缺陷定量和指纹匹配
9. `step07_orthogonal_radar_and_baseline.py` 进一步把缺陷模式压缩为 `front/back` 两类宏观正交界面，并补上面向后续 LM 的标准前向接口与三分区基准可视化
10. 当前脚本链已经具备“文献数字化 / 椭偏报告解析 -> 材料数据库 -> 全栈对齐 `n-k` 表 -> 宏观正交界面指纹字典 -> LM 接口预研”的 Phase 07 闭环

## 6. Key Physical / Numerical Assumptions

当前实现中最重要的物理和数值假设如下：

- `step02` 反演窗口为 `850-1100 nm`，`step03_forward_simulation.py` 的前向预测窗口扩展到 `850-1500 nm`
- `step04a_air_gap_diagnostic.py` 在 `850-1100 nm` 的实验采样网格上比较 `good-21` 与 `bad-23`，不重采样到均匀 1 nm 网格
- 玻璃厚板不作为相干层直接进入 TMM 相位矩阵
- ITO 数据若波长量级大于 `2000`，则按 Angstrom 自动转为 nm
- 厂家银镜基准若数值范围大于 `1.5`，则按百分比转为 `0-1` 小数
- PVK 的近红外色散来源为 [LIT-0001] Fig. 3 的 `ITO/CsFAPI` 数字化 `n` 曲线，并通过 Cauchy 模型外推到 `1100 nm`
- `750-1100 nm` 内强制采用 `k = 0`
- `1000-1100 nm` 属于超出原始椭偏测量窗口的模型外推区
- Phase 04 中 `1100-1500 nm` 的 PVK 折射率不再直接沿用表格，而是基于 `1050-1100 nm` 的真实点二次拟合 Cauchy 尾段后继续外推，且仍强制 `k = 0`
- 粗糙层采用 `50% PVK + 50% Air` 的 BEMA 有效介质
- ITO 的额外吸收以锁定实部 `n` 的色散参数 `ito_alpha` 表示，其对 `k` 的放大在 `850 nm` 处为 1，在 `1100 nm` 处为 `1 + ito_alpha`
- Phase 04 中该 ITO 长波吸收补偿在 `1100 nm` 后保持饱和，不继续向 `1500 nm` 增长
- 反演当前同时拟合 `d_bulk`、`d_rough`、`ito_alpha`、`sigma_thickness`、`pvk_b_scale` 与 `niox_k` 六个参数
- Phase 04a 的空气隙假设位置显式固定为 `SAM / PVK` 界面，即层序 `Glass -> ITO -> NiOx -> SAM -> Air_Gap -> PVK_Bulk -> PVK_Roughness -> Air`
- Phase 04a 的 7 参数诊断中，`ito_alpha`、`pvk_b_scale` 与 `niox_k` 锁定为 `good-21` 六参数最佳拟合值，只放开 `d_bulk`、`d_rough`、`sigma_thickness` 与 `d_air`
- Phase 04b 的空间定位阶段分别测试 `Glass/ITO`、`ITO/NiOx` 与 `SAM/PVK` 三个候选空气隙界面
- Phase 04b 的材料弛豫阶段允许 `ito_alpha`、`pvk_b_scale` 与 `niox_k` 在 `good-21` 基准值的 `±15%` 范围内漂移

这些假设是理解结果与后续扩展的关键锚点；若后续有改动，必须同步更新本文件。

## 7. Bug Ledger

当前尚未确认完全关闭的问题如下。

### 7.1 目录结构尚未收敛到规范态

- 表现：
  - 原始数据仍在 `test_data/`
  - 文献与拆解材料仍在 `reference/`
- 影响：
  - 新 Agent 容易在旧目录和新规范之间混淆
  - 不利于后续自动化脚本稳定约定路径
- 当前状态：
  - 已通过 `AGENTS.md` 明确新规范
  - 仓库实体结构尚未迁移

### 7.2 `step02` 尚未输出结构化反演结果文件

- 表现：
  - 目前只输出图像和终端打印
  - 尚未输出标准 CSV/JSON 记录最佳参数和拟合质量
- 影响：
  - 后续批量比较、回归测试和结果追踪不方便
- 当前状态：
  - 功能可用，但结果留痕不够完整

### 7.3 当前反演模型虽已扩展，但结构解释仍非唯一

- 表现：
  - 当前已反演 `d_bulk`、`d_rough`、`ito_alpha`、`sigma_thickness`、`pvk_b_scale` 与 `niox_k`
  - ITO/NiOx/SAM 厚度与多数材料参数仍固定
- 影响：
  - 六参数收敛仍不等于结构解释唯一
  - 对模型误差与参数耦合的吸收能力有限
- 当前状态：
  - 已比早期模型更能吸收表面粗糙度、底层吸收、峰谷展宽和短波斜率偏差
  - 不适合作为最终物理解译结论

### 7.4 图像数字化结果不是原始实验表

- 表现：
  - `phase02_fig2_fapi_optical_constants_digitized.csv` 与 `phase02_fig3_csfapi_optical_constants_digitized.csv` 来自论文图像数字化
  - 不是作者公开补充材料中的原始数值表
- 影响：
  - 可用于复核趋势、建立先验或做近似对照
  - 不应表述为“绝对无误差的原始测量数据”
- 当前状态：
  - 已优先使用论文原图而非截图
  - 已输出重绘图与叠加图作为 QA 留痕

### 7.5 PVK 常数折射率临时分支已关闭

- 表现：
  - 先前用于 smoke test 的 `n=2.45, k=0` 常数锚定分支已从 `step02` 删除
- 影响：
  - 当前主流程已改为消费基于真实 CsFAPI 数字化数据外推得到的标准 `n-k` 中间件
  - “临时常数折射率”不再是主流程隐含假设
- 当前状态：
  - 已解决

### 7.6 BEMA 粗糙层升级直接用于压低理论振幅

- 表现：
  - 在相位已经基本对齐的前提下，平滑界面模型的理论振幅高于实测振幅
- 影响：
  - 引入 `PVK_Roughness` 有效介质层后，模型可通过顶部减反效应压低理论峰值，更接近实测约 `30%` 的振幅水平
- 当前状态：
  - 已纳入 `step02_tmm_inversion.py` 主流程
  - 后续仍需结合拟合结果持续验证振幅改进是否稳定

### 7.7 条纹形状畸变的主导根因已被定位，但尚未修入主流程

- 表现：
  - 在 BEMA 粗糙层已修复振幅后，主流程仍存在长波端托平和条纹跨度失配
- 影响：
  - `diagnostics_shape_mismatch.py` 的 Probe A 显示，ITO 近红外吸收增强可将形状误差显著压低
  - 这说明当前主流程的 ITO 吸收建模仍不足，是下一轮主流程升级的优先方向
- 当前状态：
  - 已通过 ITO 色散吸收补偿并入 `step02_tmm_inversion.py`
  - 当前主流程已能把长波端托平明显拉回实测曲线附近
  - 本轮继续加入 `sigma_thickness`，用于吸收光斑尺度内的峰谷钝化与条纹展宽

### 7.8 银镜短曝光归一化与长曝光严重不一致

- 表现：
  - 对 `Ag_mirro-500us-1` 与 `Ag_mirro-10ms-1` 按 `.spe` 元数据中的真实曝光时间做 `Counts/ms` 归一化后，`N_short / N_long` 全波段中位数约为 `12.28`
  - 该失配在 `500-600 nm`、`650-710 nm` 与 `850-1055 nm` 都持续存在，而不是只发生在局部饱和峰附近
- 影响：
  - 银镜 HDR 的短曝光部分不能被视为与长曝光同一线性响应链路
  - `500-710 nm` 波段的绝对反射率解释需要把该失配当作首要 QA 风险
- 当前状态：
  - 已在 Phase 06 Dry Run 中显式暴露，不做经验缩放或非物理修补
  - 后续需回查仪器门控、导出流程或实际曝光标签

## 8. Architecture Risks

### 8.1 复用逻辑模块化刚启动，但尚未覆盖旧流程

- 已新增 `src/core/hdr_absolute_calibration.py`，用于收敛 Phase 06 的文件扫描、曝光解析和 HDR 拼接逻辑
- 但 `step01` 至 `step05` 的复用逻辑仍大量滞留在 `src/scripts/`
- 后续若继续扩展批量 HDR、批量反演或更多仪器输入格式，仍需继续把旧流程下沉到 `src/core/`

### 8.2 资源文件格式存在隐式脆弱性

- `ITO_20 Ohm_105 nm_e1e2.mat` 的扩展名与实际可解析内容不完全一致
- 当前代码已做 MAT/文本双分支兼容
- 但长期看应补资源索引文档，明确每个资源文件的真实格式与来源

### 8.3 缺少回归验证与数值基准

- 当前已有图像结果，但缺少：
  - 基准厚度的预期区间
  - 标准输入下的预期 `chi-square`
  - 自动化回归测试
- 这会导致后续重构时较难判断“模型真的没变”

### 8.4 图像数字化链路仍带有手工标定假设

- 当前 Fig. 2 / Fig. 3 数字化脚本依赖固定图框坐标和坐标轴范围
- 若后续换成新版 MinerU 图、原 PDF 裁图或其他论文图片，不能直接假定这套标定仍成立
- 建议后续把坐标框识别和图例剔除规则继续模块化，必要时加入人工校核步骤

### 8.5 PVK 色散已改为真实光谱外推，但外推边界仍需审慎

- “PVK 常数折射率锚定仍属临时验证假设”这一风险已关闭
- 当前主流程已基于 [LIT-0001] Fig. 3 的 `ITO/CsFAPI` 数字化数据，在 `750-1000 nm` 透明区进行 Cauchy 拟合并外推到 `1100 nm`
- 当前新增的主要风险是：
  - `1000-1100 nm` 属于超出原文测量窗口的外推区
  - 当前将 `k` 在近红外全部强制为 `0`
  - 数字化误差会直接传递到 Cauchy 参数 `A, B`
  - Phase 04 又基于 `1050-1100 nm` 尾段继续把 `n` 外推到 `1500 nm`，因此 `1100-1500 nm` 的预测结果更适合用作 LOD 趋势判断，而不是直接当作已验证材料常数

### 8.6 BEMA 双参数反演存在参数相关性风险

- `d_bulk` 与 `d_rough` 都会影响干涉振幅与相位，二者可能存在相关性
- 因此双参数数值收敛不自动等价于唯一物理解
- 当前升级可直接改善振幅匹配，但后续若用于定量结论，仍需通过更多先验或更多观测量约束参数空间

### 8.7 ITO 色散吸收修正已被诊断为关键缺项

- 独立诊断表明，ITO 近红外吸收增强比厚度不均匀性和 PVK 色散斜率修正更能同时修复长波托平与整体形状
- 本轮主流程进一步表明：把吸收放大限制在长波端，比全局标量吸收更符合数据
- 后续仍需关注 `ito_alpha` 是否与 `d_bulk` / `d_rough` 存在新的参数相关性

### 8.8 宏观厚度不均匀性会进一步放大参数相关性

- `sigma_thickness` 会直接影响峰谷圆润度、条纹对比度和局部形状
- 因此它可能与 `d_rough` 和 `ito_alpha` 共同吸收同一部分误差
- 该机制能提升拟合灵活性，但也会进一步削弱“单组参数唯一对应单一物理结构”的可解释性

### 8.9 PVK 斜率扰动与 NiOx 吸收会引入新的可辨识性风险

- `pvk_b_scale` 会改变短波端相位推进速度与峰谷跨度
- `niox_k` 会改变整体对比度并与 `ito_alpha` 共同承担寄生吸收
- 因此这两个新自由度虽然能显著压低残差，但也会进一步削弱“拟合最优即物理唯一”的可信度

### 8.10 结果文件命名尚未 Phase 化

- 当前图像文件名尚未显式带上 `phaseXX`
- 后续结果积累后，可能不利于多轮实验比较和回滚定位

### 8.11 空气隙假设只解释了 bad-23 的部分失配

- `step04a_air_gap_diagnostic.py` 在 `bad-23` 上得到 `d_air ≈ 39.9 nm`，且 `chi-square` 从 `0.03197` 降到 `0.01619`
- 这说明 `SAM/PVK` 界面空气隙并非完全无效，而是能解释一部分谱形失配
- 但由于 `chi-square` 仍高于 `0.01`，当前证据不足以支持“空气隙是唯一主导退化机制”的结论
- 后续应优先检查：
  - ITO 退化或近红外吸收漂移
  - PVK 色散相对 good 样品发生整体偏移
  - 其他界面或层厚参数同时退化

### 8.12 bad-20-2 的空间定位支持 L3，但材料漂移同样关键

- 在 `bad-20-2` 上，三种 7 参数空间定位模型的 `chi-square` 结果分别约为：
  - `L1 Glass/ITO = 0.07086`
  - `L2 ITO/NiOx = 0.06740`
  - `L3 SAM/PVK = 0.02862`
- 这说明若只比较空间位置，`SAM/PVK` 仍是最有希望的空气隙位置，且 `d_air ≈ 40.5 nm`
- 但 `bad-20-2` 的 6 参数基线本身约为 `0.02830`，略优于锁定材料参数时的 `L3 7p`
- 只有在最佳位置上进一步允许材料参数弛豫后，`chi-square` 才降到约 `0.01932`
- 其中：
  - `ITO Alpha` 只漂移约 `-0.96%`
  - `PVK B-Scale` 漂移约 `-4.26%`
  - `NiOx k` 触及 `-15%` 下边界
- 这说明 `bad-20-2` 的异常不能仅靠“空气隙位置正确”解释，还伴随着明显的材料吸收/色散漂移需求

### 8.13 Phase 06 仍依赖仓库外 OneDrive 目录

- 当前 `step06_single_sample_hdr_absolute_calibration.py` 直接依赖 `D:\onedrive\Data\PL\2026\0409\cor\`
- 这能满足 Dry Run，但不满足长期可移植性
- 后续应尽快建立 `data/raw/phase06/` 或稳定的数据索引文档，避免脚本只能在当前机器路径上运行

### 8.14 当前实测窗口不足以覆盖完整 1100 nm 上边界

- 本次实测数据只覆盖 `498.934-1055.460 nm`
- 因此 `850-1100 nm` 口径在当前数据上只能落实为 `850-1055.460 nm`
- 本轮已明确选择“不外推补齐窗口”，但后续比较不同批次样品时需要统一说明这一窗口截断

## 9. Recent Update Summary

- 更新时间：`2026-04-10`
- 当前 Phase：`Phase 06`
- 本次新增/修改：
  - 新增 `src/core/hdr_absolute_calibration.py`，建立 Phase 06 的单样本 HDR 绝对校准公共模块
  - 新增 `src/scripts/step06_single_sample_hdr_absolute_calibration.py`，对 `DEVICE-1-withAg` 与 `Ag_mirro` 执行 Dry Run
  - 输出系统临时目录下的 HDR QA 图、绝对反射率图、曲线表与摘要
  - 更新 `PROJECT_STATE.md`，记录 Phase 06 的 I/O 合约、波段口径与 Ag 曝光失配风险
- 已验证结论：
  - 当前实测窗口确认为 `498.934-1055.460 nm`
  - 样品 HDR 交接点主要落在 `695.699-697.792 nm`
  - 银镜 HDR 交接点主要落在 `524.347-681.878 nm`
  - `850-1055 nm` 波段内样品与银镜基本完全信任长曝光
- 仍待验证：
  - `Ag_mirro-500us` 与 `Ag_mirro-10ms` 的归一化失配根因仍未确认
  - 当前 HDR 逻辑尚未扩展到批量样品和标准 `data/raw/` 目录

## 10. Recommended Next Actions

建议后续优先处理以下事项：

1. 回查 `Ag_mirro-500us` 与 `Ag_mirro-10ms` 的归一化失配来源，优先检查仪器门控、导出流程与实际曝光标签
2. 建立 `data/raw/phase06/` 或稳定数据索引，把 OneDrive 外部路径纳入规范化入口
3. 将 Phase 06 的单样本 HDR 逻辑扩展到批量样品
4. 继续把 `step01`/`step01b`/`step02` 中可复用逻辑下沉到 `src/core/`
5. 建立 `docs/RESOURCE_INDEX.md`，说明 ITO、银镜基准、论文资料与数字化资源的来源和格式

## 11. Update Rule

后续出现以下情况时，必须更新本文件：

- 新增或完成一个 Phase
- 调整目录结构
- 新增/删除关键脚本
- 改变中间文件格式
- 修改核心物理假设
- 新增重要未解决问题或关闭既有问题

更新时优先保证：
- 目录树准确
- 数据流准确
- 风险和问题列表准确
- 不堆砌无关历史对话内容

## Phase 04c Update (2026-04-07)

- Current Phase: `Phase 04c`
- Core strategy shift: stop pursuing high-dimensional inverse fitting on `bad-20-2` absolute reflectance; use forward differential fingerprint mapping with zero-preserving normalization for morphology-only phase alignment.
- Inputs: `test_data/good-21.csv`, `test_data/bad-20-2.csv`, calibrated by step01-compatible chain.
- Baseline extraction: run 6-parameter fit on `good-21` as intact-device physical baseline (`chi-square = 0.002564`).
- Forward dictionary: lock all six baseline parameters, inject fixed `d_air = 40.0 nm` at three interfaces:
  - `L1 Glass/ITO`
  - `L2 ITO/NiOx`
  - `L3 SAM/PVK`
- Differential definitions:
  - `Delta_R_exp = bad_20_2_smooth - good_21_smooth`
  - `Delta_R_theory_L = R_theory_L - R_theory_good_6p`
- Normalization: zero-preserving normalization by `max_abs` within 850-1100 nm for both experimental and theoretical delta curves.
- Key alignment result (normalized morphology RMSE, lower is better):
  - `L1 Glass/ITO`: `1.156029`
  - `L2 ITO/NiOx`: `0.611901`
  - `L3 SAM/PVK`: `0.254985` (best)
- Phase alignment conclusion: experimental normalized differential fingerprint is best aligned with `L3 (SAM/PVK)`.

### Phase 04c Artifacts

- Script: `src/scripts/step04c_fingerprint_mapping.py`
- Figure: `results/figures/phase04c_fingerprint_mapping.png`
- Log: `results/logs/phase04c_fingerprint_mapping.md`
- Processed calibration outputs:
  - `data/processed/phase04c/good-21_calibrated.csv`
  - `data/processed/phase04c/bad-20-2_calibrated.csv`

## Phase 05 Update (2026-04-08)

- Current Phase: `Phase 05`
- Update summary:
  - 已通过结构化 Markdown 完成物理参数数据库解析。
  - 新增脚本 `src/scripts/step05_parse_ellipsometry_markdown.py`，扫描 `resources/n-kdata/*/full.md`，使用 `BeautifulSoup` 解析 HTML 表格，并辅以正则提取概览厚度。
  - 新增材料数据库 `resources/materials_master_db.json`，当前覆盖 `C60`、`ITO`、`NIOX`、`sno` 四种材料。
  - 当前输出字段包括：`thickness_nm`、`rmse`、`wavelength_range_nm`、`requires_extrapolation`、`dispersion_models`、`fit_parameters`、`derived_parameters`、`parse_warnings`。
- Data flow:
  - `resources/n-kdata/<material>/full.md`
  - `src/scripts/step05_parse_ellipsometry_markdown.py`
  - `resources/materials_master_db.json`
- Verified results:
  - `ITO`: `Thickness = 19.595 nm`, `RMSE = 0.05936`, models = `Cauchy + Lorentz`
  - `C60`: `Thickness = 18.494 nm`, `Eg = 2.22511 eV`, models = `Tauc-Lorentz + Lorentz + Lorentz`
  - `NIOX`: `Thickness = 22.443 nm`, models = `Tauc-Lorentz + Gauss + Lorentz`
  - `sno`: `Thickness = 20.156 nm`, models = `Lorentz + Tauc-Lorentz`
  - 四种材料的报告最高波长均低于 `1100 nm`，因此全部标记 `requires_extrapolation = true`
- Dependency note:
  - Phase 05 解析链新增运行依赖 `beautifulsoup4`
- Risks / pending checks:
  - 当前 `full.md` 样本都能从文本和表格中直接提取关键参数，尚未触发 `IMAGE_ONLY_ERROR`
  - 若后续报告把厚度、振子参数或拟合质量只保留为 `![](images/...)` 图像占位，现有脚本会输出 `WARNING` 并把对应 JSON 字段写为 `null`
  - `sample_id` 仍保留原始 Markdown 文本，部分报告存在源文件字符编码噪声，后续如需对样品名做检索，建议增加单独清洗规则

## Phase 05b Update (2026-04-08)

- Current Phase: `Phase 05b`
- Update summary:
  - 已完成 PDF 与 JSON 的交叉验证，数据库双重校验通过。
  - 新增脚本 `src/scripts/step05b_verify_against_pdf.py`，直接读取 `resources/n-kdata/*.pdf`，用 `PyMuPDF` 提取文本并与 `materials_master_db.json` 做宏观锚点与模型完整性比对。
  - 在数据库中新增 `pdf_validation` 字段，记录每个材料对应的 PDF 来源、通过的校验项、自动修复字段和人工介入字段。
- Data flow:
  - `resources/n-kdata/*.pdf`
  - `src/scripts/step05b_verify_against_pdf.py`
  - `resources/materials_master_db.json`
- Verified results:
  - `C60`、`ITO`、`NIOX`、`sno` 均成功映射到唯一 PDF 源文件。
  - 四种材料均通过 `thickness_nm`、`rmse`、`wavelength_range_nm` 与 `dispersion_models` 校验。
  - 当前正式数据库无宏观锚点冲突，无需自动覆写修复。
  - `requires_extrapolation` 复核后仍全部为 `true`，与 PDF 波长上限 `< 1100 nm` 一致。
- Dry-run repair validation:
  - 对临时测试 JSON 人为置空 `ITO.thickness_nm` 后，脚本可从 `ITO.pdf` 自动补回厚度。
  - 对临时测试 JSON 人为清空 `NIOX` 的 `Gauss` 参数后，脚本可按模型顺序从 PDF 结果块补回 `Amp/E0/Br`。
- Dependency note:
  - Phase 05b 使用现有环境中的 `PyMuPDF (fitz)`，未新增新的 PDF 依赖。
- Risks / pending checks:
  - PDF 表格文本抽取可稳定支持宏观锚点与空字段补漏，但对已存在的多振子详细参数仍维持 “JSON 优先，PDF 仅补漏” 原则，避免表格错位引入假修复。
  - `sample_id` 的字符编码噪声仍来自源报告文本，本轮未做额外清洗。

## Phase 05c Update (2026-04-08)

- Current Phase: `Phase 05c`
- Update summary:
  - 已新增 `src/scripts/step05c_build_aligned_nk_stack.py`，构建 `400-1100 nm`、`1 nm` 步长的统一波长网格，并输出可直接供 TMM 读取的全栈 `n-k` 表。
  - 已生成 `resources/aligned_full_stack_nk.csv`，统一包含 `Glass / ITO / NiOx / PVK / C60 / SnOx / Ag` 七种材料的对齐光学常数。
  - 已生成 `docs/images/nk_extrapolation_check.png`，用于人工核查 `ITO k` 与 `C60 n` 在 `900 nm` 拼接点附近的连续性。
- Data flow:
  - `resources/materials_master_db.json`
  - `resources/ITO-NK值.csv`, `resources/NIOX-NK值.csv`, `resources/C60nk值.csv`, `resources/SNO-NK值.csv`
  - `data/processed/CsFAPI_nk_extended.csv`
  - `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
  - `resources/Ag.csv`
  - `src/scripts/step05c_build_aligned_nk_stack.py`
  - `resources/aligned_full_stack_nk.csv`
- Extrapolation / stitching policy:
  - `ITO / NiOx / C60 / SnOx` 先对实测区做 cubic interpolation，再在真实测量上界约 `900 nm` 处执行长波外推。
  - `n` 尾部采用简化 Cauchy 公式 `n(lambda) = A + B / lambda^2` 拟合最后 `200 nm` 实测区后外推。
  - `k` 尾部按启发式分支处理：
    - `C60 / SnOx` 判定为透明尾，`900-1100 nm` 平滑收敛到 `0`
    - `ITO` 判定为 Drude-like 上升尾，保持单调不减
    - `NiOx` 尾部不满足透明条件，按保守上升尾策略延伸，避免长波震荡
  - `PVK` 采用双源拼接：
    - `750-1100 nm` 使用 `data/processed/CsFAPI_nk_extended.csv`
    - `450-749 nm` 使用 [LIT-0001] Fig. 3 数字化 `ITO/CsFAPI`
    - `400-449 nm` 通过局部边界外推补齐
  - 拼接点两侧使用 `5 nm` 小窗口局部平滑，保证工程数据表连续可读。
- Verified results:
  - `resources/aligned_full_stack_nk.csv` 共 `701` 行，全部输出列无 `NaN/Inf`。
  - 输出列顺序已固定为：
    - `Wavelength_nm`
    - `n_Glass`, `k_Glass`
    - `n_ITO`, `k_ITO`
    - `n_NiOx`, `k_NiOx`
    - `n_PVK`, `k_PVK`
    - `n_C60`, `k_C60`
    - `n_SnOx`, `k_SnOx`
    - `n_Ag`, `k_Ag`
  - `Glass` 常数列已固定为 `n = 1.515`, `k = 0`。
  - `ITO` 长波 `k` 在 `900-1100 nm` 区间保持单调不减。
  - `PVK` 在 `449/450 nm` 与 `749/750 nm` 拼接处未出现明显跳变。
- Engineering scope note:
  - 本轮 `Phase 05c` 的长波外推属于下游 TMM 读表所需的工程整理层，不等同于已经完成文献约束或实验复测验证的最终材料真值数据库。
- Risks / pending checks:
  - `NiOx` 长波 `k` 尾部当前按启发式保守延伸，尚未结合额外文献或独立红外测量做物理定标。
  - `PVK 400-449 nm` 来源于短程边界外推，仅用于补齐统一网格，不应直接作为高置信材料常数结论引用。
  - 验证图当前放置在 `docs/images/` 以服务状态文档核查；若后续形成批量图表流程，建议同步纳入 `results/figures/` 体系管理。

## Phase 06 Update (2026-04-08)

- Current Phase: `Phase 06`
- Update summary:
  - 已新增 `src/core/full_stack_microcavity.py`，把 `aligned_full_stack_nk.csv` 封装为可直接求解的全器件微腔堆栈模块。
  - 已新增 `src/scripts/step06_dual_mode_microcavity_sandbox.py`，构建 `Baseline / Case A / Case B` 三种层序，并在 `d_air = 0-50 nm` 上输出双模式差分指纹字典。
  - 已生成 `data/processed/phase06/phase06_dual_mode_fingerprint_dictionary.csv`、`results/figures/phase06_dual_mode_delta_r_40nm_850_1100.png`、`results/figures/phase06_dual_mode_radar_map.png` 与 `results/logs/phase06_dual_mode_microcavity_sandbox.md`。
- Data flow:
  - `resources/materials_master_db.json`
  - `resources/aligned_full_stack_nk.csv`
  - `src/core/full_stack_microcavity.py`
  - `src/scripts/step06_dual_mode_microcavity_sandbox.py`
  - `data/processed/phase06/phase06_dual_mode_fingerprint_dictionary.csv`
  - `results/figures/phase06_dual_mode_delta_r_40nm_850_1100.png`
  - `results/figures/phase06_dual_mode_radar_map.png`
  - `results/logs/phase06_dual_mode_microcavity_sandbox.md`
- Geometry / modeling policy:
  - `Air -> Glass` 前表面按非相干强度级联处理。
  - 玻璃后侧薄膜堆栈按法向入射相干 TMM 处理。
  - `Ag` 作为半无限背电极。
  - `d_air = 0 nm` 时 `Case A / Case B` 都必须退化为 `Baseline`。
- Verified results:
  - `Case A` 与 `Case B` 的零空气隙退化检查通过。
  - 指纹字典行数满足 `71502`。
  - 双 panel 雷达图使用相同色标，满足 A/B 形态对比需求。
- Risks / pending checks:
  - `400-650 nm` 在模型中不会被人为清零，是否在实验上近似零响应仍需后续数据验证。
  - `NiOx` 长波 `k` 与 `PVK 400-449 nm` 的工程补齐风险会直接传递到 `Phase 06` 的绝对幅值判断。
  - 当前结果更适合作为缺陷模式指纹字典，而非直接当作已验证的材料真值结论。

## Phase 07 Update (2026-04-08)

- Current Phase: `Phase 07`
- Update summary:
  - 已重构 `src/core/full_stack_microcavity.py`，将 `front/back` 界面定义、厚度覆盖和任意波长插值统一封装到 `forward_model_for_fitting()`。
  - 已新增 `src/scripts/step07_orthogonal_radar_and_baseline.py`，输出 pristine 三分区基准图与 `front/back` 正交雷达图。
  - 已生成 `data/processed/phase07/phase07_orthogonal_fingerprint_dictionary.csv`、`results/figures/phase07_baseline_3zones.png`、`results/figures/phase07_orthogonal_radar.png` 与 `results/logs/phase07_orthogonal_radar_diagnostic.md`。
- Data flow:
  - `resources/aligned_full_stack_nk.csv`
  - `resources/materials_master_db.json`
  - `src/core/full_stack_microcavity.py`
  - `src/scripts/step07_orthogonal_radar_and_baseline.py`
  - `data/processed/phase07/phase07_orthogonal_fingerprint_dictionary.csv`
  - `results/figures/phase07_baseline_3zones.png`
  - `results/figures/phase07_orthogonal_radar.png`
  - `results/logs/phase07_orthogonal_radar_diagnostic.md`
- Verified results:
  - `forward_model_for_fitting()` 的一维数组输入输出契约验证通过。
  - `front/back` 在 `d_air = 0 nm` 时都能严格退化为 pristine baseline。
  - `Phase 07` 指纹字典行数满足 `71502`。
  - `front` 在 `Zone 1` 的 `max|ΔR| ≈ 28.16%`，`back` 仅约 `0.71%`，宏观正交特征明确成立。
- Risks / pending checks:
  - `Zone 2` 当前只在文档和图中标记为后续零权重区，尚未真正进入优化器实现。
  - `NiOx` 长波 `k` 与 `PVK 400-449 nm` 的工程外推风险仍会影响 `Phase 07` 的绝对幅值。
  - 当前结论适合作为前后界面宏观判别与 LM 架构设计依据，尚不能替代后续实验拟合验证。
