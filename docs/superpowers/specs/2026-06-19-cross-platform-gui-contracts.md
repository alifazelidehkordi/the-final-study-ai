# Cross-Platform GUI Technical Contracts

This document is normative for implementation. It closes the executable
contracts intentionally left broad in the product design.

## 1. Canonical Entry Point and Exit Status

All GUI runs invoke:

```text
<pipeline-python> scripts/run_pipeline.py --event-file <events.jsonl> ...
```

`run_pipeline.py` is the only canonical orchestrator. It uses `pathlib`, Python
subprocess APIs, and explicit argument lists; it cannot depend on Bash,
`readlink`, process substitution, Unix signals, or platform-specific venv names.
The existing shell script remains a compatibility wrapper and maps legacy flags
to this entry point. A Windows CMD wrapper may do the same. The GUI calls
neither wrapper.

Mind-map execution calls that project's `scripts/pipeline.py` with the detected
environment: `.venv\Scripts\python.exe` on Windows, `.venv/bin/python` on
Linux/macOS, or legacy `.venv-linux/bin/python` on Linux.

| Code | Meaning |
|---:|---|
| `0` | Requested terminal stage completed successfully |
| `1` | Fatal run failure |
| `2` | Terminal stage reached with one or more item failures |
| `20` | Segmentation completed and review is required |
| `21` | Cooperative stop completed at an item boundary |
| `22` | Run was interrupted by immediate stop |

The GUI never infers the review gate from text or exit `0`.

## 2. Preset Invocation Contract

| Action | Source | Canonical arguments |
|---|---|---|
| Complete Study Pack | PDF | `<pdf> --work-dir <dir> --granularity <g> --index-language <lang> --ocr <mode>` |
| Markdown & Index | PDF | Complete arguments plus `--stop-after segmentation` |
| Mind Maps Only | Existing work dir | `--work-dir <dir> --start-at mindmap --require-valid-parts` |
| Approve review | Existing run | `--resume <run.json> --approve-segmentation` |
| Regenerate split | Existing run | `--resume <run.json> --rerun segmentation --granularity <g>` |
| Retry failed items | Existing run | `--resume <run.json> --retry-failed` |

Advanced reuse uses `--start-at`, `--stop-after`, and `--rerun`. The GUI does
not expose legacy skip-flag combinations. The shell wrapper maps them to the
canonical model. `--overwrite` remains explicit.

OCR values are `auto` and `off`. `force` may be added only after the converter
provides a real forced-OCR contract. UI locale and index language are separate.

## 3. Progress Event v1

`--event-file` points to an append-only UTF-8 JSON Lines file. Human stdout,
stderr, and `--log-file` remain human-readable and never carry machine state.

```json
{
  "schema": "final-study.event",
  "version": 1,
  "run_id": "01JY...",
  "seq": 42,
  "time": "2026-06-19T14:31:45.123Z",
  "type": "item.completed",
  "stage": "mindmap_opml",
  "item": {
    "id": "part-017",
    "index": 17,
    "total": 24,
    "label": "Thyroid diseases"
  },
  "artifact": {
    "kind": "opml",
    "path": "/work/opml/17_Thyroid_diseases.opml",
    "sha256": "..."
  },
  "data": {}
}
```

Required fields are `schema`, `version`, `run_id`, `seq`, `time`, `type`, and
`stage`. Sequence increases monotonically per run. Paths are absolute native
paths. Writers append one complete line and flush immediately. Unknown optional
fields are ignored.

Optional object contracts are:

- `item`: `id` string, one-based `index`, positive `total`, display `label`;
- `artifact`: `kind`, absolute `path`, SHA-256 after validation;
- `error`: stable `code`, localized-message key, retryable boolean, redacted
  detail, and optional child exit code;
- `data`: event-specific values. For `stage.progress`, allowed values are
  integer `completed`, integer `total`, and numeric `fraction` from 0 to 1.

An event writer owns an OS-level append lock while writing each line. The top
orchestrator allocates sequence numbers; child processes request or emit through
the shared event sink rather than maintaining independent sequences. On startup,
the GUI ignores a final unterminated line left by a crash and records a warning.

Stages are `preflight`, `pdf_to_markdown`, `segmentation`, `review`,
`mindmap_opml`, `opml_to_xmind`, and `finalize`.

Event types are:

- `run.started`, `run.completed`, `run.failed`, `run.stopped`
- `stage.started`, `stage.progress`, `stage.completed`, `stage.failed`
- `item.started`, `item.retrying`, `item.skipped`, `item.completed`
- `item.failed`, `item.interrupted`
- `artifact.created`, `artifact.validated`, `artifact.invalid`
- `review.required`, `warning`

