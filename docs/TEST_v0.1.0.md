# Test Report — v0.1.0

**Date:** 2026-06-19  
**Document:** `lulu fisio.pdf` (252 pages, lecture notes)  
**Environment:** Linux, Python 3.14

## Tests run

| # | Command | Result |
|---|---------|--------|
| 1 | Segment + index (`--skip-convert --skip-mindmap`) | PASS |
| 2 | Full pipeline mind map (`--approve-segment --limit 1`) | PASS |

## Test 1 — Topic segmentation + bilingual index

```bash
./scripts/run_pipeline.sh "/path/to/lulu fisio.pdf" \
  --skip-convert --skip-mindmap --overwrite --granularity normal \
  --log-file logs/test_v0.1.0_lulu_fisio.log
```

**Output:**
- 92 study parts in `lulu fisio_work/parts/`
- `STUDY_INDEX.md` — bilingual (FA + EN) with page ranges per topic
- `STUDY_INDEX.pdf` — printable index
- `SEGMENTATION_PREVIEW.md` — review summary

**Sample parts (topic-first):**
| Topic | PDF pages |
|-------|-----------|
| Blood cells and haematopoiesis | pp. 4–9 |
| PATOPHYSIOLOGY OF ERYTHROCYTES | pp. 10–16 |
| DISORDERS OF IRON METABOLISM | pp. 40–47 |

## Test 2 — Mind map integration (1 part)

```bash
./scripts/run_pipeline.sh "/path/to/lulu fisio.pdf" \
  --skip-convert --approve-segment --limit 1 --overwrite \
  --log-file logs/test_v0.1.0_mindmap_limit1.log
```

**Output:**
- OPML: `01_Blood_cells_and_haematopoiesis.opml`
- XMind: `01_Blood_cells_and_haematopoiesis.xmind`
- Batch: 1 success, 0 failures (~2.3 min)

## Bug fixed during v0.1.0

- `--skip-mindmap` no longer triggers segmentation review pause (review only applies when mind map step will run).

## Known limitations

- Lecture notes with many uppercase topic headings produce more parts than textbooks.
- Parts without `<!-- Page N -->` markers show `—` for PDF range in index.
- Step 3 requires logged-in ChatGPT session in `chatgpt-mindmap-to-xmind/chrome_profile/`.
