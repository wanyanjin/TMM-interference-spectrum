# Output Conventions

## 1. Purpose

This document defines the recommended output contract for formal tools.

## 2. Standard Outputs

Each formal tool run should produce, when applicable:

- processed data
- `summary.json`
- `manifest.json`
- `report.md`
- `figure.png` or `figures/`

## 3. Recommended Directories

```text
data/processed/<phase>/<tool_name>/<run_id>/
results/figures/<phase>/<tool_name>/<run_id>/
results/logs/<phase>/<tool_name>/<run_id>/
results/report/<phase>_<tool_name>/<run_id>/
```

## 4. Run ID Convention

Recommended `run_id`:

```text
YYYYMMDD_HHMMSS_<tool_name>_<optional_tag>
```

The optional tag may hold a short branch, sample, or scenario label when needed.

## 5. Manifest Minimum Fields

`manifest.json` should record at least:

- input paths
- input metadata
- parameters
- thresholds
- software commit if available
- output paths
- warnings
- unit conversions
- interpolation flags
- cropping flags
- smoothing flags

## 6. Traceability Rules

- A formal tool should emit machine-readable and human-readable outputs together.
- Output locations should remain stable enough for later GUI, CLI, and reporting reuse.
- Automatic transformations that can change interpretation must be disclosed in manifest or summary files.
