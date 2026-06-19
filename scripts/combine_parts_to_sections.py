#!/usr/bin/env python3
"""Combine study part markdown files into one ##-section file for run_md_to_xmind.sh."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

HEADING_RE = re.compile(r"^#{1,3}\s+(.+?)\s*$")


def clean_title(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^[*_❖⮚•`🡺]+|[*_❖⮚•`🡺]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def demote_markdown_headings(lines: list[str]) -> list[str]:
    demoted: list[str] = []
    for line in lines:
        if line.startswith("### "):
            demoted.append("#" + line)
        elif line.startswith("## "):
            demoted.append("###" + line[2:])
        elif line.startswith("# "):
            demoted.append("##" + line[1:])
        else:
            demoted.append(line)
    return demoted


def part_title_and_body(text: str, fallback: str) -> tuple[str, str]:
    lines = text.splitlines()
    title = fallback
    body_start = 0

    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        title = clean_title(match.group(1)) or fallback
        body_start = index + 1
        break

    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1

    body_lines = demote_markdown_headings(lines[body_start:])
    body = "\n".join(body_lines).strip()
    return title, body


def combine_parts(parts_dir: Path, output_file: Path) -> int:
    part_files = sorted(path for path in parts_dir.glob("*.md") if path.is_file())
    if not part_files:
        raise SystemExit(f"No .md files found in {parts_dir}")

    sections: list[str] = []
    for part_file in part_files:
        text = part_file.read_text(encoding="utf-8")
        title, body = part_title_and_body(text, part_file.stem)
        section = f"## {title}"
        if body:
            section = f"{section}\n\n{body}"
        sections.append(section.rstrip())

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n\n".join(sections).rstrip() + "\n", encoding="utf-8")
    return len(part_files)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Combine study parts into one markdown file with ## sections")
    parser.add_argument("--parts-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.parts_dir.is_dir():
        raise SystemExit(f"Parts directory not found: {args.parts_dir}")

    count = combine_parts(args.parts_dir.resolve(), args.output.resolve())
    print(f"Combined {count} parts -> {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
