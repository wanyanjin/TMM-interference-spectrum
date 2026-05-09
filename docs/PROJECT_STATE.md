# PROJECT_STATE.md

## Current Snapshot
- Date: 2026-05-09
- Phase: Phase 09E
- Focus: 引入 `refractiveindex.info` 作为 `Si` / `SiO2` 优先材料来源。

## 当前新增脚本
- `src/scripts/step09e_fetch_refractiveindex_materials.py`
  - 输入来源：
    - `https://refractiveindex.info/?shelf=main&book=Si&page=Schinke`
    - `https://refractiveindex.info/?shelf=main&book=SiO2&page=Malitson`
  - 输出：
    - raw CSV 导出
    - raw YAML full database record
    - 标准化 `n/k` CSV
    - `refractiveindex_info_index.json`

## 输出路径
- `resources/refractiveindex_info/raw/Si/`
- `resources/refractiveindex_info/raw/SiO2/`
- `resources/refractiveindex_info/normalized/`
- `resources/refractiveindex_info/refractiveindex_info_index.json`

## 已知边界
- 当前只固化材料来源与标准化 CSV，不修改 `aligned_full_stack_nk.csv`。
- `SiO2` 采用 bulk fused silica 基线；标准化 CSV 在 `400-1100 nm` 上显式取 `k = 0`，不等于所有 SiO2 工艺都无吸收。
