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

## 4. `reflectance_qc` 最小闭环

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
