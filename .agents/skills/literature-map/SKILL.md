---
name: literature-map
description: Scan `reference/` or `resources/references/` for unindexed literature, extract implementable optical-model facts from MinerU markdown, and update `docs/LITERATURE_MAP.md` with structured entries before physics-heavy coding.
---

# Literature Map

Use this skill when the task involves:

- building or changing physics-heavy code,
- adding new papers to the project knowledge base,
- checking whether a parameter source is documented,
- updating `docs/LITERATURE_MAP.md`.

## Workflow

1. Run the scanner first:

```bash
python3 .agents/skills/literature-map/scripts/update_literature_map.py
```

2. Read the TODO list. Each pending folder is a literature source that is present in `reference/` or `resources/references/` but not yet indexed in `docs/LITERATURE_MAP.md`.

3. For each pending folder, open `full.md` first. Do not read the entire paper blindly. Use targeted search terms to find implementable physics content:

- `Tauc`
- `Lorentz`
- `Cauchy`
- `Sellmeier`
- `Drude`
- `oscillator`
- `Eg`
- `bandgap`
- `refractive index`
- `extinction coefficient`
- `dielectric`
- `epsilon`
- `n`
- `k`

Recommended search pattern:

```bash
rg -n "Tauc|Lorentz|Cauchy|Sellmeier|Drude|oscillator|Eg|bandgap|refractive|extinction|dielectric|epsilon" reference/*/full.md
```

4. Extract only facts that are directly useful for implementation. Ignore broad background prose. Prioritize:

- optical dispersion model family,
- explicit formulas,
- oscillator tables,
- bandgap values,
- `n/k` or dielectric relations,
- measurement spectral window,
- layer stack assumptions,
- parameter units,
- caveats that matter for coding.

5. Append or update a standardized entry in `docs/LITERATURE_MAP.md`. Every entry must include:

- literature ID like `[LIT-0001]`,
- title,
- applicability tags,
- one or more `Source Dir` lines,
- key formulas and parameters,
- implementation notes,
- risks or ambiguity notes.

6. When a paper exists in multiple MinerU output folders for the same source PDF, prefer one literature entry with multiple `Source Dir` lines instead of duplicating the scientific content.

7. Re-run the scanner after updating the map. The task is only complete when pending count is zero for the folders you just handled.

## Rules

- `docs/LITERATURE_MAP.md` is the project memory layer; keep it concise, structured, and implementation-oriented.
- Never invent optical constants, bandgaps, units, or model forms that are not supported by the source.
- If MinerU parsing is obviously broken, note that in the entry and fall back to the PDF path for manual verification.
- If formulas are too noisy to trust from Markdown alone, summarize the usable parts and mark the exact field as `needs PDF verification`.
- If the project code already uses a parameter set from the paper, record that mapping explicitly under `Code Links` or `Implementation Notes`.
