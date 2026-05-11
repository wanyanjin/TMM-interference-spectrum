# CHANGELOG_DIGEST.md

## Phase 09
- 建立工具平台架构文档、core 沙箱规则与最小骨架。

## Phase 09B
- 实现 `reflectance_qc` 最小 CLI + workflow 闭环。

## Phase 09C-1
- 实现 GUI MVP（以 processed 结果查看为主）。

## Phase 09C-2
- 修正 GUI 产品方向：默认改为 Raw sample/reference 一键 QC。
- GUI 通过 `run_reflectance_qc_workflow` 执行计算，禁止 GUI 重写 core 逻辑。
- 保留 processed result viewer 作为辅助模式。
- 新增 `Open Output Folder`，并保持 GUI 导出到受控目录。

## Phase 09D
- 新增 `src/scripts/step09d_two_layer_interference_spectra.py`，使用现有 `aligned_full_stack_nk.csv` 生成双层结构 TMM 干涉谱。
- 输出 `Glass(1 mm)/PVK(700 nm)` 与 `PVK(700 nm)/Glass(1 mm)` 在 `400-1100 nm` 的 `R/T/A` CSV、manifest、Markdown 报告与 PNG/PDF 图。
- 玻璃统一按厚基底非相干处理，保持与仓库现有 Phase 08/09 厚玻璃建模口径一致。

## Phase 09E
- 新增 `refractiveindex.info` 材料来源接入闭环，首批固化 `Si` 与 `SiO2`。
- 保存网站 `CSV` 导出与 `Full database record`（YAML），并生成标准化 `n/k` CSV 与索引 manifest。
- 在 `AGENTS.md` 中新增材料 `n/k` 查询优先级：先查 `refractiveindex.info`，不足时再转其他来源。

## Phase 09F
- 新增 `src/scripts/step09f_si_air_interface_reflectance.py`，基于 `Si / Schinke 2015` 标准化 `n/k` 数据计算 `Si/Air` 单界面在 `400-1100 nm` 的法向反射率。
- 输出 `csv`、manifest、Markdown 报告和 PNG/PDF 图到受控目录。
- **工具正式化**：新增 `si_reference_curve` 正式工具单元（`domain`/`core`/`workflow`/`cli`），支持多层氧化层对比模拟与自动化测试。
