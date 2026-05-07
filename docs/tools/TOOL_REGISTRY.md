# Tool Registry

| Tool name | Status | Phase | CLI | GUI | Workflow | Core module | Docs | Notes |
|---|---|---|---|---|---|---|---|---|
| `reference_comparison` | active | Phase 08 | `src/cli/reference_comparison.py` | planned | planned | `src/core/reference_comparison.py` | `docs/cli/reference_comparison.md` | Formal CLI exists; workflow layer not yet split out. |
| `phase06_hdr_calibration` | script-only | Phase 06 | `src/scripts/step06_single_sample_hdr_absolute_calibration.py`, `src/scripts/step06_batch_hdr_calibration.py` | planned | planned | `src/core/hdr_absolute_calibration.py` | `docs/cli/phase06_hdr_calibration.md` | Core exists, but entry remains script-first. |
| `phase07_dual_window_inversion` | script-only | Phase 07 | `src/scripts/step07_dual_window_inversion.py` | planned | planned | `src/core/phase07_dual_window.py` | `docs/cli/phase07_dual_window_inversion.md` | Not yet formalized into workflow + stable CLI split. |
| `reflectance_qc` | experimental | Phase 09C-2 | `src/cli/reflectance_qc.py` | experimental (`src/gui/reflectance_qc/app.py`) | `src/workflows/reflectance_qc_workflow.py` | `src/core/reflectance_qc.py` | `docs/cli/reflectance_qc.md`, `docs/tools/reflectance_qc.md`, `docs/gui/reflectance_qc_gui.md` | GUI supports raw spectra QC and processed result viewer; still not a full TMM fitting GUI. |
