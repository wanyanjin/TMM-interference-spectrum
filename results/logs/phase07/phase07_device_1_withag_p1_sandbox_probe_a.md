# Phase 07 Sandbox Probe A: DEVICE-1-withAg-P1

## Setup

- Geometry locked: `d_ITO = 100 nm`, `d_NiOx = 45 nm`, `sigma_front_rms_nm = 0`
- Fixed rear parameters: `d_bulk = 700`, `d_rough = 0`, `sigma_thickness = 0`, `ito_alpha = 0`, `pvk_b_scale = 1`, `niox_k = 0`
- Probe compares short-wave extra absorption on `NiOx` and `ITO` separately.

## Results

- baseline_cost: `11.813532`
- niox_best_extra_k: `0.000400`
- niox_best_cost: `11.816109`
- ito_best_extra_k: `0.278787`
- ito_best_cost: `6.655461`
- better_target: `ITO`

## Interpretation

- If `NiOx` probe fails to lower cost while `ITO` helps, the original `NiOx short-wave absorption missing` hypothesis is likely false.
- If neither branch crosses `0.05`, then a single scalar short-wave absorber is insufficient to explain the front-window mismatch.

- figure: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/results/figures/phase07/phase07_device_1_withag_p1_sandbox_probe_a.png`
