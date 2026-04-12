# Phase A-1.1 PVK Seam Audit

## Inputs

- aligned stack: `resources/aligned_full_stack_nk.csv`
- pristine baseline: `data/processed/phaseA1/phaseA1_pristine_baseline.csv`
- PVK extended middleware: `data/processed/CsFAPI_nk_extended.csv`
- PVK digitized source: `resources/digitized/phase02_fig3_csfapi_optical_constants_digitized.csv`
- stitch builder: `src/scripts/step05c_build_aligned_nk_stack.py`

## Audit Scope

- 几何口径沿用 Phase A-1：Glass(incoherent) / ITO(100) / NiOx(45) / SAM(5) / PVK(700) / C60(15) / Ag(100)。
- 不做拟合、不改主链路数据表、不做平滑修复。

## Q1. 749/750 nm 处，PVK n/k/eps1/eps2 是否存在明显 seam？

- `n_PVK`: 749 nm = `2.622376`, 750 nm = `2.632196`, step = `+0.009820`
- `k_PVK`: 749 nm = `0.043034`, 750 nm = `0.021517`, step = `-0.021517`
- `eps1`: step = `+0.052991`
- `eps2`: step = `-0.112429`
- 结论：seam 被确认存在，且在 `k_PVK` 与 `eps2` 上尤为明显。

## Q2. 这个 seam 是数值跳点、导数跳点，还是 k=0 硬切换？

- `n_PVK` 存在值跳点，但更强的是导数变化：slope_jump = `-0.007544`
- `k_PVK` 同时存在值跳点和导数尖峰：slope_jump = `+0.014345`
- `extended_csv` 在 750 nm 起 `k=0`：`True`
- 结论：当前 seam 更接近“右侧 k=0 硬约束 + 拼接导数不连续”的组合，而不是单纯的平滑 band-edge。

## Q3. seam 来自哪一个上游步骤？

- 当前最直接来源是：`digitized 左段 + extended 右段的 step05c 拼接逻辑`。
- digitized 数据承担 450-749 nm 左段，extended middleware 承担 750 nm 及以上右段。
- step05c 在 744->750 nm 先做线性 bridge，再在 750 nm 周围做 rolling smooth，但并未消除导数不连续。
- step05c 证据：`upper_mask = WL_GRID >= PVK_MID_BOUNDARY_NM`
- step05c 证据：`middle_mask = (WL_GRID >= PVK_LOW_BOUNDARY_NM) & (WL_GRID < PVK_MID_BOUNDARY_NM)`
- step05c 证据：`n_values = bridge_to_boundary(n_values, 744, 750)`
- step05c 证据：`k_values = bridge_to_boundary(k_values, 744, 750)`
- step05c 证据：`n_values = smooth_join_region(n_values, 750)`
- step05c 证据：`k_values = smooth_join_region(k_values, 750, force_nonnegative=True)`

## Q4. 在最简堆栈中 seam 是否已经能看到？

- `Glass / PVK / Air` 的 749->750 nm 反射率步长 = `+0.008775`
- `Glass / ITO / NiOx / SAM / PVK / Air` 的步长 = `+0.012712`
- `Glass / ITO / NiOx / SAM / PVK / C60 / Ag / Air` 的步长 = `+0.113042`
- 结论：最简堆栈已经可以看到同类 seam，不是完整器件才首次生成的问题。

## Q5. 完整 stack 是否显著放大了 seam？

- simple -> mid -> full 的步长依次为 `+0.008775`, `+0.012712`, `+0.113042`
- 结论：层序复杂化会逐步放大 seam；完整 stack 可视为 `PVK seam × 微腔增强` 的乘积结果。

## Q6. Ag 终端边界是否是重要放大因子？

- finite Ag `R_stack` step = `+0.113042`
- semi-infinite Ag `R_stack` step = `+0.113062`
- 结论：Ag 终端只弱影响 seam，不是主导来源。

## Q7. 当前证据更支持哪种解释？

- 1. `PVK 数据拼接伪影`：`k_PVK` 在 749/750 nm 附近出现显著跃迁，且 `n_PVK/eps2` 导数尖峰与 step05c 的 bridge+smooth 拼接逻辑一致。
- 2. `多因素共同作用`：最简堆栈已可见 seam，但完整堆栈 step 从 `0.008775` 放大到 `0.113042`，说明微腔会增强材料 seam。
- 3. `真实 band-edge 急变`：不能完全排除，但当前接缝与上游拼接边界精确同位，更弱于数据伪影假说。
- 4. `代码实现 bug`：当前未发现层序切换、插值 off-by-one 或边界条件误切换；

## Code-Level Audit

- 插值：当前主链路没有在 Phase A-1 内对 PVK 再做额外插值，波长网格是整数 1 nm，对齐表与 baseline CSV 一致。
- 边界条件：`R_stack` 没有发现 749/750 nm 附近的边界条件切换。
- 图像显示：Phase A-1 CSV 原始数值本身存在 749/750 nm 附近步长，不是仅图像采样造成。
- 未发现代码级实现错误。
- 当前更支持材料 seam 而非代码 bug 假说。

## Outputs

- local audit csv: `data/processed/phaseA1_seam_audit/pvk_seam_local_audit.csv`
- source comparison csv: `data/processed/phaseA1_seam_audit/pvk_source_comparison.csv`
- stack sensitivity csv: `data/processed/phaseA1_seam_audit/seam_stack_sensitivity.csv`
- ag sensitivity csv: `data/processed/phaseA1_seam_audit/seam_ag_boundary_sensitivity.csv`
- figures: `results/figures/phaseA1_seam_audit/*.png`

## Recommended Next Fix Direction

- 当前最优先建议是 `blend-zone repair`，因为 seam 已明确锚定在上游拼接边界，且主要表现为 `k` 右侧过硬与导数不连续；先修复拼接区，比直接改 Ag 终端或重写主链路更对症。
