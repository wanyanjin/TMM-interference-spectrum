# Phase 04a Air Gap Diagnostic

## Inputs

- good raw: `/Users/luxin/code/TMM-interference-spectrum/test_data/good-21.csv`
- bad raw: `/Users/luxin/code/TMM-interference-spectrum/test_data/bad-23.csv`
- good calibrated: `/Users/luxin/code/TMM-interference-spectrum/data/processed/phase04a/good-21_calibrated.csv`
- bad calibrated: `/Users/luxin/code/TMM-interference-spectrum/data/processed/phase04a/bad-23_calibrated.csv`

## Good-21 6-Parameter Fit

- success: `True`
- chi-square: `0.002652`
- d_bulk: `444.388 nm`
- d_rough: `50.966 nm`
- sigma_thickness: `26.071 nm`
- ito_alpha: `13.461566`
- pvk_b_scale: `1.696030`
- niox_k: `0.484044`

## Bad-23 6-Parameter Fit

- success: `True`
- chi-square: `0.031967`
- d_bulk: `409.300 nm`
- d_rough: `99.871 nm`
- sigma_thickness: `45.423 nm`
- ito_alpha: `11.352921`
- pvk_b_scale: `0.596959`
- niox_k: `0.039561`

## Bad-23 7-Parameter Fit

- success: `True`
- chi-square: `0.016193`
- relative improvement: `49.34%`
- d_bulk: `465.629 nm`
- d_bulk 95% CI: `[463.645, 467.612]`
- d_rough: `36.217 nm`
- d_rough 95% CI: `[33.555, 38.879]`
- sigma_thickness: `26.359 nm`
- sigma_thickness 95% CI: `[25.356, 27.362]`
- d_air: `39.923 nm`
- d_air 95% CI: `[38.652, 41.195]`
- CI method: `stderr_approx_95`
- stuck at lower bound: `False`
- stuck at initial value: `False`
- no material improvement: `False`
- chi-square below 0.01: `False`

## Conclusion

- 空气隙单因子解释不足。需要优先检查 ITO 退化、PVK 色散漂移、或其他界面/层退化。
