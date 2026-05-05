# Phase 08 Single-Wavelength Trace Report

## 1. 审计目标与输入文件
- dual manifest: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/data/processed/phase08/reference_comparison/phase08_0429_dual_reference_manifest_pvk_x01.json`
- calibrated reflectance: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/data/processed/phase08/reference_comparison/phase08_0429_dual_reference_calibrated_reflectance_pvk_x01.csv`
- theory csv: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/data/processed/phase08/reference_comparison/phase08_0429_dual_reference_tmm_theory_curves_pvk_x01.csv`
- nk csv: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/resources/aligned_full_stack_nk_phase08_x01.csv`
- sample csv: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/test_data/0429/glass-PVK-withoutfliter-20ms 2026 四月 29 14_45_45.csv`
- reference csv: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/test_data/0429/glass-Ag-withoutfliter-20ms 2026 四月 29 14_42_25.csv`
- ag corrected csv: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/data/processed/phase08/reference_comparison/phase08_0429_ag_mirror_background_corrected_pvk_x01.csv`
- ag frame qc csv: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/data/processed/phase08/reference_comparison/phase08_0429_ag_mirror_frame_qc_pvk_x01.csv`

## 2. 目标波长与实际使用波长
- `target_wavelength_nm = 600.0`
- `lambda_used_nm = 599.987374448794`
- `delta_nm = -0.012625551206`
- `row_index = 469`

## 3. 实验计数与曝光归一化
- `Glass_PVK_Counts = 8055.259765625000`
- `Glass_Ag_Counts = 27229.900390625000`
- `Ag_Mirror_Corrected_Counts = 30159.105959595960`
- `sample_exposure_ms = 20.000000000000`
- `glass_ag_exposure_ms = 20.000000000000`
- `ag_mirror_exposure_ms = 20.000000000000`
- `Glass_PVK_CountsPerMs = Glass_PVK_Counts / sample_exposure_ms = 402.762988281250`
- `Glass_Ag_CountsPerMs = Glass_Ag_Counts / glass_ag_exposure_ms = 1361.495019531250`
- `Ag_Mirror_Corrected_CountsPerMs = Ag_Mirror_Corrected_Counts / ag_mirror_exposure_ms = 1507.955297979798`

## 4. glass/Ag 参比校准链
- 公式：
```text
R_exp_by_glassAg(λ) = [I_glassPVK(λ) / t_glassPVK] / [I_glassAg(λ) / t_glassAg] × R_TMM_glassAg(λ)
```
- `I_glassPVK = 8055.259765625000`
- `t_glassPVK = 20.000000000000`
- `I_glassAg = 27229.900390625000`
- `t_glassAg = 20.000000000000`
- `R_TMM_glassAg = 0.983493821013`
- `counts_ratio_glassAg = 0.295824062889`
- `R_exp_by_glassAg = 0.290941137959`

## 5. Ag mirror 参比校准链
- 公式：
```text
R_exp_by_AgMirror(λ) = [I_glassPVK(λ) / t_glassPVK] / [I_AgMirror_corrected(λ) / t_AgMirror] × R_TMM_AgMirror(λ)
```
- `I_glassPVK = 8055.259765625000`
- `t_glassPVK = 20.000000000000`
- `I_AgMirror_corrected = 30159.105959595960`
- `t_AgMirror = 20.000000000000`
- `R_TMM_AgMirror = 0.988236844080`
- `counts_ratio_AgMirror = 0.267092127214`
- `R_exp_by_AgMirror = 0.263950280877`

## 6. Ag mirror 多帧与背景扣除展开
- `Pixel_Index = 551`
- `lambda_pixel_nm = 599.987374448794`
- `Ag frame count total = 100`
- `Ag frames dropped = [1]`
- `Ag frames used = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100]`
- `BK frame count total = 100`
- `Ag mean counts at pixel = 30794.595959595961`
- `BK mean counts at pixel = 635.490000000000`
- `Ag corrected counts = Ag mean - BK mean = 30159.105959595960`
- `Ag first frame counts at pixel = 36948.000000000000`
- 说明：Ag 使用 frame 2-100 的 mean；BK 使用 frame 1-100 的 mean；第 1 帧显式 drop。

