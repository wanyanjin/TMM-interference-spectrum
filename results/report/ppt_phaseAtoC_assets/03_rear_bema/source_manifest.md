# Source Manifest

- 原始 CSV：
  - `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`
- 参考报告：
  - `results/report/phaseB1_rear_bema_sandbox/PHASE_B1_REPORT.md`
- 直接复用图：无
- 基于已有数据重绘：
  - `structure_schematic.png/.svg`
  - `rear_bema_deltaRtotal_heatmap.png`
  - `rear_bema_selected_rtotal_curves.png`
- 结构图实现方式：
  - 程序绘制（matplotlib），未使用 imagegen 位图生成
- 结构层序定义：
  - `Air / Glass / ITO / NiOx / SAM / PVK_bulk / BEMA(PVK/C60) / C60_bulk / Ag / Air`
- phase 物理对应：
  - 高亮后界面 BEMA 混合层，表示 rear-only intermixing
- 代表参数：
  - rear-BEMA: `0 / 10 / 20 / 30 nm`
  - observable: `R_total`
