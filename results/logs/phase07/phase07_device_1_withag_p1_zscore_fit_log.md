# Phase 07 Dual-Window Inversion Log: DEVICE-1-withAg-P1

## Sample

- source_mode: `hdr_csv`
- source_path: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/test_data/phase7_data/DEVICE-1-withAg-P1_hdr_curves.csv`
- with_ag: `True`

## Window Scales

- front: n=`356`, median=`0.023976`, MAD=`0.002537`, scale=`0.023976`
- rear: n=`476`, median=`0.063783`, MAD=`0.029433`, scale=`0.063783`

## Best Parameters

- d_bulk: `810.305767`
- d_rough: `0.000000`
- sigma_thickness: `56.132510`
- ito_alpha: `4.407106`
- pvk_b_scale: `0.800000`
- niox_k: `0.000000`
- d_C60_bulk_best: `15.000000` nm
- window_cost_front: `5.360842`
- window_cost_rear: `0.023758`
- total_cost: `5.384599`
- rear_derivative_correlation: `0.052690`

## Masked Band Residual

- mean: `3.225684e-01`
- std: `2.371808e-01`
- max_abs: `6.346106e-01`

## Coarse Basin Candidates

- basins_nm: `[635.0, 838.0]`

## Boundary Checks

- bound_hit_flags: `{"d_bulk": false, "d_rough": true, "ito_alpha": false, "niox_k": true, "pvk_b_scale": true, "sigma_thickness": false}`
- warnings: `["d_rough 接近边界", "pvk_b_scale 接近边界", "niox_k 接近边界"]`

## Optimizer Stages

```json
[
  {
    "basin_center_nm": 635.0,
    "de_fun": 5.3765897110451135,
    "de_nit": 6,
    "de_nfev": 210,
    "lmfit_nfev": 80,
    "lmfit_success": false,
    "total_cost": 5.280104509628027,
    "rear_derivative_correlation": 0.05216547327217215,
    "params": {
      "d_bulk": 622.100646792503,
      "d_rough": 14.726628069960231,
      "sigma_thickness": 0.2762740864316287,
      "ito_alpha": 3.252629473243966,
      "pvk_b_scale": 0.8000000149011613,
      "niox_k": 5.327309393319701e-27
    }
  },
  {
    "basin_center_nm": 838.0,
    "de_fun": 5.522889680086068,
    "de_nit": 6,
    "de_nfev": 210,
    "lmfit_nfev": 80,
    "lmfit_success": false,
    "total_cost": 5.384599264197111,
    "rear_derivative_correlation": 0.052690225789244156,
    "params": {
      "d_bulk": 810.3057666031594,
      "d_rough": 1.0596280946695395e-07,
      "sigma_thickness": 56.13251009831351,
      "ito_alpha": 4.407106011670192,
      "pvk_b_scale": 0.8000000000000002,
      "niox_k": 2.52990769332436e-35
    }
  }
]
```
