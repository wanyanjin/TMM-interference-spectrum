# Phase 07 Sandbox Probe D Audit: DEVICE-1-withAg-P1

## Inputs

- raw_dir: `/Users/luxin/Library/CloudStorage/OneDrive-共享的库-onedrive/Data/PL/2026/0409/cor`
- hdr_curve: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/test_data/phase7_data/DEVICE-1-withAg-P1_hdr_curves.csv`
- gcc_xlsx: `/Users/luxin/百度网盘同步/Code/TMM-interference-spectrum/resources/GCC-1022系列xlsx.xlsx`

## Route 1: Theory Audit

- Model: `Air -> Glass(incoherent) -> ITO(100 nm) -> NiOx(45 nm) -> PVK(semi-infinite)`
- No roughness, no SAM, no optimizer.
- target_wavelength_nm: `550.000`
- R_front_air_glass_only: `4.193131%`
- R_total_theory: `11.889254%`

## Route 2: Calibration Audit

- audit_wavelength_nm: `550.146546200`

### Raw Counts and Exposure

- sample_short_raw_counts: `32617.833333` at `150.000000 ms`
- sample_long_raw_counts: `64895.000000` at `2000.000000 ms`
- ag_short_raw_counts: `40565.949219` at `0.500000 ms`
- ag_long_raw_counts: `64899.000000` at `10.000000 ms`

### Raw Counts / Time

- sample_short_raw_counts_per_ms: `217.452222`
- sample_long_raw_counts_per_ms: `32.447500`
- ag_short_raw_counts_per_ms: `81131.898438`
- ag_long_raw_counts_per_ms: `6489.900000`

### HDR Branch and Alignment

- sample_short_scale_factor: `0.948791125`
- ag_short_scale_factor: `0.092795963`
- sample_w_long_at_550: `0.000000`
- ag_w_long_at_550: `0.000000`
- sample_n_short_aligned: `206.316739`
- ag_n_short_aligned: `7528.712606`
- sample_hdr_counts_per_ms: `206.316739`
- ag_hdr_counts_per_ms: `7528.712606`

### Mirror Reference

- ag_theory_reflectance_at_550: `97.454396%`

### Manual Reproduction

- manual_raw_short_short = `(sample_short_raw_n / ag_short_raw_n) * R_ref` = `0.261200%`
- manual_raw_long_long = `(sample_long_raw_n / ag_long_raw_n) * R_ref` = `0.487242%`
- manual_hdr = `(sample_hdr_n / ag_hdr_n) * R_ref` = `2.670639%`

### Exported Comparison

- rebuilt_hdr_reflectance_at_550: `2.670639%`
- exported_hdr_curve_index: `121`
- exported_hdr_curve_wavelength_nm: `550.146546200`
- exported_hdr_curve_reflectance_at_550: `2.709895%`
- export_vs_rebuild_delta_percentage_point: `0.039256`

## Engineering Verdict

- 550 nm 极简理论正算得到 `R_theory = 11.889%`，明显高于实验校准值。
- 使用 0409 原始文件重建 HDR 后，550 nm 得到 `R_hdr_manual = 2.671%`；与导出表的 `2.710%` 仅差 `0.039 个百分点`。
- 说明当前 Phase 06/07 的校准代码在 550 nm 处是**算理自洽**的；不存在把 10% 错算成 2.5% 的隐藏曝光时间解析 Bug。
- 反而，若直接忽略 HDR 对齐因子、仅用原始短曝光 `Counts/Time` 计算，会得到更低的 `0.261%`，这与导出结果不符。
- 因此，当前主要落差不是代码把理论值压低，而是实验观测到的镜面收集强度显著低于理想正反射模型。就 550 nm 这一点看，`11.89% -> 2.67%` 的差距更符合几何 NA/散射漏光一类观测损失。