`item.completed` is emitted only after integrity validation. Item counts take
precedence over synthetic percentages. `run_pipeline.py` emits run, stage,
review, and failure events. PDF conversion and segmentation emit stage/artifact
details. The separate mind-map repository adds `--event-file` to
`pipeline.py`, `batch_pdf.py`, `batch_markdown.py`, and
`convert_opml_batch.py` for item events.

ETA remains hidden until two items complete. It uses the median of the last five
completed-item durations multiplied by remaining items and is labeled
approximate. Retries and skipped items do not enter the sample.

## 4. Run Manifest v1

```json
{
  "schema": "final-study.run",
  "version": 1,
  "run_id": "01JY...",
  "created_at": "2026-06-19T14:00:00Z",
  "updated_at": "2026-06-19T14:31:45Z",
  "status": "awaiting_review",
  "preset": "complete",
  "source": {
    "kind": "pdf",
    "path": "/data/book.pdf",
    "size": 123456,
    "mtime_ns": 123456789,
    "sha256": "..."
  },
  "paths": {
    "work_dir": "/data/book_work",
    "event_file": "/app-data/runs/01JY/events.jsonl",
    "log_file": "/app-data/runs/01JY/run.log"
  },
  "options": {
    "granularity": "normal",
    "ocr": "auto",
    "index_language": "fa",
    "overwrite": false,
    "limit": null
  },
  "tool_versions": {},
  "stages": {},
  "items": {},
  "artifacts": [],
  "last_error": null
}
```

Statuses are `created`, `running`, `awaiting_review`, `stop_requested`,
`stopped`, `interrupted`, `partial`, `failed`, and `completed`. Writes use a
temporary file plus atomic replace. Unknown newer versions open read-only and
cannot resume.

Each `stages[stage_name]` object contains `status`, `started_at`, `finished_at`,
`completed`, `total`, and `error_code`. Each `items[item_id]` object contains
`stage`, `index`, `label`, `status`, `attempts`, `started_at`, `finished_at`, and
artifact IDs. Each artifact contains `id`, `kind`, `path`, `sha256`, `size`,
`created_at`, and `validator_version`.

Allowed presets are `complete`, `markdown_index`, and `mindmaps_only`. Source
kind is `pdf` for the first two and `work_dir` for mindmaps-only.

## 5. Integrity and Invalidation

| Artifact | Valid when |
|---|---|
| Source PDF | Size and SHA-256 match; mtime is an optimization, not proof |
| Markdown | UTF-8, non-empty, has a `<!-- Page N -->` marker, hash matches |
| Parts | `parts-manifest.json` validates; every ordered file is UTF-8/non-empty and its hash matches |
| Index Markdown | UTF-8/non-empty, expected part count present, hash matches |
| Index PDF | PyMuPDF opens it, page count is positive, hash matches |
| OPML | UTF-8 XML parses; OPML body has at least one outline; hash matches |
| XMind | ZIP `testzip()` succeeds; required JSON entries parse; sheet/root topic exists; hash matches |

Segmentation writes `parts-manifest.json` atomically with source fingerprint,
granularity, index language, ordered part IDs, page ranges, filenames, and
hashes. Generated files use temporary suffixes and are renamed only after
validation. Partial outputs never qualify for resume.

A changed source, OCR mode, or converter version invalidates Markdown and all
downstream stages. Changed granularity, index language, or segmentation version
invalidates parts/index and downstream stages. Changed prompt hash or mind-map
tool version invalidates OPML and XMind. Valid unaffected upstream stages remain
reusable.

## 6. Review, Stop, and Resume

Complete Study Pack emits `review.required` and exits `20` after segmentation.
Markdown & Index uses `--stop-after segmentation`, exits `0`, and does not enter
the gate because no mind-map work is pending.

Current mind-map loops do not support a cooperative stop. The GUI must not show
Stop After Current Item until that repository gains a stop-file argument checked
immediately before each part/section. The active Selenium request is never
paused.

Stop Now terminates the process tree. The active item is `interrupted`; any
`.crdownload`, temporary OPML, or XMind being written is invalid. Resume skips
only validated outputs and retries the interrupted item.

## 7. Error Registry

| Code | Meaning |
|---|---|
| `E_INPUT_NOT_FOUND` | Source or work directory no longer exists |
| `E_INPUT_INVALID` | Source type/content is unsupported |
| `E_DISK_SPACE` | Required free-space threshold is not met |
| `E_DEP_MISSING` | Required dependency is absent |
| `E_DEP_UNSUPPORTED` | Version/platform is unsupported |
| `E_PROFILE_LOCKED` | Browser profile is in use |
| `E_CHATGPT_LOGIN` | Login probe did not find a usable editor |
| `E_CONVERT_FAILED` | PDF conversion failed |
| `E_SEGMENT_FAILED` | Segmentation/index generation failed |
| `E_OPML_INVALID` | OPML validation failed |
| `E_XMIND_INVALID` | XMind archive validation failed |
| `E_BROWSER_AUTOMATION` | Selenium/PyAutoGUI operation failed |
| `E_CHILD_PROCESS` | Child process exited unexpectedly |
| `E_MANIFEST_INCOMPATIBLE` | Manifest is unsupported/inconsistent |
| `E_ARTIFACT_CHANGED` | Recorded artifact changed after completion |
| `E_STOPPED` | User-requested stop ended the run |

