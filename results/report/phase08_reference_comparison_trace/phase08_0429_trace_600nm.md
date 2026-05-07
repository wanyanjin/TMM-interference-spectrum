# Phase 08 Single-Wavelength Trace Report

## 0. 执行摘要
- 本报告审计目标波长为 `600.000 nm`，实际使用最近数据点 `599.987374448794 nm`，偏差 `-0.012625551206 nm`。
- 手写单层相干公式与 `coh_tmm` 一致，一致性阈值为 `1.0e-08`。
- 手写厚玻璃非相干级联与现有 CSV 一致。
- 该点实验反射率分别为 `glass/Ag = 0.290941137959`、`Ag mirror = 0.263950280877`，而 `R_TMM_GlassPVK_Fixed = 0.128761870208`。
- 当前结论：公式实现与输出 CSV 在该点自洽，但实验与理论仍存在显著差异；下一步应继续审查 `n,k` 适用性、实验参比链路、显微收光与散射贡献。

## 0.1 审计状态表
| 检查项 | 状态 | 说明 |
| --- | --- | --- |
| target wavelength matched to nearest data point | PASS | target=600.000 nm, used=599.987374 nm, Δ=-0.012626 nm |
| Ag first frame excluded | PASS | Ag 第 1 帧显式剔除；若无 Ag trace 则不检查。 |
| Ag frames reduced by mean | PASS | Ag 用 frame 2–100 求 mean；BK 用 frame 1–100 求 mean。 |
| manual coherent formula vs coh_tmm | PASS | 一致性阈值 abs_diff <= 1.0e-08 |
| manual incoherent cascade vs CSV | PASS | 一致性阈值 abs_diff <= 1.0e-08 |
| experimental reflectance manual vs CSV | PASS | 手算实验反射率与输出 CSV 对比。 |
| PVK n,k suitability | WARNING | 当前只审计 output_tag=pvk_x01 对应 nk 来源，不能证明该 nk 全谱适用。 |
| specular-only TMM vs microscope measurement equivalence | WARNING | 公式自洽不等于显微镜实测必然等于理想 specular reflectance。 |

## 1. 输入数据与版本
| 角色 | 路径 |
| --- | --- |
| dual manifest | `data/processed/phase08/reference_comparison/phase08_0429_dual_reference_manifest_pvk_x01.json` |
| calibrated reflectance | `data/processed/phase08/reference_comparison/phase08_0429_dual_reference_calibrated_reflectance_pvk_x01.csv` |
| theory csv | `data/processed/phase08/reference_comparison/phase08_0429_dual_reference_tmm_theory_curves_pvk_x01.csv` |
| nk csv | `resources/aligned_full_stack_nk_phase08_x01.csv` |
| sample csv | `test_data/0429/glass-PVK-withoutfliter-20ms 2026 四月 29 14_45_45.csv` |
| reference csv | `test_data/0429/glass-Ag-withoutfliter-20ms 2026 四月 29 14_42_25.csv` |
| ag corrected csv | `data/processed/phase08/reference_comparison/phase08_0429_ag_mirror_background_corrected_pvk_x01.csv` |
| ag frame qc csv | `data/processed/phase08/reference_comparison/phase08_0429_ag_mirror_frame_qc_pvk_x01.csv` |
| source output tag | `pvk_x01` |

## 2. 目标波长与实际使用波长
| quantity | value |
| --- | --- |
| target_wavelength_nm | 600.000000000000 |
| lambda_used_nm | 599.987374448794 |
| delta_nm | -0.012625551206 |
| row_index | 469 |

## 3. 实验计数与曝光归一化
$$
I_{\mathrm{counts/ms}}(\lambda)=\frac{I_{\mathrm{counts}}(\lambda)}{t_{\mathrm{exposure}}}
$$
| quantity | value |
| --- | --- |
| Glass_PVK_Counts | 8055.259765625000 |
| Glass_Ag_Counts | 27229.900390625000 |
| Ag_Mirror_Corrected_Counts | 30159.105959595960 |
| sample_exposure_ms | 20.000000000000 |
| glass_ag_exposure_ms | 20.000000000000 |
| ag_mirror_exposure_ms | 20.000000000000 |
| Glass_PVK_CountsPerMs | 402.762988281250 |
| Glass_Ag_CountsPerMs | 1361.495019531250 |
| Ag_Mirror_Corrected_CountsPerMs | 1507.955297979798 |