## 7. nk 插值结果
- `n_air = 1 + 0i`
- `n_glass = 1.515 + 0i; |.|=1.515; phase=0 rad = 0 deg`
- `n_PVK = 2.69997547957 + 0.545587752541i; |.|=2.75454780064; phase=0.199386469079 rad = 11.4240031702 deg`
- `n_Ag = 0.0492047779835 + 3.9979487945i; |.|=3.99825157708; phase=1.55848944236 rad = 89.294867463 deg`
- `n_complex = n + i k`
- 相邻插值点：
  - Glass lower: `{'Wavelength_nm': 599.0, 'n': 1.515, 'k': 0.0}`
  - Glass upper: `{'Wavelength_nm': 600.0, 'n': 1.515, 'k': 0.0}`
  - PVK lower: `{'Wavelength_nm': 599.0, 'n': 2.700378988579365, 'k': 0.5485989676846645}`
  - PVK upper: `{'Wavelength_nm': 600.0, 'n': 2.6999703198998883, 'k': 0.5455492481506058}`
  - Ag lower: `{'Wavelength_nm': 599.0, 'n': 0.0492656197686775, 'k': 3.989721254713048}`
  - Ag upper: `{'Wavelength_nm': 600.0, 'n': 0.049204, 'k': 3.998054}`

## 8. Fresnel 界面反射
- `air_glass`: r = -0.204771371769 + 0i; |.|=0.204771371769; phase=3.14159265359 rad = 180 deg; `R = 0.041931314696`
- `glass_pvk`: r = -0.292980573691 + -0.0915168170426i; |.|=0.306941271845; phase=-2.83883096541 rad = -162.653033069 deg; `R = 0.094212944362`
- `pvk_air`: r = 0.470959132411 + 0.0780108461648i; |.|=0.477376367786; phase=0.164152021753 rad = 9.40521804501 deg; `R = 0.227888196521`
- `glass_ag`: r = -0.742840188899 + -0.657274399909i; |.|=0.991877604858; phase=-2.41723199571 rad = -138.497191458 deg; `R = 0.983821183020`
- `ag_air`: r = 0.877174120418 + 0.468022627718i; |.|=0.994223122638; phase=0.490131654056 rad = 28.0824751832 deg; `R = 0.988479617588`
- `air_ag`: r = -0.877174120418 + -0.468022627718i; |.|=0.994223122638; phase=-2.65146099953 rad = -151.917524817 deg; `R = 0.988479617588`

## 9. 相干薄膜 TMM 展开

### 9.1 Glass / PVK / Air
- `fixed` (`d = 700.000000000000 nm`)
  - `r_01 = -0.292980573691 + -0.0915168170426i; |.|=0.306941271845; phase=-2.83883096541 rad = -162.653033069 deg`
  - `r_12 = 0.470959132411 + 0.0780108461648i; |.|=0.477376367786; phase=0.164152021753 rad = 9.40521804501 deg`
  - `δ = 19.792270454 + 3.99945126776i; |.|=20.1923148789; phase=0.199386469079 rad = 11.4240031702 deg`
  - `exp(2iδ) = -0.000103928695466 + 0.000319345078202i; |.|=0.000335830988316; phase=1.88542906491 rad = 108.027127991 deg`
  - `r_total = -0.29304108322 + -0.0913815944209i; |.|=0.306958746827; phase=-2.83931022728 rad = -162.680492752 deg`
  - `R_stack_by_formula = 0.094223672254`
  - `R_stack_by_coh_tmm = 0.094223672254`
  - absolute_difference = 2.775557561563e-17
