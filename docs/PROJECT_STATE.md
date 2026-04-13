# PROJECT_STATE.md

本文件用于持续同步 `TMM-interference-spectrum` 项目的当前状态，是后续 AI Agent 和架构师恢复上下文的首要入口。

## 1. Current Snapshot

- 更新时间：2026-04-13
- 当前判断 Phase：`Phase D-1`
- 阶段定义：`建立 realistic thickness + roughness background 下的 air-gap discrimination database，统一整理 thickness / roughness / front-gap / rear-gap 的 R_total 判别输入`
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
  - 已新增 `step06_batch_hdr_calibration.py`，可对 `0409/cor` 目录下全部样本执行 HDR 绝对校准批处理，并同步写出项目目录与 OneDrive 原址存档
  - 已有 `diagnostics_shape_mismatch.py`，可在独立沙盒中对 ITO 近红外吸收、厚度不均匀性和 PVK 色散斜率做形状畸变诊断
  - 已有 `step02_digitize_fapi_optical_constants.py`，可从 `LIT-0001` 的 Fig. 2 原图数字化提取 FAPI 的 `n/κ` 曲线并输出 QA 图
  - 已有 `step02_digitize_csfapi_optical_constants.py`，可从 `LIT-0001` 的 Fig. 3 原图数字化提取 CsFAPI 的 `n/κ` 曲线并输出 QA 图
  - 已有 `step05_parse_ellipsometry_markdown.py`，可从 `resources/n-kdata/*/full.md` 解析椭偏报告并构建 `materials_master_db.json`
  - 已有 `step05b_verify_against_pdf.py`，可用原始 PDF 交叉验证材料数据库中的厚度、RMSE、波段范围与模型完整性
  - 已有 `step05c_build_aligned_nk_stack.py`，可生成 `400-1100 nm / 1 nm` 的全栈对齐 `n-k` 表 `aligned_full_stack_nk.csv`
  - 已有 `src/core/full_stack_microcavity.py`，可基于 `aligned_full_stack_nk.csv` 构建 `Baseline / Case A / Case B / Front / Back` 五类全器件微腔堆栈，并暴露 `forward_model_for_fitting()` 作为后续 LM 目标函数入口
  - 已有 `step06_dual_mode_microcavity_sandbox.py`，可扫描 `d_air = 0-50 nm`，输出双模式 `R / ΔR` 指纹字典、40 nm 对比图和 2D 雷达热力图
  - 已有 `step07_orthogonal_radar_and_baseline.py`，可输出 pristine 全谱三分区基准图、Front/Back 正交雷达图与 `Phase 07` 指纹字典
  - 已新增 `src/core/phase07_dual_window.py`，可基于 `aligned_full_stack_nk.csv` 构建 `Glass / ITO / NiOx / SAM / PVK / PVK-C60 Roughness / C60 / Ag(or Air)` Phase 07 堆栈，执行 C60 守恒约束、双窗加权残差、`d_bulk` 后窗 basin 扫描、DE 全局搜索、局部 least-squares 精修与 Phase 07 诊断出图
  - 已新增 `step07_dual_window_inversion.py`，可优先读取原始多曝光目录并复用 Phase 06 HDR 逻辑，或直接消费 `*_hdr_curves.csv`，统一落盘为 `fit_input -> fit_summary / fit_curve / optimizer_log / 4 张诊断图`
  - 已新增 `step08_theoretical_tmm_modeling.py`，可读取 `phase07_fit_summary.csv` 与对应 `fit_input`，冻结 Phase 07 最优参数并重建理论反射率、前表面散射因子和后窗 z-score 对比，统一落盘为 `phase08_theory_curve / phase08_theory_summary / phase08_source_manifest / theory_vs_measured 图`
  - 已新增 `stepA1_pristine_baseline.py`，可严格基于 `aligned_full_stack_nk.csv` 和常数玻璃 `n=1.515, k=0` 生成 `R_front / R_stack / R_total` 的 pristine baseline decomposition，并输出三曲线图、三区图与标准日志
  - 已新增 `stepA1_1_pvk_seam_audit.py`，可围绕 `749/750 nm` 对 PVK seam 做局部 n-k/eps/导数审计、上游三源追溯、简化堆栈敏感性比较、Ag 终端边界对照与代码路径核查
  - 已新增 `stepA1_2_build_pvk_surrogate_v2.py`，可在不覆盖 v1 材料表的前提下，对 PVK 的 `740-780 nm` band-edge 区域执行局部 surrogate rebuild，并输出 `aligned_full_stack_nk_pvk_v2.csv`、候选过渡带指标表与 v1/v2 QA 图
  - 已新增 `stepA1_2_rerun_pristine_with_pvk_v2.py`，可复用 Phase A-1 pristine decomposition 口径，用 `PVK surrogate v2` 重跑 `R_front / R_stack / R_total`，并输出 v1/v2 全谱与局部对照
  - 已新增 `stepA2_pvk_thickness_scan.py`，可基于 `aligned_full_stack_nk_pvk_v2.csv` 扫描 `d_PVK = 500-900 nm`、输出 `R_stack / R_total / ΔR` 热力图、peak/valley tracking 与特征汇总表
  - 已建立 `results/report/` 汇报资产层，并补齐 `Phase A-1.2` 与 `Phase A-2` 的精选 CSV / PNG / Markdown 报告
  - 已新增 `stepB1_rear_bema_sandbox.py`，可在 `PVK/C60` 后界面插入固定 `50/50` Bruggeman BEMA 层、执行厚度守恒扫描并与 `d_PVK` 指纹做对照
  - 已新增 `stepA2_1_pvk_uncertainty_ensemble.py`，可构建 `nominal / more_absorptive / less_absorptive` 三成员 PVK ensemble，重跑代表性 thickness / rear-BEMA 子集并输出 robustness summary
  - 已新增 `stepB2_front_bema_sandbox.py`，可在固定 `SAM` 厚度前提下引入 `NiOx/PVK` front-side BEMA proxy，输出 front-only roughness 主扫描、与 thickness/rear-BEMA 的正交对照，以及 uncertainty spot-check
  - 已新增 `stepC1a_rear_air_gap_sandbox.py`，可在 `PVK/C60` 后界面插入真实 air gap，输出 low-gap 高分辨主扫描、LOD 粗评估、branch-aware tracking 和与 thickness / rear-BEMA / front-BEMA 的四机制对照
  - 已新增 `stepC1b_front_air_gap_sandbox.py`，可在 `SAM/PVK` 前界面插入真实 air gap，输出 low-gap 高分辨主扫描、前/过渡/后窗分窗响应、LOD 粗评估、uncertainty spot-check 与五机制对照
  - 已新增 `stepPPT_phaseAtoC_assets.py`，可基于现有 `data/processed` 结果重绘一套统一风格的 `R_total-only` PPT 汇报资产，并同步生成每页 `slide_text.md / source_manifest.md`
  - 已新增 `stepD1_airgap_discrimination_database.py`，可在 realistic `d_PVK + front/rear roughness` 背景上统一构建 `thickness nuisance / roughness nuisance / front-gap overlay / rear-gap overlay` 的 `R_total / Delta_R_total` 判别数据库，并输出 rear shift analysis、feature atlas 与算法讨论用 report 资产
  - 已产出标准中间文件 `data/processed/target_reflectance.csv` 与 `data/processed/CsFAPI_nk_extended.csv`
  - 已完成 Phase 02 形状畸变诊断，当前证据指向：ITO 近红外吸收失真是长波端托平与整体形状失配的主导因素
  - 已完成 Phase 04 空气隙前向预测，当前基线下 `d_air = 2 nm` 与 `5 nm` 的 `max(|ΔR|)` 分别约为 `0.538%` 与 `1.347%`，均高于 `0.2%` 典型噪声线
  - 已完成 Phase 04a 空气隙诊断沙盒：在 `bad-23` 上加入 `d_air` 后，`chi-square` 由 `0.03197` 降至 `0.01619`，`d_air` 收敛到约 `39.9 nm`，但仍未低于 `0.01`
  - 已完成 Phase 04b 空气隙空间定位：对 `bad-20-2` 的 L1/L2/L3 三个 7 参数模型中，L3 (`SAM/PVK`) 的 `chi-square` 最低，但材料参数锁死时仍未优于 6 参数基线；释放材料参数后 `chi-square` 可进一步降至 `0.01932`
  - 已完成 Phase 06 单样本 HDR Dry Run：对 `DEVICE-1-withAg` 的 `150 ms / 2000 ms` 三重复和 `Ag_mirro` 的 `500 us / 10 ms` 单重复完成均值提纯、HDR 融合和绝对校准
  - 已完成 Phase 06c 全量批处理：`DEVICE-1-withAg`、`DEVICE-1-withoutAg`、`DEVICE-2-withAg`、`DEVICE-2-withoutAg` 共 `4` 个样本全部成功落盘，无异常抛出
  - 已完成 Phase 07 双窗反演首轮冒烟：`DEVICE-1-withAg-P1` 与 `DEVICE-1-withoutAg-P1` 均可从 `hdr_curves` 入口完成拟合、写出 `fit_input / fit_summary / fit_curve / optimizer_log / full_spectrum / dual_window_zoom / residual_diagnostics / rear_basin_scan`
  - 已确认当前实测窗口仅覆盖 `498.934-1055.460 nm`，未外推到 `400-498.934 nm` 或 `1055.460-1100 nm`
  - 已确认 `850-1055 nm` 区间的样品与银镜都几乎完全信任长曝光，因此近红外区并非本次 HDR 拼接主战场
  - 已明确暴露银镜短曝光异常：按 `.spe` 元数据的真实曝光时间归一化后，`Ag_mirro-500us` 相对 `Ag_mirro-10ms` 的 `Counts/ms` 比值中位数约为 `12.28`
