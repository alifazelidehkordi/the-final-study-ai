#!/usr/bin/env python3
"""Export STUDY_INDEX.md (or structured part data) to a printable PDF."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN = 36
ROWS_PER_PAGE = 28

CSS = """
body {
  font-family: sans-serif;
  font-size: 9.5pt;
  line-height: 1.35;
  direction: rtl;
  text-align: right;
}
h1 { font-size: 16pt; margin: 0 0 8pt 0; }
h2 { font-size: 12pt; margin: 14pt 0 6pt 0; color: #1a365d; }
p, li { margin: 3pt 0; }
table {
  width: 100%;
  border-collapse: collapse;
  margin: 6pt 0 10pt 0;
  font-size: 8.5pt;
}
th, td {
  border: 1px solid #cbd5e0;
  padding: 4pt 5pt;
  vertical-align: top;
}
th { background: #edf2f7; font-weight: 600; }
.meta { color: #4a5568; font-size: 9pt; }
"""


def parse_index_tables(index_md: str) -> tuple[str, list[tuple[str, list[list[str]]]]]:
    """Parse STUDY_INDEX.md into a title and section tables."""
    lines = index_md.splitlines()
    title = "فهرست پارت‌های مطالعاتی"
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()

    sections: list[tuple[str, list[list[str]]]] = []
    current_title = ""
    current_rows: list[list[str]] = []
    in_table = False

    for line in lines:
        if line.startswith("## "):
            if current_title and current_rows:
                sections.append((current_title, current_rows))
            current_title = line[3:].strip()
            current_rows = []
            in_table = False
            continue
        if not line.startswith("|"):
            if in_table and current_title and current_rows:
                sections.append((current_title, current_rows))
                current_title = ""
                current_rows = []
            in_table = False
            continue
        if line.startswith("|---"):
            in_table = True
            continue
        if not in_table:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        current_rows.append(cells)

    if current_title and current_rows:
        sections.append((current_title, current_rows))
    return title, sections


def chunk_rows(rows: list[list[str]], size: int) -> list[list[list[str]]]:
    if not rows:
        return []
    header, *body = rows
    chunks: list[list[list[str]]] = []
    for start in range(0, len(body), size):
        chunks.append([header, *body[start : start + size]])
    return chunks


def render_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header, *body = rows
    head_html = "".join(f"<th>{html.escape(cell)}</th>" for cell in header)
    body_html = ""
    for row in body:
        body_html += "<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>"
    return f"<table><thead><tr>{head_html}</tr></thead><tbody>{body_html}</tbody></table>"


def extract_intro(index_md: str) -> str:
    lines = index_md.splitlines()
    intro: list[str] = []
    for line in lines[1:]:
        if line.startswith("## "):
            break
        if line.startswith("|"):
            break
        if line.strip() in {"---", ""}:
            intro.append("<br>")
            continue
        if line.startswith("- "):
            intro.append(f"<li>{html.escape(line[2:])}</li>")
            continue
        if line.startswith(">"):
            intro.append(f"<p><em>{html.escape(line.lstrip('> '))}</em></p>")
            continue
        intro.append(f"<p>{html.escape(line)}</p>")
    if any(item.startswith("<li>") for item in intro):
        items = [item for item in intro if item.startswith("<li>")]
        return "<ul>" + "".join(items) + "</ul>"
    return "".join(intro)


def export_index_pdf(index_md_path: Path, output_pdf_path: Path) -> None:
    try:
        import fitz
    except ImportError as exc:
        raise SystemExit(
            "PyMuPDF is required. Use the pdf-to-markdown venv python or install pymupdf."
        ) from exc

    index_text = index_md_path.read_text(encoding="utf-8")
    title, sections = parse_index_tables(index_text)
    intro_html = extract_intro(index_text)

    doc = fitz.open()
    content_rect = fitz.Rect(MARGIN, MARGIN, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN)

    def add_page(html_body: str) -> None:
        page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        page.insert_htmlbox(content_rect, f"<style>{CSS}</style><body>{html_body}</body>")

    add_page(f"<h1>{html.escape(title)}</h1>{intro_html}")

    for section_title, rows in sections:
        for chunk in chunk_rows(rows, ROWS_PER_PAGE):
            add_page(f"<h2>{html.escape(section_title)}</h2>{render_table(chunk)}")

    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_pdf_path)
    doc.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export STUDY_INDEX.md to STUDY_INDEX.pdf")
    parser.add_argument("--index-md", type=Path, required=True, help="Path to STUDY_INDEX.md")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output PDF path (default: beside index as STUDY_INDEX.pdf)",
    )
    args = parser.parse_args()
    if not args.index_md.exists():
        raise SystemExit(f"Index not found: {args.index_md}")

    output = args.output or args.index_md.with_suffix(".pdf")
    export_index_pdf(args.index_md.resolve(), output.resolve())
    print(f"PDF index: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
