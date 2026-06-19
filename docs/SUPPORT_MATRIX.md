# Support Matrix — v0.2.0 GUI

**Branch:** `feature/cross-platform-gui`  
**Date:** 2026-06-19

This matrix describes what is automated in CI, what is qualified on a developer
workstation, and what still requires a manual interactive acceptance run.

## Desktop GUI shell

| Capability | Windows | Linux (X11) | Linux (Wayland) | macOS |
|---|---|---|---|---|
| Install from locked requirements | CI | CI | CI | CI |
| Launch smoke (offscreen) | CI | CI | CI | CI |
| Setup / dependency probes | Supported | Supported | Supported | Supported |
| New Run — Markdown & Index | Supported | Supported | Supported | Supported |
| New Run — Complete Study Pack | After interactive gate | After interactive gate | **Blocked** | **Blocked** |
| New Run — Mind Maps Only | After interactive gate | After interactive gate | **Blocked** | **Blocked** |
| Progress / Review / Results / History | Supported | Supported | Supported | Supported |
| Persian RTL UI | Supported | Supported | Supported | Supported |
| Packaged build (`pyside6-deploy`) | CI | CI | CI | CI |

## Pipeline backends

| Component | Windows | Linux X11 | Linux Wayland | macOS |
|---|---|---|---|---|
| `run_pipeline.py` CLI | Supported | Supported | Supported | Supported |
| PDF → Markdown | Supported | Supported | Supported | Supported |
| Segmentation + index | Supported | Supported | Supported | Supported |
| Mind-map browser automation | Manual gate | Manual gate | Not qualified | Not qualified |
| Cooperative stop between parts | Supported | Supported | Supported | Supported |

## CI coverage

| Check | ubuntu-latest | windows-latest | macos-latest |
|---|---|---|---|
| Ruff / MyPy / Bandit | Yes | Yes | Yes |
| pytest (GUI + CLI) | Yes | Yes | Yes |
| GUI resource validation | Yes | Yes | Yes |
| Offscreen launch smoke | Yes | Yes | Yes |
| `pyside6-deploy` dry-run + build | Yes | Yes | Yes |
| Interactive ChatGPT / PyAutoGUI | **No** | **No** | **No** |

Hosted CI cannot prove live browser automation. Complete and Mind Maps Only
presets stay gated until the interactive checklist in
[`INTERACTIVE_ACCEPTANCE_CHECKLIST.md`](INTERACTIVE_ACCEPTANCE_CHECKLIST.md)
passes on the target OS.

## Platform notes

### Linux X11

Qualified when `DISPLAY` is set, Tkinter is importable, and `scrot` is on `PATH`.
This environment matches the historical `chatgpt-mindmap-to-xmind` validation.

### Linux Wayland

The GUI runs, but mind-map presets are **blocked** because screenshot/input
automation is not qualified on pure Wayland sessions. Use an X11 session or a
Wayland desktop that exposes `DISPLAY` for XWayland.

### macOS

Mind-map presets remain **unsupported** until Accessibility/Screen Recording
permissions, Selenium profile locking, and a full fixture run are validated
manually.

### Signing

Internal CI builds are unsigned. Public Windows/macOS production releases
require signing/notarization credentials outside the repository.

## خلاصه فارسی

| قابلیت | ویندوز | لینوکس X11 | لینوکس Wayland | macOS |
|---|---|---|---|---|
| رابط گرافیکی و تبدیل PDF | پشتیبانی می‌شود | پشتیبانی می‌شود | پشتیبانی می‌شود | پشتیبانی می‌شود |
| preset «Markdown و ایندکس» | پشتیبانی می‌شود | پشتیبانی می‌شود | پشتیبانی می‌شود | پشتیبانی می‌شود |
| presetهای مایندمپ | پس از تست تعاملی | پس از تست تعاملی | **مسدود** | **مسدود** |
| RTL فارسی | پشتیبانی می‌شود | پشتیبانی می‌شود | پشتیبانی می‌شود | پشتیبانی می‌شود |

راهنمای نصب: [`GUI_WINDOWS_INSTALL.md`](GUI_WINDOWS_INSTALL.md) · [`GUI_LINUX_INSTALL.md`](GUI_LINUX_INSTALL.md) · [`GUI_SOURCE_INSTALL.md`](GUI_SOURCE_INSTALL.md)  
عیب‌یابی: [`GUI_TROUBLESHOOTING.md`](GUI_TROUBLESHOOTING.md)