- 当前未完成内容：
  - 尚未把历史目录完全迁移到 `AGENTS.md` 规定的新结构
  - 尚未形成规范化的 Phase 日志、资源索引和结构化结果台账
  - 尚未将 Phase 06 批量 HDR 输入规范化迁移到 `data/raw/phase06/`
  - Phase 07 当前两例真实样本都存在参数贴边，说明双窗架构已跑通，但材料先验与边界设定仍需继续收敛
  - Phase 08 目前仅建立“固定参数前向重建”链路，尚未引入新的物理先验、层结构变体扫描或跨样本共享参数约束
  - `Phase A-2.1` 已完成 first-pass uncertainty propagation，但尚未扩展到更高维的 surrogate family 或参数化介电函数不确定性
  - `Phase B-2` 当前仍是 front-side optical proxy，而不是完整化学界面模型
  - `Phase C-1a / C-1b` 当前仍是单侧 gap only 的 specular TMM 模型，不含散射、dual-gap 或 gap+BEMA 耦合
  - `Phase D-1` 当前仅覆盖 thickness / roughness / gap 三类结构机制，尚未纳入 composition variation、实验噪声模型与真实分类器训练
  - `constant-glass vs dispersive-glass` 与参数化 band-edge dielectric model 仍未展开

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
│   │   ├── full_stack_microcavity.py
│   │   ├── hdr_absolute_calibration.py
│   │   └── phase07_dual_window.py
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
│       ├── step06_batch_hdr_calibration.py
│       ├── step06_single_sample_hdr_absolute_calibration.py
│       ├── step07_dual_window_inversion.py
│       ├── step07_orthogonal_radar_and_baseline.py
│       ├── step08_theoretical_tmm_modeling.py
│       ├── stepA1_pristine_baseline.py
│       ├── stepA1_1_pvk_seam_audit.py
│       ├── stepA1_2_build_pvk_surrogate_v2.py
│       ├── stepA1_2_rerun_pristine_with_pvk_v2.py
│       ├── stepA2_pvk_thickness_scan.py
│       ├── stepA2_1_pvk_uncertainty_ensemble.py
│       ├── stepB1_rear_bema_sandbox.py
│       ├── stepB2_front_bema_sandbox.py
│       ├── stepC1a_rear_air_gap_sandbox.py
│       ├── stepC1b_front_air_gap_sandbox.py
│       └── stepD1_airgap_discrimination_database.py
├── data/
│   └── processed/
│       ├── CsFAPI_nk_extended.csv
│       ├── phase03_batch_fit/
│       ├── phase04a/
│       ├── phase04b/
│       ├── phase04c/
│       ├── phase06/
│       ├── phase07/
│       ├── phase08/
│       ├── phaseA1/
│       ├── phaseA1_2/
│       ├── phaseA2/
│       ├── phaseA2_1/
│       ├── phaseB1/
│       ├── phaseB2/
│       ├── phaseC1a/
│       ├── phaseC1b/
│       ├── phaseD1/
│       ├── phaseA1_seam_audit/
│       └── target_reflectance.csv
├── resources/
│   ├── digitized/
│   │   ├── phase02_fig2_fapi_optical_constants_digitized.csv
│   │   └── phase02_fig3_csfapi_optical_constants_digitized.csv
│   ├── n-kdata/
│   ├── pvk_ensemble/
│   ├── aligned_full_stack_nk.csv
│   ├── aligned_full_stack_nk_pvk_v2.csv
│   ├── materials_master_db.json
│   ├── GCC-1022系列xlsx.xlsx
│   ├── ITO_20 Ohm_105 nm_e1e2.mat
│   ├── CsFAPI_TL_parameters_and_formulas.md
│   └── MinerU-0.13.1-arm64.dmg
├── results/
│   ├── figures/
│   │   ├── phaseA2/
│   │   ├── phaseA2_1/
│   │   ├── phaseB1/
│   │   ├── phaseB2/
│   │   ├── phaseC1a/
│   │   ├── phaseC1b/
│   │   ├── phaseA1_2/
│   │   ├── phaseA1_seam_audit/
│   │   ├── phaseA1/
│   │   ├── phase08/
│   │   ├── phase07/
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
│       ├── phaseA2/
│       ├── phaseA2_1/
│       ├── phaseB1/
│       ├── phaseB2/
│       ├── phaseC1a/
│       ├── phaseC1b/
│       ├── phaseD1/
│       ├── phaseA1_2/
│       ├── phaseA1_seam_audit/
│       ├── phaseA1/
│       ├── phase08/
│       ├── phase07/
│       ├── phase04c_fingerprint_mapping.md
│       ├── phase04a_air_gap_diagnostic.md
│       ├── phase04b_localization.md
│       ├── phase06_dual_mode_microcavity_sandbox.md
│       ├── phase07_orthogonal_radar_diagnostic.md
│       ├── phase02_shape_diagnostic_report.md
│       ├── phase02_fig2_fapi_digitization_notes.md
│       ├── phase02_fig3_csfapi_digitization_notes.md
│   └── report/
│       ├── README.md
│       ├── report_manifest.csv
│       ├── phaseA1_2_pvk_surrogate_and_pristine/
│       ├── phaseA2_1_pvk_uncertainty_ensemble/
│       ├── phaseA2_pvk_thickness_scan/
│       ├── phaseB1_rear_bema_sandbox/
│       ├── phaseB2_front_bema_sandbox/
│       ├── phaseC1a_rear_air_gap_sandbox/
│       ├── phaseC1b_front_air_gap_sandbox/
│       ├── phaseD1_airgap_discrimination_database/
│       └── ppt_phaseAtoC_assets/
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
- `src/core/` 已开始建立，但目前只承载 Phase 06 的 HDR 逻辑；更早阶段的大量复用代码仍散落在 `src/scripts/`
- 项目根尚无 `README.md`

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

### 4.12 `step06_batch_hdr_calibration.py`

- 文件位置：`src/scripts/step06_batch_hdr_calibration.py`
- 主要职责：批量扫描 OneDrive `0409/cor` 目录中的所有样本前缀，统一复用 `Ag_mirro` HDR 参考，输出项目内标准结果和 OneDrive 原址存档

输入：
- `D:\onedrive\Data\PL\2026\0409\cor\*-cor.csv`
- `resources/GCC-1022系列xlsx.xlsx`

输出：
- `data/processed/phase06_batch/[Sample_Prefix]_curve_table.csv`
- `data/processed/phase06_batch/phase06_batch_summary.csv`
- `results/figures/phase06_batch/[Sample_Prefix]_QA_plot.png`
- `D:\onedrive\Data\PL\2026\0409\cor\hdr_results\[Sample_Prefix]_hdr_curves.csv`
- `D:\onedrive\Data\PL\2026\0409\cor\hdr_results\[Sample_Prefix]_hdr_qa.png`
- `D:\onedrive\Data\PL\2026\0409\cor\hdr_results\00_batch_summary_0409.csv`

### 4.13 `diagnostics_shape_mismatch.py`

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

### 4.13 `step07_dual_window_inversion.py`

- 文件位置：`src/scripts/step07_dual_window_inversion.py`
- 核心依赖：`src/core/phase07_dual_window.py`、`src/core/hdr_absolute_calibration.py`
- 主要职责：将 `Phase 06` HDR 绝对标定与 `Phase 07` 双窗联合反演接成标准流水线，并显式输出反演台账、图表和告警

输入：
- `test_data/phase7_data/*_hdr_curves.csv`
  - 当前仓库内已验证的直接入口
- 或 `test_data/phase7_data/*-cor.csv + *.spe`
  - 若存在原始多曝光数据，则优先复用 `Phase 06` HDR 公共模块现场重建 `R_abs`
- `resources/aligned_full_stack_nk.csv`
- `resources/GCC-1022系列xlsx.xlsx`

核心处理流程：
- 扫描输入目录，优先识别原始多曝光组；若缺少原始文件，则回退到 `*_hdr_curves.csv`
- 统一改写为 `data/processed/phase07/fit_inputs/*_fit_input.csv`，字段至少包含：
  - `Wavelength_nm`
  - `Absolute_Reflectance`
  - `window_label`
  - `with_ag`
- 使用 `src/core/phase07_dual_window.py` 构建 `Glass / ITO / NiOx / SAM / PVK / PVK-C60 Roughness / C60 / Ag(or Air)` 全栈模型
- 在运行时对 `d_rough` 执行 C60 守恒剥离：
  - `d_C60_bulk = max(0, 15 - 0.5 * d_rough)`
- 仅对 `500-650 nm` 与 `860-1055 nm` 执行加权优化，`650-860 nm` 仅保留为 PL/失配诊断区
- 先对 `d_bulk` 做后窗 basin 扫描，再执行 DE 全局搜索和局部 least-squares 精修
- 输出逐波长拟合表、单样本汇总表、优化日志及 4 张图

输出：
- `data/processed/phase07/phase07_source_manifest.csv`
- `data/processed/phase07/phase07_fit_summary.csv`
- `data/processed/phase07/fit_results/*_fit_curve.csv`
- `data/processed/phase07/fit_results/*_fit_summary.csv`
- `results/figures/phase07/*_full_spectrum.png`
- `results/figures/phase07/*_dual_window_zoom.png`
- `results/figures/phase07/*_residual_diagnostics.png`
- `results/figures/phase07/*_rear_basin_scan.png`
- `results/logs/phase07/*_optimizer_log.md`

