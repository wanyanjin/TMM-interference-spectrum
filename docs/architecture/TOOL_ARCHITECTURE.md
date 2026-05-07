# Tool Architecture

## 1. Purpose

This document defines the long-term structure for formal tools in `TMM-interference-spectrum`.

The target flow is:

```text
GUI / CLI
  -> workflows
  -> core + storage + visualization
  -> data/processed + results/*
```

This architecture is intended to reduce technical debt while keeping physics logic, file adapters, and presentation layers separated.

## 2. Layer Responsibilities

### `src/domain/`

- Unified domain data models.
- Carries typed concepts such as axes, spectra, QC summaries, and run manifests.
- Must not read files, write files, parse CLI flags, or hold GUI state.

### `src/core/`

- Pure computation, pure algorithms, and pure physics logic.
- Owns TMM, Fresnel, EMA, residual definitions, optimization math, and reusable numerical transforms.
- Must stay sandboxed from storage format details and GUI dependencies.

### `src/storage/`

- Input and output adapter layer.
- Owns file format detection, readers, writers, and serialization details.
- Converts external files into domain models and converts domain results into persisted artifacts.

### `src/workflows/`

- Orchestration layer shared by GUI and CLI.
- Validates workflow-level inputs, selects adapters, calls core modules, and organizes outputs.
- Must not duplicate physics formulas from `src/core/`.

### `src/cli/`

- Command-line entry points.
- Parses arguments, calls workflows, and exposes stable formal tool interfaces.
- Must not become a replacement for reusable business logic.

### `src/gui/`

- GUI entry points and tool-specific view code.
- Owns widgets, user interactions, view models, and action dispatch.
- Must call workflows instead of directly implementing core science logic.

### `src/visualization/`

- Reusable plotting and rendering helpers.
- Supports report generation and future GUI adapters without embedding business logic into plots.

### `src/common/`

- Shared exceptions, registries, unit constants, path helpers, and other small infrastructure pieces.
- Keeps lightweight reusable primitives out of `core` and `storage`.

### `src/scripts/`

- Historical scripts, experimental scripts, and thin ad hoc entry points.
- Can remain in place for legacy and exploratory work.
- New formal tools must not be piled directly into this directory.

## 3. Rules for Formal Tools

- New formal tools must not be implemented directly in `src/scripts/`.
- `src/scripts/` may continue to host historical or experimental scripts.
- High-frequency, reusable, or future GUI-facing functionality must use the formal tool structure.
- Legacy scripts are not migrated in this phase unless a separate task explicitly requests it.

## 4. Recommended Formal Tool Layout

```text
src/domain/<tool_related_models>.py
src/core/<tool_name>.py
src/storage/readers/...
src/storage/writers/...
src/workflows/<tool_name>_workflow.py
src/cli/<tool_name>.py
src/gui/<tool_name>/...
tests/unit/test_<tool_name>_core.py
tests/integration/test_<tool_name>_workflow.py
docs/cli/<tool_name>.md
docs/gui/<tool_name>_gui.md
docs/tools/<tool_name>.md
```

## 5. Migration Guidance

- New code must follow this architecture.
- Existing script-heavy flows remain valid historical facts and are not restructured in this task.
- Old modules can be migrated gradually when a concrete tool is formalized.
