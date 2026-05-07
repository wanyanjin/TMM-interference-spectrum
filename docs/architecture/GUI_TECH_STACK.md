# GUI Tech Stack

## 1. Standard Stack

The default GUI stack for new formal tools is:

```text
PySide6 + pyqtgraph
```

## 2. Role Split

### `PySide6`

Used for:

- windows
- widgets
- layouts
- menus
- file dialogs
- status bars
- action wiring

### `pyqtgraph`

Used for:

- spectrum curves
- multi-curve overlays
- zooming
- panning
- point inspection
- fast refresh

### `matplotlib`

- Primarily for report and publication style static figures.
- Not the default live plotting backend for on-site GUI interaction.

## 3. GUI Boundary Rules

GUI must not implement:

- TMM, Fresnel, or EMA formulas
- fitting objective functions
- core data cleaning logic
- complex export logic

GUI must:

- call workflows
- translate domain results into view state
- keep PySide6 and pyqtgraph usage inside `src/gui/` or GUI-only adapters

## 4. Import Boundary

- `PySide6` and `pyqtgraph` are only allowed in `src/gui/` or GUI-specific adapters.
- They must not be imported by `src/core/`, `src/domain/`, or `src/workflows/` in this architecture.

## 5. Future Tool Pattern

Recommended path for a GUI tool:

```text
GUI event
  -> workflow call
  -> storage adapters + core logic
  -> domain result
  -> GUI view model
  -> PySide6 widgets + pyqtgraph plots
```