## 4. glass/Ag 参比校准链
$$
R_{\mathrm{exp}}^{\mathrm{glass/Ag}}(\lambda)=
\frac{I_{\mathrm{PVK}}(\lambda)/t_{\mathrm{PVK}}}{I_{\mathrm{glass/Ag}}(\lambda)/t_{\mathrm{glass/Ag}}}
\cdot R_{\mathrm{TMM}}^{\mathrm{glass/Ag}}(\lambda)
$$
| quantity | value |
| --- | --- |
| I_glassPVK | 8055.259765625000 |
| t_glassPVK_ms | 20.000000000000 |
| I_glassAg | 27229.900390625000 |
| t_glassAg_ms | 20.000000000000 |
| R_TMM_glassAg | 0.983493821013 |
| counts_ratio_glassAg | 0.295824062889 |
| R_exp_by_glassAg | 0.290941137959 |

## 5. Ag mirror 参比校准链
$$
R_{\mathrm{exp}}^{\mathrm{Ag\ mirror}}(\lambda)=
\frac{I_{\mathrm{PVK}}(\lambda)/t_{\mathrm{PVK}}}{I_{\mathrm{Ag\ mirror,corr}}(\lambda)/t_{\mathrm{Ag\ mirror}}}
\cdot R_{\mathrm{TMM}}^{\mathrm{Ag\ mirror}}(\lambda)
$$
| quantity | value |
| --- | --- |
| I_glassPVK | 8055.259765625000 |
| t_glassPVK_ms | 20.000000000000 |
| I_AgMirror_corrected | 30159.105959595960 |
| t_AgMirror_ms | 20.000000000000 |
| R_TMM_AgMirror | 0.988236844080 |
| counts_ratio_AgMirror | 0.267092127214 |
| R_exp_by_AgMirror | 0.263950280877 |

## 6. Ag mirror 多帧与背景扣除展开
Ag 使用 `frame 2–100` 的 mean，BK 使用 `frame 1–100` 的 mean；第 1 帧显式 drop，完整帧列表保留在 JSON。
| quantity | value |
| --- | --- |
| Pixel_Index | 551 |
| lambda_pixel_nm | 599.987374448794 |
| Ag frame count total | 100 |
| Ag frames dropped | 1 |
| Ag frames used | 2–100, total 99 frames |
| BK frame count total | 100 |
| Ag mean counts at pixel | 30794.595959595961 |
| BK mean counts at pixel | 635.490000000000 |
| Ag corrected counts | 30159.105959595960 |
| Ag first frame counts at pixel | 36948.000000000000 |

## 7. nk 插值结果
$\tilde n = n + ik$
| material | lower_nm | lower_n | lower_k | upper_nm | upper_n | upper_k | interp_n | interp_k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Glass | 599.000 | 1.515000000000 | 0.000000000000 | 600.000 | 1.515000000000 | 0.000000000000 | 1.515000000000 | 0.000000000000 |
| PVK | 599.000 | 2.700378988579 | 0.548598967685 | 600.000 | 2.699970319900 | 0.545549248151 | 2.699975479567 | 0.545587752541 |
| Ag | 599.000 | 0.049265619769 | 3.989721254713 | 600.000 | 0.049204000000 | 3.998054000000 | 0.049204777984 | 3.997948794498 |

## 8. Fresnel 界面反射
$$
r_{ij}=\frac{\tilde n_i-\tilde n_j}{\tilde n_i+\tilde n_j},\qquad R_{ij}=|r_{ij}|^2
$$
注意：界面反射率不是最终薄膜反射率；相干薄膜中的多次往返振幅不能简单相加为总反射率。
| quantity | real | imag | magnitude | phase_rad | phase_deg | reflectance |
| --- | --- | --- | --- | --- | --- | --- |
| air_glass | -0.204771371769 | 0.000000000000 | 0.204771371769 | 3.141592653590 | 180.000000000000 | 0.041931314696 |
| glass_pvk | -0.292980573691 | -0.091516817043 | 0.306941271845 | -2.838830965411 | -162.653033069103 | 0.094212944362 |
| pvk_air | 0.470959132411 | 0.078010846165 | 0.477376367786 | 0.164152021753 | 9.405218045013 | 0.227888196521 |
| glass_ag | -0.742840188899 | -0.657274399909 | 0.991877604858 | -2.417231995711 | -138.497191458224 | 0.983821183020 |
| ag_air | 0.877174120418 | 0.468022627718 | 0.994223122638 | 0.490131654056 | 28.082475183158 | 0.988479617588 |
| air_ag | -0.877174120418 | -0.468022627718 | 0.994223122638 | -2.651460999534 | -151.917524816842 | 0.988479617588 |

