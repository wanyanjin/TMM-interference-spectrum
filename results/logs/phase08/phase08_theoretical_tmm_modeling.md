# Phase 08 Theoretical TMM Modeling Batch Log

## Scope

- Inputs: `data/processed/phase07/phase07_fit_summary.csv` + `data/processed/phase07/fit_inputs/*.csv`
- Optical stack: `resources/aligned_full_stack_nk.csv`
- Observation model: reuses Phase 07 front-surface Debye-Waller attenuation and rear-window z-score diagnostics

## Samples

### DEVICE-1-withAg-P1

- full_rmse: `0.131001`
- front_rmse: `0.005780`
- masked_rmse: `0.117495`
- rear_rmse: `0.183078`
- rear_derivative_correlation: `0.038880`
- d_bulk: `630.074795` nm
- d_rough: `0.000000` nm
- sigma_front_rms_nm: `31.355301` nm

### DEVICE-1-withoutAg-P1

- full_rmse: `0.024501`
- front_rmse: `0.005514`
- masked_rmse: `0.023713`
- rear_rmse: `0.032661`
- rear_derivative_correlation: `0.053492`
- d_bulk: `747.059130` nm
- d_rough: `30.000000` nm
- sigma_front_rms_nm: `31.661435` nm
