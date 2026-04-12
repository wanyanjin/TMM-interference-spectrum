# Source Manifest

- 原始 CSV：
  - `data/processed/phaseB2/phaseB2_front_bema_scan.csv`
- 参考报告：
  - `results/report/phaseB2_front_bema_sandbox/PHASE_B2_REPORT.md`
- 直接复用图：无
- 基于已有数据重绘：
  - `structure_schematic.png/.svg`
  - `front_bema_deltaRtotal_heatmap.png`
  - `front_bema_selected_rtotal_curves.png`
- 结构图实现方式：
  - 程序绘制（matplotlib），未使用 imagegen 位图生成
- 结构层序定义：
  - `Air / Glass / ITO / NiOx / SAM / BEMA_front(NiOx/PVK proxy) / PVK_bulk / C60 / Ag / Air`
- phase 物理对应：
  - 高亮前界面 proxy BEMA 层，表示 front-side transition-layer/intermixing proxy
- 代表参数：
  - front-BEMA: `0 / 10 / 20 nm`
  - observable: `R_total`