## 9. 相干薄膜 TMM 展开
$$
\delta = \frac{2\pi \tilde n_1 d_1}{\lambda}
$$
$$
r_{\mathrm{total}}=
\frac{r_{01}+r_{12}\exp(2i\delta)}{1+r_{01}r_{12}\exp(2i\delta)},\qquad
R_{\mathrm{stack}}=|r_{\mathrm{total}}|^2
$$

### 9.1 Glass / PVK / Air (fixed)
`d_1 = 700.000000000000 nm`
| quantity | real | imag | magnitude | phase_rad | phase_deg |
| --- | --- | --- | --- | --- | --- |
| r_01 | -0.292980573691 | -0.091516817043 | 0.306941271845 | -2.838830965411 | -162.653033069103 |
| r_12 | 0.470959132411 | 0.078010846165 | 0.477376367786 | 0.164152021753 | 9.405218045013 |
| delta | 19.792270453996 | 3.999451267759 | 20.192314878867 | 0.199386469079 | 11.424003170223 |
| exp(2i delta) | -0.000103928695 | 0.000319345078 | 0.000335830988 | 1.885429064914 | 108.027127990873 |
| numerator | -0.293054432239 | -0.091374526127 | 0.306969386552 | -2.839345155245 | -162.682493976434 |
| denominator | 1.000034661131 | -0.000034929175 | 1.000034661741 | -0.000034927964 | -0.002001224934 |
| r_total | -0.293041083220 | -0.091381594421 | 0.306958746827 | -2.839310227280 | -162.680492751500 |
| quantity | manual | csv/coh_tmm | abs_diff | rel_diff_percent |
| --- | --- | --- | --- | --- |
| R_stack_glass_pvk_fixed | 0.094223672254 | 0.094223672254 | 2.775557561563e-17 | 2.94571151302e-14 |

### 9.2 Glass / PVK / Air (best-d)
`d_1 = 458.000000000000 nm`
| quantity | real | imag | magnitude | phase_rad | phase_deg |
| --- | --- | --- | --- | --- | --- |
| r_01 | -0.292980573691 | -0.091516817043 | 0.306941271845 | -2.838830965411 | -162.653033069103 |
| r_12 | 0.470959132411 | 0.078010846165 | 0.477376367786 | 0.164152021753 | 9.405218045013 |
| delta | 12.949799811329 | 2.616783829477 | 13.211543163601 | 0.199386469079 | 11.424003170223 |
| exp(2i delta) | 0.003841313046 | 0.003701455826 | 0.005334459780 | 0.766858393939 | 43.937749456885 |
| numerator | -0.291460225933 | -0.089473918537 | 0.304884642773 | -2.843739982149 | -162.934299009729 |
| denominator | 0.999741527210 | -0.000737666964 | 0.999741799357 | -0.000737857546 | -0.042276123266 |
| r_total | -0.291469385175 | -0.089712114014 | 0.304963384515 | -2.843002124603 | -162.892022886464 |
| quantity | manual | csv/coh_tmm | abs_diff | rel_diff_percent |
| --- | --- | --- | --- | --- |
| R_stack_glass_pvk_bestD | 0.093002665895 | 0.093002665895 | 0.000000000000e+00 | 0 |

