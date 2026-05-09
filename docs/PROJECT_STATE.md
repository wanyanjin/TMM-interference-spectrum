# PROJECT_STATE.md

## Current Snapshot
- Date: 2026-05-09
- Phase: Phase 09D
- Focus: 基于现有 `aligned_full_stack_nk.csv` 输出双层结构 TMM 干涉谱。

## 当前新增脚本
- `src/scripts/step09d_two_layer_interference_spectra.py`
  - 输入：`resources/aligned_full_stack_nk.csv`
  - 结构一：`Air / Glass(1 mm, incoherent) / PVK(700 nm, coherent) / Air`
  - 结构二：`Air / PVK(700 nm, coherent) / Glass(1 mm, incoherent) / Air`
  - 波段：`400-1100 nm`
  - 输出：`R/T/A` CSV、manifest JSON、Markdown 报告、PNG/PDF 图

## 输出路径
- `data/processed/phase09/two_layer_interference/`
- `results/figures/phase09/two_layer_interference/`
- `results/report/phase09_two_layer_interference/`

## 已知边界
- 当前结果是理想法向 specular TMM，不含角度平均、粗糙层与散射。
- `1 mm` 玻璃按非相干厚基底处理，因此输出的是厚基底级联后的包络谱，不保留全相干玻璃超密条纹。