### 4.14 `step08_theoretical_tmm_modeling.py`

- 文件位置：`src/scripts/step08_theoretical_tmm_modeling.py`
- 核心依赖：`src/core/phase07_dual_window.py`
- 主要职责：冻结 `Phase 07` 最优参数并在实测空间重建理论反射率，形成 `Phase 08` 的批量 TMM 前向建模基线

输入：
- `data/processed/phase07/phase07_fit_summary.csv`
- `data/processed/phase07/fit_inputs/*_fit_input.csv`
- `resources/aligned_full_stack_nk.csv`

核心处理流程：
- 逐样本读取 `Phase 07 fit_summary + fit_input`
- 复用 `calc_macro_reflectance()` 重建全栈物理反射率
- 复用 `apply_front_scattering_observation_model()` 把物理曲线映射回 collected reflectance
- 对后窗额外输出 `z-score` 理论对比与导数相关性，检查干涉形貌是否被保留
- 批量写出理论曲线表、批次摘要、来源清单和理论对比图

输出：
- `data/processed/phase08/phase08_theory_summary.csv`
- `data/processed/phase08/phase08_source_manifest.csv`
- `data/processed/phase08/theory_curves/*_theory_curve.csv`
- `results/figures/phase08/*_theory_vs_measured.png`
- `results/logs/phase08/phase08_theoretical_tmm_modeling.md`

### 4.15 `stepA1_pristine_baseline.py`

- 文件位置：`src/scripts/stepA1_pristine_baseline.py`
- 核心依赖：`src/core/full_stack_microcavity.py`
- 主要职责：建立零缺陷 pristine baseline decomposition，显式拆分 `R_front / R_stack / R_total`

输入：
- `resources/aligned_full_stack_nk.csv`
  - 作为本轮唯一 `n-k` 输入来源

核心处理流程：
- 校验 `aligned_full_stack_nk.csv` 的材料列和 `400-1100 nm / 1 nm` 波长网格
- 强制覆盖玻璃为常数 `n_glass = 1.515`, `k_glass = 0`
- 计算 `Air / Glass` 前表面 Fresnel 反射 `R_front`
- 计算 `Glass -> ITO -> NiOx -> SAM -> PVK -> C60 -> Ag(100 nm) -> Air` 的相干反射 `R_stack`
- 用厚玻璃强度级联计算 `R_total`
- 输出三曲线分解图、三区基线图和 Markdown 结果说明

输出：
- `data/processed/phaseA1/phaseA1_pristine_baseline.csv`
- `results/figures/phaseA1/phaseA1_pristine_decomposition.png`
- `results/figures/phaseA1/phaseA1_pristine_3zones.png`
- `results/logs/phaseA1/phaseA1_pristine_baseline.md`

### 4.16 `stepA1_1_pvk_seam_audit.py`

- 文件位置：`src/scripts/stepA1_1_pvk_seam_audit.py`
- 核心依赖：`src/core/full_stack_microcavity.py`
- 主要职责：对 `749/750 nm` 附近的 PVK seam 做法医式审计，确认接缝来源、结构放大链路与边界条件影响

输入：
- `resources/aligned_full_stack_nk.csv`
- `data/processed/phaseA1/phaseA1_pristine_baseline.csv`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
- `src/scripts/step05c_build_aligned_nk_stack.py`

核心处理流程：
- 抽取 `730-770 nm` 的 `n_PVK / k_PVK / eps1 / eps2` 与一阶导数
- 对照 digitized / extended / aligned 三份 PVK 数据，定位 seam 的引入步骤
- 比较 `Glass/PVK/Air`、`Glass/ITO/NiOx/SAM/PVK/Air` 与完整 stack 的局部反射率，判断 seam 是否被层序放大
- 比较 `finite Ag + Air exit` 与 `semi-infinite Ag`，判断 Ag 终端是否是重要放大器
- 核查 Phase A-1 与全栈主链路是否存在插值、层序或边界条件 bug

输出：
- `data/processed/phaseA1_seam_audit/pvk_seam_local_audit.csv`
- `data/processed/phaseA1_seam_audit/pvk_source_comparison.csv`
- `data/processed/phaseA1_seam_audit/seam_stack_sensitivity.csv`
- `data/processed/phaseA1_seam_audit/seam_ag_boundary_sensitivity.csv`
- `results/figures/phaseA1_seam_audit/*.png`
- `results/logs/phaseA1_seam_audit/phaseA1_seam_audit.md`

### 4.17 `stepA1_2_build_pvk_surrogate_v2.py`

- 文件位置：`src/scripts/stepA1_2_build_pvk_surrogate_v2.py`
- 主要职责：基于 `digitized + extended + aligned v1 + seam audit` 结果，重建 `PVK surrogate v2`，在材料层而不是反射率层消除 `740-780 nm` 带边 seam artifact

输入：
- `resources/aligned_full_stack_nk.csv`
- `data/processed/CsFAPI_nk_extended.csv`
- `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
- `data/processed/phaseA1_seam_audit/pvk_seam_local_audit.csv`
- `data/processed/phaseA1_seam_audit/pvk_source_comparison.csv`

核心处理流程：
- 对 `744-760 nm`、`740-770 nm`、`740-780 nm` 三个候选 transition zone 做局部 surrogate 比较
- 在过渡带左侧用 pre-seam `aligned v1` 锚点拟合单调 `PCHIP` 左参考
- 在过渡带内对 `n` 使用 `smoothstep` 权重桥接到 long-wave extended 趋势
- 在过渡带内对 `k` 使用 `smoothstep + cosine-tail decay`，避免 `750 nm` 起硬清零
- 以 `ΔR_stack(749->750)`、`ΔR_total(749->750)`、`Δeps2`、导数/二阶差分平滑性及 `810-1100 nm` fringe 保真度联合打分，选出主推荐版本

输出：
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `data/processed/phaseA1_2/pvk_v2_candidate_metrics.csv`
- `data/processed/phaseA1_2/pvk_v1_v2_local_comparison.csv`
- `results/figures/phaseA1_2/pvk_v2_nk_local_zoom.png`
- `results/figures/phaseA1_2/pvk_v2_eps_local_zoom.png`
- `results/figures/phaseA1_2/pvk_v2_derivative_local_zoom.png`
- `results/figures/phaseA1_2/pvk_v1_vs_v2_overlay.png`
- `results/logs/phaseA1_2/phaseA1_2_pvk_surrogate_build.md`

### 4.18 `stepA1_2_rerun_pristine_with_pvk_v2.py`

- 文件位置：`src/scripts/stepA1_2_rerun_pristine_with_pvk_v2.py`
- 主要职责：保持几何和其他材料完全不变，仅替换 PVK surrogate 为 v2，重跑 pristine baseline 并完成 v1/v2 定量对照

输入：
- `resources/aligned_full_stack_nk.csv`
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `data/processed/phaseA1/phaseA1_pristine_baseline.csv`
- `data/processed/phaseA1_2/pvk_v2_candidate_metrics.csv`

核心处理流程：
- 复用 `stepA1_pristine_baseline.py` 的常数玻璃与厚玻璃非相干级联口径
- 生成 `R_front / R_stack / R_total` 的 v2 pristine baseline
- 比较 `749->750 nm` 的 seam 步长、`740-780 nm` 的导数/二阶差分平滑性，以及 `810-1100 nm` 后窗 fringe 保真度
- 输出局部 `720-780 nm` 对照图、全谱 v1/v2 对照图与 Phase A-1.2 结论日志

输出：
- `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- `results/figures/phaseA1_2/phaseA1_2_pristine_decomposition.png`
- `results/figures/phaseA1_2/phaseA1_2_pristine_3zones.png`
- `results/figures/phaseA1_2/phaseA1_2_pristine_720_780_zoom.png`
- `results/figures/phaseA1_2/phaseA1_2_pristine_v1_vs_v2_full_spectrum.png`
- `results/logs/phaseA1_2/phaseA1_2_pvk_surrogate_rebuild.md`

### 4.19 `stepA2_pvk_thickness_scan.py`

- 文件位置：`src/scripts/stepA2_pvk_thickness_scan.py`
- 主要职责：基于 `PVK surrogate v2` 扫描 `d_PVK` 对 pristine baseline 的调制规律，建立厚度-条纹相位-谱形图谱

输入：
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `src/scripts/stepA1_pristine_baseline.py`

核心处理流程：
- 固定 `Glass / ITO / NiOx / SAM / C60 / Ag` 与常数玻璃口径，仅扫描 `d_PVK`
- 以 `500-900 nm`、`5 nm` 步长重算 `R_stack / R_total`
- 相对 `700 nm` 参考厚度构造 `ΔR_stack` 与 `ΔR_total`
- 在 `810-1100 nm` 后窗提取主峰、主谷、峰谷间距与代表波长反射率
- 输出 `R_stack / R_total / ΔR` 热力图、peak/valley tracking 图和代表厚度曲线图

输出：
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseA2/phaseA2_pvk_feature_summary.csv`
- `results/figures/phaseA2/phaseA2_R_stack_heatmap.png`
- `results/figures/phaseA2/phaseA2_R_total_heatmap.png`
- `results/figures/phaseA2/phaseA2_deltaR_stack_vs_700nm_heatmap.png`
- `results/figures/phaseA2/phaseA2_deltaR_total_vs_700nm_heatmap.png`
- `results/figures/phaseA2/phaseA2_peak_valley_tracking.png`
- `results/figures/phaseA2/phaseA2_selected_thickness_curves.png`
- `results/logs/phaseA2/phaseA2_pvk_thickness_scan.md`

### 4.20 `stepB1_rear_bema_sandbox.py`

- 文件位置：`src/scripts/stepB1_rear_bema_sandbox.py`
- 主要职责：在保持 `PVK surrogate v2` 与名义几何不变的前提下，仅对 `PVK/C60` 后界面引入 `50/50` solid-solid Bruggeman 粗糙层，建立 rear-only roughness 指纹字典

输入：
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseA2/phaseA2_pvk_feature_summary.csv`

