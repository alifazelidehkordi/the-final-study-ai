# Release Notes — v0.2.0 GUI (beta)

**Date:** 2026-06-19  
**Branch:** `feature/cross-platform-gui`

## Highlights

- Cross-platform **PySide6 desktop GUI** with English and Persian (RTL) UI
- Canonical orchestrator: `scripts/run_pipeline.py` with JSONL events and Run Manifest v1
- Screens: Setup, New Run, Progress, Segmentation Review, Results, History
- Dependency gating, visible ChatGPT login probe, exclusive browser-profile lock
- Locked requirements (`requirements/gui-lock.txt`, `requirements/dev-lock.txt`)
- `pyside6-deploy` packaging spec and GitHub Actions matrix (Windows, Ubuntu, macOS)

## Presets

| Preset | CLI equivalent | Review gate |
|---|---|---|
| Complete Study Pack | Full pipeline | Yes (exit `20`) |
| Markdown & Index | `--stop-after segmentation` | No |
| Mind Maps Only | `--mindmap-only --require-valid-parts` | No |

## Breaking / migration notes

- `run_pipeline.sh` remains a compatibility wrapper; the GUI calls `run_pipeline.py` directly.
- Mind-map project must be on ref `feature/pipeline-events` (see compatibility manifest).
- `--resume` validates persisted artifacts and restarts at conversion, segmentation, or mind-map as required.

## Known limitations

- macOS mind-map presets are blocked until interactive acceptance passes.
- Linux Wayland sessions block mind-map presets; X11 is required for automation.
- Hosted CI does not run live ChatGPT / Selenium acceptance.
- Resume intentionally works only at validated stage boundaries; an interrupted in-flight browser item is retried.

## Upgrade from v0.1.0 CLI

Existing shell commands and environment variables continue to work. To try the GUI:

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements/dev-lock.txt
python -m gui
```

## Install guides

- Windows: [`GUI_WINDOWS_INSTALL.md`](GUI_WINDOWS_INSTALL.md)
- Linux: [`GUI_LINUX_INSTALL.md`](GUI_LINUX_INSTALL.md)
- All platforms (source): [`GUI_SOURCE_INSTALL.md`](GUI_SOURCE_INSTALL.md)

## Related documents

- [`RELEASE_QUALIFICATION_v0.2.0-gui.md`](RELEASE_QUALIFICATION_v0.2.0-gui.md)
- [`SUPPORT_MATRIX.md`](SUPPORT_MATRIX.md)
- [`GUI_SOURCE_INSTALL.md`](GUI_SOURCE_INSTALL.md)
- [`GUI_TROUBLESHOOTING.md`](GUI_TROUBLESHOOTING.md)
- [`INTERACTIVE_ACCEPTANCE_CHECKLIST.md`](INTERACTIVE_ACCEPTANCE_CHECKLIST.md)
