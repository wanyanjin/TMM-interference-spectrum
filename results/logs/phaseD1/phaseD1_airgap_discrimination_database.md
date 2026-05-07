# Phase D-1 air-gap discrimination database

## 1. 输入与定位

- 材料主表：`resources/aligned_full_stack_nk_pvk_v2.csv`
- 参考 phase：`A-2 / B-1 / B-2 / C-1a / C-1b`
- 当前定位：不是最终分类器，而是 **realistic thickness + roughness background** 下的 `R_total` 前向判别数据库

## 2. 为什么 thickness scan 收窄到 700 ± 25 nm

宽范围 `500-900 nm` 更适合建立“全局机制字典”，但不适合直接映射真实器件中的局部膜厚起伏。本轮将 thickness nuisance 收窄到 `675-725 nm`，目的是把厚度变化限制在更现实的局部褶皱/起伏尺度上，让后续算法面对的 nuisance 分布更接近实验场景。

## 3. 为什么 BEMA 不再当作单独专题，而视为 roughness background

本轮的目标是区分 thickness / roughness / air-gap，而不是继续扩展单一粗糙机制故事线。因此 front-BEMA 与 rear-BEMA 只保留其“effective roughness proxy”角色，用作 realistic background / nuisance family；真正重点是看 gap 在这种背景上是否仍能保留可判别指纹。

## 4. realistic background 下仍保留的 gap 指纹

- `front-gap`：主要保留 `front + transition` 窗口响应，并伴随次级 rear-window 耦合
- `rear-gap`：主要保留 `transition + rear` 的非均匀重构与更强的 rear shift / 非刚性残差
- 相比之下，thickness 仍更像 rear-window 的“可平移型” fringe 漂移

## 5. 哪些特征更像 thickness

- `rear_best_shift_nm` 较大
- `rear_shift_explained_fraction` 较高
- `front_plus_transition_to_rear_ratio` 较低

这说明 local thickness nuisance 仍然更接近“rear-window rigid shift”而非强局部重构。

## 6. 哪些特征更像 roughness

- `front_roughness_nuisance`：前窗与过渡区 RMS 响应较强，`front_plus_transition_to_rear_ratio` 偏高
- `rear_roughness_nuisance`：rear-window 幅度微扰明显，但 `rear_shift_explained_fraction` 低于 thickness

也就是说，roughness 更像 envelope / amplitude perturbation，而不是 rigid phase shift。

## 7. 哪些特征最有希望区分 front-gap vs rear-gap

- `front_plus_transition_to_rear_ratio`
- `rear_best_shift_nm`
- `rear_shift_explained_fraction`
- `front_rms_deltaR_500_650`
- `rear_rms_deltaR_810_1055`

其中：
- `front-gap` 更偏前窗/过渡区占优，且存在次级 rear 耦合
- `rear-gap` 更偏 transition/rear 主导，并保留更强的非刚性 rear-window 重构

## 8. 当前还不能回答什么

- 尚未纳入 composition variation / 成分工程
- 尚未进行实验拟合或真实噪声建模
- 仍是 specular TMM，不含散射
- 当前 roughness 仍是 BEMA proxy，不等于真实 AFM RMS 真值

## 9. 数据库规模摘要

- physical cases（manifest 唯一物理 case）：`153`
- logical family cases（feature DB 行数）：`176`
- 关键 family 统计：
```csv
family,n_cases,mean_front_rms,std_front_rms,mean_transition_rms,std_transition_rms,mean_rear_rms,std_rear_rms,mean_rear_best_shift_nm,std_rear_best_shift_nm,mean_rear_shift_explained_fraction,std_rear_shift_explained_fraction,family_fingerprint_comment
background_anchor,7,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0,Reference roughness anchor for gap overlays and nuisance comparisons.
front_gap_on_background,56,0.005817630231056679,0.005682244917635337,0.005496724593806229,0.0063059391163549005,0.0072840484421589765,0.007916383378740276,-2.0714285714285716,2.506114970406976,0.3461680098115387,0.2906045837814848,Front-gap keeps a front-to-transition dominant signature with secondary rear coupling.
front_roughness_nuisance,3,0.002833628983519902,0.0020037178190746075,0.00713371328817364,0.005064165757538322,0.010289074319348222,0.00727671767657015,0.0,2.449489742783178,0.46278346885496086,0.37995150582529275,Front roughness primarily reshapes front and transition-window envelope/background.
rear_gap_on_background,56,0.00011914792096122684,0.0001272342931213368,0.005925200969541486,0.0061075161092599695,0.010041306486471991,0.010761322581513282,-3.517857142857143,3.7984539685272494,0.6831539401648727,0.2745723560667973,Rear-gap keeps a transition-to-rear nonlinear reconstruction signature on roughness background.
rear_roughness_nuisance,3,2.3725443965795426e-05,1.753005896171987e-05,0.0008390435427717676,0.0006248773105503579,0.0006078998494451845,0.000453390867504185,0.0,0.0,0.3333333333333333,0.4714045207910317,Rear roughness acts more like rear-window envelope/amplitude perturbation than rigid shift.
thickness_nuisance,51,0.0006223817300384074,0.00036927817889890037,0.02542990255390081,0.015731403815477458,0.035370725213017866,0.02038661487721158,0.09803921568627451,14.874975566907972,0.8435722616446748,0.024487942191142836,Rear-window fringe shift remains the dominant signature of local PVK thickness variation.
```

## 10. 初步判别结论

- `thickness_nuisance` 的 family 平均 `rear_shift_explained_fraction` 为 `0.844`
- `rear_gap_on_background` 的 family 平均 `rear_best_shift_nm` 为 `-3.518 nm`
- `front_gap_on_background` 的 family 平均前窗 RMS 为 `0.582%`

这些结果支持：在 realistic thickness + roughness background 下，gap 指纹没有消失，只是必须依赖窗口分布 + rear shift/nonrigid residual 的联合特征去区分。
