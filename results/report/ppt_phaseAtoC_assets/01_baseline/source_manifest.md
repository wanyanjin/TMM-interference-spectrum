# Source Manifest

- 原始 CSV：
  - `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- 参考报告：
  - `results/report/phaseA1_2_pvk_surrogate_and_pristine/PHASE_A1_2_REPORT.md`
- 直接复用图：无
- 基于已有数据重绘：
  - `structure_schematic.png/.svg`：新绘制的 baseline 结构示意图
  - `baseline_structure_schematic.png`：与历史命名兼容的同图副本
  - `baseline_rtotal_curve.png`：基于 `phaseA1_2_pristine_baseline.csv` 仅重绘 `R_total`
- 结构图实现方式：
  - 程序绘制（matplotlib），未使用 imagegen 位图生成
- 结构层序定义：
  - `Air / Glass / ITO / NiOx / SAM / PVK / C60 / Ag / Air`
- 代表参数：
  - pristine baseline
  - windows: front `400–650 nm`, transition `650–810 nm`, rear `810–1100 nm`
