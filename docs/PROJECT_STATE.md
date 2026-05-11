# PROJECT_STATE.md

## Current Snapshot
- Date: 2026-05-09
- Phase: Phase 09F
- Focus: 基于 `Si / Schinke 2015` 标准化 `n/k` 计算 `Si/Air` 单界面反射率。

## 当前新增脚本
- `src/scripts/step09f_si_air_interface_reflectance.py`
  - 输入来源：
    - `resources/refractiveindex_info/normalized/si_schinke_2015_nk.csv`
  - 输出：
    - `Si/Air` 反射率 CSV
    - manifest JSON
    - Markdown 报告
    - PNG/PDF 图

## 当前正式工具
- `si_reference_curve`
  - 结构：`domain` / `core` / `workflow` / `cli`
  - 能力：支持 `Air / SiO2(t) / Si` 多层干涉谱模拟，支持多厚度对比。

## 输出路径
- `data/processed/phase09/si_air_interface/`
- `results/figures/phase09/si_air_interface/`
- `results/report/phase09_si_air_interface/`

## 已知边界
- 当前模型是理想 `Air / Si` 单界面 Fresnel 反射，不含原生氧化层、粗糙度、多层结构和角度平均。
- 结果依赖 `Si / Schinke 2015` 的标准化 `n/k` 数据。
