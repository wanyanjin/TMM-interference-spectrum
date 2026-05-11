from pathlib import Path


def test_material_storage_layout_and_constitutions() -> None:
    root = Path(__file__).resolve().parents[2]
    required = [
        root / 'resources/materials/inbox/manual_imports',
        root / 'resources/materials/inbox/codex_collected',
        root / 'resources/materials/raw_sources/literature',
        root / 'resources/materials/raw_sources/vendor',
        root / 'resources/materials/raw_sources/ellipsometry',
        root / 'resources/materials/raw_sources/user_uploaded',
        root / 'resources/materials/quarantine/unit_ambiguous',
        root / 'resources/materials/quarantine/schema_unrecognized',
        root / 'resources/materials/quarantine/failed_qc',
        root / 'resources/materials/manifests/imports',
        root / 'docs/architecture/OPTICAL_CONSTANTS_STORAGE_GUIDE.md',
        root / 'AGENTS.md',
        root / 'GEMINI.md',
        root / 'resources/aligned_full_stack_nk.csv',
    ]
    for p in required:
        assert p.exists(), f'missing: {p}'

    agents = (root / 'AGENTS.md').read_text(encoding='utf-8')
    gemini = (root / 'GEMINI.md').read_text(encoding='utf-8')
    for t in [agents, gemini]:
        assert 'AGENTS.md / GEMINI.md ????' in t
        assert '??????????' in t
