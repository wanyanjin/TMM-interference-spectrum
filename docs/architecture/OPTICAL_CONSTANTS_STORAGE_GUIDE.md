# OPTICAL_CONSTANTS_STORAGE_GUIDE

## Scope
This guide defines lifecycle governance for optical constants (`n/k`) files.

## Lifecycle
`inbox -> raw_sources -> curves -> registry -> derived`

Failed or ambiguous inputs must go to `quarantine` and cannot be indexed.

## Directory Roles
- `resources/materials/inbox/manual_imports/`: user-dropped temporary files.
- `resources/materials/inbox/codex_collected/`: agent-collected temporary files.
- `resources/materials/raw_sources/*`: immutable raw evidence archive.
- `resources/materials/curves/*`: standardized program-callable curves only.
- `resources/materials/quarantine/*`: invalid/ambiguous failed imports.
- `resources/materials/manifests/imports/`: machine-readable import records.

## Curve CSV Schema
All files under `curves/<family>/` must be:
`wavelength_nm,n,k,region,quality_flag`

Allowed `region` values:
- measured
- digitized
- interpolated
- extrapolated
- stitched
- converted_from_epsilon
- constant
- aligned_derived

Allowed `quality_flag` values:
- high_confidence
- medium_confidence
- low_confidence
- review_required

## Meta JSON Minimum Schema
```json
{
  "schema_version": "1.0",
  "material_id": "pvk__csfapi__example_source__v1",
  "material_family": "pvk",
  "display_name": "Example PVK optical constants",
  "composition": "CsFAPI",
  "source_type": "literature_digitized",
  "source_reference": "unknown",
  "source_path": "resources/materials/raw_sources/literature/example_original.csv",
  "standard_curve_path": "resources/materials/curves/pvk/pvk__csfapi__example_source__v1.csv",
  "input_columns": ["wavelength", "n", "k"],
  "input_wavelength_unit": "nm",
  "output_wavelength_unit": "nm",
  "optical_quantity_input": "n_k",
  "conversion_applied": [],
  "wavelength_range_nm": {"min": 400, "max": 1100},
  "measured_range_nm": {"min": 400, "max": 1100},
  "has_interpolation": false,
  "has_extrapolation": false,
  "confidence_level": "B",
  "recommended_use": ["forward_simulation", "qualitative_comparison"],
  "not_recommended_use": ["final_quantitative_fitting_without_validation"],
  "notes": "Imported and standardized by future material import workflow.",
  "status": "experimental",
  "version": "v1",
  "created_at": "YYYY-MM-DD",
  "created_by": "material_import_skill"
}
```

## Material ID Convention
`<family>__<composition_or_variant>__<source_or_method>__v<version>`

## Unit Rules
- Default wavelength unit is `nm` only when not contradictory.
- Suspicious ranges must warn or quarantine.
- `um -> nm`: `wavelength_nm = wavelength_um * 1000`
- `eV -> nm`: `wavelength_nm = 1239.841984 / energy_eV`
- After eV conversion, sort by ascending `wavelength_nm`.

## epsilon to n/k
`epsilon = (n + i k)^2 = epsilon1 + i epsilon2`

`n = sqrt((sqrt(epsilon1^2 + epsilon2^2) + epsilon1) / 2)`

`k = sqrt((sqrt(epsilon1^2 + epsilon2^2) - epsilon1) / 2)`

Record:
- `optical_quantity_input = epsilon1_epsilon2`
- `conversion_applied = ["epsilon_to_nk"]`

## Codex Collection Rule
Any web-collected source must first go to:
`resources/materials/inbox/codex_collected/<task_id>/`
with `original_source.*`, `source_notes.md`, `download_manifest.json`.

## Import Skill Contract (Planned)
1. scan inbox
2. detect format
3. read table
4. detect columns
5. detect wavelength unit
6. detect quantity type
7. apply unit conversion if needed
8. apply epsilon->n/k if needed
9. sort/dedupe/clean
10. run QC
11. archive raw source
12. write standard curve
13. write meta
14. update index
15. write import manifest
16. write human report
17. on failure move to quarantine with reason
