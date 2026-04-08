# Phase 06 Dual-Mode Microcavity Defect Sandbox

## Stack Definition

- Baseline: `Glass / ITO / NiOx / PVK / C60 / Ag`
- Case A: `Glass / ITO / NiOx / PVK / C60 / Air_Gap / Ag`
- Case B: `Glass / ITO / NiOx / PVK / Air_Gap / C60 / Ag`
- Geometry: `Air -> Glass` front surface incoherent, rear thin-film stack coherent, normal incidence, Ag semi-infinite.

## Thicknesses

- ITO: `19.595 nm`
- NiOx: `22.443 nm`
- PVK: `500.000 nm`
- C60: `18.494 nm`

## Consistency Checks

- Case A zero-gap fallback vs baseline: `max_abs_diff = 0.000e+00`
- Case B zero-gap fallback vs baseline: `max_abs_diff = 0.000e+00`
- Dictionary rows: `71502`
- Expected rows: `71502`

## Band Metrics

### Case A: Glass/ITO/NiOx/PVK/C60/Air/Ag

- max(|Delta R|) over 400-650 nm, all d_air: `1.0957%`
- max(|Delta R|) over 850-1100 nm, all d_air: `21.4728%`
- max(|Delta R|) over 400-650 nm, d_air=40 nm: `0.9127%`
- max(|Delta R|) over 850-1100 nm, d_air=40 nm: `18.7232%`

### Case B: Glass/ITO/NiOx/PVK/Air/C60/Ag

- max(|Delta R|) over 400-650 nm, all d_air: `0.7068%`
- max(|Delta R|) over 850-1100 nm, all d_air: `16.9296%`
- max(|Delta R|) over 400-650 nm, d_air=40 nm: `0.5917%`
- max(|Delta R|) over 850-1100 nm, d_air=40 nm: `14.6215%`

## Outputs

- Dictionary: `data/processed/phase06/phase06_dual_mode_fingerprint_dictionary.csv`
- Delta comparison figure: `results/figures/phase06_dual_mode_delta_r_40nm_850_1100.png`
- Radar map figure: `results/figures/phase06_dual_mode_radar_map.png`

## Interpretation Note

- 本轮不对 400-650 nm 人为清零；该波段是否接近零响应，仅作为全栈前向模型的数值结果记录。
- `aligned_full_stack_nk.csv` 中的 NiOx 长波 k 与 PVK 400-449 nm 仍属于 Phase 05c 的工程补齐层，不应直接视为最终材料真值。
