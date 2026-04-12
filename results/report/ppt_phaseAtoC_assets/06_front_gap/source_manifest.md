# Source Manifest

- 原始 CSV：
  - `data/processed/phaseC1b/phaseC1b_front_air_gap_scan.csv`
- 参考报告：
  - `results/report/phaseC1b_front_air_gap_sandbox/PHASE_C1B_REPORT.md`
- 直接复用图：无
- 基于已有数据重绘：
  - `structure_schematic.png/.svg`
  - `front_gap_deltaRtotal_heatmap.png`
  - `front_gap_selected_rtotal_curves.png`
- 结构图实现方式：
  - 程序绘制（matplotlib），未使用 imagegen 位图生成
- 结构层序定义：
  - `Air / Glass / ITO / NiOx / SAM / Air gap / PVK / C60 / Ag / Air`
- phase 物理对应：
  - 高亮前界面真实空气隙，表示 front-interface real separation
- 代表参数：
  - front-gap: `0 / 1 / 2 / 3 / 5 / 10 / 20 / 30 / 50 nm`
  - observable: `R_total`
