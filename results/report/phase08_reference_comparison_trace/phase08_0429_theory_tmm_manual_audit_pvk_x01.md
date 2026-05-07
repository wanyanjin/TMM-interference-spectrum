# Phase 08 TMM Theoretical Reflectance Manual Audit

## 1. Convention
- 时间因子：`exp(-iωt)`
- 前进方向：`+z`
- 统一使用 `s polarization` 展示
- 当前入射半无限介质非吸收，因此 `R = |r|²`
- 目标波长使用 trace 最近点：`lambda_used_nm = 599.987374448794`

## 2. Glass / PVK / Air coherent stack
$$r_{01}=\frac{N_0-N_1}{N_0+N_1},\qquad r_{12}=\frac{N_1-N_2}{N_1+N_2}$$
$$\delta = \frac{2\pi N_1 d_1}{\lambda}$$
$$r_{\mathrm{stack}} = \frac{r_{01}+r_{12}e^{2 i \delta}}{1+r_{01}r_{12}e^{2 i \delta}},\qquad R_{\mathrm{stack}}=|r_{\mathrm{stack}}|^2$$

| quantity | value |
| --- | --- |
| N_glass | 1.515000000000 + 0.000000000000i |
| N_pvk | 2.699975479567 + 0.545587752541i |
| N_air | 1.000000000000 + 0.000000000000i |
| d_pvk_nm | 700.000000000000 |
| r01 | -0.292980573691 + -0.091516817043i |
| r12 | 0.470959132411 + 0.078010846165i |
| delta | 19.792270453996 + 3.999451267759i |
| exp(2i delta) | -0.000103928695 + 0.000319345078i |
| r_stack_manual | -0.293041083220 + -0.091381594421i |
| R_stack_manual | 0.094223672254 |
| R_stack_tmm | 0.094223672254 |
| abs_diff | 2.776e-17 |
| PASS | True |

## 3. Thick-glass incoherent cascade
$$R_{\mathrm{total}} = R_{01} + \frac{T_{01}T_{10}P^2R_{\mathrm{stack}}}{1-R_{10}P^2R_{\mathrm{stack}}}$$
当前简化条件：`Glass k≈0`，`P≈1`，`R01=R10=R_front`，`T01 T10=(1-R_front)^2`
$$R_{\mathrm{total}} = R_{\mathrm{front}} + \frac{(1-R_{\mathrm{front}})^2 R_{\mathrm{stack}}}{1-R_{\mathrm{front}}R_{\mathrm{stack}}}$$

| quantity | value |
| --- | --- |
| R_front | 0.041931314696 |
| R_stack | 0.094223672254 |
| T01 | 0.958068685304 |
| T10 | 0.958068685304 |
| P | 1.000000000000 |
| R_total_general_formula | 0.128761870208 |
| R_total_simplified_formula | 0.128761870208 |
| R_TMM_GlassPVK_Fixed_csv | 0.128761870208 |
| abs_diff | 0.000e+00 |
| PASS | True |

## 4. Reference theory audit
| case | manual | tmm | csv | abs_diff | PASS |
| --- | --- | --- | --- | --- | --- |
| glass/Ag stack | 0.983481888037 | 0.983481888037 | — | 0.000e+00 | True |
| glass/Ag total | 0.983493821013 | — | 0.983493821013 | 1.110e-16 | True |
| Ag mirror | 0.988236844080 | 0.988236844080 | 0.988236844080 | 3.331e-16 | True |

## 5. Convention sanity check
下表仅用于说明 `exp(-2i delta)` 没被当成主物理逻辑。

| quantity | value |
| --- | --- |
| R_stack_by_exp(-2i delta) | 10.623591669636 |
| abs_diff_vs_tmm | 1.053e+01 |
| PASS | False |

## 6. Conclusion boundary
- 本审计证明当前手写公式、`tmm.coh_tmm()` 与现有 CSV 在当前模型假设下自洽。
- 本审计不证明 `n,k` 数据一定代表真实样品，也不证明显微测量一定等于理想 specular reflectance。
- Ag mirror caveat：This only audits consistency with the current model; whether the physical Ag mirror is equivalent to Air / 100 nm Ag / Air still needs sample-level confirmation.
