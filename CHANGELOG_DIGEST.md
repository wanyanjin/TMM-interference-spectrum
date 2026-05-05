# CHANGELOG_DIGEST.md

本文件记录可证实的项目历史摘要。仅写入可由以下来源证实的信息：

- 已跟踪文件
- `git log`
- `docs/PROJECT_STATE.md`
- 当前仓库内明确存在的脚本/结果/文档

证据不足或语义不确定内容，不写入确定性历史，应放入 `docs/KNOWN_ISSUES.md` 的“待核对”区。

---

## 历史摘要（按 Phase）

### Phase 00（证据：`git log`）

- 提交记录：`[Phase 00] 新增 RAG 文献驱动与知识库开发准则`
- 结果：仓库存在 `docs/LITERATURE_MAP.md`，文献索引机制建立。

### Phase 01（证据：已跟踪脚本）

- 证据文件：`src/scripts/step01_absolute_calibration.py`
- 结果：绝对反射率标定脚本存在并可作为流程入口。

### Phase 02（证据：`git log` + 已跟踪脚本）

- 提交记录覆盖：
  - `CsFAPI` 外推接入
  - BEMA 粗糙层引入
  - ITO 吸收补偿方案迭代
  - 宏观厚度不均匀性反演项
  - 形状失配诊断
- 证据文件：
  - `src/scripts/step01b_cauchy_extrapolation.py`
  - `src/scripts/step02_tmm_inversion.py`
  - `src/scripts/diagnostics_shape_mismatch.py`
  - `src/scripts/step02_digitize_fapi_optical_constants.py`
  - `src/scripts/step02_digitize_csfapi_optical_constants.py`

### Phase 03（证据：`git log` + 已跟踪脚本）

- 提交记录：六参数反演与批量拟合能力上线。
- 证据文件：
  - `src/scripts/step03_batch_fit_samples.py`
  - `src/scripts/step03_forward_simulation.py`

### Phase 04（证据：`git log` + 已跟踪脚本）

- 提交记录：空气隙诊断与差分指纹映射。
- 证据文件：
  - `src/scripts/step04a_air_gap_diagnostic.py`
  - `src/scripts/step04b_air_gap_localization.py`
  - `src/scripts/step04c_fingerprint_mapping.py`

### Phase 05（证据：`git log` + 已跟踪资源/脚本）

- 提交记录：椭偏 Markdown 解析、PDF 交叉校验、全栈 `n-k` 对齐。
- 证据文件：
  - `src/scripts/step05_parse_ellipsometry_markdown.py`
  - `src/scripts/step05b_verify_against_pdf.py`
  - `src/scripts/step05c_build_aligned_nk_stack.py`
  - `resources/aligned_full_stack_nk.csv`
  - `resources/materials_master_db.json`

### Phase 06（证据：`git log` + 已跟踪核心模块/脚本）

- 提交记录：HDR 绝对反射率校准链路和双模式微腔沙盒。
- 证据文件：
  - `src/core/hdr_absolute_calibration.py`
  - `src/scripts/step06_single_sample_hdr_absolute_calibration.py`
  - `src/scripts/step06_batch_hdr_calibration.py`
  - `src/scripts/step06_dual_mode_microcavity_sandbox.py`

### Phase 07（证据：`git log` + 已跟踪核心模块/脚本）

- 提交记录：双窗联合反演、诊断探针、拟合结果流程。
- 证据文件：
  - `src/core/phase07_dual_window.py`
  - `src/scripts/step07_dual_window_inversion.py`
  - `src/scripts/step07_orthogonal_radar_and_baseline.py`
  - `src/scripts/step07_sandbox_probe_a.py`
  - `src/scripts/step07_sandbox_probe_b_heatmap.py`
  - `src/scripts/step07_sandbox_probe_d_audit.py`
  - `src/scripts/step07_zscore_sanity_check.py`

### Phase 08（证据：`git log` + 已跟踪脚本）

- 提交记录：`[Phase 08] 新增固定参数TMM理论前向建模脚本`
- 证据文件：
  - `src/scripts/step08_theoretical_tmm_modeling.py`

### Phase A-D（证据：`git log` + 已跟踪脚本 + 结果目录）

- 提交记录与文件证实以下专题已形成独立脚本链：
  - Phase A：`stepA1*`、`stepA2*`、`stepA_local*`
  - Phase B：`stepB1*`、`stepB2*`
  - Phase C：`stepC1a*`、`stepC1b*`
  - Phase D：`stepD1*`、`stepD2*`
- 结果目录证据：`results/figures/phaseA*`、`phaseB*`、`phaseC*`、`phaseD*` 与 `results/report/phase*` 子目录存在。

---

## 当前治理重构条目

### Phase 08：参比几何验证与治理规范收敛

- 目标：为下一步 `glass/PVK` 与 `glass/Ag`、`Ag mirror` 参比比较流程建立稳定治理层。
- 本次仅进行治理文档重构，不修改业务代码与结果数据。
- 后续已形成 `reference-comparison` CLI 与 dual-reference 数据链，可在 Phase 08 内对不同 PVK 光学常数来源做并排重算与比较。
