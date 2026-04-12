# Phase 07 Two-Step Inversion Log: DEVICE-1-withoutAg-P1

## Sample

- source_mode: `hdr_csv`
- source_path: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/test_data/phase7_data/DEVICE-1-withoutAg-P1_hdr_curves.csv`
- with_ag: `False`

## Stage 1 Front Lock

- d_ITO: `90.000000` nm
- d_NiOx: `35.000000` nm
- sigma_front_rms_nm: `31.661435` nm
- stage1_front_cost: `0.059456`

## Stage 2 Rear Fit

- d_bulk: `747.059130`
- d_rough: `30.000000`
- sigma_thickness: `0.030032`
- ito_alpha: `5.000000`
- pvk_b_scale: `0.800000`
- niox_k: `0.120000`
- d_C60_bulk_best: `0.000000` nm
- window_cost_front: `0.059456`
- window_cost_rear: `0.130547`
- total_cost: `0.189046`
- rear_derivative_correlation: `0.053492`

## Boundary Checks

- bound_hit_flags: `{"d_ITO": true, "d_NiOx": true, "d_bulk": false, "d_rough": true, "ito_alpha": true, "niox_k": true, "pvk_b_scale": true, "sigma_front_rms_nm": false, "sigma_thickness": true}`
- warnings: `["d_ITO 接近边界", "d_NiOx 接近边界", "d_rough 接近边界", "sigma_thickness 接近边界", "ito_alpha 接近边界", "pvk_b_scale 接近边界", "niox_k 接近边界", "d_C60_bulk 退化到 0 nm，粗糙层已耗尽致密 C60"]`

## Optimizer Stages

```json
[
  {
    "stage": "stage1_front",
    "de_fun": 0.07518127799342818,
    "de_nit": 6,
    "de_nfev": 105,
    "lmfit_nfev": 24,
    "lmfit_success": true,
    "params": {
      "d_ITO": 90.00000000000001,
      "d_NiOx": 35.00000000000014,
      "sigma_front_rms_nm": 31.661434818347736
    },
    "front_cost": 0.05945562732528796
  },
  {
    "stage": "stage2_rear",
    "basin_center_nm": 768.0,
    "de_fun": 0.18736399393670888,
    "de_nit": 6,
    "de_nfev": 210,
    "lmfit_nfev": 62,
    "lmfit_success": true,
    "total_cost": 0.18904569480374586,
    "front_cost": 0.05849886641974167,
    "rear_cost": 0.13054682838400422,
    "rear_derivative_correlation": 0.05349213974833774,
    "params": {
      "d_bulk": 747.0591298440057,
      "d_rough": 29.999999999999996,
      "sigma_thickness": 0.030032484830881816,
      "ito_alpha": 4.9999999999993525,
      "pvk_b_scale": 0.800000000011471,
      "niox_k": 0.11999999999963283
    }
  }
]
```
