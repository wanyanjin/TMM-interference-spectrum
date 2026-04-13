# Phase D-1 REPORT

## 1. 阶段目标

本阶段从 A-C 的“单机制字典”推进到 **realistic background 下的 air-gap 判别数据库**。目标不是训练分类器，而是先建立一套统一的前向判别输入，回答在局部 thickness 起伏与前后 roughness 背景存在时，front-gap / rear-gap 是否仍保留可识别的 `R_total` 指纹。

## 2. 为什么本轮不引入成分模型

本轮先冻结 composition engineering，不再继续扩展成分扰动或 surrogate uncertainty。这样可以把问题收敛为 thickness / roughness / gap 三类结构机制之间的判别问题，避免在算法路线选择前引入额外高维不确定性。

## 3. 模型定义

### realistic baseline

- `d_PVK = 700 nm`
- `d_BEMA_front = 10 nm`
- `d_BEMA_rear = 20 nm`
- `d_gap_front = 0`
- `d_gap_rear = 0`

### thickness nuisance family

- `d_PVK = 675-725 nm`
- `d_BEMA_front = 10 nm`
- `d_BEMA_rear = 20 nm`
- no gap

### roughness nuisance family

- front roughness: `d_BEMA_front = 5, 10, 15 nm`
- rear roughness: `d_BEMA_rear = 10, 20, 30 nm`

### gap overlays on realistic anchors

- 7 个 anchor backgrounds
- front-gap overlay: `d_gap_front = 0, 0.5, 1, 2, 3, 5, 10, 15 nm`
- rear-gap overlay: `d_gap_rear = 0, 0.5, 1, 2, 3, 5, 10, 15 nm`

## 4. 关键结果

### 局部 thickness 变化主要保留什么指纹

- rear-window `810-1055 nm` 仍是主敏感窗口
- `rear_best_shift_nm` 与 `rear_shift_explained_fraction` 仍然较高
- 在 realistic roughness background 上，thickness 仍然更像可平移型 fringe 漂移

### roughness 变化主要保留什么指纹

- front roughness 更偏前窗背景与 transition 包络变化
- rear roughness 更偏 rear-window 的 envelope / amplitude perturbation
- 两者都不像纯 thickness 那样能被单一 shift 高比例解释

### gap 叠加 roughness 后仍可用的窗口特征

- front-gap：`front + transition` 的 RMS 分布和次级 rear coupling 仍可用
- rear-gap：`transition + rear` 的非刚性重构、较强 rear shift / residual 组合仍可用
- 因此 gap 在 realistic background 上没有“消失”，只是需要用联合特征识别

## 5. 对后续算法的启发

最值得优先尝试的 robust features：

- `rear_best_shift_nm`
- `rear_shift_explained_fraction`
- `front_plus_transition_to_rear_ratio`
- `front_rms_deltaR_500_650`
- `rear_rms_deltaR_810_1055`

这些特征分别刻画：

- rear-window 是否更像 rigid shift
- rear-window 是否存在非刚性 residual
- 响应是否偏前侧还是偏后侧

## 6. 限制

- 未引入 composition variation
- 未做实验拟合
- 仍为 specular TMM
- BEMA 仍是 proxy，而不是真实 AFM 粗糙度真值
- gap 仍为理想平面 separation

## 7. 数据规模

- manifest 物理 case 数：`153`
- feature DB 逻辑 family case 数：`176`

## 8. 下一步算法建议

当前数据库更适合作为后续算法比较的输入，而不是直接当作最终分类器。下一步可优先比较：

1. 基于 hand-crafted features 的线性 / 树模型基线
2. 基于 rear shift + nonrigid residual 的两阶段判别
3. 基于窗口化 `Delta R_total` 的低维嵌入 + family classification
