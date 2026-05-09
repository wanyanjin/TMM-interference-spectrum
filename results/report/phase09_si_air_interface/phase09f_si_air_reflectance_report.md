# Phase 09F Si/Air Interface Reflectance

## 1. 执行摘要

- 使用 `refractiveindex.info` 的 `Si / Schinke 2015` 标准化 `n/k` 数据，计算了 `Si/Air` 在 `400-1100 nm` 的法向入射反射率。
- 模型为单界面 Fresnel 反射，不含薄膜干涉、粗糙层、角度平均或表面氧化层。

## 2. 输入与公式

- 输入 `n/k`：`resources/refractiveindex_info/normalized/si_schinke_2015_nk.csv`
- 界面：`Air / Si`
- 入射条件：法向入射

$$
R(\lambda)=\left|\frac{n_{\mathrm{air}}-\tilde{n}_{\mathrm{Si}}(\lambda)}{n_{\mathrm{air}}+\tilde{n}_{\mathrm{Si}}(\lambda)}\right|^2
$$

## 3. 关键结果

| Metric | Value |
| --- | --- |
| wavelength range (nm) | 400-1100 |
| point count | 71 |
| reflectance min | 0.313551 |
| reflectance max | 0.488476 |
| reflectance 400 nm | 0.488476 |
| reflectance 600 nm | 0.353324 |
| reflectance 1100 nm | 0.313551 |

## 4. 输出文件

- CSV: `data/processed/phase09/si_air_interface/phase09f_si_air_reflectance.csv`
- Figure PNG: `results/figures/phase09/si_air_interface/phase09f_si_air_reflectance.png`
- Figure PDF: `results/figures/phase09/si_air_interface/phase09f_si_air_reflectance.pdf`

## 5. 风险与假设

- 这里是理想平整 `Si/Air` 单界面模型，不代表含原生氧化层、粗糙度或多层结构的真实样品表面。
- `Si` 的 `n/k` 来自 `Schinke 2015`，波段覆盖 `250-1450 nm`；本次仅截取 `400-1100 nm`。
- 结果为能量反射率 `0-1`，不是百分比。
