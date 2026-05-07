# PROJECT_STATE.md

本文档用于维护 `TMM-interference-spectrum` 当前仓库状态、主能力边界与最近治理进展。

## 1. Current Snapshot

- 更新时间：2026-05-07
- 当前判断 Phase：`Phase 09B`
- 阶段定义：`在 Phase 09 架构骨架基础上，落地第一个正式小工具 reflectance_qc 的最小 workflow + CLI 闭环，输出 processed CSV、QC summary JSON 与 Markdown report`

## 2. 当前仓库能力

### 2.1 历史主能力

- 已有绝对反射率标定相关脚本：`src/scripts/step01_absolute_calibration.py`
- 已有 TMM 反演与相关专题脚本：`src/scripts/step02_*` 至 `src/scripts/step08_*`
- 已有 HDR 标定核心模块：`src/core/hdr_absolute_calibration.py`
- 已有 Phase 07 双窗反演核心模块：`src/core/phase07_dual_window.py`
- 已有 Phase 08 参比比较正式 CLI：`src/cli/reference_comparison.py`

### 2.2 Phase 09 架构治理成果

- 已新增 `docs/architecture/*.md`，明确正式工具标准分层、core 沙箱、domain naming、IO adapter、GUI 技术路线与输出约定。
- 已新增 `docs/tools/TOOL_REGISTRY.md` 与 `docs/tools/TOOL_TEMPLATE.md`。
- 已新增 `src/common/`、`src/domain/`、`src/storage/`、`src/workflows/`、`src/visualization/`、`src/gui/common/` 最小骨架。
- 已新增基础对象：`SpectrumData`、`QCSummary`、`ToolRunManifest`、`SpectrumReaderRegistry`。

### 2.3 Phase 09B `reflectance_qc` 最小闭环

- 已新增 `src/domain/reflectance.py`
- 已新增 `src/core/reflectance_qc.py`
- 已新增 `src/storage/readers/csv_spectrum_reader.py`
- 已新增 `src/storage/writers/reflectance_qc_writer.py`
- 已新增 `src/workflows/reflectance_qc_workflow.py`
- 已新增 `src/cli/reflectance_qc.py`
- 已新增 `docs/cli/reflectance_qc.md` 与 `docs/tools/reflectance_qc.md`

### 2.4 生成物路径治理补充

- 已新增 `AGENTS.md` `4.5`，把根目录零污染、产物分流、默认 `output_dir`、以及任务结束前根目录检查写成强制规则。
- 已强化 `.gitignore`，覆盖 pytest 缓存、临时目录、coverage、debug/export、以及本地生成 vendor 目录。
- 当前治理口径要求：正式产物继续落在 `data/processed/` 与 `results/*`，临时产物默认进入 `tmp/pytest/` 或对应受控临时目录，测试必须使用 `tmp_path / tmp_path_factory`。
- 本轮已移除部分根目录生成物（如 `.pytest-tmp-0909b`、`.pytest-tmp-0909c`、`.plot_vendor/`）；少量 `.pytest-tmp` / `pytest-cache-files-*` 目录仍受 Windows ACL 限制，尚待后续在可删环境中处理。

## 3. 当前正式工具边界

标准分层：

```text
GUI / CLI
  -> workflow
  -> core + storage + visualization
  -> data/processed + results/*
```

当前已落地的正式工具状态：

- `reference_comparison`：`active`
- `reflectance_qc`：`experimental`

仍保持脚本入口的历史能力：

- `phase06_hdr_calibration`
- `phase07_dual_window_inversion`

## 4. 当前目录结构重点

```text
src/
  cli/
  common/
  core/
  domain/
  gui/
  scripts/
  storage/
    readers/
    writers/
  visualization/
  workflows/

docs/
  architecture/
  cli/
  tools/

data/
  processed/

results/
  figures/
  logs/
  report/
```

## 5. 当前验证边界

- `reflectance_qc` 当前只支持最小 CSV/TXT reader。
- `reflectance_qc` 当前只做 sample/reference ratio 与初步 reflectance 现场 QC。
- 当前默认 `reference_reflectance = 1`，不等同于最终物理定标。
- 当前未实现 `reflectance_qc` GUI。
- 当前未实现 H5/Zarr/LightField reader adapter。
- 当前所有新增正式工具与脚本都应显式接收 `output_dir`，不得把项目根目录或 `Path.cwd()` 当作默认输出位置。

## 6. 下一步建议

1. 为 `reflectance_qc` 增加真实参比反射率模型与更严格的 reference conversion。
2. 扩展 `storage/readers` 到 H5/Zarr/LightField。
3. 在 `src/gui/reflectance_qc/` 上实现 PySide6 + pyqtgraph GUI，但仍只调用 workflow。
