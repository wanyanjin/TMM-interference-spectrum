# Phase A-local Thickness Window

## 1. 为什么本轮把 thickness 范围收窄到 700 ± 25 nm

- 这次要代表的是器件局部褶皱、轻微起伏和小尺度膜厚不均，而不是整片器件从 500 nm 到 900 nm 的大范围工艺漂移。
- 以 700 nm 为中心、只看 ±25 nm，更接近后续实际判别里会遇到的局部 thickness 扰动量级。

## 2. 相比原始 500–900 nm 扫描，这一版更适合代表什么物理场景

- 旧版更适合展示“厚度从明显偏薄到明显偏厚”的全局趋势。
- 这一版更适合代表真实器件中局部位置之间只有几十纳米差异的厚度起伏场景。

## 3. 在这个更现实的范围内，R_total 的主要变化集中在哪个窗口

- front 窗口的最大 RMS Delta R_total 约为 `0.138%`，变化最弱。
- transition 窗口的最大 RMS Delta R_total 约为 `5.269%`，已经开始明显响应。
- rear 窗口的最大 RMS Delta R_total 约为 `7.521%`，是最主要的变化区。

## 4. 局部 thickness 变化最直观的谱形指纹是什么

- 最直观的指纹不是新增孤立异常峰，而是 rear-window fringe 整体沿波长方向系统漂移。
- 在这组扫描里，rear peak-valley spacing 保持在 `101.0-102.0 nm`，说明主要是条纹位置移动，而不是条纹类型突然改变。
- 700 nm 参考曲线本身的 rear peak / valley 位于 `947.0 nm` / `845.0 nm`，可作为后续判别的零点。

## 5. 这一版图在后续区分 thickness / roughness / air-gap 时有什么作用

- 它先给出一个更现实的 thickness 基线，告诉我们局部厚度起伏通常会把 rear-window 条纹整体推来推去。
- 后续如果看到的是局部异常结构、包络被扭曲、或前窗也同步出现不成比例变化，就更像 roughness 或 air-gap，而不只是 thickness。
- 因此这套图更适合作为后续机制判别里的“局部 thickness 字典”。

