# Phase 09D Two-Layer Interference Spectra

## 1. 执行摘要

- 使用现有 `resources/aligned_full_stack_nk.csv` 在 `400-1100 nm` 计算了两种层序的 TMM 干涉谱。
- 结构一：`Air / Glass(1 mm, incoherent) / PVK(700 nm, coherent) / Air`。
- 结构二：`Air / PVK(700 nm, coherent) / Glass(1 mm, incoherent) / Air`。
- 玻璃按厚基底非相干处理，PVK 按相干单层处理，与仓库现有厚玻璃建模口径一致。

## 2. 输入与模型

- `n/k` 来源：`resources/aligned_full_stack_nk.csv`。
- PVK 列沿用仓库已对齐的光学常数表；该表的文献脉络见 `docs/LITERATURE_MAP.md` 中 `[LIT-0001]` 与 `[LIT-0002]`。
- 入射条件：法向入射，`s` 偏振。
- 厚度：`d_glass = 1 mm`，`d_PVK = 700 nm`。

采用的强度量为：

$$
R(\lambda) = \text{inc\_tmm}\left(\lambda\right), \qquad
A(\lambda) = 1 - R(\lambda) - T(\lambda)
$$

其中玻璃层在 coherency list 中标记为 `i`，PVK 标记为 `c`。

## 3. 关键结果

| Structure | R_min | R_max | T_min | T_max | A_min | A_max |
| --- | --- | --- | --- | --- | --- | --- |
| glass_1mm_pvk_700nm | 0.071005 | 0.410007 | 0.000000 | 0.919512 | 0.000000 | 0.876465 |
| pvk_700nm_glass_1mm | 0.080488 | 0.410007 | 0.000000 | 0.919512 | 0.000000 | 0.779406 |

## 4. 输出文件

- CSV: `data/processed/phase09/two_layer_interference/phase09d_two_layer_interference_spectra.csv`
- Figure PNG: `results/figures/phase09/two_layer_interference/phase09d_two_layer_interference_spectra.png`
- Figure PDF: `results/figures/phase09/two_layer_interference/phase09d_two_layer_interference_spectra.pdf`

## 5. 风险与假设

- 本结果是理想法向 specular TMM，不含角度平均、表面粗糙、仪器带宽和散射。
- 1 mm 玻璃被视为非相干厚基底，因此这里输出的是包络意义上的基底级联结果，而不是保留玻璃全相干超密条纹。
- `aligned_full_stack_nk.csv` 的 PVK 列代表当前仓库采用的 surrogate / 对齐版本，不等同于对真实样品来源的最终证明。
