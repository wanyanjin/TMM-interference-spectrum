# Phase A-1.2 PVK Surrogate Rebuild + Pristine Rerun

## Inputs

- aligned v1: `resources/aligned_full_stack_nk.csv`
- aligned v2: `resources/aligned_full_stack_nk_pvk_v2.csv`
- baseline v1: `data/processed/phaseA1/phaseA1_pristine_baseline.csv`
- local PVK comparison: `data/processed/phaseA1_2/pvk_v1_v2_local_comparison.csv`
- candidate metrics: `data/processed/phaseA1_2/pvk_v2_candidate_metrics.csv`

## Surrogate Build Choice

- selected transition zone: `740-780 nm`
- blend / bridge method: `smoothstep blend in transition zone + cosine-tail k decay + relaxed n target toward extended trend`
- right-side hard zero at 750 nm: `removed`

## Seam Metrics

- `Δn(749->750)`: v1 `+0.009820`, v2 `+0.001408`
- `Δk(749->750)`: v1 `-0.021517`, v2 `-0.006187`
- `Δeps2(749->750)`: v1 `-0.112429`, v2 `-0.030895`
- `ΔR_stack(749->750)`: v1 `+0.113042`, v2 `+0.001713`
- `ΔR_total(749->750)`: v1 `+0.107011`, v2 `+0.001580`

## Local Smoothness Metrics (740-780 nm)

- `max(|dn/dlambda|)`: v1 `0.017367`, v2 `0.003422`
- `max(|dk/dlambda|)`: v1 `0.035862`, v2 `0.009411`
- `max(|Δ²n|)`: v1 `0.008678`, v2 `0.000379`
- `max(|Δ²k|)`: v1 `0.018793`, v2 `0.000756`

## Fringe Preservation (810-1100 nm)

- `R_total fringe RMSE`: `0.000000`
- `R_total fringe correlation`: `1.000000`
- mean peak/valley shift: `0.000 nm`

## Judgement

- seam removed enough: `True`
- band-edge jump downgraded to continuous transition: `True`
- rear-window fringe preserved: `True`
- 750 nm 附近的原始台阶已从明显跳变压低为连续但较陡的 band-edge 过渡。
- 修复主要局限在 740-800 nm，810-1100 nm 后窗微腔结构基本保留。

## Outputs

- baseline csv: `data/processed/phaseA1_2/phaseA1_2_pristine_baseline.csv`
- decomposition figure: `results/figures/phaseA1_2/phaseA1_2_pristine_decomposition.png`
- 3-zone figure: `results/figures/phaseA1_2/phaseA1_2_pristine_3zones.png`
- zoom figure: `results/figures/phaseA1_2/phaseA1_2_pristine_720_780_zoom.png`
- full-spectrum comparison: `results/figures/phaseA1_2/phaseA1_2_pristine_v1_vs_v2_full_spectrum.png`

## Next Direction

- 建议下一步优先进入 `d_PVK thickness scan`。当前 zero-defect baseline 已去掉最显著 seam artifact，且后窗 fringe 仍保持，可直接用于评估 `d_PVK` 对条纹相位与周期的灵敏度。
- `PVK uncertainty ensemble` 适合作为紧随其后的第二步，用于量化 band-edge surrogate 不确定性对 baseline 的传播。
