# Phase A-local Report

## 1. 任务目标

- 重新建立更接近真实器件局部厚度起伏的 PVK thickness 指纹图。
- 仅扫描 `d_PVK = 675-725 nm`，以 `700 nm` 为参考，输出 `R_total` 与 `Delta_R_total`。

## 2. 模型口径

- `Air / Glass(1 mm, incoherent) / ITO 100 / NiOx 45 / SAM 5 / PVK variable / C60 15 / Ag 100 / Air`
- normal incidence
- wavelength range: `400-1100 nm`, step `1 nm`
- optical constants: `resources/aligned_full_stack_nk_pvk_v2.csv`

## 3. 为什么采用 700 ± 25 nm

- 这次要代表的是局部膜厚起伏，而不是整个样品在极宽厚度区间内的全局偏差。
- `700 ± 25 nm` 既保留了足够清楚的微腔调制，又更接近真实器件里局部褶皱或小尺度厚度不均的量级。

## 4. 关键结果

- rear-window 的最强 RMS Delta R_total 出现在 `d_PVK = 725 nm`，约为 `7.521%`。
- transition-window 的最强 RMS Delta R_total 出现在 `d_PVK = 675 nm`，约为 `5.269%`。
- 热图显示主要变化集中在 transition / rear，尤其是 rear-window fringe 的系统漂移。
- 代表曲线图显示前窗变化较小，厚度效应更像条纹整体平移，而不是新长出局部异常结构。

## 5. 这套局部 thickness 字典对后续判别 air-gap 的意义

- 它先给出一个现实 thickness 背景下的标准谱形，帮助区分“条纹整体漂移”和“局部异常调制”这两类机制。
- 如果后续某组异常更像 rear-window 局部包络扭曲、非刚性变化或前窗联动异常，就不应直接归因于 thickness。
- 因此这套结果适合作为后续区分 thickness / roughness / air-gap 的基线参照。

## 6. 同步资产

- `phaseA_local_thickness_scan.csv`
- `phaseA_local_thickness_feature_summary.csv`
- `phaseA_local_deltaRtotal_heatmap.png`
- `phaseA_local_selected_curves.png`
- `phaseA_local_thickness_window.md`

