# IO Adapter Guide

## 1. Purpose

This document defines how external file formats enter the system.

The core principle is that file formats live only in the storage adapter layer.

## 2. Recommended Concepts

- `DataSource`
- `SpectrumReader` protocol
- `SpectrumReaderRegistry`
- `CSVReader`
- `TXTReader`
- `H5Reader`
- `ZarrReader`
- `LightFieldCSVReader`

## 3. Rules

- File-format logic belongs in `src/storage/readers/`.
- `workflow` code must not scatter `if csv / if h5 / if txt`.
- `core` must remain completely unaware of file formats.
- Adding a new file format should require a new reader adapter, not changes to `core`.

## 4. Suggested Flow

```text
external file
  -> DataSource
  -> SpectrumReaderRegistry
  -> concrete reader adapter
  -> domain model
  -> workflow
  -> core
```

## 5. Pseudocode Example

```python
source = DataSource(path=input_path, format_hint=None)
reader = registry.read(source)
result = workflow.run(reader)
```

More explicitly:

```python
registry = SpectrumReaderRegistry()
registry.register(CSVReader())
registry.register(H5Reader())

spectrum = registry.read(DataSource(path=path))
workflow_result = run_workflow(spectrum)
```

## 6. Adapter Responsibilities

Reader adapters may:

- inspect file suffixes
- inspect headers
- parse file metadata
- normalize columns
- convert units before building domain models

Reader adapters must also record important automatic behavior, such as:

- detected format
- unit conversion
- interpolation
- cropping
- smoothing or denoising if any

These records should appear in a manifest or summary when the behavior affects scientific interpretation.
