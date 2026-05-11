# MATERIAL_DATABASE_GUIDE

Canonical material database root is `resources/materials/`.

This guide is complemented by:
- `docs/architecture/OPTICAL_CONSTANTS_STORAGE_GUIDE.md` (lifecycle, storage governance, import contracts)

Key distinction:
- `resources/materials/curves/`: standardized callable material curves.
- `resources/materials/derived/`: derived caches (including aligned tables), not raw truth sources.

Thickness naming rules:
- source ellipsometry sample thickness: `source_sample_thickness_nm`
- device layer thickness in stack context: `thickness_nm` (or explicit `layer_thickness_nm` in metadata)
