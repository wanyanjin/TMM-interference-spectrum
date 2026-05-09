# CURRENT_TASK.md

## 当前任务
`Phase 09D：双层结构 TMM 干涉谱输出`

## 本轮目标
- 基于现有 `resources/aligned_full_stack_nk.csv` 计算：
  - `Glass(1 mm) / PVK(700 nm)`
  - `PVK(700 nm) / Glass(1 mm)`
- 波长范围固定为 `400-1100 nm`
- 输出 `csv`、`manifest json`、`markdown report` 与折线图

## 完成状态
- 新增 `src/scripts/step09d_two_layer_interference_spectra.py`
- 输出目录：
  - `data/processed/phase09/two_layer_interference/`
  - `results/figures/phase09/two_layer_interference/`
  - `results/report/phase09_two_layer_interference/`
- 玻璃按 `1 mm` 非相干厚基底处理，PVK 按 `700 nm` 相干单层处理
- 已生成两种层序的 `R/T/A` 光谱并导出图

## 待办
1. 清理并提交 Phase 09D 相关文件。
