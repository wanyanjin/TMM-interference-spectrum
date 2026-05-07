# Core Sandbox Rules

## 1. Scope

This document defines the sandbox boundary for new code under `src/core/`.

The goal is to make `core` reusable from CLI, GUI, notebooks, tests, and future services without coupling it to file formats or UI frameworks.

## 2. Allowed Dependencies

New `src/core/` modules may depend on:

- `numpy`
- `scipy`
- `dataclasses`
- `typing`
- `math`
- `tmm`
- `lmfit`

## 3. Forbidden Dependencies

New `src/core/` modules must not depend on:

- `pandas`
- `h5py`
- `zarr`
- `PySide6`
- `pyqtgraph`
- `matplotlib`
- `argparse`
- `json`
- `yaml`
- `toml`
- direct file path I/O
- GUI state
- CLI argument objects

## 4. Behavioral Rules

`core` must not:

- read files
- write files
- draw figures
- show dialogs
- parse command-line arguments
- decide file format from suffix
- branch on `.csv`, `.h5`, `.txt`, `.zarr`, or similar

`core` must:

- accept domain models or `ndarray` inputs
- return domain results or `ndarray` outputs
- keep physics and numerical logic explicit and testable

## 5. Boundary Contract

Formal responsibility split:

- `storage`: file formats, adapters, serialization
- `workflows`: orchestration, adapter selection, output organization
- `gui`: interaction, rendering, action triggering
- `cli`: argument parsing and execution entry
- `core`: algorithms and physics

## 6. Legacy Note

Some existing historical modules under `src/core/` may not fully satisfy this sandbox rule set yet.

Policy:

- new code must comply immediately
- legacy code migrates gradually
- this phase does not force a large-scale refactor of old modules
