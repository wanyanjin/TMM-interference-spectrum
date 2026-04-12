# Phase A-2 d_PVK Thickness Scan

## Inputs

- optical stack: `resources/aligned_full_stack_nk_pvk_v2.csv`
- geometry: `Glass(1 mm incoherent) / ITO 100 / NiOx 45 / SAM 5 / PVK variable / C60 15 / Ag 100 nm / Air`
- incidence: `normal`

## Scan Range

- d_PVK range: `500-900 nm`
- step: `5 nm`
- reference thickness: `700 nm`

## Primary Outputs

- scan csv: `data/processed/phaseA2/phaseA2_pvk_thickness_scan.csv`
- feature summary csv: `data/processed/phaseA2/phaseA2_pvk_feature_summary.csv`
- R_stack heatmap: `results/figures/phaseA2/phaseA2_R_stack_heatmap.png`
- R_total heatmap: `results/figures/phaseA2/phaseA2_R_total_heatmap.png`
- Delta R_stack heatmap: `results/figures/phaseA2/phaseA2_deltaR_stack_vs_700nm_heatmap.png`
- Delta R_total heatmap: `results/figures/phaseA2/phaseA2_deltaR_total_vs_700nm_heatmap.png`
- tracking figure: `results/figures/phaseA2/phaseA2_peak_valley_tracking.png`
- selected curves: `results/figures/phaseA2/phaseA2_selected_thickness_curves.png`

## Rear-Window Sensitivity

- R_total peak tracking Spearman: `-0.2330`
- R_total valley tracking Spearman: `0.5676`
- R_total peak drift slope: `-0.1131 nm peak shift / nm thickness`
- R_total valley drift slope: `0.3299 nm valley shift / nm thickness`
- rear-window monotonic sensitivity (R_total): `False`
- rear-window monotonic sensitivity (R_stack): `False`

## Most Sensitive Wavelengths

- rear-window R_stack top wavelengths: `1100 nm (11.59%), 1099 nm (11.56%), 1098 nm (11.52%)`
- rear-window R_total top wavelengths: `1100 nm (11.29%), 1099 nm (11.26%), 1098 nm (11.22%)`
- front-window R_stack top wavelengths: `650 nm (0.57%), 649 nm (0.56%), 648 nm (0.55%)`
- front-window R_total top wavelengths: `650 nm (0.52%), 649 nm (0.51%), 648 nm (0.51%)`

## R_stack vs R_total

- rear-window max std(R_stack): `11.59%`
- rear-window max std(R_total): `11.29%`
- front-window max std(R_stack): `0.57%`
- front-window max std(R_total): `0.52%`
- stack more sensitive than total in rear window: `True`

## Interpretation

- 后窗对 d_PVK 明显敏感，但把整个 500-900 nm 扫描压缩为单一“主峰/主谷”轨迹时会出现模式切换；因此更合理的结论是：后窗存在清晰系统漂移和可辨识局部近线性区间，而不是全范围单一模态严格单调。
- 最敏感波长集中在后窗 fringe 斜率最大的区域；前窗虽有变化，但幅度明显弱于后窗。
- `R_total` 由于叠加了固定 `R_front` 背景，会比 `R_stack` 略钝化，因此 `R_stack` 更适合做纯理论灵敏度分析，`R_total` 更接近实验可见量。
- 从谱形上看，厚度变化主要表现为后窗 fringe 的整体相位漂移和峰谷位置系统移动；这与界面缺陷常见的局部振幅扭曲、背景抬升或特定窗口异常并不相同。
- 因此 `d_PVK` 更像是“全局微腔光程变化”，而后续 BEMA / air gap 更可能表现为局部界面调制，两者虽然可耦合，但在后窗结构上并非完全混淆。

## Risks / Limits

- 当前扫描仍建立在 `PVK surrogate v2` 上，不代表 band-edge 真值已经确定。
- 本轮没有引入玻璃色散敏感性，也没有把 PVK surrogate 不确定性传播到厚度扫描结果。
- 峰谷追踪使用的是后窗主导极值的工程定义，适合建立厚度-条纹相位图谱，但不应替代更完整的模式标号分析。

## Next Step

- 建议下一步进入 `PVK uncertainty ensemble`，量化 surrogate band-edge 不确定性对 thickness scan 结论的传播范围。
- 在 uncertainty envelope 明确后，再进入 `BEMA only` 或 `air gap only` 的缺陷调制扫描会更稳妥。
