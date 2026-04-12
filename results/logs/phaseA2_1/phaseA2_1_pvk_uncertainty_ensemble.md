# Phase A-2.1 PVK Uncertainty Ensemble

## Inputs

- nominal aligned stack: `resources/aligned_full_stack_nk_pvk_v2.csv`
- Phase A-2 scan: `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- Phase B-1 scan: `data/processed/phaseB1/phaseB1_rear_bema_scan.csv`

## Ensemble Definition

- `nominal`: Repaired PVK surrogate v2 without extra perturbation | window `740-850 (soft 730-900)` | method `none`
- `more_absorptive`: Locally stronger band-edge absorption tail in 740-850 nm | window `740-850 (soft 730-900)` | method `smooth_k_up_with_linked_n_shift`
- `less_absorptive`: Locally weaker band-edge absorption tail in 740-850 nm | window `740-850 (soft 730-900)` | method `smooth_k_down_with_linked_n_shift`

## PVK QA

- `nominal` 749->750 step: Δn=`+0.001408`, Δk=`-0.006187`
- `more_absorptive` 749->750 step: Δn=`-0.000147`, Δk=`-0.008515`
- `less_absorptive` 749->750 step: Δn=`+0.002964`, Δk=`-0.004067`
- 三条曲线的差异主要集中在 `740-850 nm` band-edge / absorption-tail 区域。
- 所有 ensemble 成员都保持连续，没有重新引入新的 seam。
- `850-1100 nm` 的 nominal long-wave 趋势基本保持，仅允许很轻微的尾部联动。

## Thickness Propagation

- thickness amplitude max relative spread across ensemble: `0.000`
- 后窗主敏感窗口仍稳定落在 `810-1100 nm`。
- `d_PVK` 的“全局 fringe 相位/条纹位置漂移”结论在 ensemble 下仍成立，是稳健结论。

## Rear-BEMA Propagation

- rear-BEMA amplitude max relative spread across ensemble: `0.563`
- rear-BEMA 的“局部包络/轻微振幅微扰，非全局相位变化”结论在 ensemble 下仍成立。
- rear-BEMA 与 d_PVK 的正交性仍保留，但 amplitude 量级会受到 band-edge 先验一定影响。

## Robust vs Sensitive Features

- robust features: `rear-window dominant DeltaR wavelength under d_PVK; rear-window DeltaR amplitude under d_PVK; rear-window dominant DeltaR wavelength under rear-BEMA; band-edge DeltaR amplitude under d_PVK`
- surrogate-sensitive features: `rear-window DeltaR amplitude under rear-BEMA; band-edge DeltaR amplitude under rear-BEMA; absolute R_total at 780 nm under d_PVK; absolute R_total at 780 nm under rear-BEMA`

## Recommendation

- 建议下一步进入 `Phase B-2 front-only BEMA`，因为 thickness 与 rear-BEMA 的主要结论在当前 ensemble 下已经足够稳健，适合继续增加一个新的界面机制维度。
- `air-gap only` 更适合放在 front/rear 粗糙机制字典进一步完善之后，再做更清晰的机制比较。
