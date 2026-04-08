# Phase 07 Orthogonal Radar Diagnostic

## Spectral Anatomy

- 400-650 nm: `Zone 1: Complete Absorption (Front-only Probe)`
- 650-810 nm: `Zone 2: Chaos & PL (Masked in Fitting)`
- 810-1100 nm: `Zone 3: Transparent Cavity (Thickness Fitting)`

## Baseline

- Zone 1 mean reflectance: `5.8826%`
- Zone 2 mean reflectance: `35.7462%`
- Zone 3 mean reflectance: `80.0417%`

## Consistency Checks

- Dictionary rows: `71502`
- Expected rows: `71502`
- Front zero-gap fallback: `0.000e+00`
- Back zero-gap fallback: `0.000e+00`

## Max |Delta R| by Zone

- Front / Zone 1: `28.1573%`
- Front / Zone 2: `18.9505%`
- Front / Zone 3: `23.5588%`
- Back / Zone 1: `0.7068%`
- Back / Zone 2: `17.4583%`
- Back / Zone 3: `16.9296%`

## Phase 07 Conclusion

- Front stronger than back in Zone 1: `True`
- Zone 2 is retained for visualization but should be masked in the later LM weighting design.
- Zone 3 remains the primary transparent-cavity region for thickness-phase fitting.

## Outputs

- Baseline figure: `results/figures/phase07_baseline_3zones.png`
- Radar figure: `results/figures/phase07_orthogonal_radar.png`
- Dictionary: `data/processed/phase07/phase07_orthogonal_fingerprint_dictionary.csv`
