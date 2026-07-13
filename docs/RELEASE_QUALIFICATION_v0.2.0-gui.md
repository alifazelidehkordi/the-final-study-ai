# Release Qualification — v0.2.0 GUI

**Date:** 2026-06-19  
**Host:** Linux 6.17, X11 (`DISPLAY=:0`, `XDG_SESSION_TYPE=x11`)  
**Python:** 3.14 (local venv); CI uses 3.12  
**Repository at qualification:** `the-final-study-ai-gui` (now consolidated into `the-final-study-ai`)

## Automated gates

Command:

```bash
bash scripts/ci/run_release_qualification.sh
```

| Gate | Result |
|---|---|
| Ruff | PASS |
| MyPy (53 GUI/script modules) | PASS |
| Bandit (`gui/`, `scripts/`) | PASS |
| pytest GUI + CLI (72 collected, 4 screenshot tests skipped) | **68 PASS**, 4 SKIP |
| GUI resource validation | PASS |
| Offscreen launch smoke | PASS |
| CLI regression (`run_pipeline`, mind-map integration, contracts, validators, segmentation) | PASS |

## Regression scope

### CLI (preserved v0.1.0 behavior)

- `run_pipeline.py` review exit `20`, cooperative stop exit `21`
- JSONL monotonic `seq`, manifest atomic writes
- Parts manifest hashing and artifact validators
- Manifest resume invalidation across conversion, segmentation, and mind-map stages
- Mind-map integration with `--event-file` / `--stop-file`

### GUI

- Setup dependency registry and install-plan gating
- New Run validation, disk-space thresholds, preset blocking
- Progress from JSONL with ETA sampling rules
- Review approve/regenerate commands
- Results artifact catalog with changed-file warnings
- History listing and integrity-validated resume from `runs/*/run.json`
- Persian RTL shell translations (pytest-qt)
- CI packaging workflow on Windows, Ubuntu, macOS

## Platform qualification encoded in probes

| Rule | Implementation |
|---|---|
| macOS mind-map presets unavailable | `probe_mindmap_project` → `UNSUPPORTED` on `darwin` |
| Linux Wayland not qualified for automation | `probe_linux_desktop` → `UNSUPPORTED` when only Wayland |
| Linux X11 qualified with `scrot` + Tkinter | `probe_linux_desktop` → `READY` |

## Manual gates still open

| Gate | Status |
|---|---|
| Windows interactive browser acceptance | **Pending** — see checklist |
| Linux X11 interactive browser acceptance | **Pending** — see checklist |
| Linux Wayland | **Rejected** for mind-map presets (by design) |
| macOS interactive browser acceptance | **Pending** — presets blocked in app |
| Public signed Windows/macOS artifacts | **Out of repo** — credentials required |

## Sign-off

Automated qualification on this workstation: **PASS**  
Interactive mind-map acceptance: **NOT RUN** (documented checklist provided)

Next step before merging to `main`: complete interactive checklist on at least one
Windows and one Linux X11 session, then update this file with tester sign-off.