核心处理流程：
- 构建层序：
  - `Glass / ITO / NiOx / SAM / PVK_bulk / BEMA(PVK,C60) / C60_bulk / Ag / Air`
- 固定 Bruggeman 体积分数为 `50% PVK + 50% C60`
- 对 `d_BEMA,rear = 0-30 nm` 做 `1 nm` 扫描
- 执行厚度守恒：
  - `d_PVK,bulk = 700 - 0.5 * d_BEMA,rear`
  - `d_C60,bulk = max(0, 15 - 0.5 * d_BEMA,rear)`
- 计算 `R_stack / R_total / ΔR`，提取后窗峰谷、对比度和最大 `|ΔR|`
- 与 `Phase A-2` 的 `d_PVK` 指纹做后窗 `ΔR` 对照

输出：
- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_feature_summary.csv`
- `results/figures/phaseB1/phaseB1_R_stack_heatmap.png`
- `results/figures/phaseB1/phaseB1_R_total_heatmap.png`
- `results/figures/phaseB1/phaseB1_deltaR_stack_heatmap.png`
- `results/figures/phaseB1/phaseB1_deltaR_total_heatmap.png`
- `results/figures/phaseB1/phaseB1_selected_bema_curves.png`
- `results/figures/phaseB1/phaseB1_peak_valley_tracking.png`
- `results/figures/phaseB1/phaseB1_contrast_vs_bema.png`
- `results/figures/phaseB1/phaseB1_bema_vs_pvk_deltaR_comparison.png`
- `results/logs/phaseB1/phaseB1_rear_bema_sandbox.md`

### 4.21 `stepA2_1_pvk_uncertainty_ensemble.py`

- 文件位置：`src/scripts/stepA2_1_pvk_uncertainty_ensemble.py`
- 主要职责：围绕 `PVK surrogate v2` 的 `740-850 nm` band-edge / absorption-tail 不确定性构建小型 ensemble，并把这组先验扰动传播到 `d_PVK` 与 rear-only BEMA 两类机制

输入：
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseA2/phaseA2_pvk_feature_summary.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_feature_summary.csv`

核心处理流程：
- 以 `PVK surrogate v2` 为 nominal 成员，构建：
  - `nominal`
  - `more_absorptive`
  - `less_absorptive`
- 在 `740-850 nm` 主扰动窗内对 `k(λ)` 施加 smooth envelope 缩放，并用弱耦合 `n(λ)` 修正保证 `n/k/eps1/eps2` 连续且导数平滑
- 额外在 `730-900 nm` 软窗内收尾，避免引入新的 band-edge seam
- 输出 ensemble 的 `n/k/eps/导数` QA 图和 local comparison 表
- 对代表性厚度子集 `d_PVK = 600 / 700 / 800 nm` 重算 `R_stack / R_total / ΔR`
- 对代表性 rear-BEMA 子集 `d_BEMA,rear = 0 / 10 / 20 / 30 nm` 重算 `R_stack / R_total / ΔR`
- 计算 rear-window 与 transition-window 的稳健性摘要，并输出 `robust vs surrogate-sensitive` 特征矩阵

输出：
- `resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_*.csv`
- `data/processed/phaseA2_1/pvk_ensemble_manifest.csv`
- `data/processed/phaseA2_1/pvk_ensemble_local_comparison.csv`
- `data/processed/phaseA2_1/phaseA2_1_thickness_ensemble_scan.csv`
- `data/processed/phaseA2_1/phaseA2_1_thickness_robustness_summary.csv`
- `data/processed/phaseA2_1/phaseA2_1_rear_bema_ensemble_scan.csv`
- `data/processed/phaseA2_1/phaseA2_1_rear_bema_robustness_summary.csv`
- `data/processed/phaseA2_1/phaseA2_1_feature_robustness_matrix.csv`
- `results/figures/phaseA2_1/*.png`
- `results/logs/phaseA2_1/phaseA2_1_pvk_uncertainty_ensemble.md`

### 4.22 `stepB2_front_bema_sandbox.py`

- 文件位置：`src/scripts/stepB2_front_bema_sandbox.py`
- 主要职责：在固定 `SAM` 厚度和名义层厚口径下，使用 `NiOx/PVK` 作为前界面 optical proxy，建立 front-only BEMA 指纹字典，并做代表性 uncertainty spot-check

输入：
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_{nominal,more_absorptive,less_absorptive}.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- `data/processed/phaseA2_1/phaseA2_1_feature_robustness_matrix.csv`

核心处理流程：
- 构建前界面 proxy 层序：
  - `Glass / ITO / NiOx / SAM / BEMA_front(NiOx,PVK) / PVK_bulk / C60 / Ag / Air`
- 固定 Bruggeman 体积分数为 `50% NiOx + 50% PVK`
- 固定 `SAM = 5 nm`、`NiOx = 45 nm`、`C60 = 15 nm`
- 对 `d_BEMA,front = 0-30 nm` 做 `1 nm` 扫描，并执行守恒：
  - `d_PVK,bulk = 700 - d_BEMA,front`
- 输出 `R_stack / R_total / ΔR` 热力图、前窗/过渡区重点图、代表曲线、peak/valley tracking 与三机制对照图
- 对 `d_BEMA,front = 0 / 10 / 20 nm` 做 `nominal / more_absorptive / less_absorptive` spot-check，提取稳健与敏感特征

输出：
- `data/processed/phaseB2/phaseB2_front_bema_scan.csv`
- `data/processed/phaseB2/phaseB2_front_bema_feature_summary.csv`
- `data/processed/phaseB2/phaseB2_front_bema_ensemble_spotcheck.csv`
- `data/processed/phaseB2/phaseB2_front_bema_robustness_summary.csv`
- `results/figures/phaseB2/*.png`
- `results/logs/phaseB2/phaseB2_front_bema_sandbox.md`

### 4.23 `stepC1a_rear_air_gap_sandbox.py`

- 文件位置：`src/scripts/stepC1a_rear_air_gap_sandbox.py`
- 主要职责：仅在 `PVK/C60` 后界面引入真实 rear air gap，建立 low-gap 高分辨指纹字典，并完成 LOD 粗评估与 uncertainty spot-check

输入：
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_{nominal,more_absorptive,less_absorptive}.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- `data/processed/phaseB2/phaseB2_front_bema_scan.csv`

核心处理流程：
- 构建层序：
  - `Glass / ITO / NiOx / SAM / PVK / Air_gap_rear / C60 / Ag / Air`
- rear-gap 被视为真实分离层，不做厚度守恒扣减：
  - `d_PVK = 700 nm` fixed
  - `d_C60 = 15 nm` fixed
- 采用低 gap 高分辨扫描：
  - `0-20 nm`，步长 `0.5 nm`
  - 额外补 `25 / 30 / 40 / 50 nm`
- 输出 `R_stack / R_total / ΔR` 热力图、transition/rear 响应图、branch-aware peak/valley tracking、波数轴对照和四机制比较图
- 对 `1 / 2 / 3 / 5 / 10 nm` 给出基于 `ΔR_noise ≈ 0.2%` 的理论 LOD 粗评估
- 对 `0 / 2 / 5 / 10 nm` 做三成员 ensemble spot-check，判断哪些结论稳健、哪些绝对量敏感

