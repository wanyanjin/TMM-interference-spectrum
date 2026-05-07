# Phase A-1 Pristine Baseline

## Inputs

- n-k input: `resources/aligned_full_stack_nk.csv`
- required columns validated: `Wavelength_nm, n_ITO, k_ITO, n_NiOx, k_NiOx, n_PVK, k_PVK, n_C60, k_C60, n_Ag, k_Ag`
- aligned_full_stack_nk.csv 包含 n_Glass/k_Glass；本轮仅将其作为一致性参考，不参与求解。

## Geometry And Solver Contract

- incidence: `normal incidence`
- front medium: `Air`
- thick glass handling: `1 mm glass treated as incoherent, excluded from phase matrix`
- constant glass override: `n_glass = 1.515`, `k_glass = 0`
- stack geometry: `Glass -> ITO(100 nm) -> NiOx(45 nm) -> SAM(5 nm) -> PVK(700 nm) -> C60(15 nm) -> Ag(100 nm) -> Air`
- Ag boundary mode: `100 nm finite Ag film + semi-infinite Air exit medium`

## Disabled Modulations

- `d_air = 0`
- `d_rough = 0`
- `sigma_thickness = 0`
- `ito_alpha = 0`
- `pvk_b_scale = 1`
- `front_scale` unused
- `BEMA` disabled
- empirical background / absorption corrections disabled

## Key Numbers

- `R_front(550 nm) = 4.1931%`
- `R_stack(550 nm) = 7.1041%`
- `R_total(550 nm) = 10.7335%`
- `R_total` minimum: `4.5379% @ 463 nm`
- `R_total` maximum: `79.7261% @ 947 nm`
- Zone 1 mean `R_total`: `8.7984%`
- Zone 2 mean `R_total`: `31.5064%`
- Zone 3 mean `R_total`: `62.7946%`

## Spectral Summary

- `R_front` 基本为平滑弱背景，而 `R_stack` 与 `R_total` 在长波端结构更强；`R_total` 的主要峰谷范围约为 `4.54% - 79.73%`。

## Three-Zone Interpretation

- Zone 1 (`400-650 nm`): R_total 主要由后侧 stack 控制，R_front 在该段占据显著比例；同时后侧 stack 已出现明显结构性调制。
- Zone 2 (`650-810 nm`): 可以视为从强吸收主导向透明干涉主导的过渡区，且 微腔效应已经开始显现。
- Zone 3 (`810-1100 nm`): 已出现清晰干涉条纹，这些 fringe 的主导来源 可视为 PVK 与上下边界共同形成的多层微腔效应。

## Validation

- 强度级联闭合误差 max_abs = 0.000e+00

## Anomalies

- 未发现列缺失、波长网格异常、反射率越界、NaN 或 Inf。

## Outputs

- csv: `data/processed/phaseA1/phaseA1_pristine_baseline.csv`
- figure (decomposition): `results/figures/phaseA1/phaseA1_pristine_decomposition.png`
- figure (3 zones): `results/figures/phaseA1/phaseA1_pristine_3zones.png`
- log: `results/logs/phaseA1/phaseA1_pristine_baseline.md`

## Note

- 后续可在同一 pristine baseline 上做 `constant-glass vs dispersive-glass` sensitivity check。