- `best_d` (`d = 458.000000000000 nm`)
  - `r_01 = -0.292980573691 + -0.0915168170426i; |.|=0.306941271845; phase=-2.83883096541 rad = -162.653033069 deg`
  - `r_12 = 0.470959132411 + 0.0780108461648i; |.|=0.477376367786; phase=0.164152021753 rad = 9.40521804501 deg`
  - `δ = 12.9497998113 + 2.61678382948i; |.|=13.2115431636; phase=0.199386469079 rad = 11.4240031702 deg`
  - `exp(2iδ) = 0.0038413130459 + 0.00370145582553i; |.|=0.00533445978004; phase=0.766858393939 rad = 43.9377494569 deg`
  - `r_total = -0.291469385175 + -0.089712114014i; |.|=0.304963384515; phase=-2.8430021246 rad = -162.892022886 deg`
  - `R_stack_by_formula = 0.093002665895`
  - `R_stack_by_coh_tmm = 0.093002665895`
  - absolute_difference = 0.000000000000e+00

### 9.2 Glass / Ag / Air
- `r_01 = -0.742840188899 + -0.657274399909i; |.|=0.991877604858; phase=-2.41723199571 rad = -138.497191458 deg`
- `r_12 = 0.877174120418 + 0.468022627718i; |.|=0.994223122638; phase=0.490131654056 rad = 28.0824751832 deg`
- `δ = 0.0515282072982 + 4.18673028704i; |.|=4.18704736688; phase=1.55848944236 rad = 89.294867463 deg`
- `exp(2iδ) = 0.000229689924519 + 2.37551779711e-05i; |.|=0.000230915070765; phase=0.103056414596 rad = 5.90469760813 deg`
- `r_total = -0.742547279994 + -0.657347263636i; |.|=0.99170655339; phase=-2.41698124875 rad = -138.482824715 deg`
- `R_stack_glass_ag = 0.983481888037`
- `R_stack_by_coh_tmm = 0.983481888037`
- absolute_difference = 0.000000000000e+00

### 9.3 Air / Ag / Air
- `r_01 = -0.877174120418 + -0.468022627718i; |.|=0.994223122638; phase=-2.65146099953 rad = -151.917524817 deg`
- `r_12 = 0.877174120418 + 0.468022627718i; |.|=0.994223122638; phase=0.490131654056 rad = 28.0824751832 deg`
- `δ = 0.0515282072982 + 4.18673028704i; |.|=4.18704736688; phase=1.55848944236 rad = 89.294867463 deg`
- `exp(2iδ) = 0.000229689924519 + 2.37551779711e-05i; |.|=0.000230915070765; phase=0.103056414596 rad = 5.90469760813 deg`
- `r_total = -0.876983117496 + -0.468121197669i; |.|=0.994101023076; phase=-2.65128307143 rad = -151.907330288 deg`
- `R_stack_air_ag = 0.988236844080`
- `R_stack_by_coh_tmm = 0.988236844080`
- absolute_difference = 2.220446049250e-16

## 10. 厚玻璃非相干级联
- `R_TMM_GlassPVK_Fixed`
  - `R_front = 0.041931314696`
  - `R_stack = 0.094223672254`
  - `numerator = 0.086487494720`
  - `denominator = 0.996049077547`
  - `R_total = 0.128761870208`
  - `CSV = 0.128761870208`
  - difference = 0.000000000000e+00
- `R_TMM_GlassPVK_BestD`
  - `R_front = 0.041931314696`
  - `R_stack = 0.093002665895`
  - `numerator = 0.085366738349`
  - `denominator = 0.996100275949`
  - `R_total = 0.127632263095`
  - `CSV = 0.127632263095`
  - difference = 0.000000000000e+00
- `R_TMM_GlassAg`
  - `R_front = 0.041931314696`
  - `R_stack = 0.983481888037`
  - `numerator = 0.902733703373`
  - `denominator = 0.958761311455`
  - `R_total = 0.983493821013`
  - `CSV = 0.983493821013`
  - difference = 1.110223024625e-16

