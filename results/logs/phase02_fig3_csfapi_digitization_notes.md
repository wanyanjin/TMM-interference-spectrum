# Phase 02 Fig. 3 CsFAPI 光学常数图数字化说明

- 来源文献：`[LIT-0001] Khan et al. (2024)`
- 源图路径 (a)：`reference/Khan 等 - 2024 - Optical constants manipulation of formamidinium lead iodide perovskites ellipsometric and spectrosc.pdf-64661b05-c239-4731-a3f7-2c0456a4df66/images/4ad6d50871967bd68ad9d2d4b0a12bb3fe5adf116e9eec0d34d4752f2f7dac43.jpg`
- 源图路径 (b)：`reference/Khan 等 - 2024 - Optical constants manipulation of formamidinium lead iodide perovskites ellipsometric and spectrosc.pdf-64661b05-c239-4731-a3f7-2c0456a4df66/images/885e29d3301c8a26446578a1fe59d2783c89f227369fe031c7e24c763be6dc1c.jpg`
- 提取对象：Fig. 3 中 (a) 折射率 `n` 与 (b) 消光系数 `κ` 两个子图
- 提取方法：基于论文原始 MinerU 导出的图像做颜色分割与像素坐标标定，不使用截图二次压缩图。
- 样品命名按论文原图保留为 `Glass/CsFAPI` 与 `ITO/CsFAPI`。
- 精度边界：该 CSV 是“图像数字化数据”，不是论文作者公开的原始数值表；其准确度受原始图像分辨率和线宽限制。

## 轴标定

- Panel (a): `x = 450-1000 nm`, `y = 1.5-3.0`
- Panel (b): `x = 450-1000 nm`, `y = 0.0-1.2`
- 标定依据：Panel (a) 结合图框边界、刻度排布和正文给出的 `530 nm -> n≈2.81`、`800 nm -> n≈2.59` 做反校；Panel (b) 与 Fig. 2(b) 刻度体系一致。

## 数据范围检查

| panel | series | wavelength_min_nm | wavelength_max_nm | value_min | value_max |
| --- | --- | ---: | ---: | ---: | ---: |
| a | Glass/CsFAPI | 450.000 | 1000.000 | 2.350000 | 2.839286 |
| a | ITO/CsFAPI | 450.000 | 1000.000 | 2.389286 | 2.767857 |
| b | Glass/CsFAPI | 450.000 | 861.969 | 0.011538 | 0.842308 |
| b | ITO/CsFAPI | 450.000 | 1000.000 | 0.025962 | 0.954808 |
