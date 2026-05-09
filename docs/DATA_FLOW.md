# DATA_FLOW.md

本文档记录当前仓库中可证实的数据链路与正式工具平台的 I/O 约束。

---

## 1. 数据分层

- `data/raw/`：规范目标中的原始数据层
- `test_data/`：当前本地测试夹具与部分历史原始样本入口
- `data/processed/`：标准中间数据层
- `results/figures/`：图表结果
- `results/logs/`：运行日志与摘要
- `results/report/`：汇报友好的 Markdown / HTML / 精选资产

---

## 2. 既有主链路

### 2.1 绝对反射率与 TMM 历史链路

```text
raw CSV
  -> src/scripts/step01_absolute_calibration.py
  -> data/processed/target_reflectance.csv
  -> src/scripts/step02_tmm_inversion.py
  -> results/figures/tmm_inversion_result.png
```

### 2.2 HDR 与双窗反演链路

```text
raw multiexposure data
  -> src/core/hdr_absolute_calibration.py
  -> src/scripts/step06_*hdr*.py
  -> data/processed/phase06/*
  -> src/core/phase07_dual_window.py
  -> src/scripts/step07_dual_window_inversion.py
  -> data/processed/phase07/*
  -> results/figures/phase07/*
  -> results/logs/phase07/*
```

### 2.3 Phase 08 参比比较与审计链路

```text
sample/reference CSV
  -> src/cli/reference_comparison.py
  -> src/core/reference_comparison.py
  -> data/processed/phase08/reference_comparison/*
  -> results/figures/phase08/reference_comparison/*
  -> results/logs/phase08/reference_comparison/*
  -> results/report/phase08_reference_comparison/*
```

---

## 3. 正式工具平台数据流

正式工具平台的标准数据流为：

```text
external files
  -> storage/readers
  -> domain model
  -> workflow
  -> core
  -> storage/writers
  -> processed/results/report
```

约束：

- `core` 不接触文件格式。
- 文件格式识别、列名归一、元数据提取与 reader 选择只允许出现在 `src/storage/readers/`。
- `workflow` 负责连接 reader、domain model、core 与 writer，不得散落基于文件后缀的 `if/else`。
- GUI 与 CLI 必须尽量复用同一套 workflow。

---

## 4. 生成物路径治理

路径分流原则：

- 正式产物继续进入 `data/processed/`、`results/figures/`、`results/logs/`、`results/report/`
- 测试临时文件默认进入 `tmp/pytest/` 或 pytest 自带的 `tmp_path`
- scratch、debug、benchmark、coverage 与本地 cache 进入 `tmp/` 或对应受控临时目录
- 新工具不得把 `Path.cwd()` 或项目根目录当作默认输出目录

如果某类新文件当前没有规定存放位置：

1. 先判断产物性质。
2. 选择已有受控目录。
3. 没有合适目录时再创建清晰命名的新目录。
4. 更新文档、`.gitignore` 和相关工具说明。
5. 在回报中说明新目录与数据流。

---

## 5. `reflectance_qc` 最小闭环

Phase 09B 新增的第一个正式工具闭环为：

```text
sample/reference CSV
  -> storage.readers.CSVSpectrumReader
  -> domain.SpectrumData
  -> workflows.reflectance_qc_workflow
  -> core.reflectance_qc
  -> storage.writers.reflectance_qc_writer
  -> data/processed/phase09/reflectance_qc/<run_id>/
  -> results/report/phase09_reflectance_qc/<run_id>/
```

说明：

- `core.reflectance_qc` 只接收 `SpectrumData` 和配置对象，不识别 CSV/TXT 后缀。
- CLI 只解析参数并调用 workflow，不复制 QC 计算与导出逻辑。
- 当前输出为 `processed_reflectance.csv`、`qc_summary.json`、`qc_report.md`，不输出 PNG 图。

---

## 6. Phase 09D 双层干涉谱链路

```text
resources/aligned_full_stack_nk.csv
  -> src/scripts/step09d_two_layer_interference_spectra.py
  -> data/processed/phase09/two_layer_interference/phase09d_two_layer_interference_spectra.csv
  -> data/processed/phase09/two_layer_interference/phase09d_two_layer_interference_manifest.json
  -> results/figures/phase09/two_layer_interference/phase09d_two_layer_interference_spectra.png
  -> results/figures/phase09/two_layer_interference/phase09d_two_layer_interference_spectra.pdf
  -> results/report/phase09_two_layer_interference/phase09d_two_layer_interference_report.md
```

说明：

- 使用 `tmm.inc_tmm` 计算 `R/T/A`，法向入射、`s` 偏振。
- `Glass(1 mm)` 通过 coherency list 标记为非相干厚基底。
- `PVK(700 nm)` 作为相干单层参与干涉计算。
- 当前脚本复用现有对齐 `nk` 表，不新增 raw 数据入口。

---

## 7. Phase 09E refractiveindex.info 材料接入链路

```text
refractiveindex.info material pages
  -> src/scripts/step09e_fetch_refractiveindex_materials.py
  -> resources/refractiveindex_info/raw/<Material>/*.csv
  -> resources/refractiveindex_info/raw/<Material>/*.yml
  -> resources/refractiveindex_info/normalized/*.csv
  -> resources/refractiveindex_info/refractiveindex_info_index.json
```

说明：

- 当前首批材料为 `Si` 与 `SiO2`
- raw 层同时保存网站 `CSV` 导出与 `Full database record`
- 标准化层统一输出 `Wavelength_nm / n / k`
- `SiO2/Malitson` 使用公式型来源，在 `400-1100 nm` 上重新评价 `n` 并显式取 `k = 0`

---

## 8. Phase 09F Si/Air 单界面反射率链路

```text
resources/refractiveindex_info/normalized/si_schinke_2015_nk.csv
  -> src/scripts/step09f_si_air_interface_reflectance.py
  -> data/processed/phase09/si_air_interface/phase09f_si_air_reflectance.csv
  -> data/processed/phase09/si_air_interface/phase09f_si_air_reflectance_manifest.json
  -> results/figures/phase09/si_air_interface/phase09f_si_air_reflectance.png
  -> results/figures/phase09/si_air_interface/phase09f_si_air_reflectance.pdf
  -> results/report/phase09_si_air_interface/phase09f_si_air_reflectance_report.md
```

说明：

- 使用法向入射 Fresnel 公式计算 `Air / Si` 单界面反射率
- 输入 `Si` 光学常数来自 `refractiveindex.info` 的 `Schinke 2015` 标准化 CSV
- 当前输出仅代表理想单界面，不包含氧化层或多层干涉
