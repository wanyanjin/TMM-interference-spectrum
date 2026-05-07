# Data Model Guide

## 1. Purpose

This document defines naming and modeling conventions for cross-module domain data.

The goal is to keep `core`, `storage`, `workflows`, `cli`, and `gui` aligned on explicit field names and unit semantics.

## 2. Core Model Concepts

### `Axis`

- Represents a sampled axis, typically wavelength.
- Typical fields:
  - `values`
  - `unit`
  - `name`

### `SpectrumData`

- Represents one spectrum and its metadata.
- Typical fields:
  - `wavelength_nm`
  - `intensity`
  - `label`
  - `exposure_ms`
  - `metadata`

### `SpectrumSet`

- Represents a grouped collection of spectra sharing context.
- Typical fields may include:
  - `spectra`
  - `source_name`
  - `shared_metadata`

### `ReferenceReflectance`

- Represents a reference spectrum used for calibration or comparison.
- Typical fields may include:
  - `wavelength_nm`
  - `reflectance`
  - `reference_type`
  - `metadata`

### `ReflectanceResult`

- Represents a calibrated or modeled reflectance output.
- Typical fields may include:
  - `wavelength_nm`
  - `reflectance`
  - `label`
  - `metadata`

### `QCFlag`

- Represents one QC issue or notice.
- Typical fields:
  - `name`
  - `severity`
  - `message`

### `QCSummary`

- Represents tool-level QC status and metrics.
- Typical fields:
  - `overall_status`
  - `metrics`
  - `flags`
  - `metadata`

### `ToolRunManifest`

- Represents run-level traceability.
- Typical fields:
  - `tool_name`
  - `run_id`
  - `parameters`
  - `inputs`
  - `outputs`
  - `warnings`

## 3. Field Naming Rules

- Wavelength must be named `wavelength_nm`.
- Exposure time must be named `exposure_ms`.
- Thickness must be named `thickness_nm`.
- Angle must be named `angle_deg` or `angle_rad`.
- Reflectance in `0-1` form must be named `reflectance`.
- Reflectance in percent form must be named `reflectance_percent`.
- Avoid generic cross-module field names such as `x`, `y`, `data`, or `value`.

## 4. Unit Handling Rules

- Units must be explicit in field names when the quantity is exchanged across module boundaries.
- Do not rely on implicit unit guessing at `core` boundaries.
- If automatic unit detection or conversion occurs, it must be recorded in a manifest or summary.

## 5. Design Rules

- Domain models may depend on `numpy`.
- Domain models must not depend on `pandas`.
- Domain models must not depend on `Path`.
- Domain models must not depend on GUI frameworks.
- Domain models must not read or write files.
