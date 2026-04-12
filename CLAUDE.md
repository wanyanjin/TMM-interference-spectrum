# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **TMM (Transfer Matrix Method) interference spectrum analysis project** for perovskite solar cells (PSCs). It performs non-contact quantitative analysis of the internal Z-axis optical structure using rigorous TMM combined with Levenberg-Marquardt (LM) optimization.

**Key Domain Concepts:**
- **TMM**: Transfer Matrix Method for optical simulation of thin-film stacks
- **LM**: Levenberg-Marquardt optimization algorithm for parameter inversion
- **HDR**: High Dynamic Range spectral data fusion
- **n-k**: Refractive index (n) and extinction coefficient (k) optical constants
- **PVK**: Perovskite layer (the active material)

**Current Phase**: Phase 07 (Dual-window joint inversion with HDR pipeline)

## Project Structure

```
TMM-interference-spectrum/
├── AGENTS.md              # Project development standards (MUST READ)
├── docs/
│   ├── PROJECT_STATE.md   # Current project state (MUST READ before work)
│   └── LITERATURE_MAP.md  # Literature references [LIT-XXXX] for physics models
├── src/
│   ├── core/              # Reusable core physics modules
│   │   ├── full_stack_microcavity.py
│   │   ├── phase07_dual_window.py
│   │   └── hdr_absolute_calibration.py
│   └── scripts/           # Executable pipeline scripts (stepXX_*.py)
├── data/
│   ├── raw/                 # Original experimental data (READ-ONLY)
│   └── processed/           # Intermediate data products
├── resources/               # Physical constants, n-k databases
│   ├── aligned_full_stack_nk.csv
│   ├── materials_master_db.json
│   └── n-kdata/             # Material optical constants
├── results/
│   ├── figures/             # Generated plots
│   └── logs/                # Execution logs
└── test_data/               # Test fixtures
```

## Common Commands

### Environment Setup
```bash
# Create virtual environment (already exists at .venv)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Scripts

**Phase 01 - Absolute Reflectance Calibration (Standard):**
```bash
python src/scripts/step01_absolute_calibration.py
```

**Phase 06 - HDR Calibration:**
```bash
# Single sample HDR dry run
python src/scripts/step06_single_sample_hdr_absolute_calibration.py

# Batch HDR calibration
python src/scripts/step06_batch_hdr_calibration.py
```

**Phase 07 - Dual-Window Inversion:**
```bash
python src/scripts/step07_dual_window_inversion.py
```

**Other Key Scripts:**
```bash
# Build aligned n-k stack
python src/scripts/step05c_build_aligned_nk_stack.py

# Run full microcavity sandbox
python src/scripts/step06_dual_mode_microcavity_sandbox.py
```

## Key Architecture Patterns

### 1. Script I/O Contracts
Every script in `src/scripts/` must define clear inputs/outputs:
- **Input**: Explicit file paths (no hardcoded temp paths)
- **Output**: Written to `data/processed/` or `results/`
- **Phase naming**: Output files should include phase (e.g., `phase07_fit_result.csv`)

### 2. Core Module Design
Reusable physics goes in `src/core/`:
- `full_stack_microcavity.py`: TMM forward models for microcavity stacks
- `phase07_dual_window.py`: Dual-window inversion with DE + LM optimization
- `hdr_absolute_calibration.py`: HDR spectral fusion from .spe files

### 3. Literature-First Development
All physics implementations must cite literature:
- Check `docs/LITERATURE_MAP.md` before implementing new models
- Reference format: `[LIT-0001]` in code comments
- Current primary reference: Khan et al. (2024) for perovskite optical constants

### 4. Phase-Based Development
Work is organized in numbered Phases:
- Phase 01: Absolute reflectance calibration
- Phase 02: TMM forward simulation
- Phase 03: LM inversion
- Phase 04: Air gap diagnostics
- Phase 06: HDR pipeline + full microcavity
- Phase 07: Dual-window joint inversion (current)

Git commits must use format: `[Phase XX] Chinese description`

## Critical Physics Constants

From `src/core/full_stack_microcavity.py` and `phase07_dual_window.py`:

```python
# Standard layer thicknesses (nm)
ITO_THICKNESS_NM = 100.0
NIOX_THICKNESS_NM = 45.0
SAM_THICKNESS_NM = 5.0
C60_THICKNESS_NM = 15.0
AG_THICKNESS_NM = 100.0
PVK_THICKNESS_NM = 700.0  # Variable in fitting

# Wavelength windows
FRONT_WINDOW_NM = (500.0, 650.0)    # Interference fringes
REAR_WINDOW_NM = (860.0, 1055.0)    # Absorption tail
MASKED_WINDOW_NM = (650.0, 860.0) # Excluded (PVK absorption)

# Material indices
SAM_NK = 1.5 + 0.0j
AIR_INDEX = 1.0 + 0.0j
```

## Dependencies

Key packages (from `requirements.txt`):
- `numpy`, `pandas`, `scipy`: Core numerical computing
- `matplotlib`: Plotting
- `lmfit`: Levenberg-Marquardt optimization
- `tmm`: Transfer Matrix Method (pip package, not to be confused with local code)
- `beautifulsoup4`, `PyMuPDF`: PDF parsing for literature processing

## File Naming Conventions

- Scripts: `step{NN}_{descriptive_name}.py`
- Core modules: `{phase}_{functionality}.py`
- Output figures: `phase{NN}_{description}.png`
- Output data: `phase{NN}_{description}.csv`

## Important Notes for Claude

1. **ALWAYS read `docs/PROJECT_STATE.md` before starting work** - it contains the current project state and what needs to be done next.

2. **ALWAYS read `AGENTS.md` first** - it contains mandatory project standards that override generic best practices.

3. **Use Phase-based git commits**: `[Phase XX] 中文描述`

4. **Never place files in root directory** - use appropriate subdirectories per AGENTS.md section 2.1

5. **Literature-first development**: Check `docs/LITERATURE_MAP.md` before implementing physics models

6. **Maintain `docs/PROJECT_STATE.md`** - Update it when completing significant work
