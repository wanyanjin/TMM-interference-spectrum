# CHANGELOG_DIGEST.md

本文档记录可证实的关键阶段变化、能力新增与治理决策。

---

## 治理补充

- 新增 `AGENTS.md` `4.5` 生成物路径治理与根目录零污染规则，明确稳定入口、正式产物与临时产物的路径边界。
- 强化 `.gitignore`，补入 pytest 缓存、临时目录、coverage、debug/export、`.plot_vendor/` 等根目录生成物忽略项。
- 清理过程中已移除部分根目录生成物（包括 `.pytest-tmp-0909b`、`.pytest-tmp-0909c` 与 `.plot_vendor/`）；少量 `.pytest-tmp` / `pytest-cache-files-*` 目录仍因 Windows ACL 拒绝访问而暂未能删除，后续需在具备权限的环境中继续处理。
- 将新工具默认 `output_dir` 不得回退到项目根目录、不得依赖 `Path.cwd()` 的约束同步写入记忆文档与数据流文档。

## 历史摘要

### Phase 01

- 已形成绝对反射率标定脚本入口：`src/scripts/step01_absolute_calibration.py`

### Phase 02

- 已形成 TMM 反演与材料常数数字化相关脚本：`src/scripts/step02_*`

### Phase 03

- 已形成批量拟合与前向模拟脚本：`src/scripts/step03_*`

### Phase 04

- 已形成空气隙诊断、定位与指纹映射脚本：`src/scripts/step04*`

### Phase 05

- 已形成椭偏 Markdown 解析、PDF 交叉验证与对齐 `n-k` 数据构建链路：`src/scripts/step05*`

### Phase 06

- 已形成 HDR 标定核心模块与脚本入口：`src/core/hdr_absolute_calibration.py`、`src/scripts/step06_*`

### Phase 07

- 已形成双窗联合反演核心模块与脚本入口：`src/core/phase07_dual_window.py`、`src/scripts/step07_*`

### Phase 08

- 已形成 `reference_comparison` 正式 CLI 与参比审计相关链路。
- 已形成本地 HTML 审计 deck 生成脚本：`src/scripts/step08_build_audit_slide_deck.py`

### Phase 09：工具平台架构规范与 core 沙箱骨架

- 新增 `docs/architecture/TOOL_ARCHITECTURE.md`
- 新增 `docs/architecture/CORE_SANDBOX_RULES.md`
- 新增 `docs/architecture/DATA_MODEL_GUIDE.md`
- 新增 `docs/architecture/IO_ADAPTER_GUIDE.md`
- 新增 `docs/architecture/GUI_TECH_STACK.md`
- 新增 `docs/architecture/OUTPUT_CONVENTIONS.md`
- 新增 `docs/tools/TOOL_REGISTRY.md` 与 `docs/tools/TOOL_TEMPLATE.md`
- 新增 `src/common/`、`src/domain/`、`src/storage/`、`src/workflows/`、`src/visualization/`、`src/gui/common/` 最小骨架
- 新增 `tests/unit/test_domain_spectrum.py` 与 `tests/unit/test_reader_registry.py`

### Phase 09B：reflectance_qc 最小 workflow + CLI 闭环

- 新增 `src/domain/reflectance.py`，建立 `reflectance_qc` 的最小 domain model。
- 新增 `src/core/reflectance_qc.py`，实现 sample/reference 共同波长对齐、插值、ratio、初步 reflectance 与 QC metrics。
- 新增 `src/storage/readers/csv_spectrum_reader.py` 与 `src/storage/writers/reflectance_qc_writer.py`，把 CSV/TXT 读取与 CSV/JSON/Markdown 输出约束在 storage 层。
- 新增 `src/workflows/reflectance_qc_workflow.py` 与 `src/cli/reflectance_qc.py`，形成第一个符合 Phase 09 架构的正式非 GUI 工具闭环。
- 新增 `tests/unit/test_csv_spectrum_reader.py`、`tests/unit/test_reflectance_qc_core.py`、`tests/integration/test_reflectance_qc_workflow.py`、`tests/integration/test_reflectance_qc_cli.py`。
- 新增 `docs/cli/reflectance_qc.md` 与 `docs/tools/reflectance_qc.md`。
- `docs/tools/TOOL_REGISTRY.md` 中 `reflectance_qc` 状态从 `planned` 更新为 `experimental`。