## 11. 与现有 CSV 输出对比
- `R_TMM_GlassPVK_Fixed`: manual=0.128761870208, csv=0.128761870208, abs_diff=0.000000000000e+00, rel_diff=0%
- `R_TMM_GlassPVK_BestD`: manual=0.127632263095, csv=0.127632263095, abs_diff=0.000000000000e+00, rel_diff=0%
- `R_TMM_GlassAg`: manual=0.983493821013, csv=0.983493821013, abs_diff=1.110223024625e-16, rel_diff=1.12885612589e-14%
- `R_Exp_GlassPVK_by_GlassAg`: manual=0.290941137959, csv=0.290941137959, abs_diff=0.000000000000e+00, rel_diff=0%
- `R_Exp_GlassPVK_by_AgMirror`: manual=0.263950280877, csv=0.263950280877, abs_diff=0.000000000000e+00, rel_diff=0%
- `R_TMM_GlassAg_theory_csv`: manual=0.983493821013, csv=0.983493821013, abs_diff=1.110223024625e-16, rel_diff=1.12885612589e-14%
- `R_TMM_AgMirror_theory_csv`: manual=0.988236844080, csv=0.988236844080, abs_diff=3.330669073875e-16, rel_diff=3.37031461013e-14%
- `R_TMM_GlassPVK_Fixed_theory_csv`: manual=0.128761870208, csv=0.128761870208, abs_diff=0.000000000000e+00, rel_diff=0%
- `R_TMM_GlassPVK_BestD_theory_csv`: manual=0.127632263095, csv=0.127632263095, abs_diff=0.000000000000e+00, rel_diff=0%

## 12. 单点实验-理论残差
- `R_Exp_GlassPVK_by_GlassAg = 0.290941137959`
- `R_Exp_GlassPVK_by_AgMirror = 0.263950280877`
- `R_TMM_GlassPVK_Fixed = 0.128761870208`
- `R_TMM_GlassPVK_BestD = 0.127632263095`
- `Residual_Fixed_by_GlassAg = 0.162179267751`
- `Residual_BestD_by_GlassAg = 0.163308874864`
- `Residual_Fixed_by_AgMirror = 0.135188410669`
- `Residual_BestD_by_AgMirror = 0.136318017782`
- Glass/Ag 实验值相对 fixed 高，差值 `0.162179267751`，相对误差 `125.952867482559%`
- Ag mirror 实验值相对 fixed 高，差值 `0.135188410669`，相对误差 `104.991027585171%`

## 13. 人工解释
1. 该波长点的实验反射率先把样品和参比计数除以各自曝光时间，得到 counts/ms；再取样品/参比比值，乘以对应参比的理论反射率。
2. TMM 不是简单把各界面反射率相加，因为薄膜内部会发生多次往返反射，振幅相位会相干叠加。
3. 相位 `δ = 2π n d / λ` 控制薄膜内部往返波的相长/相消，是干涉条纹的核心。
4. 厚玻璃前表面与后侧薄膜栈之间的光程远大于相干长度，因此当前代码把前表面与后侧相干栈按非相干级联处理，而不是整体相干求和。
5. 本报告中的单层解析公式与 `coh_tmm` 在 `Glass/PVK/Air`、`Glass/Ag/Air`、`Air/Ag/Air` 三个栈上逐点比对。
6. 结果：手写相干公式与 `coh_tmm` 一致；手写非相干级联与 CSV 一致。
7. 因此如果一致，可以判断当前代码的公式层面没有明显硬错误；若不一致，则优先排查波长点选择、插值、输出列或手写公式实现。
8. 在该点上，实验与理论差异主要来自实验 counts ratio 对应的反射率明显高于 `glass/PVK` TMM 理论值，而不是单层公式或非相干级联公式本身计算错误。

## 14. 发现的问题、风险与下一步建议
- `Ag mirror` 曝光口径：当前 manifest 记录为 `20.000000000000` ms，trace 复算与 CSV 一致。
- 最新 dual 输出来自 `output_tag=pvk_x01`；本报告只审计该结果集，不等于其它 tag 也完全相同。
- 若后续要继续定位实验-理论偏差，优先检查参比有效反射、ROI/收光几何、散射/背景残差，而不是先怀疑当前 TMM 公式层。
