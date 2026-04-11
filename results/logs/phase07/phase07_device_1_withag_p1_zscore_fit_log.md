# Phase 07 Dual-Window Inversion Log: DEVICE-1-withAg-P1

## Sample

- source_mode: `hdr_csv`
- source_path: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/test_data/phase7_data/DEVICE-1-withAg-P1_hdr_curves.csv`
- with_ag: `True`

## Window Scales

- front: n=`356`, median=`0.023976`, MAD=`0.002537`, scale=`0.023976`
- rear: n=`476`, median=`0.063783`, MAD=`0.029433`, scale=`0.063783`

## Best Parameters

- d_bulk: `815.348576`
- d_rough: `0.006690`
- sigma_thickness: `70.565227`
- front_scale: `0.217180`
- ito_alpha: `4.999999`
- pvk_b_scale: `0.800000`
- niox_k: `0.120000`
- d_C60_bulk_best: `14.996655` nm
- window_cost_front: `0.012189`
- window_cost_rear: `0.014232`
- total_cost: `0.026421`
- rear_derivative_correlation: `0.057747`

## Masked Band Residual

- mean: `2.835315e-01`
- std: `2.020025e-01`
- max_abs: `6.052529e-01`

## Coarse Basin Candidates

- basins_nm: `[635.0, 838.0]`

## Boundary Checks

- bound_hit_flags: `{"d_bulk": false, "d_rough": true, "front_scale": false, "ito_alpha": true, "niox_k": true, "pvk_b_scale": true, "sigma_thickness": false}`
- warnings: `["d_rough 接近边界", "ito_alpha 接近边界", "pvk_b_scale 接近边界", "niox_k 接近边界"]`

## Optimizer Stages

```json
[
  {
    "basin_center_nm": 635.0,
    "de_fun": 0.03469862110233715,
    "de_nit": 6,
    "de_nfev": 245,
    "lmfit_nfev": 80,
    "lmfit_success": false,
    "total_cost": 0.028649727723914477,
    "rear_derivative_correlation": 0.05301815855459433,
    "params": {
      "d_bulk": 603.6929614397329,
      "d_rough": 29.99899376693536,
      "sigma_thickness": 57.265390738522164,
      "front_scale": 0.20268745631562743,
      "ito_alpha": 3.131992224382694,
      "pvk_b_scale": 1.2499999999927862,
      "niox_k": 0.11999999999998208
    }
  },
  {
    "basin_center_nm": 838.0,
    "de_fun": 0.06400534728797236,
    "de_nit": 6,
    "de_nfev": 245,
    "lmfit_nfev": 80,
    "lmfit_success": false,
    "total_cost": 0.02642063670177512,
    "rear_derivative_correlation": 0.057747296988607685,
    "params": {
      "d_bulk": 815.3485761865301,
      "d_rough": 0.006689507040073474,
      "sigma_thickness": 70.56522729632174,
      "front_scale": 0.21717984113938368,
      "ito_alpha": 4.9999988779485705,
      "pvk_b_scale": 0.8000000088534238,
      "niox_k": 0.11999999996160601
    }
  }
]
```