### 9.3 Glass / Ag / Air
`d_1 = 100.000000000000 nm`
| quantity | real | imag | magnitude | phase_rad | phase_deg |
| --- | --- | --- | --- | --- | --- |
| r_01 | -0.742840188899 | -0.657274399909 | 0.991877604858 | -2.417231995711 | -138.497191458224 |
| r_12 | 0.877174120418 | 0.468022627718 | 0.994223122638 | 0.490131654056 | 28.082475183158 |
| delta | 0.051528207298 | 4.186730287037 | 4.187047366885 | 1.558489442362 | 89.294867463033 |
| exp(2i delta) | 0.000229689925 | 0.000023755178 | 0.000230915071 | 0.103056414596 | 5.904697608129 |
| numerator | -0.742649828802 | -0.657146062400 | 0.991649996495 | -2.417201714400 | -138.495456466923 |
| denominator | 0.999942945829 | -0.000220453078 | 0.999942970130 | -0.000220465653 | -0.012631751441 |
| r_total | -0.742547279994 | -0.657347263636 | 0.991706553390 | -2.416981248747 | -138.482824715482 |
| quantity | manual | csv/coh_tmm | abs_diff | rel_diff_percent |
| --- | --- | --- | --- | --- |
| R_stack_glass_ag | 0.983481888037 | 0.983481888037 | 0.000000000000e+00 | 0 |

### 9.4 Air / Ag / Air
`d_1 = 100.000000000000 nm`
| quantity | real | imag | magnitude | phase_rad | phase_deg |
| --- | --- | --- | --- | --- | --- |
| r_01 | -0.877174120418 | -0.468022627718 | 0.994223122638 | -2.651460999534 | -151.917524816842 |
| r_12 | 0.877174120418 | 0.468022627718 | 0.994223122638 | 0.490131654056 | 28.082475183158 |
| delta | 0.051528207298 | 4.186730287037 | 4.187047366885 | 1.558489442362 | 89.294867463033 |
| exp(2i delta) | 0.000229689925 | 0.000023755178 | 0.000230915071 | 0.103056414596 | 5.904697608129 |
| numerator | -0.876983760322 | -0.467894290209 | 0.993994759885 | -2.651484760170 | -151.918886200977 |
| denominator | 0.999893085908 | -0.000201667175 | 0.999893106245 | -0.000201688735 | -0.011555913303 |
| r_total | -0.876983117496 | -0.468121197669 | 0.994101023076 | -2.651283071434 | -151.907330287674 |
| quantity | manual | csv/coh_tmm | abs_diff | rel_diff_percent |
| --- | --- | --- | --- | --- |
| R_stack_air_ag | 0.988236844080 | 0.988236844080 | 2.220446049250e-16 | 2.24687640676e-14 |

## 10. 厚玻璃非相干级联
$$
R_{\mathrm{front}} = \left|\frac{\tilde n_{\mathrm{air}}-\tilde n_{\mathrm{glass}}}{\tilde n_{\mathrm{air}}+\tilde n_{\mathrm{glass}}}\right|^2
$$
$$
R_{\mathrm{total}} = R_{\mathrm{front}} + \frac{(1-R_{\mathrm{front}})^2 R_{\mathrm{stack}}}{1-R_{\mathrm{front}}R_{\mathrm{stack}}}
$$
| quantity | R_front | R_stack | numerator | denominator | R_total |
| --- | --- | --- | --- | --- | --- |
| R_TMM_GlassPVK_Fixed_manual | 0.041931314696 | 0.094223672254 | 0.086487494720 | 0.996049077547 | 0.128761870208 |
| R_TMM_GlassPVK_BestD_manual | 0.041931314696 | 0.093002665895 | 0.085366738349 | 0.996100275949 | 0.127632263095 |
| R_TMM_GlassAg_manual | 0.041931314696 | 0.983481888037 | 0.902733703373 | 0.958761311455 | 0.983493821013 |

## 11. 与现有 CSV 输出对比
| quantity | manual | csv/coh_tmm | abs_diff | rel_diff_percent |
| --- | --- | --- | --- | --- |
| R_TMM_GlassPVK_Fixed | 0.128761870208 | 0.128761870208 | 0.000000000000e+00 | 0 |
| R_TMM_GlassPVK_BestD | 0.127632263095 | 0.127632263095 | 0.000000000000e+00 | 0 |
| R_TMM_GlassAg | 0.983493821013 | 0.983493821013 | 1.110223024625e-16 | 1.12885612589e-14 |
| R_Exp_GlassPVK_by_GlassAg | 0.290941137959 | 0.290941137959 | 0.000000000000e+00 | 0 |
| R_Exp_GlassPVK_by_AgMirror | 0.263950280877 | 0.263950280877 | 0.000000000000e+00 | 0 |
| R_TMM_GlassAg_theory_csv | 0.983493821013 | 0.983493821013 | 1.110223024625e-16 | 1.12885612589e-14 |
| R_TMM_AgMirror_theory_csv | 0.988236844080 | 0.988236844080 | 3.330669073875e-16 | 3.37031461013e-14 |
| R_TMM_GlassPVK_Fixed_theory_csv | 0.128761870208 | 0.128761870208 | 0.000000000000e+00 | 0 |
| R_TMM_GlassPVK_BestD_theory_csv | 0.127632263095 | 0.127632263095 | 0.000000000000e+00 | 0 |

