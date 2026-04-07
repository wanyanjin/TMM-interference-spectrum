#!/usr/bin/env python3
"""Scan reference folders and report literature items not yet indexed in docs/LITERATURE_MAP.md.

This script is intentionally conservative:
- It only decides "indexed or not indexed" by source folder path, not by semantic similarity.
- It supports both the historical `reference/` layout and the target `resources/references/` layout.
- It does not edit the map automatically; it produces a deterministic TODO list for the skill/user.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ENTRY_ID_PATTERN = re.compile(r"^###\s+\[(LIT-\d{4})\]", re.MULTILINE)
SOURCE_DIR_PATTERN = re.compile(r"- Source Dir:\s+`([^`]+)`")
FOLDER_UUID_SUFFIX_PATTERN = re.compile(r"\.pdf-[0-9a-fA-F-]+$")


@dataclass
class LiteratureFolder:
    rel_dir: str
    title_guess: str
    full_md: str | None
    pdfs: list[str]
    has_content_index: bool
    duplicate_group: str
    suggested_id: str


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists() or (candidate / "AGENTS.md").exists():
            return candidate
    return start


def detect_reference_root(repo_root: Path, override: str | None) -> Path:
    if override:
        path = (repo_root / override).resolve() if not Path(override).is_absolute() else Path(override)
        return path

    candidates = [
        repo_root / "reference",
        repo_root / "resources" / "references",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def normalize_title_from_dir_name(name: str) -> str:
    title = FOLDER_UUID_SUFFIX_PATTERN.sub("", name)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def canonical_duplicate_key(title: str) -> str:
    normalized = title.lower()
    normalized = normalized.replace(".pdf", "")
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized


def discover_literature_dirs(reference_root: Path, repo_root: Path) -> list[tuple[Path, str]]:
    if not reference_root.exists():
        return []

    discovered: list[tuple[Path, str]] = []
    for child in sorted(reference_root.iterdir()):
        if not child.is_dir():
            continue
        has_full_md = (child / "full.md").exists()
        has_pdf = any(child.glob("*.pdf"))
        has_content_index = (child / "content_list_v2.json").exists()
        if has_full_md or has_pdf or has_content_index:
            rel_dir = child.relative_to(repo_root).as_posix()
            discovered.append((child, rel_dir))
    return discovered


def parse_existing_map(map_path: Path) -> tuple[set[str], list[str]]:
    if not map_path.exists():
        return set(), []
    text = map_path.read_text(encoding="utf-8")
    indexed_dirs = set(SOURCE_DIR_PATTERN.findall(text))
    entry_ids = ENTRY_ID_PATTERN.findall(text)
    return indexed_dirs, entry_ids


def next_entry_id(existing_ids: list[str], offset: int) -> str:
    if not existing_ids:
        return f"LIT-{offset + 1:04d}"
    max_id = max(int(item.split("-")[1]) for item in existing_ids)
    return f"LIT-{max_id + offset + 1:04d}"


def build_todo_items(reference_root: Path, map_path: Path, repo_root: Path) -> dict[str, object]:
    indexed_dirs, existing_ids = parse_existing_map(map_path)
    discovered = discover_literature_dirs(reference_root, repo_root)

    duplicate_groups: dict[str, list[str]] = {}
    for folder_path, rel_dir in discovered:
        title_guess = normalize_title_from_dir_name(folder_path.name)
        key = canonical_duplicate_key(title_guess)
        duplicate_groups.setdefault(key, []).append(rel_dir)

    pending: list[LiteratureFolder] = []
    indexed_count = 0

    for folder_path, rel_dir in discovered:
        if rel_dir in indexed_dirs:
            indexed_count += 1
            continue

        title_guess = normalize_title_from_dir_name(folder_path.name)
        duplicate_key = canonical_duplicate_key(title_guess)
        full_md = (folder_path / "full.md")
        pdfs = sorted(path.relative_to(repo_root).as_posix() for path in folder_path.glob("*.pdf"))
        pending.append(
            LiteratureFolder(
                rel_dir=rel_dir,
                title_guess=title_guess,
                full_md=full_md.relative_to(repo_root).as_posix() if full_md.exists() else None,
                pdfs=pdfs,
                has_content_index=(folder_path / "content_list_v2.json").exists(),
                duplicate_group=duplicate_key if len(duplicate_groups[duplicate_key]) > 1 else "",
                suggested_id=next_entry_id(existing_ids, len(pending)),
            )
        )

    return {
        "repo_root": repo_root.as_posix(),
        "reference_root": reference_root.relative_to(repo_root).as_posix() if reference_root.exists() else reference_root.as_posix(),
        "map_path": map_path.relative_to(repo_root).as_posix(),
        "indexed_folder_count": indexed_count,
        "pending_folder_count": len(pending),
        "pending": [asdict(item) for item in pending],
    }


def render_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Literature Map Scan",
        "",
        f"- Reference Root: `{summary['reference_root']}`",
        f"- Map Path: `{summary['map_path']}`",
        f"- Indexed Folders: {summary['indexed_folder_count']}",
        f"- Pending Folders: {summary['pending_folder_count']}",
        "",
    ]

    pending = summary["pending"]
    if not pending:
        lines.append("No unindexed literature folders found.")
        return "\n".join(lines)

    lines.extend(
        [
            "## TODO",
            "",
        ]
    )

    for item in pending:
        lines.append(f"### {item['suggested_id']} :: {item['title_guess']}")
        lines.append(f"- Source Dir: `{item['rel_dir']}`")
        if item["full_md"]:
            lines.append(f"- full.md: `{item['full_md']}`")
        if item["pdfs"]:
            for pdf in item["pdfs"]:
                lines.append(f"- pdf: `{pdf}`")
        lines.append(f"- content_list_v2.json: {'yes' if item['has_content_index'] else 'no'}")
        if item["duplicate_group"]:
            lines.append(f"- duplicate_group: `{item['duplicate_group']}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", help="Reference root, relative to repo root or absolute path.")
    parser.add_argument(
        "--map-path",
        default="docs/LITERATURE_MAP.md",
        help="Literature map path, relative to repo root or absolute path.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format for the TODO summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(Path.cwd().resolve())
    reference_root = detect_reference_root(repo_root, args.reference_dir)
    map_path = (repo_root / args.map_path).resolve() if not Path(args.map_path).is_absolute() else Path(args.map_path)

    summary = build_todo_items(reference_root, map_path, repo_root)

    if args.format == "json":
        json.dump(summary, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(summary))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