Codes are stable. OS detail belongs in structured error data, not ad-hoc codes.

## 8. Dependency and Platform Matrix

| Dependency | Detection | Managed installation | Manual fallback |
|---|---|---|---|
| Python | Bundled version/executable probe | Included standalone; source mode creates `.venv` with 3.10+ | Install supported CPython and select it |
| PySide6 | Import/version probe | Locked GUI requirements | Exact lock-file pip command |
| PDF conversion | Locate app/custom checkout; import `pymupdf4llm>=1.27.2.3,<2`; run `--help` | Clone pinned release after AGPL notice; create dedicated venv | Select checkout and Python |
| OCR | Probe engine and requested language data | Confirmed OS provider where available | OS-specific instructions |
| Mind-map project | Verify checkout, scripts, and compatible commit/version | Clone pinned release; create dedicated venv | Select existing checkout |
| Mind-map packages | Import Selenium, PyAutoGUI, Pyperclip | Install pinned requirements in its venv | Exact venv pip command |
| Chrome/Chromium | Executable/version plus Selenium startup probe | Official link or confirmed package action; no silent bundle | Install/select executable |
| Linux desktop support | Tk import, display server, screenshot/input probe | Confirmed package action where supported | Distro-specific commands |
| Profile/login | Lock probe plus interactive editor probe | Create app-managed profile; user logs in | Select/reset profile with confirmation |

Windows uses PowerShell/winget only when available and confirmed. macOS uses
signed downloads or Homebrew only if already present and confirmed. Linux
detects its distribution/package manager and never assumes `apt`. No provider
modifies shell startup files.

The compatibility manifest pins Python `>=3.10,<3.14`, PySide6 `>=6.8,<7`,
PyMuPDF4LLM `>=1.27.2.3,<2`, Selenium `>=4.20,<5`, PyAutoGUI `>=0.9.54,<1`, and
Pyperclip `>=1.9,<2`. The lock records exact versions and hashes. Browser support
covers current stable Chrome/Chromium and two preceding majors after tests.

## 9. Login and Profile Contract

The app does not inspect cookies to claim login. It launches a visible Selenium
probe with the exact run profile, opens `chatgpt.com`, and waits for either a
usable prompt editor or login controls. Timeout yields Unknown/Needs Login. The
profile has one exclusive lock shared by Setup and pipeline runs.

## 10. UX and Runtime Numbers

- Minimum content size: `1024 × 700` device-independent pixels.
- `>= 1280`: three columns; `1024–1279`: compact columns; below `1024`: recovery
  layout with status below and controlled scrolling.
- Hard free-space threshold: `max(1 GiB, 3 × source size)`.
- Warning threshold: `max(5 GiB, 5 × source size)`.
- One active pipeline run across GUI instances.
- Drag-and-drop always has native Browse fallback.
- UI locale and index language are independent settings.
- Translation sources are Qt `.ts`, compiled to `.qm`.
- Latin paths and filenames use isolated LTR runs in Persian layouts.
- UI targets WCAG 2.2 AA contrast and keyboard behavior where applicable.

## 11. Packaging and Release Gates

The package includes GUI, Python/Qt runtime, translations, icons, orchestrator,
segmentation/index code, schemas, and diagnostics. It excludes Chrome, profile,
OCR engines, and the separate mind-map repository. External tools are installed
into app-managed directories after confirmation.

The initial compressed-size budget is `<= 180 MiB`. Unsigned builds are for
internal testing. Public Windows/macOS production releases require signing and
notarization.

The mind-map repository currently documents Linux and Windows only. macOS
mind-map presets remain Experimental/Unavailable until Accessibility and Screen
Recording permission UX, Selenium/PyAutoGUI behavior, profile locking, and an
interactive complete fixture pass.

CI uses `windows-latest`, `ubuntu-latest`, and `macos-latest` for packaged
launches and non-browser fixtures. Hosted CI does not prove PyAutoGUI. Each
supported OS requires a manual interactive browser-automation acceptance run.

## 12. Test Tooling

Use `pytest-qt` for UI behavior and deterministic Qt screenshots for visual
regression with fixed fonts, scale, locale, theme, and window size. Test Windows
fractional scaling, Persian RTL mixed with Latin paths, profile-lock conflicts,
manifest migration, interruption, review exit `20`, and all artifact validators.

