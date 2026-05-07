# Phase D-2 quantitative feature dictionary

## 1. Why rear-window FFT must use wavenumber

Rear fringes are approximately periodic in optical phase, not in wavelength itself. Direct FFT on wavelength smears the dominant period and mixes rigid shift with envelope distortion. Uniform `1/lambda` resampling restores near-stationary fringe spacing, so dominant frequency, bandwidth, and sideband energy become physically interpretable.

## 2. Which features best quantify thickness as rigid shift

`rear_best_shift_nm`, `rear_shift_explained_fraction`, `rear_corr_after_shift`, and low `rear_phase_slope_error`.

## 3. Which features best quantify roughness as amplitude / broadening perturbation

Front roughness: `front_plus_transition_to_rear_ratio`, `wavelet_energy_front`, `wavelet_entropy_front`.
Rear roughness: `rear_sideband_energy_fraction`, `rear_dom_freq_bandwidth`, `rear_spectral_entropy`.

## 4. Which features best quantify rear-gap as non-rigid reconstruction / sideband increase

`rear_sideband_energy_fraction`, `rear_second_peak_to_first_peak_ratio`, `rear_phase_slope_error`, `rear_spectral_entropy`.

## 5. Which features best quantify front-gap as front-window response plus secondary rear coupling

`front_rms_deltaR_500_650`, `wavelet_energy_front`, `sim_to_front_gap_template`, and non-zero rear complexity without rear-gap dominance.

## 6. Which features have the strongest separability

- 1. front_to_rear_ratio: F=164.905, eta^2=0.801
- 2. wavelet_energy_front: F=57.470, eta^2=0.584
- 3. wavelet_entropy_front: F=54.032, eta^2=0.569
- 4. front_plus_transition_to_rear_ratio: F=38.955, eta^2=0.487
- 5. sim_to_front_gap_template: F=37.446, eta^2=0.477
- 6. rear_rms_deltaR_810_1055: F=34.166, eta^2=0.455
- 7. rear_unaligned_rms_residual: F=34.166, eta^2=0.455
- 8. transition_rms_deltaR_650_810: F=33.858, eta^2=0.452
- 9. rear_shift_explained_fraction: F=29.585, eta^2=0.419
- 10. rear_corr_before_shift: F=27.890, eta^2=0.405

## 7. Which features look unstable or low-value

Less useful or unstable in this run: rear_peak_scale, wavelet_entropy_rear, rear_best_shift_nm, rear_phase_slope_error, d_PVK_nm, d_BEMA_front_nm, d_BEMA_rear_nm, rear_second_peak_to_first_peak_ratio.
