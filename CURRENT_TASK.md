# CURRENT_TASK.md

## 当前任务
`Phase 09F：Si/Air 单界面反射率模拟`

## 本轮目标
- 基于现有 `Si` 标准化 `n/k` 数据模拟 `Si/Air` 在 `400-1100 nm` 的反射率
- 输出 `csv`、`manifest json`、`markdown report` 与折线图

## 完成状态
- 已新增正式脚本：`src/scripts/step09f_si_air_interface_reflectance.py`
- 输入数据：
  - `resources/refractiveindex_info/normalized/si_schinke_2015_nk.csv`
- 输出目录：
  - `data/processed/phase09/si_air_interface/`
  - `results/figures/phase09/si_air_interface/`
  - `results/report/phase09_si_air_interface/`
- 已补：
  - 单元测试

## 待办
1. 运行脚本并提交 Phase 09F 相关文件。
