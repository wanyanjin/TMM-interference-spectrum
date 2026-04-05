# Phase 02 Fig. 2 FAPI 光学常数图数字化说明

- 来源文献：`[LIT-0001] Khan et al. (2024)`
- 源图路径：`reference/Khan 等 - 2024 - Optical constants manipulation of formamidinium lead iodide perovskites ellipsometric and spectrosc.pdf-64661b05-c239-4731-a3f7-2c0456a4df66/images/b3c499f799c0be47f32bf58a0c588af9c30db72b33cb6d3577d4c4317a76a48d.jpg`
- 提取对象：Fig. 2 中 (a) 折射率 `n` 与 (b) 消光系数 `κ` 两个子图
- 提取方法：基于论文原始 MinerU 导出的图像做颜色分割与像素坐标标定，不使用截图二次压缩图。
- 采样策略：保留曲线在原图像素列上的原生采样，不向 1 nm 网格做额外插值。
- 精度边界：该 CSV 是“图像数字化数据”，不是论文作者公开的原始数值表；其准确度受原始图像分辨率和线宽限制。

## 轴标定

- Panel (a): `x = 450-1000 nm`, `y = 1.2-2.5`
- Panel (b): `x = 450-1000 nm`, `y = 0.0-1.2`
- 标定依据：图框边界、刻度位置和正文描述相互校对；其中 Panel (a) 顶部边界高于 `2.4` 刻度半个主刻度，对应 `2.5`。

## 数据范围检查

| panel | series | wavelength_min_nm | wavelength_max_nm | value_min | value_max |
| --- | --- | ---: | ---: | ---: | ---: |
| a | Glass/FAPI | 450.000 | 997.860 | 1.811951 | 2.363659 |
| a | ITO/FAPI | 450.000 | 997.860 | 1.643902 | 2.227317 |
| b | Glass/FAPI | 450.000 | 905.098 | 0.040191 | 1.053589 |
| b | ITO/FAPI | 450.000 | 1000.000 | 0.014354 | 1.030622 |
