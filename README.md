# The Final Study AI

**Topic-first PDF study pipeline** — from raw PDF to topic-based study parts, a bilingual index with page ranges, and editable XMind mind maps.

> **Languages:** English (this page) · [فارسی — README.fa.md](README.fa.md)

[![Release](https://img.shields.io/github/v/release/alifazelidehkordi/the-final-study-ai)](https://github.com/alifazelidehkordi/the-final-study-ai/releases/tag/v0.1.0)
[![Test report](https://img.shields.io/badge/tested-v0.1.0-brightgreen)](docs/TEST_v0.1.0.md)

```
PDF
  → Markdown (high-fidelity)
  → study parts by TOPIC + bilingual STUDY_INDEX (md + pdf)
  → [user review]
  → OPML → XMind (ChatGPT automation)
```

**Version:** v0.1.0 · **Test report:** [`docs/TEST_v0.1.0.md`](docs/TEST_v0.1.0.md)

---

## Why this project?

Most tools either chop PDFs without respecting topic structure, or skip the index and page-range metadata you need for serious study sessions. This pipeline is built around a different rule:

**Split by topic, record where each topic lives in the PDF.**

| What it does | Why it matters |
|---|---|
| **Topic-first splitting** | One file = one topic — not an arbitrary page count |
| **Page ranges in the index** | Every part shows `pp. X–Y` for its coverage in the source PDF |
| **Bilingual index (FA + EN)** | Persian and English tables plus a combined Quick Reference |
| **Printable index PDF** | `STUDY_INDEX.pdf` for offline planning |
| **Segmentation review** | You approve (or adjust granularity) before mind maps run |
| **XMind output** | Integrates with the tested [`chatgpt-mindmap-to-xmind`](https://github.com/alifazelidehkordi/chatgpt-mindmap-to-xmind) project |

> The “5–10 pages per session” guideline in the index is **orientation only** — not a split rule. A two-page topic stays one part; a long topic may span many pages.

---

## Quick start

```bash
git clone https://github.com/alifazelidehkordi/the-final-study-ai.git
cd the-final-study-ai
chmod +x scripts/*.sh scripts/*.py

# Full pipeline (stops after segmentation for your review)
./scripts/run_pipeline.sh "/absolute/path/to/book.pdf" --overwrite
```

After reviewing `SEGMENTATION_PREVIEW.md` and `STUDY_INDEX.md`:

```bash
./scripts/run_pipeline.sh "/absolute/path/to/book.pdf" \
  --skip-convert --approve-segment --overwrite
```

**Index only (no browser / no mind maps):**

```bash
./scripts/run_pipeline.sh "/absolute/path/to/book.pdf" \
  --skip-convert --skip-mindmap --overwrite
```

---

## Architecture

```
the-final-study-ai/
├── scripts/
│   ├── run_pipeline.sh                 # 3-step orchestrator
│   ├── run_pipeline.py                 # canonical cross-platform orchestrator
│   ├── segment_markdown_study_parts.py # topic split + bilingual index
│   ├── export_study_index_pdf.py       # STUDY_INDEX.md → PDF
│   └── combine_parts_to_sections.py    # optional: merge parts into one file
├── docs/
│   └── TEST_v0.1.0.md                  # test report
└── logs/                               # local debug logs (gitignored)
```

### External dependencies

| Component | Default path / repo | Role |
|-----------|---------------------|------|
| pdf-to-markdown | `~/.grok/skills/pdf-to-markdown` | PDF → Markdown via PyMuPDF4LLM |
| chatgpt-mindmap-to-xmind | `~/projects/chatgpt-mindmap-to-xmind` | OPML + XMind via ChatGPT browser automation |
| PyMuPDF venv | inside pdf-to-markdown | renders `STUDY_INDEX.pdf` |

---

## Installation

### 1. Clone this repo

```bash
git clone https://github.com/alifazelidehkordi/the-final-study-ai.git
cd the-final-study-ai
chmod +x scripts/*.sh scripts/*.py
```

### 2. Set up pdf-to-markdown

```bash
# If you use the Grok skill layout:
ls ~/.grok/skills/pdf-to-markdown/.venv/bin/python

# Or override paths:
export PDF_TO_MD_PY="/path/to/venv/bin/python"
export PDF_TO_MD_SCRIPT="/path/to/convert_pdf.py"
```

### 3. Set up chatgpt-mindmap-to-xmind (for Step 3)

```bash
git clone https://github.com/alifazelidehkordi/chatgpt-mindmap-to-xmind.git \
  ~/projects/chatgpt-mindmap-to-xmind
cd ~/projects/chatgpt-mindmap-to-xmind && ./setup.sh

# Log in to ChatGPT once inside chrome_profile/
```

---

## Pipeline steps

### Step 1 — PDF → Markdown

High-fidelity extraction with PyMuPDF4LLM. OCR is off by default (`--no-ocr`); use OCR only for scanned PDFs.

### Step 2 — Topic split + index

```bash
python3 scripts/segment_markdown_study_parts.py \
  --input book.md \
  --output-dir book_work \
  --source-pdf book.pdf \
  --granularity normal
```

Produces:
- `parts/` — one markdown file per topic
- `STUDY_INDEX.md` — bilingual index with PDF page ranges
- `STUDY_INDEX.pdf` — printable index
- `SEGMENTATION_PREVIEW.md` — summary for review

### Step 3 — Mind map → XMind

```bash
cd ~/projects/chatgpt-mindmap-to-xmind
INPUT_DIR=book_work/parts OPML_DIR=book_work/opml XMIND_DIR=book_work/xmind \
  ./run_pdf_to_xmind.sh --overwrite
```

Or let `run_pipeline.sh` call this after you pass `--approve-segment`.

---

## Output layout

For `book.pdf` in `/data/books/`:

```text
/data/books/book.md
/data/books/book_images/
/data/books/book_work/
├── STUDY_INDEX.md           # bilingual index (FA + EN)
├── STUDY_INDEX.pdf          # printable index
├── SEGMENTATION_PREVIEW.md  # review summary
├── parts/                   # one file = one topic
│   ├── 01_Topic_A.md
│   └── ...
├── opml/
└── xmind/                   # final XMind files
```

### Sample index rows

| # | Part | PDF pages | Study focus |
|---|------|-----------|-------------|
| 1 | Blood cells and haematopoiesis | **pp. 4–9** (6 pg) | Study: Blood cells… |
| 2 | PATOPHYSIOLOGY OF ERYTHROCYTES | **pp. 10–16** (7 pg) | Study: PATOPHYSIOLOGY… |

The full index also includes a Persian block, an English block, and a **Quick Reference** table combining both.

---

## Segmentation philosophy

| Principle | Meaning |
|-----------|---------|
| **Topic** | Each part covers one main topic or a clear subtopic |
| **Coverage** | `pp. X–Y` in the index = where that topic appears in the PDF |
| **Natural boundaries** | Topic change = split boundary — even for short sections |
| **Granularity** | Controls subtopic depth only — not page count |

### `--granularity`

| Value | Behavior |
|-------|----------|
| `normal` | Major topics + clear subtopics (⮚ / ❖) — **default** |
| `fine` | More subtopics, smaller parts |
| `coarse` | Major topics only, fewer larger parts |

```bash
# Fewer, larger parts
./scripts/run_pipeline.sh book.pdf --skip-convert --granularity coarse --overwrite

# More, smaller parts
./scripts/run_pipeline.sh book.pdf --skip-convert --granularity fine --overwrite
```

---

## Segmentation review workflow

The pipeline **pauses after Step 2** (unless you use `--skip-mindmap` or `--approve-segment`) so you can inspect the split before mind maps consume API/browser time.

1. Pipeline runs Step 2
2. Read `SEGMENTATION_PREVIEW.md`, `STUDY_INDEX.md`, and `STUDY_INDEX.pdf`
3. Choose one:
   - **Approve** → re-run with `--approve-segment`
   - **Coarser** → re-run with `--granularity coarse`
   - **Finer** → re-run with `--granularity fine`

> `--skip-mindmap` does **not** trigger the review pause — the pause only applies when Step 3 would run.
>
> The review gate exits with status `20`. This is an expected “awaiting review”
> state for GUI and automation clients, not a pipeline failure.

---

## `run_pipeline.sh` flags

| Flag | Effect |
|------|--------|
| `--skip-convert` | Reuse existing `<stem>.md` beside the PDF |
| `--skip-segment` | Reuse existing `parts/` in the work dir |
| `--skip-mindmap` | Stop after index generation |
| `--mindmap-only` | Skip convert + segment; run mind maps only |
| `--approve-segment` | Skip review pause and continue to mind maps |
| `--granularity LEVEL` | `fine` \| `normal` \| `coarse` |
| `--limit N` | Process only the first N parts in Step 3 |
| `--overwrite` | Overwrite generated outputs |
| `--log-file PATH` | Append full stdout/stderr to a log file |
| `--work-dir PATH` | Custom workspace (default: `<pdf_dir>/<stem>_work`) |
| `--event-file PATH` | Append machine-readable JSONL progress events |
| `--start-at STAGE` | Start at `conversion`, `segmentation`, or `mindmap` |
| `--stop-after STAGE` | Finish successfully after a selected stage |

`run_pipeline.sh` is now a compatibility wrapper around
`scripts/run_pipeline.py`. Existing flags remain available, while the Python
entry point provides the platform-neutral contract used by the future GUI.

### Environment variables

```bash
export PDF_TO_MD_PY=...          # Python with PyMuPDF4LLM
export PDF_TO_MD_SCRIPT=...      # path to convert_pdf.py
export MINDMAP_PROJECT=~/projects/chatgpt-mindmap-to-xmind
export PROMPT_FILE=~/projects/chatgpt-mindmap-to-xmind/prompts/prompt-mind-map.md
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Empty Markdown | Scanned PDF — try OCR in `convert_pdf.py` |
| ChatGPT login error | Log in once in `chatgpt-mindmap-to-xmind/chrome_profile/` |
| Too many parts | `--granularity coarse` |
| Parts too large / too few | `--granularity fine` |
| `STUDY_INDEX.pdf` missing | `PDF_TO_MD_PY` must have PyMuPDF installed |
| Spaces in PDF filename | Handled automatically (`lulu_fisio_images`) |
| Parts show `—` for page range | Source markdown lacks `<!-- Page N -->` markers |

---

## Testing

Full report: [`docs/TEST_v0.1.0.md`](docs/TEST_v0.1.0.md)

Validated on `lulu fisio.pdf` (252 pages, lecture notes):

| Test | Result |
|------|--------|
| Segment + index (`--skip-convert --skip-mindmap`) | **PASS** — 92 topic parts |
| Mind map (`--approve-segment --limit 1`) | **PASS** — OPML + XMind in ~2.3 min |

```bash
# Quick segment + index test
./scripts/run_pipeline.sh "lulu fisio.pdf" --skip-convert --skip-mindmap --overwrite

# Mind map smoke test (1 part)
./scripts/run_pipeline.sh "lulu fisio.pdf" --skip-convert --approve-segment --limit 1 --overwrite
```

---

## Roadmap

- [ ] Auto-translate study-focus descriptions to Persian
- [ ] Full textbook chapter support (sanei-style structure)
- [ ] pdf-to-markdown as a git submodule
- [ ] Web UI or Obsidian plugin

---

## License & author

MIT (proposed) — **Ali Fazeli Dehkordi** ([@alifazelidehkordi](https://github.com/alifazelidehkordi))

### Related projects

- [chatgpt-mindmap-to-xmind](https://github.com/alifazelidehkordi/chatgpt-mindmap-to-xmind) — OPML + XMind automation
- [chatgpt-mindmap-pipeline](https://github.com/alifazelidehkordi/chatgpt-mindmap-pipeline) — earlier pipeline experiments
