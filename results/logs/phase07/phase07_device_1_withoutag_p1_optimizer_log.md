# Phase 07 Dual-Window Inversion Log: DEVICE-1-withoutAg-P1

## Sample

- source_mode: `hdr_csv`
- source_path: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/test_data/phase7_data/DEVICE-1-withoutAg-P1_hdr_curves.csv`
- with_ag: `False`

## Window Scales

- front: n=`356`, median=`0.022800`, MAD=`0.002461`, scale=`0.022800`
- rear: n=`476`, median=`0.038246`, MAD=`0.005508`, scale=`0.038246`

## Best Parameters

- d_bulk: `733.641689`
- d_rough: `0.000000`
- sigma_thickness: `0.038006`
- ito_alpha: `8.000000`
- pvk_b_scale: `0.800000`
- niox_k: `0.016909`
- d_C60_bulk_best: `15.000000` nm
- window_cost_front: `6.078931`
- window_cost_rear: `1.639710`
- total_cost: `7.718641`
- rear_derivative_correlation: `0.032788`

## Masked Band Residual

- mean: `9.681447e-02`
- std: `3.756663e-02`
- max_abs: `1.660968e-01`

## Coarse Basin Candidates

- basins_nm: `[735.0]`

## Boundary Checks

- bound_hit_flags: `{"d_bulk": false, "d_rough": true, "ito_alpha": true, "niox_k": false, "pvk_b_scale": true, "sigma_thickness": true}`
- warnings: `["d_rough 接近边界", "sigma_thickness 接近边界", "ito_alpha 接近边界", "pvk_b_scale 接近边界"]`

## Optimizer Stages

```json
[
  {
    "basin_center_nm": 735.0,
    "de_fun": 7.7384092288294575,
    "de_nit": 18,
    "de_nfev": 912,
    "lmfit_nfev": 153,
    "lmfit_success": true,
    "total_cost": 7.718641306139649,
    "rear_derivative_correlation": 0.03278842792696273,
    "params": {
      "d_bulk": 733.6416888816067,
      "d_rough": 4.01544773207604e-08,
      "sigma_thickness": 0.038005685757816016,
      "ito_alpha": 7.99999999997677,
      "pvk_b_scale": 0.8000000000000002,
      "niox_k": 0.016908841629822542
    }
  }
]
```
