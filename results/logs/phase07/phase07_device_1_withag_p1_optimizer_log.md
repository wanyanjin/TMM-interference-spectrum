# Phase 07 Dual-Window Inversion Log: DEVICE-1-withAg-P1

## Sample

- source_mode: `hdr_csv`
- source_path: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/test_data/phase7_data/DEVICE-1-withAg-P1_hdr_curves.csv`
- with_ag: `True`

## Window Scales

- front: n=`356`, median=`0.023976`, MAD=`0.002537`, scale=`0.023976`
- rear: n=`476`, median=`0.063783`, MAD=`0.029433`, scale=`0.063783`

## Best Parameters

- d_bulk: `580.000006`
- d_rough: `24.905558`
- sigma_thickness: `0.003067`
- ito_alpha: `8.000000`
- pvk_b_scale: `0.800000`
- niox_k: `0.120000`
- d_C60_bulk_best: `2.547221` nm
- window_cost_front: `6.027978`
- window_cost_rear: `10.479079`
- total_cost: `16.507057`
- rear_derivative_correlation: `0.015145`

## Masked Band Residual

- mean: `3.123812e-01`
- std: `2.342527e-01`
- max_abs: `6.211412e-01`

## Coarse Basin Candidates

- basins_nm: `[608.0, 854.0]`

## Boundary Checks

- bound_hit_flags: `{"d_bulk": true, "d_rough": false, "ito_alpha": true, "niox_k": true, "pvk_b_scale": true, "sigma_thickness": true}`
- warnings: `["d_bulk 接近边界", "sigma_thickness 接近边界", "ito_alpha 接近边界", "pvk_b_scale 接近边界", "niox_k 接近边界"]`

## Optimizer Stages

```json
[
  {
    "basin_center_nm": 608.0,
    "de_fun": 16.968428285859236,
    "de_nit": 18,
    "de_nfev": 912,
    "lmfit_nfev": 150,
    "lmfit_success": true,
    "total_cost": 16.507056789587537,
    "rear_derivative_correlation": 0.015144644247777535,
    "params": {
      "d_bulk": 580.0000058988979,
      "d_rough": 24.905558240915536,
      "sigma_thickness": 0.0030671694324644386,
      "ito_alpha": 7.999999999999999,
      "pvk_b_scale": 0.8000000000000002,
      "niox_k": 0.11999999999999998
    }
  },
  {
    "basin_center_nm": 854.0,
    "de_fun": 23.797057094767474,
    "de_nit": 18,
    "de_nfev": 912,
    "lmfit_nfev": 109,
    "lmfit_success": true,
    "total_cost": 21.994929641899432,
    "rear_derivative_correlation": 0.024427598915481484,
    "params": {
      "d_bulk": 777.2677576850081,
      "d_rough": 29.99999999999774,
      "sigma_thickness": 0.03128208052650969,
      "ito_alpha": 7.999999999999999,
      "pvk_b_scale": 0.8000000000000002,
      "niox_k": 0.11999999999999998
    }
  }
]
```
