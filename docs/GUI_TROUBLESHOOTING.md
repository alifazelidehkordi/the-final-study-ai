# GUI Troubleshooting

## Application will not start

| Symptom | Likely cause | Fix |
|---|---|---|
| `No module named 'PySide6'` | GUI dependencies not installed | `pip install -r requirements/gui-lock.txt` |
| `No module named 'gui'` | Wrong working directory | Run from repo root: `python -m gui` |
| Blank window offscreen | Expected in CI | Use a normal desktop session for daily use |

## Setup screen

| Symptom | Fix |
|---|---|
| All presets blocked | Open **Setup**, refresh probes, install/repair missing items |
| PDF conversion missing | Point `PDF_TO_MD_PY` / `PDF_TO_MD_SCRIPT` or use the install plan |
| Mind-map project repairable | Checkout `chatgpt-mindmap-to-xmind` at `feature/pipeline-events` |
| Chrome missing | Install Chrome/Chromium and ensure it is on `PATH` |
| Profile locked | Close other GUI/CLI sessions using the same browser profile |
| Login probe failed | Click **Run login probe**, sign in visibly, retry |

## Windows

| Symptom | Fix |
|---|---|
| SmartScreen blocks `__main__.exe` | More info → Run anyway (unsigned CI build) |
| App won't start from zip | Extract the full zip; run `gui\deployment\__main__.dist\__main__.exe` |
| `Activate.ps1` blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Mind-map presets greyed out | Open **Setup**, install Chrome + mind-map project, run login probe |

Full walkthrough: [`GUI_WINDOWS_INSTALL.md`](GUI_WINDOWS_INSTALL.md)

## Linux

| Symptom | Fix |
|---|---|
| `ImportError: libEGL.so.1` | `sudo apt install libegl1 libgl1 libglib2.0-0 libxkbcommon0 libxcb-cursor0` |
| Complete / Mind Maps Only blocked on Wayland | Log into an **X11** session (`Ubuntu on Xorg`) or use Markdown & Index only |
| Linux desktop repairable | `sudo apt install python3-tk scrot` |
| Packaged `.bin` won't start | Keep full `__main__.dist` folder; `chmod +x`; install Qt system libs |
| Headless server | GUI shell can run offscreen; mind-map automation requires a desktop with `DISPLAY` |

Full walkthrough: [`GUI_LINUX_INSTALL.md`](GUI_LINUX_INSTALL.md)

## New Run

| Symptom | Fix |
|---|---|
| Start disabled | Select a valid PDF or work directory and output folder |
| Low disk space warning | Free space or confirm continue; hard block needs more disk |
| Preset card greyed out | Read the dependency name on the card; fix it in Setup |

## Progress / stop

| Symptom | Fix |
|---|---|
| No item counts yet | Wait for JSONL events; segmentation and mind-map stages emit items |
| ETA says “Calculating estimate” | Normal until two items complete |
| Stop After Current Item missing | Only shown during mind-map stages with stop-file support |
| Stop Now | Kills the process tree; use History → Resume to continue from the last validated boundary |

## Review / results

| Symptom | Fix |
|---|---|
| Stuck after segmentation | Expected for Complete preset — approve or regenerate in Review |
| Results show “changed” | Source artifact hash differs from manifest; rerun affected stage |
| History resume disabled | Only stopped, interrupted, partial, and failed runs can resume; use Review for `awaiting_review` |

## Packaging

| Symptom | Fix |
|---|---|
| `pyside6-deploy` fails on Linux | Install `patchelf`; build natively on target OS |
| Package over 180 MiB | Inspect `dist/package-size-report.json` and trim bundled extras |

## Logs and diagnostics

- Human pipeline log: path shown in Progress / manifest `log_file`
- Machine events: `events.jsonl` under app-data `runs/<run_id>/`
- Run manifest: `run.json` in the same folder

## عیب‌یابی سریع (فارسی)

- preset مایندمپ روی **Wayland** یا **macOS** عمداً غیرفعال است.
- برای مایندمپ روی لینوکس از نشست **X11** استفاده کنید.
- قبل از اجرا صفحه **Setup** باید وابستگی‌های لازم را Ready نشان دهد.
