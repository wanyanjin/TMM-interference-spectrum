# Phase 07 Two-Step Inversion Log: DEVICE-1-withAg-P1

## Sample

- source_mode: `hdr_csv`
- source_path: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/test_data/phase7_data/DEVICE-1-withAg-P1_hdr_curves.csv`
- with_ag: `True`

## Stage 1 Front Lock

- d_ITO: `90.000000` nm
- d_NiOx: `35.000000` nm
- sigma_front_rms_nm: `31.355301` nm
- stage1_front_cost: `0.063307`

## Stage 2 Rear Fit

- d_bulk: `630.074795`
- d_rough: `0.000000`
- sigma_thickness: `0.062096`
- ito_alpha: `5.000000`
- pvk_b_scale: `0.800000`
- niox_k: `0.000000`
- d_C60_bulk_best: `15.000000` nm
- window_cost_front: `0.063307`
- window_cost_rear: `0.096633`
- total_cost: `0.154753`
- rear_derivative_correlation: `0.038880`

## Boundary Checks

- bound_hit_flags: `{"d_ITO": true, "d_NiOx": true, "d_bulk": false, "d_rough": true, "ito_alpha": true, "niox_k": true, "pvk_b_scale": true, "sigma_front_rms_nm": false, "sigma_thickness": true}`
- warnings: `["d_ITO 接近边界", "d_NiOx 接近边界", "d_rough 接近边界", "sigma_thickness 接近边界", "ito_alpha 接近边界", "pvk_b_scale 接近边界", "niox_k 接近边界"]`

## Optimizer Stages

```json
[
  {
    "stage": "stage1_front",
    "de_fun": 0.0796899402706716,
    "de_nit": 6,
    "de_nfev": 105,
    "lmfit_nfev": 24,
    "lmfit_success": true,
    "params": {
      "d_ITO": 90.00000000000001,
      "d_NiOx": 35.00000000000001,
      "sigma_front_rms_nm": 31.35530117074431
    },
    "front_cost": 0.0633074258836142
  },
  {
    "stage": "stage2_rear",
    "basin_center_nm": 641.0,
    "de_fun": 0.17566981571695658,
    "de_nit": 6,
    "de_nfev": 210,
    "lmfit_nfev": 68,
    "lmfit_success": true,
    "total_cost": 0.15475288738231652,
    "front_cost": 0.05812009295138484,
    "rear_cost": 0.09663279443093165,
    "rear_derivative_correlation": 0.03888029303382088,
    "params": {
      "d_bulk": 630.0747945204143,
      "d_rough": 4.822026044295479e-12,
      "sigma_thickness": 0.06209593357280302,
      "ito_alpha": 4.999999999999999,
      "pvk_b_scale": 0.8000000000000002,
      "niox_k": 2.0811834731263983e-19
    }
  },
  {
    "stage": "stage2_rear",
    "basin_center_nm": 855.0,
    "de_fun": 0.4844143236703416,
    "de_nit": 6,
    "de_nfev": 210,
    "lmfit_nfev": 80,
    "lmfit_success": false,
    "total_cost": 0.20520181636180876,
    "front_cost": 0.060024202611364506,
    "rear_cost": 0.14517761375044425,
    "rear_derivative_correlation": 0.047532875068581545,
    "params": {
      "d_bulk": 818.7328544817894,
      "d_rough": 0.025639016262928353,
      "sigma_thickness": 75.09778493527119,
      "ito_alpha": 4.999999999999986,
      "pvk_b_scale": 0.8000000000000002,
      "niox_k": 0.11999999999999961
    }
  }
]
```