输出：
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_scan.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_feature_summary.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_lod_summary.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_ensemble_spotcheck.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_robustness_summary.csv`
- `results/figures/phaseC1a/*.png`
- `results/logs/phaseC1a/phaseC1a_rear_air_gap_sandbox.md`

### 4.24 `stepC1b_front_air_gap_sandbox.py`

- 文件位置：`src/scripts/stepC1b_front_air_gap_sandbox.py`
- 主要职责：仅在 `SAM/PVK` 前界面引入真实 front air-gap，建立 low-gap 高分辨指纹字典，并完成 LOD 粗评估、uncertainty spot-check 与五机制对照

输入：
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_{nominal,more_absorptive,less_absorptive}.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseB2/phaseB2_front_bema_scan.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_scan.csv`

核心处理流程：
- 构建层序：
  - `Glass / ITO / NiOx / SAM / Air_gap_front / PVK / C60 / Ag / Air`
- front-gap 被视为真实分离层，不做厚度守恒扣减：
  - `d_SAM = 5 nm` fixed
  - `d_PVK = 700 nm` fixed
  - `d_C60 = 15 nm` fixed
- 采用低 gap 高分辨扫描：
  - `0-20 nm`，步长 `0.5 nm`
  - 额外补 `25 / 30 / 40 / 50 nm`
- 输出 `R_stack / R_total / ΔR` 热力图、front/transition/rear 分窗响应图、rear-window peak/valley tracking、波数轴对照和五机制比较图
- 对 `1 / 2 / 3 / 5 / 10 nm` 给出基于 `ΔR_noise ≈ 0.2%` 的理论 LOD 粗评估
- 对 `0 / 2 / 5 / 10 nm` 做三成员 ensemble spot-check，判断哪些结论稳健、哪些绝对量敏感

输出：
- `data/processed/phaseC1b/phaseC1b_front_air_gap_scan.csv`
- `data/processed/phaseC1b/phaseC1b_front_air_gap_feature_summary.csv`
- `data/processed/phaseC1b/phaseC1b_front_air_gap_lod_summary.csv`
- `data/processed/phaseC1b/phaseC1b_front_air_gap_ensemble_spotcheck.csv`
- `data/processed/phaseC1b/phaseC1b_front_air_gap_robustness_summary.csv`
- `results/figures/phaseC1b/*.png`
- `results/logs/phaseC1b/phaseC1b_front_air_gap_sandbox.md`

### 4.25 `stepPPT_phaseAtoC_assets.py`

- 文件位置：`src/scripts/stepPPT_phaseAtoC_assets.py`
- 主要职责：基于 `Phase A-1.2` 到 `Phase C-1b` 的既有 `processed/report` 结果，重绘一套统一风格的 `R_total-only` PPT 汇报资产，不引入任何新的物理模拟

输入：
- `data/processed/phaseA1/phaseA1_pristine_baseline.csv`
- `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- `data/processed/phaseA1_2/pvk_v1_v2_local_comparison.csv`
- `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- `data/processed/phaseB2/phaseB2_front_bema_scan.csv`
- `data/processed/phaseC1a/phaseC1a_rear_air_gap_scan.csv`
- `data/processed/phaseC1b/phaseC1b_front_air_gap_scan.csv`
- `results/report/phaseA*_*/PHASE_*.md`
- `results/report/phaseB*_*/PHASE_*.md`
- `results/report/phaseC*_*/PHASE_*.md`

核心处理流程：
- 统一重绘 baseline、thickness、rear-BEMA、front-BEMA、rear-gap、front-gap 的 `R_total / Delta R_total` 主图
- 为每一页输出 `main_figure.png / secondary_figure.png / slide_text.md / source_manifest.md`
- 生成 `07_summary/mechanism_summary_matrix.png` 和 `appendix_pvk_surrogate_fix` 两张附录图
- 生成总 `00_manifest.md`，用于快速拼装 Phase A→C 的 PPT 叙事线
- 同步更新 `results/report/README.md` 与 `report_manifest.csv`

输出：
- `results/report/ppt_phaseAtoC_assets/00_manifest.md`
- `results/report/ppt_phaseAtoC_assets/01_baseline/*`
- `results/report/ppt_phaseAtoC_assets/02_thickness/*`
- `results/report/ppt_phaseAtoC_assets/03_rear_bema/*`
- `results/report/ppt_phaseAtoC_assets/04_front_bema/*`
- `results/report/ppt_phaseAtoC_assets/05_rear_gap/*`
- `results/report/ppt_phaseAtoC_assets/06_front_gap/*`
- `results/report/ppt_phaseAtoC_assets/07_summary/*`
- `results/report/ppt_phaseAtoC_assets/appendix_pvk_surrogate_fix/*`

### 4.26 `stepD1_airgap_discrimination_database.py`

- 文件位置：`src/scripts/stepD1_airgap_discrimination_database.py`
- 主要职责：在 realistic `d_PVK + front/rear roughness` 背景上统一建立 `thickness nuisance / roughness nuisance / front-gap overlay / rear-gap overlay` 的 `R_total` 判别数据库，为后续 air-gap 识别算法比较提供结构化输入

输入：
- `resources/aligned_full_stack_nk_pvk_v2.csv`
- `results/report/phaseA2_pvk_thickness_scan/PHASE_A2_REPORT.md`
- `results/report/phaseA2_1_pvk_uncertainty_ensemble/PHASE_A2_1_REPORT.md`
- `results/report/phaseB1_rear_bema_sandbox/PHASE_B1_REPORT.md`
- `results/report/phaseB2_front_bema_sandbox/PHASE_B2_REPORT.md`
- `results/report/phaseC1a_rear_air_gap_sandbox/PHASE_C1A_REPORT.md`
- `results/report/phaseC1b_front_air_gap_sandbox/PHASE_C1B_REPORT.md`

核心处理流程：
- 复用 `full_stack_microcavity.py` 的组合入口，在同一 coherent stack 中统一加入 `d_PVK`、front/rear BEMA background 与单侧 gap overlay
- 设定 realistic baseline：`d_PVK=700 nm, d_BEMA_front=10 nm, d_BEMA_rear=20 nm, no gap`
- 构建五类 logical family：
  - `thickness_nuisance`
  - `front_roughness_nuisance`
  - `rear_roughness_nuisance`
  - `front_gap_on_background`
  - `rear_gap_on_background`
- 额外保留 `background_anchor` 作为 reference tracking family
- 对每个 logical case 输出：
  - `R_total`
  - `Delta_R_total_vs_reference`
  - front / transition / rear 窗口特征
  - rear-window shift matching
  - peak/valley 工程摘要
- 进一步生成 feature scatter / boxplots / discrimination atlas，并同步写出 report 层资产

输出：
- `data/processed/phaseD1/phaseD1_case_manifest.csv`
- `data/processed/phaseD1/phaseD1_rtotal_database.csv`
- `data/processed/phaseD1/phaseD1_feature_database.csv`
- `data/processed/phaseD1/phaseD1_discrimination_summary.csv`
- `results/figures/phaseD1/*.png`
- `results/logs/phaseD1/phaseD1_airgap_discrimination_database.md`
- `results/report/phaseD1_airgap_discrimination_database/`

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

D:\onedrive\Data\PL\2026\0409\cor\*-cor.csv
resources/GCC-1022系列xlsx.xlsx
    -> step06_batch_hdr_calibration.py
    -> src/core/hdr_absolute_calibration.py (公共 Ag HDR 参考 -> 逐样本 HDR 拼接 -> 绝对反射率 -> 汇总台账)
    -> data/processed/phase06_batch/*_curve_table.csv
    -> data/processed/phase06_batch/phase06_batch_summary.csv
    -> results/figures/phase06_batch/*_QA_plot.png
    -> D:\onedrive\Data\PL\2026\0409\cor\hdr_results\*_hdr_curves.csv
    -> D:\onedrive\Data\PL\2026\0409\cor\hdr_results\*_hdr_qa.png
    -> D:\onedrive\Data\PL\2026\0409\cor\hdr_results\00_batch_summary_0409.csv

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

test_data/phase7_data/*_hdr_curves.csv
or test_data/phase7_data/*-cor.csv + *.spe
resources/GCC-1022系列xlsx.xlsx
resources/aligned_full_stack_nk.csv
    -> step07_dual_window_inversion.py (原始多曝光/HDR 中间件双入口 -> 标准化 fit_input -> 双窗加权 TMM -> basin 扫描 -> DE + least-squares -> 图表 / 日志 / 台账)
    -> data/processed/phase07/phase07_source_manifest.csv
    -> data/processed/phase07/phase07_fit_summary.csv
    -> data/processed/phase07/fit_inputs/*_fit_input.csv
    -> data/processed/phase07/fit_results/*_fit_curve.csv
    -> data/processed/phase07/fit_results/*_fit_summary.csv
    -> results/figures/phase07/*_full_spectrum.png
    -> results/figures/phase07/*_dual_window_zoom.png
    -> results/figures/phase07/*_residual_diagnostics.png
    -> results/figures/phase07/*_rear_basin_scan.png
    -> results/logs/phase07/*_optimizer_log.md

data/processed/phase07/phase07_fit_summary.csv
data/processed/phase07/fit_inputs/*_fit_input.csv
resources/aligned_full_stack_nk.csv
    -> step08_theoretical_tmm_modeling.py (冻结 Phase 07 参数 -> 重建物理反射率 -> 前表面散射映射 -> 后窗 z-score 理论核对 -> 批量输出)
    -> data/processed/phase08/phase08_theory_summary.csv
    -> data/processed/phase08/phase08_source_manifest.csv
    -> data/processed/phase08/theory_curves/*_theory_curve.csv
    -> results/figures/phase08/*_theory_vs_measured.png
    -> results/logs/phase08/phase08_theoretical_tmm_modeling.md

resources/aligned_full_stack_nk.csv
    -> stepA1_pristine_baseline.py (常数玻璃覆盖 -> Fresnel 前表面 -> 后侧相干 stack -> 厚玻璃非相干级联 -> 分解图 / 三区图 / 日志)
    -> data/processed/phaseA1/phaseA1_pristine_baseline.csv
    -> results/figures/phaseA1/phaseA1_pristine_decomposition.png
    -> results/figures/phaseA1/phaseA1_pristine_3zones.png
    -> results/logs/phaseA1/phaseA1_pristine_baseline.md

resources/aligned_full_stack_nk.csv
data/processed/phaseA1/phaseA1_pristine_baseline.csv
data/processed/CsFAPI_nk_extended.csv
resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv
src/scripts/step05c_build_aligned_nk_stack.py
    -> stepA1_1_pvk_seam_audit.py (PVK seam 局部法医审计 -> 三源追溯 -> 堆栈放大比较 -> Ag 边界对照 -> 代码级排查)
    -> data/processed/phaseA1_seam_audit/*.csv
    -> results/figures/phaseA1_seam_audit/*.png
    -> results/logs/phaseA1_seam_audit/phaseA1_seam_audit.md

resources/aligned_full_stack_nk.csv
data/processed/CsFAPI_nk_extended.csv
resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv
data/processed/phaseA1_seam_audit/*.csv
    -> stepA1_2_build_pvk_surrogate_v2.py (候选 transition zone 扫描 -> smoothstep n bridge + cosine-tail k decay -> seam 指标 / 平滑性 / fringe 保真度联合打分)
    -> resources/aligned_full_stack_nk_pvk_v2.csv
    -> data/processed/phaseA1_2/pvk_v2_candidate_metrics.csv
    -> data/processed/phaseA1_2/pvk_v1_v2_local_comparison.csv
    -> results/figures/phaseA1_2/pvk_v2_*.png
    -> results/logs/phaseA1_2/phaseA1_2_pvk_surrogate_build.md

resources/aligned_full_stack_nk_pvk_v2.csv
data/processed/phaseA1/phaseA1_pristine_baseline.csv
    -> stepA1_2_rerun_pristine_with_pvk_v2.py (仅替换 PVK surrogate -> pristine baseline rerun -> seam 步长 / 局部平滑性 / 后窗 fringe 保真度对照)
    -> data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv
    -> results/figures/phaseA1_2/phaseA1_2_pristine_*.png
    -> results/logs/phaseA1_2/phaseA1_2_pvk_surrogate_rebuild.md

resources/aligned_full_stack_nk_pvk_v2.csv
    -> stepA2_pvk_thickness_scan.py (扫描 d_PVK -> pristine baseline rerun -> rear-window peak/valley tracking -> R/ΔR 热力图)
    -> data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
    -> data/processed/phaseA2/phaseA2_pvk_feature_summary.csv
    -> results/figures/phaseA2/phaseA2_*.png
    -> results/logs/phaseA2/phaseA2_pvk_thickness_scan.md

resources/aligned_full_stack_nk_pvk_v2.csv
data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv
data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
    -> stepB1_rear_bema_sandbox.py (rear-only PVK/C60 BEMA -> 厚度守恒 -> R/ΔR 热力图 -> d_PVK 正交对照)
    -> data/processed/phaseB1/phaseB1_rear_bema_scan.csv
    -> data/processed/phaseB1/phaseB1_rear_bema_feature_summary.csv
    -> results/figures/phaseB1/phaseB1_*.png
    -> results/logs/phaseB1/phaseB1_rear_bema_sandbox.md

resources/aligned_full_stack_nk_pvk_v2.csv
data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
data/processed/phaseB1/phaseB1_rear_bema_scan.csv
    -> stepA2_1_pvk_uncertainty_ensemble.py (PVK nominal/more/less absorptive ensemble -> thickness 子集传播 -> rear-BEMA 子集传播 -> robustness summary / feature matrix)
    -> resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_*.csv
    -> data/processed/phaseA2_1/*.csv
    -> results/figures/phaseA2_1/*.png
    -> results/logs/phaseA2_1/phaseA2_1_pvk_uncertainty_ensemble.md

resources/aligned_full_stack_nk_pvk_v2.csv
resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_*.csv
data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
data/processed/phaseB1/phaseB1_rear_bema_scan.csv
    -> stepB2_front_bema_sandbox.py (front-only NiOx/PVK proxy BEMA -> PVK 守恒扣减 -> R/ΔR 热力图 -> front/rear/thickness 对照 -> lightweight uncertainty spot-check)
    -> data/processed/phaseB2/*.csv
    -> results/figures/phaseB2/*.png
    -> results/logs/phaseB2/phaseB2_front_bema_sandbox.md

resources/aligned_full_stack_nk_pvk_v2.csv
resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_*.csv
data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
data/processed/phaseB1/phaseB1_rear_bema_scan.csv
data/processed/phaseB2/phaseB2_front_bema_scan.csv
    -> stepC1a_rear_air_gap_sandbox.py (rear air-gap only -> low-gap high-resolution scan -> branch-aware tracking -> LOD粗评估 -> thickness/rear-BEMA/front-BEMA 四机制对照 -> uncertainty spot-check)
    -> data/processed/phaseC1a/*.csv
    -> results/figures/phaseC1a/*.png
    -> results/logs/phaseC1a/phaseC1a_rear_air_gap_sandbox.md

resources/aligned_full_stack_nk_pvk_v2.csv
resources/pvk_ensemble/aligned_full_stack_nk_pvk_ens_*.csv
data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv
data/processed/phaseB2/phaseB2_front_bema_scan.csv
data/processed/phaseC1a/phaseC1a_rear_air_gap_scan.csv
    -> stepC1b_front_air_gap_sandbox.py (front air-gap only -> low-gap high-resolution scan -> front/transition/rear 分窗响应 -> LOD粗评估 -> thickness/front-BEMA/rear-gap 五机制对照 -> uncertainty spot-check)
    -> data/processed/phaseC1b/*.csv
    -> results/figures/phaseC1b/*.png
    -> results/logs/phaseC1b/phaseC1b_front_air_gap_sandbox.md

selected phase outputs
    -> results/report/ (精选 CSV / PNG / Markdown 汇报层)
    -> results/report/phaseA1_2_pvk_surrogate_and_pristine/*
    -> results/report/phaseA2_1_pvk_uncertainty_ensemble/*
    -> results/report/phaseA2_pvk_thickness_scan/*
    -> results/report/phaseB1_rear_bema_sandbox/*
    -> results/report/phaseB2_front_bema_sandbox/*
    -> results/report/phaseC1a_rear_air_gap_sandbox/*
    -> results/report/phaseC1b_front_air_gap_sandbox/*
    -> results/report/ppt_phaseAtoC_assets/*
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
10. `step07_dual_window_inversion.py` 则把 `Phase 06 HDR`、`Phase 05c 对齐 n-k` 和 `Phase 07 双窗反演` 接成当前主干闭环，能够直接把 `hdr_curves` 样本转为标准化拟合输入、参数表、逐波长拟合表、优化日志和诊断图
11. `step08_theoretical_tmm_modeling.py` 在不新增拟合自由度的前提下，把 `Phase 07` 的最优参数固化为可复现的前向建模输出，便于后续做结构假设对比和跨样本理论审计
12. `stepA1_pristine_baseline.py` 则进一步把全栈材料表压缩为最严格的零缺陷参考谱，显式拆开 `R_front`、`R_stack` 与 `R_total`
13. `stepA1_1_pvk_seam_audit.py` 则把 Phase A-1 中暴露的 `749/750 nm` 台阶追溯到 PVK seam，本质上为后续 repair 提供证据链而不是直接修复
14. `stepA1_2_build_pvk_surrogate_v2.py` 在材料层重建 `PVK surrogate v2`，把 `749/750 nm` 的跳点降级为连续 band-edge 过渡
15. `stepA1_2_rerun_pristine_with_pvk_v2.py` 进一步验证修复后 `ΔR_stack(749->750)` 与 `ΔR_total(749->750)` 已显著压低，同时后窗 fringe 保持稳定
16. `stepA2_pvk_thickness_scan.py` 进一步把 repaired pristine baseline 推进为厚度-条纹相位图谱，可直接区分“厚度导致的全局 fringe 漂移”与“界面缺陷导致的局部扰动”
17. `stepB1_rear_bema_sandbox.py` 则把 rear-only `PVK/C60` intermixing 单独拆成独立机制，得到与 `d_PVK` 可比较的后界面粗糙指纹
18. `stepA2_1_pvk_uncertainty_ensemble.py` 则把 `PVK surrogate v2` 的 band-edge 不确定性正式传播到 thickness 与 rear-BEMA 两类机制，用于区分高置信度结构指纹和 surrogate-sensitive 特征
19. `stepB2_front_bema_sandbox.py` 则把前界面 `NiOx/PVK` optical proxy 单独拆成第三类机制，形成与 thickness / rear-BEMA 并列的 front-side roughness 指纹
20. `stepC1a_rear_air_gap_sandbox.py` 则把真实 rear air-gap 作为第四类机制单独引入，提供与 thickness / front-BEMA / rear-BEMA 可直接比较的分离层指纹与理论 LOD
21. 当前脚本链已经具备“文献数字化 / 椭偏报告解析 -> 材料数据库 -> 全栈对齐 `n-k` 表 -> pristine baseline decomposition -> seam forensic audit -> surrogate rebuild -> pristine rerun -> thickness scan -> rear-only BEMA sandbox -> PVK uncertainty propagation -> front-only BEMA sandbox -> rear air-gap sandbox -> 宏观正交界面指纹字典 -> 双窗联合反演 -> 固定参数理论重建”的前向-反演联合基线

## 6. Key Physical / Numerical Assumptions

当前实现中最重要的物理和数值假设如下：

- `step02` 反演窗口为 `850-1100 nm`，`step03_forward_simulation.py` 的前向预测窗口扩展到 `850-1500 nm`
- `step04a_air_gap_diagnostic.py` 在 `850-1100 nm` 的实验采样网格上比较 `good-21` 与 `bad-23`，不重采样到均匀 1 nm 网格
- 玻璃厚板不作为相干层直接进入 TMM 相位矩阵
- ITO 数据若波长量级大于 `2000`，则按 Angstrom 自动转为 nm
- 厂家银镜基准若数值范围大于 `1.5`，则按百分比转为 `0-1` 小数
- PVK 的近红外色散来源为 [LIT-0001] Fig. 3 的 `ITO/CsFAPI` 数字化 `n` 曲线，并通过 Cauchy 模型外推到 `1100 nm`
- `750-1100 nm` 内强制采用 `k = 0`
- Phase A-1.2 新增 `PVK surrogate v2`：
  - 仅对 `740-780 nm` band-edge 区域做局部 surrogate rebuild
  - 主推荐 transition zone 为 `740-780 nm`
  - `n` 用 `smoothstep` 桥接到 long-wave 趋势，`k` 用 `smoothstep + cosine-tail` 衰减到透明尾
  - 不再允许 `750 nm` 起 `k = 0` 的硬切换
- Phase A-2 固定 `PVK surrogate v2` 与其余材料参数，仅扫描 `d_PVK`，因此当前厚度灵敏度图谱反映的是“零缺陷微腔光程变化”，不是缺陷调制叠加结果
- Phase B-1 固定 `PVK surrogate v2` 与名义层厚，仅在 `PVK/C60` 后界面加入 `50/50` solid-solid BEMA，并执行 `PVK/C60` 守恒扣减，因此当前 rear-BEMA 指纹反映的是“后界面 intermixing + 相邻层变薄”的联合机制
- Phase A-2.1 进一步引入三成员 PVK uncertainty ensemble：
  - `nominal` 直接沿用 `PVK surrogate v2`
  - `more_absorptive` 在 `740-850 nm` 增强 `k(λ)` 吸收尾，并做弱耦合 `n(λ)` 上调
  - `less_absorptive` 在 `740-850 nm` 削弱 `k(λ)` 吸收尾，并做弱耦合 `n(λ)` 下调
  - 三成员都要求在 `730-900 nm` 保持连续、无新 seam，且不破坏 `850-1100 nm` 的 nominal rear-window 趋势
- 当前 A-2.1 的 first-pass 传播结果表明：
  - `d_PVK` 的 rear-window 相位/峰位漂移结论对 surrogate 选择高度稳健
  - rear-only BEMA 的“局部包络/轻微振幅扰动”结论仍成立，但其幅值量级对 band-edge 先验敏感
  - 绝对 `R_total(780 nm)` 一类 band-edge 邻域观测量不宜直接作为高置信度结构归因特征
- Phase B-2 进一步引入 front-only `NiOx/PVK` proxy BEMA：
  - 层序固定为 `Glass / ITO / NiOx / SAM / BEMA_front(NiOx,PVK) / PVK_bulk / C60 / Ag / Air`
  - `SAM`、`NiOx` 与 `C60` 厚度固定不变
  - 守恒仅作用于 `PVK`：`d_PVK,bulk = 700 - d_BEMA,front`
  - 当前结果表明 front-BEMA 的主响应偏向 `400-810 nm` 的前窗/过渡区，而不是 rear-window 主相位机制
- Phase B-2 的 spot-check 进一步表明：
  - front-window 平均 `ΔR` 属于较稳健特征
  - transition/rear 振幅量级与 `R_total(780 nm)` 仍会受到 surrogate 先验影响
- Phase C-1a 进一步引入 rear air-gap only：
  - 层序固定为 `Glass / ITO / NiOx / SAM / PVK / Air_gap_rear / C60 / Ag / Air`
  - rear-gap 被视为真实分离层，不做 `PVK/C60` 厚度守恒扣减
  - 低 gap 区域采用 `0-20 nm / 0.5 nm` 高分辨扫描，并补 `25 / 30 / 40 / 50 nm`
- 当前 C-1a 的 first-pass 结果表明：
  - rear-gap 的主敏感窗口位于 transition/rear，理论 LOD 在 `1 nm` 级已经超过 `0.2%`
  - rear-gap 比 rear-BEMA 更强、更非线性，也比 thickness 更不像全局平移
  - rear-gap 可作为与 thickness / rear-BEMA / front-BEMA 并列的第四类机制字典
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
- Phase 07 的拟合窗口固定为：
  - `500-650 nm` 前窗
  - `650-860 nm` 屏蔽区
  - `860-1055 nm` 后窗
- Phase 07 的粗糙层已改为 `50% PVK + 50% C60` 的 BEMA，而非旧 Phase 的 `PVK + Air`
- Phase 07 强制执行 C60 守恒：
  - `d_C60_bulk = max(0, 15 - 0.5 * d_rough)`
- Phase 07 中 `d_rough` 的物理上限固定为 `30 nm`
- Phase 07 的窗口归一化尺度采用：
  - `scale_w = max(median(R_meas_w), 1.4826 * MAD(R_meas_w), 0.005)`
- Phase 07 的厚玻璃总反射率采用：
  - `R_total = R_front + (T_front^2 * R_stack) / (1 - R_front * R_stack)`
- Phase 07 的优化策略为：
  - `d_bulk` 后窗 basin 扫描
  - basin 内 DE 全局搜索
  - 稀疏双窗 least-squares 精修
  - 全分辨率回投与打分

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

### 8.15 Phase 06c 的 OneDrive 原址存档会引入双份结果副本

- 当前 `step06_batch_hdr_calibration.py` 同时向项目目录和 `D:\onedrive\Data\PL\2026\0409\cor\hdr_results\` 写出结果
- 这能满足实验侧浏览需求，但也会带来“哪一份是权威结果”的维护风险
- 后续应在文档中明确：项目目录为标准分析产物，OneDrive 目录为实验侧镜像存档

### 8.16 Phase 07 首轮真实样本出现多参数贴边

- 当前 `DEVICE-1-withAg-P1` 与 `DEVICE-1-withoutAg-P1` 都已完整跑通 `step07_dual_window_inversion.py`
- 但首轮结果显示：
  - `ito_alpha` 与 `pvk_b_scale` 多次贴近上/下边界
  - `withAg` 样本的 `d_bulk` 更靠近下边界
  - `650-860 nm` 的 masked 残差仍明显偏大
- 这说明当前 Phase 07 已经解决“链路能否跑通”的工程问题，但还没有解决“真实样本是否已被充分约束”的物理问题
- 后续优先检查方向：
  - `ITO / NiOx / PVK` 长波先验是否过紧
  - `withAg / withoutAg` 是否应采用不同的参数边界
  - 是否需要把后窗 fringe 形状约束从 tie-break 提升为正式辅助残差

## 9. Recent Update Summary

- 更新时间：`2026-04-13`
- 当前 Phase：`Phase D-1`
- 本次新增/修改：
  - 新增 `src/scripts/stepD1_airgap_discrimination_database.py`，基于 realistic `d_PVK + front/rear roughness` 背景统一生成 `R_total` 判别数据库
  - 在 `src/core/full_stack_microcavity.py` 新增组合前向入口，允许在同一 coherent stack 中叠加 `front/rear BEMA background` 与单侧 `front-gap / rear-gap`
  - 新增 `data/processed/phaseD1/`、`results/figures/phaseD1/`、`results/logs/phaseD1/` 与 `results/report/phaseD1_airgap_discrimination_database/`
  - 产出 case manifest、全谱库、窗口特征库、rear shift analysis、family summary 和 discrimination atlas
- 已验证结论：
  - 局部 thickness nuisance 在 realistic background 上仍主要表现为 rear-window fringe 的高可解释 shift
  - front / rear roughness 更像 envelope / amplitude perturbation，而不是 rigid shift
  - front-gap / rear-gap 叠加 roughness background 后，仍保留不同的窗口分布与非刚性 residual 指纹
- 仍待验证：
  - 还没有正式训练或比较分类器，当前数据库仍是算法讨论输入，不是最终识别器
  - composition variation 尚未纳入，因此当前 separability 仅覆盖 thickness / roughness / gap 三类结构机制
  - 仍是 specular TMM；散射、dual-gap、gap+BEMA 联合机制与实验噪声模型尚未引入

## 10. Recommended Next Actions

建议后续优先处理以下事项：

1. 优先进入 `Phase C-2 gap vs BEMA coupled comparison`，在 separation vs intermixing 两类缺陷之间建立系统混淆边界
2. 并行评估是否需要新增 `Phase C-3 front-gap vs rear-gap symmetry comparison`，对前后界面分离机制做统一归一化比较
3. 回查 `Ag_mirro-500us` 与 `Ag_mirro-10ms` 的归一化失配来源，优先检查仪器门控、导出流程与实际曝光标签
4. 基于 `phase07_fit_summary.csv` 的贴边结果，重新评估 `ito_alpha`、`pvk_b_scale` 与 `niox_k` 的边界和先验
5. 建立 `data/raw/phase06/` 或稳定数据索引，把 OneDrive 外部路径纳入规范化入口

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

## Phase 07 Implementation Update (2026-04-10)

- Current Phase: `Phase 07`
- Update summary:
  - 已新增 `src/core/phase07_dual_window.py`，将 Phase 07 的全栈 forward model、双窗残差、C60 守恒、后窗 basin 扫描、DE 全局搜索、least-squares 精修和四类图表输出统一封装。
  - 已新增 `src/scripts/step07_dual_window_inversion.py`，支持“原始多曝光优先，`*_hdr_curves.csv` 回退”的双入口数据管线。
  - 已建立 `data/processed/phase07/fit_inputs/`、`data/processed/phase07/fit_results/`、`results/figures/phase07/` 与 `results/logs/phase07/` 的标准输出目录。
  - 已生成 `phase07_source_manifest.csv`、`phase07_fit_summary.csv`、两例样本的逐波长拟合表、优化日志和 8 张诊断图。
- Data flow:
  - `test_data/phase7_data/*_hdr_curves.csv`
  - `src/scripts/step07_dual_window_inversion.py`
  - `src/core/phase07_dual_window.py`
  - `data/processed/phase07/fit_inputs/*_fit_input.csv`
  - `data/processed/phase07/fit_results/*_fit_curve.csv`
  - `data/processed/phase07/fit_results/*_fit_summary.csv`
  - `results/figures/phase07/*`
  - `results/logs/phase07/*_optimizer_log.md`
- Verified results:
  - `C60` 守恒检查通过：`d_rough = 0/10/20/30 nm` 时，`d_C60_bulk = 15/10/5/0 nm`。
  - `withAg / withoutAg` 两种终端边界下，前向模型均返回有限且 `0-1` 范围内的反射率。
  - 两个现有 `Phase 07` 样本都已完整跑通拟合与落盘流程。
  - 前窗与后窗的窗口尺度均未触发小于 `0.005` 的权重爆炸。
- Risks / pending checks:
  - `DEVICE-1-withAg-P1` 与 `DEVICE-1-withoutAg-P1` 当前都出现不同程度的贴边解，说明真实样本的参数空间仍未被充分约束。
  - `650-860 nm` 的 masked 残差仍然较大，当前只被解释为 PL/模型失配形态，还未进入更强的背景建模。
  - 需要进一步判断 `withAg / withoutAg` 是否必须采用不同边界或更强先验。

## Phase 07 Z-Score Rear-Window Update (2026-04-11)

- Current Phase: `Phase 07`
- Update summary:
  - 已将 `src/core/phase07_dual_window.py` 的后窗残差从“绝对反射率加权差”切换为“Z-Score 形态差”，前窗 `500-650 nm` 仍保持绝对值残差。
  - 已恢复 `ito_alpha` 的默认边界到 `[0.0, 5.0]`，避免后窗极弱信号下由绝对强度误差把 ITO 长波吸收强行挤到非物理区域。
  - 已新增 `src/scripts/step07_zscore_sanity_check.py`，用于对 `DEVICE-1-withAg-P1` 执行后窗峰谷物理自证、输出平滑对比图，并直接跑通 Z-Score 版本拟合。
- Data flow:
  - `test_data/phase7_data/DEVICE-1-withAg-P1_hdr_curves.csv`
  - `src/scripts/step07_zscore_sanity_check.py`
  - `src/core/phase07_dual_window.py`
  - `results/figures/phase07/phase07_device_1_withag_p1_rear_sanity_check.png`
  - `results/figures/phase07/phase07_device_1_withag_p1_dual_window_zoom.png`
  - `data/processed/phase07/fit_results/phase07_device_1_withag_p1_fit_summary.csv`
- Verified results:
  - 后窗 `860-1055 nm` 经强平滑后识别到一组主极值：`lambda_peak = 870.774 nm`，`lambda_valley = 1034.331 nm`。
  - 基于 `aligned_full_stack_nk.csv` 中 `PVK` 折射率插值得到 `n_avg = 2.4289`，相邻峰谷公式给出 `d_estimate = 566.8 nm`。
  - 该值略低于原先预期的 `600-800 nm`，但仍处在同一量级，说明后窗仍保留可解释的干涉形态信息，适合继续用于相位/形态学约束。
  - Z-Score 拟合后，`DEVICE-1-withAg-P1` 的最佳解落在 `d_bulk = 810.3 nm`，后窗残差成本降为 `0.0238`，右侧双窗图已改为 `z_meas / z_model` 直接对比。
- Risks / pending checks:
  - 当前峰谷推算厚度 `566.8 nm` 与 Z-Score 拟合最优 `d_bulk = 810.3 nm` 仍存在显著偏差，提示“单一峰谷公式”与“多层完整 TMM 相位”之间仍有系统差。
  - `rear_derivative_correlation` 仍偏低，说明后窗虽有形态信息，但噪声、长波色散与多层耦合仍在削弱相位锁定能力。
  - `pvk_b_scale` 继续贴在下界，后续仍需评估是否应进一步收紧 PVK 长波色散先验，或为后窗增加更稳定的包络/频域约束。

## Phase 07 Baseline Finalization Update (2026-04-11)

- Current Phase: `Phase 07`
- Update summary:
  - 已将 `src/core/full_stack_microcavity.py` 的默认几何口径同步为 `Glass / ITO(100) / NiOx(45) / SAM(5) / PVK(700) / C60(15) / Ag(100) / Air`，终止旧 `19.595/22.443/500/18.494` 默认值与 Phase 07 主链路并存的混乱。
  - 已在 `src/core/phase07_dual_window.py` 中新增 `front_scale` 参数，仅作用于前窗 `500-650 nm` 的观测层反射率，用于吸收积分球/探头未完整收集镜面反射所导致的宏观几何漏光。
  - 已将全谱诊断图的 `650-860 nm` masked 区改为仅视觉用途的平滑桥接，不参与 cost 计算。
- Verified results:
  - 使用真实样本 `DEVICE-1-withAg-P1` 重新拟合后，前窗 cost 从旧版的数量级显著压低至 `0.0122`，后窗 Z-Score cost 为 `0.0142`，总 cost 为 `0.0264`。
  - 最优前窗几何缩放为 `front_scale = 0.2172`，与前期独立探测得到的 `~0.22` 一致，支持“前端几何收集效率损失”而非“材料吸收缺失”的解释。
  - 后窗最佳解仍落在 `d_bulk = 815.3 nm`，说明 `front_scale` 未破坏后窗形态学锁相。
  - `full_stack_microcavity.py` 几何同步后已通过前向冒烟，默认厚度输出为 `100/45/5/700/15/100 nm`。
- Risks / pending checks:
  - `front_scale` 是观测几何修正，不是材料参数；其存在意味着当前绝对反射率链路仍未完全闭合到“无几何损失”的实验口径。
  - `ito_alpha`、`niox_k`、`pvk_b_scale` 仍贴边，说明前后窗之间仍有结构-色散退化，需要在 Phase 08 前向探伤沙盒中继续拆分。
  - masked 区平滑桥接仅用于视觉连续性，不能被解释为真实 PL 背景模型。

## Phase 07 Diagnostic Sandbox Update (2026-04-11)

- Current Phase: `Phase 07`
- Update summary:
  - 已新增 `src/scripts/step07_sandbox_probe_a.py`，用于在锁死前场几何与零 Debye-Waller 的条件下，单独探测前窗短波附加吸收是否能解释 `500-650 nm` 幅值失配。
  - 已新增 `src/scripts/step07_sandbox_probe_b_heatmap.py`，用于在锁定当前 Stage 1 结果后，对后窗 `d_bulk` 与 `pvk_b_scale` 做二维网格扫描并输出 Z-Score Cost 热力图。
- Verified results:
  - Probe A 明确反驳了“NiOx 短波缺吸收”这一主假说：`NiOx` 额外短波吸收的最优解几乎为 `0`，且无法降低前窗 cost；`ITO` 额外短波吸收能部分改善前窗，但单参数最优 cost 仍远高于目标线，说明前窗失配不能被单一局部吸收项解释。
  - Probe B 的后窗热力图显示：全局最小值位于 `d_bulk ≈ 630 nm`、`pvk_b_scale = 0.5` 的扫描边界；谷底轨迹近乎竖直，说明当前主导问题不是典型强 `n-d` 斜向简并，而更像 `pvk_b_scale` 被整体推向低边界后，`d_bulk` 在约 `630 nm` 附近形成局部吸引盆。
- Risks / pending checks:
  - 前窗问题更像“缺失的前端物理机制”或“吸收位置/形式不对”，而不是简单的 `NiOx k` 不足。
  - 后窗问题暂未显示出预想中的长斜谷，提示后续更应优先收紧 `pvk_b_scale` 先验、检查长波折射率口径，而不是盲目把 `d_bulk` 与 `pvk_b_scale` 一起继续放宽。

## Phase 07 Sandbox Probe D Audit Update (2026-04-11)

- Current Phase: `Phase 07`
- Update summary:
  - 已新增 `src/scripts/step07_sandbox_probe_d_audit.py`，用于对 `DEVICE-1-withAg-P1` 在 `550 nm` 处执行双路线法医学审查：一条极简前表面理论正算，一条从 0409 原始 `*-cor.csv + .spe` 重建 HDR 并手工复算绝对反射率。
  - 已输出 `results/logs/phase07/phase07_device_1_withag_p1_sandbox_probe_d_audit.md` 与 `results/figures/phase07/phase07_device_1_withag_p1_sandbox_probe_d_theory_audit.png`。
- Verified results:
  - Theory audit 对 `Air -> Glass(incoherent) -> ITO(100) -> NiOx(45) -> PVK(semi-infinite)` 在 `550 nm` 给出 `R_total = 11.889%`；其中单独 `Air/Glass` Fresnel 前表面约为 `4.193%`。
  - Calibration audit 从 0409 原始文件重建后，在 `550.147 nm` 处得到：
    - 样品原始均值：`32617.83 counts @ 150 ms`，`64895.00 counts @ 2000 ms`
    - 银镜原始均值：`40565.95 counts @ 0.5 ms`，`64899.00 counts @ 10 ms`
    - 厂家银镜反射率：`97.454%`
  - 若直接忽略 HDR 对齐，仅按原始 `Counts/Time` 手算，则得到：
    - `short-short = 0.261%`
    - `long-long = 0.487%`
  - 但按 HDR 对齐后的实际流水线口径手工复算：
    - `manual_hdr = 2.671%`
    - 与同批原始文件重建出的 `2.671%` 完全一致
    - 与导出 `hdr_curves.csv` 中的 `2.710%` 仅差约 `0.039` 个百分点
  - 这说明当前 Phase 06/07 校准代码在 `550 nm` 处是算理自洽的；不存在把理论 `~10%` 错算成 `~2.5%` 的隐藏曝光时间解析 Bug。相反，若不做 HDR 曝光对齐，反射率会更低。
- Risks / pending checks:
  - `11.889%` 的理想正反射模型与 `2.67%` 的实验校准值之间仍存在约 `4.45x` 的差距；这更符合观测几何 NA 截断、散射漏光或镜面收集损失，而不是当前代码公式错误。
  - 银镜短曝光与长曝光之间仍存在显著经验对齐因子，说明仪器短曝光链路不能直接按 `Counts/Time` 视为与长曝光严格同口径。