## 12. 单点实验-理论残差
$$
\mathrm{Residual} = R_{\mathrm{exp}} - R_{\mathrm{TMM}}
$$
| quantity | value |
| --- | --- |
| R_Exp_GlassPVK_by_GlassAg | 0.290941137959 |
| R_Exp_GlassPVK_by_AgMirror | 0.263950280877 |
| R_TMM_GlassPVK_Fixed | 0.128761870208 |
| R_TMM_GlassPVK_BestD | 0.127632263095 |
| Residual_Fixed_by_GlassAg | 0.162179267751 |
| Residual_BestD_by_GlassAg | 0.163308874864 |
| Residual_Fixed_by_AgMirror | 0.135188410669 |
| Residual_BestD_by_AgMirror | 0.136318017782 |

- `glass/Ag` 链相对 fixed 为 **高**，差值 `0.162179267751`，相对误差 `125.952867482559%`。
- `Ag mirror` 链相对 fixed 为 **高**，差值 `0.135188410669`，相对误差 `104.991027585171%`。
- 当前单点偏差主要来自实验 counts ratio 对应的反射率明显高于 `glass/PVK` TMM 理论值，而不是 TMM 公式展开本身。

## 13. 人工解释
1. 这个单点 trace 的作用，是把从计数到实验反射率、再到 TMM 理论反射率的整条链路显式展开，便于人工审计。
2. 实验反射率的核心步骤是：先把样品和参比计数除以曝光时间，得到 counts/ms；再取样品/参比比值；最后乘上对应参比的理论反射率。
3. TMM 不能把各界面反射率直接相加，因为薄膜中存在多次往返反射，必须在振幅层面结合相位 `\delta` 做相干叠加。
4. 厚玻璃前表面与后侧薄膜栈的光程远大于相干长度，因此前表面与后侧相干栈之间采用非相干级联，而不是整体相干求和。
5. 本报告中手写单层公式与 `coh_tmm` 一致，手写非相干级联与 CSV 一致。
6. 因而该点可以证明：当前代码的公式实现层没有明显硬错误；但不能证明全谱、材料光学常数或显微镜测量语义已经完全正确。

## 本报告不能证明什么
- 单波长 trace 不能证明全谱所有波长点都无误。
- 公式与 CSV 一致，不能证明当前 PVK `n,k` 就是正确的样品光学常数。
- 公式与 CSV 一致，不能证明实验反射率必然等于理想 TMM 的 specular reflectance。
- 当前 Ag mirror 链仍基于理想 `Air/Ag/Air` 模型，不等于已经证明真实 Ag 参比完全符合该模型。
- 本报告只审计当前 `output_tag=pvk_x01` 对应结果集，不代表所有历史结果都相同。

## 组会讲解摘要
- 这个 600 nm 单点 trace 的目的，是把 Phase 08 的反射率校准和 TMM 计算从黑箱拆成可以逐项核对的步骤。
- 它证明了当前代码在该点的公式实现、TMM 单层解析式、厚玻璃非相干级联以及 CSV 输出之间是自洽的。
- 它没有证明当前 PVK `n,k`、Ag 参比模型或显微镜实测一定等价于理想 specular TMM。
- 当前核心矛盾仍是实验反射率显著高于理论值，且该差异不是由本报告审计到的公式错误造成的。
- 下一步应优先检查 `nk_audit`、`nk_envelope`、实验收光几何、散射和参比有效反射。

## 14. 发现的问题、风险与下一步建议
- `Ag mirror` 曝光口径在该结果集中记录为 `20.000000000000` ms，本报告复算与 CSV 一致。
- 该报告仅改变展示形式，不改变任何单点数值结果或核心 TMM/反射率计算逻辑。
- 后续若生成正式展示图，应遵守 `docs/REPORTING_AND_FIGURE_STYLE.md` 的比例、图例和坐标轴规范。
