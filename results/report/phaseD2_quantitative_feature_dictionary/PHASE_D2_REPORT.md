# Phase D-2 REPORT

## 1. 阶段目标

从 D-1 的描述性判别数据库推进到可计算、可排序、可路由的特征字典，为自动缺陷 routing 和 family-specific 全谱拟合建立输入层。

## 2. 特征设计逻辑

- 窗口能量：看响应长在哪个窗口。
- rear rigid-shift：看后窗是否像厚度刚体平移。
- rear 频谱：看主频、展宽、侧带和复杂度。
- wavelet / 时频：看局域复杂重构。
- template similarity：把 family mean signature 变成可直接比较的路由特征。

## 3. 关键结果

- thickness 最像 rear-window rigid shift。
- roughness 更像 envelope / amplitude perturbation。
- rear-gap 更像非刚性重构与侧带增加。
- front-gap 更像前窗新增响应加次级 rear 耦合。
- 当前结果已经支持“先分类，再按 family 受限拟合”的路线。

## 4. 推荐算法路线

1. 轻量 hand-crafted feature + tree model
2. 两阶段 routing
3. 低维 embedding + family classification
4. family-specific full-spectrum fitting

## 5. 限制

- 仍未引入 composition variation
- 仍为 specular TMM
- 仍基于 proxy roughness
- 频谱特征对窗口长度和预处理敏感

## 6. 最终汇报

1. 一共提取了 38 个新增特征。
2. 我认为最有效的前 10 个特征是：front_to_rear_ratio, wavelet_energy_front, wavelet_entropy_front, front_plus_transition_to_rear_ratio, sim_to_front_gap_template, rear_rms_deltaR_810_1055, rear_unaligned_rms_residual, transition_rms_deltaR_650_810, rear_shift_explained_fraction, rear_corr_before_shift。
3. 哪些特征更适合区分 front vs rear：front_to_rear_ratio, wavelet_energy_front, wavelet_entropy_front, front_plus_transition_to_rear_ratio, sim_to_front_gap_template, rear_rms_deltaR_810_1055。
4. 哪些特征更适合区分 thickness vs rear-gap：sim_to_front_gap_template, front_plus_transition_to_rear_ratio, rear_shift_explained_fraction, rear_corr_before_shift, wavelet_entropy_front, rear_unaligned_rms_residual。
5. 哪些特征更适合区分 roughness vs gap：sim_to_front_gap_template, front_to_rear_ratio, front_plus_transition_to_rear_ratio, rear_shift_explained_fraction, wavelet_entropy_front, wavelet_energy_front。
6. 推荐的自动 routing 路线：先做 hand-crafted feature routing，再做 family-specific full-spectrum fitting。
7. 当前仍缺的物理维度：composition variation、真实粗糙形貌、非镜面散射、实验噪声与工艺漂移。
