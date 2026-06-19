# Cross-Platform GUI Design

> Normative implementation contracts are defined in
> [`2026-06-19-cross-platform-gui-contracts.md`](2026-06-19-cross-platform-gui-contracts.md).
> Where this vision document is broad, the contracts document takes precedence.

## Summary

The Final Study AI will gain a polished desktop GUI for Windows, macOS, and
Linux. The GUI will make the existing PDF-to-study pipeline usable without
requiring command-line knowledge while preserving the current CLI behavior.

The application will support:

- native PDF and output-directory selection;
- guided, preset pipeline modes;
- dependency detection, installation, and repair;
- live progress for long-running work, especially mind-map generation;
- segmentation review before browser automation continues;
- bilingual Persian and English interfaces with true RTL/LTR layouts;
- automatic light/dark theme selection with a manual override;
- run history and safe resume of interrupted work;
- source execution and standalone installers for all three desktop platforms.

Version 1 processes one PDF per run. Batch queues are explicitly out of scope.

## Product Principles

1. **Protect the existing pipeline.** The GUI is an adapter around the existing
   scripts, not a replacement for them.
2. **Show real state.** Progress, errors, and completion counts must reflect
   durable pipeline output rather than decorative animations.
3. **Hide incidental complexity.** Common workflows use presets. Advanced flags
   remain available without dominating the primary interface.
4. **Never surprise the user with system changes.** Dependency installation
   requires explicit confirmation immediately before execution.
5. **Remain usable at realistic desktop sizes.** Layout behavior is specified
   for compact laptops as well as large monitors.
6. **Keep secrets outside the app.** The application never asks for or stores a
   ChatGPT password or token.

## Scope

### Included in Version 1

- A PySide6 desktop application in an independent `gui/` package.
- A first-run setup and diagnostics experience.
- Native file selection and drag-and-drop for one PDF.
- Preset execution modes:
  - Complete Study Pack: PDF through XMind.
  - Markdown & Index: PDF through segmentation and index generation.
  - Mind Maps Only: existing study parts through XMind.
  - Resume Previous Run: continue a durable interrupted run.
- Output-directory selection.
- Granularity selection through the segmentation review flow.
- Live stage, item count, elapsed time, and estimated remaining time.
- Stop after the current mind-map item where supported, stop immediately,
  retry, and resume at validated boundaries.
- Run history stored locally.
- Output discovery and open-file/open-folder actions.
- Persian and English localization.
- System, light, and dark theme modes.
- Dependency checks and user-approved installation or repair.
- Standalone packaging on Windows, macOS, and Linux.

### Explicitly Excluded from Version 1

- Processing multiple PDFs in a queue.
- Cloud execution or account synchronization.
- Editing Markdown or mind maps inside the application.
- Reimplementing PDF conversion, segmentation, or XMind generation.
- Automatic collection of ChatGPT credentials.
- Silent privileged installation.
- Mobile or browser-hosted versions.

## Technical Architecture

### Repository Isolation

Development occurs on `feature/cross-platform-gui` in a separate Git worktree.
The GUI lives under `gui/`. Existing scripts keep their documented command-line
interfaces. Any necessary core changes must remain backward compatible and
receive focused regression tests.

### Major Components

#### Application Shell

Owns top-level navigation, theme, locale, window state, and responsive layout.
It contains no pipeline execution logic.

#### Pipeline Adapter

Translates GUI choices into existing script arguments and environment
variables. It exposes typed operations such as:

- `run_complete`
- `run_markdown_and_index`
- `run_mindmaps_only`
- `resume_run`
- `rerun_segmentation`

The adapter is the only GUI component allowed to know command-line details.

#### Platform Entry Point

`scripts/run_pipeline.py` becomes the canonical cross-platform orchestrator.
The GUI calls it directly with an explicit Python executable and argument list.
It cannot depend on Bash or platform-specific virtual-environment names.

`scripts/run_pipeline.sh` remains a compatibility wrapper that maps legacy
flags to the Python orchestrator. A Windows `.cmd` wrapper may delegate to the
same entry point, but neither wrapper is used by the GUI. The mind-map project
is invoked through its existing `scripts/pipeline.py` with the environment
discovered according to the companion contracts document.


#### Process Controller

Uses `QProcess` to start and monitor external programs without blocking the UI.
Arguments are passed as separate values rather than shell-concatenated strings.
The controller streams standard output and error, reports process state, and
maps exit codes into structured results.

The controller never executes the full pipeline through a platform shell.

#### Progress Parser

Converts versioned JSONL pipeline events into structured state:

- active stage;
- completed and total items;
- current item;
- elapsed time;
- estimated remaining time;
- warning or failure details;
- output artifacts discovered.

Machine progress never relies on regex parsing of human logs. Participating
tools append JSON Lines to `--event-file`; human output remains unchanged.
Precise mind-map progress requires the same contract in the mind-map repository.

#### Run Store

Persists run manifests in the user's application-data directory, never in the
source checkout. Each run records:

- stable run ID;
- source PDF and output path;
- selected preset and options;
- timestamps and current status;
- completed stages and items;
- generated artifact paths;
- resumability information;
- last structured error.

Writes use an atomic save strategy. Source documents and generated study
content are not copied into the application-data directory.

#### Dependency Manager

Defines dependencies as independent checks with:

- identifier and purpose;
- detected version and location;
- supported version range;
- health state;
- install/repair plan;
- privilege requirement;
- manual fallback instructions.

Detection is read-only. Install and repair operations require confirmation.
The manager supports platform-specific providers without embedding package
manager logic into the UI.

#### Localization and Appearance

User-facing strings are stored in translation resources. Switching locale
updates text direction and alignment, not only translated labels. The chosen
locale, theme override, and accessible scaling preference persist across runs.

### Data Flow

1. The user selects a PDF, destination, and preset.
2. Validation checks paths, free space, required dependencies, and resumable
   output state.
3. A run manifest is created before processing begins.
4. The Pipeline Adapter creates the platform-neutral command invocation.
5. The Process Controller starts the process and streams output.
6. The Progress Parser updates the run manifest and UI.
7. Segmentation pauses at the review gate unless the chosen preset ends there.
8. After approval, browser automation continues with its local browser profile.
9. Completed artifacts are verified and exposed on the Results screen.

## UX and Visual System

### Visual Direction

The selected direction combines:

- the dark, precise, status-focused character of **Precision Workbench**;
- the large drag-and-drop file selector from **Luminous Guided**;
- the **Balanced** density option.

The visual language uses disciplined spacing, strong information hierarchy,
restrained color, and clear operational states. It avoids generic gradient
cards, excessive glow, decorative dashboards, and arbitrary rounded surfaces.

Dark mode uses a deep neutral background with a restrained green status accent.
Light mode retains the same hierarchy and spacing rather than becoming a
separate visual design.

### Main Layout

At regular desktop widths the shell has:

1. a compact fixed navigation rail;
2. a flexible central workspace;
3. a bounded status/output panel.

The central workspace receives remaining width and has a defined minimum. The
status panel has minimum and maximum widths rather than percentage sizing.
Long paths elide in the middle or end and expose the complete path in a tooltip.

At narrow widths:

- the status panel moves below the central workspace;
- preset cards wrap without shrinking below their usable minimum;
- navigation collapses to icons or a compact top bar;
- controlled scrolling is enabled;
- controls never overlap or clip.

The minimum content size is `1024 × 700` device-independent pixels. At widths
`>= 1280`, the layout uses three columns. From `1024–1279`, columns become
compact. Below `1024`, a recovery layout moves status below the workspace and
enables controlled scrolling.

Responsive decisions use the available application-window width, not the
physical screen size. Layouts reflow through explicit window-width states
instead of scaling the entire interface uniformly. Geometry uses Qt layout
managers and device-independent coordinates; absolute screen coordinates are
not used. Qt 6 high-DPI behavior remains enabled, vector or high-resolution
assets are provided, and fractional Windows scaling is part of acceptance
testing.

Platform-native differences remain where they improve familiarity: standard
menu placement, file dialogs, window controls, keyboard shortcuts, and system
colors follow the host OS. Product identity, information hierarchy, and spacing
tokens remain consistent across platforms.

### Screen Flow

#### 1. Setup

Displayed on first launch and available later from navigation. It shows each
dependency as Ready, Missing, Unsupported, Repairable, or Checking. Each item
explains why it is needed. Install/repair opens a confirmation sheet listing
the exact action and whether administrator privileges are required.

The screen launches the dedicated browser profile for manual login. A visible
Selenium probe opens `chatgpt.com` with that exact profile and reports Ready only
when the prompt editor is usable. It never reads cookies to infer login. The
profile has one exclusive lock shared by Setup and pipeline runs.

#### 2. New Run

Contains:

- a large drag-and-drop PDF target with a native Browse action;
- selected-file metadata and validation;
- output-directory selection;
- preset cards;
- a single primary Start action;
- a collapsed Advanced section for granularity, limits, overwrite behavior,
  OCR mode, index language, custom work directory, reusable-stage controls,
  custom tool paths, and diagnostics.

Mind Maps Only replaces the PDF picker with an existing-work-directory picker.

Unavailable presets explain which dependency is missing and link to Setup.

#### 3. Progress

Shows:

- overall pipeline stage and progress;
- the current operation;
- completed/total item count where measurable;
- elapsed time;
- estimated remaining time;
- completed artifact counts;
- concise recent activity;
- expandable full logs;
- Stop After Current Item, Stop Now, and Retry actions when applicable.

Mind-map progress is item-based, such as `17 of 24`. Remaining time uses the
observed duration of completed items. Until enough samples exist, the label is
“Calculating estimate” rather than a fabricated value. Estimates must tolerate
outliers and may be shown as an approximate range.

#### 4. Segmentation Review

Displays the generated part list with topic names and source page ranges.
Actions open the preview and index in native viewers. The user can:

- approve and continue;
- regenerate with coarser segmentation;
- regenerate with finer segmentation;
- stop with current outputs preserved.

Regeneration clearly identifies which outputs will be replaced.

The review gate emits `review.required` and exits `20`. The GUI maps it to
`awaiting_review`, never success or failure. Markdown & Index exits successfully
after segmentation and does not enter the gate.

#### 5. Results

Presents verified artifact groups:

- Markdown;
- Study Index Markdown and PDF;
- segmented parts;
- OPML;
- XMind.

Each group supports opening the primary file or containing folder. Missing or
partial artifacts are represented accurately.

#### 6. History

Lists complete, failed, stopped, and resumable runs. A run opens into a detail
view with configuration, artifacts, elapsed time, and error summary. Resume is
offered only after a fresh validity check confirms that required source and
intermediate files still exist.

## Installation and Platform Support

### Source Installation

The repository provides documented creation of a Python virtual environment and
installation of locked GUI dependencies. A developer command launches the app
from source without requiring a packaged build.

### Standalone Distribution

`pyside6-deploy` is the primary packaging path. Builds run natively on:

- Windows for Windows artifacts;
- macOS for `.app` and installer artifacts;
- Linux for Linux artifacts.

Cross-compiling all platforms from one host is not assumed. CI jobs verify each
platform independently. Signing and notarization configuration is supported,
but publishing signed artifacts requires platform credentials outside the
repository.

The package includes GUI, Python/Qt runtime, translations, orchestrator,
segmentation/index code, schemas, and diagnostics. It excludes Chrome, browser
profiles, OCR engines, and the separate mind-map repository.

The initial compressed-size budget is `<= 180 MiB`. Public Windows/macOS
production releases require signing/notarization; unsigned builds are internal.
The current mind-map project documents Linux and Windows only. macOS mind-map
presets remain Experimental/Unavailable until interactive tests pass.

## Dependency Installation Policy

1. Detection is always safe and read-only.
2. The application shows the planned command or operation before installation.
3. The user explicitly confirms each privileged operation.
4. Windows elevation, macOS authorization, or Linux `sudo` is requested by the
   operating system when required.
5. Passwords are entered only into the operating system's trusted prompt.
6. Failure displays a plain-language reason, technical log, and copyable manual
   instructions.
7. Partial installations are checked again before being marked Ready.
8. The app does not alter unrelated system packages or shell configuration.

## Resume, Stop, and Failure Semantics

- Version 1 does not pause inside a ChatGPT request.
- Stop After Current Item appears only after the mind-map dependency supports a
  cooperative stop file checked between parts. Until then only Stop Now exists.
- Stop Now terminates the process tree and invalidates the active partial item.
- Completed artifacts are retained.
- A run is resumable only at explicit stage or item boundaries.
- Resume uses the normative integrity table; existence alone is insufficient.
- Overwrite decisions are explicit and recorded in the run manifest.
- A crash or power loss is recognized on next launch from a run left in an
  active state.
- Errors have a stable code, user-facing summary, suggested action, command
  context with secrets removed, and a detailed log reference.

## Security and Privacy

- No ChatGPT password, session token, or browser cookie is copied into the run
  manifest or application logs.
- Browser authentication stays in the dedicated local browser profile.
- Process arguments and logs are redacted before display where sensitive values
  could appear.
- The dependency installer uses fixed trusted sources and verifies downloads
  where upstream checksums or signatures are available.
- The application never uploads source PDFs itself.

## Testing Strategy

### Unit Tests

- preset-to-command translation;
- platform path and quoting behavior;
- progress event parsing;
- time estimation, including low-sample and outlier cases;
- dependency state transitions;
- run manifest migration and atomic persistence;
- resumability and artifact validation;
- locale and direction selection.

### Integration Tests

- controlled fake processes for success, warning, failure, stop, and retry;
- end-to-end execution against small fixture documents;
- segmentation review and regeneration;
- interrupted-run recovery;
- dependency detection with mocked platform providers;
- opening verified output paths.

### UI Tests

- English LTR and Persian RTL;
- system, light, and dark themes;
- keyboard navigation and visible focus;
- text scaling;
- long filenames and paths;
- minimum window size, common laptop sizes, and large displays;
- responsive transition of the status panel;
- visual regression snapshots for core screens.

UI behavior uses `pytest-qt`; deterministic screenshots use fixed fonts, scale,
locale, theme, and window size.

### Packaging Tests

The CI matrix uses Windows, Ubuntu, and macOS hosted runners for package launch
and non-browser fixtures. Hosted CI does not prove PyAutoGUI; production support
requires an interactive acceptance run per supported OS.

### Regression Protection

Existing CLI commands and current test fixtures run before and after GUI-related
core changes. GUI tests may not replace CLI regression tests.

## Delivery Sequence

1. Add `run_pipeline.py`, canonical exit codes, and preset contracts.
2. Add JSONL events to participating repositories without changing human CLI.
3. Add manifest v1, integrity validators, and resume invalidation rules.
4. Build the shell together with `.ts/.qm` localization, RTL/LTR, high-DPI,
   responsive tokens, and keyboard foundations.
5. Implement Setup, dependency providers, profile lock, and login probe.
6. Implement PDF and existing-work-directory New Run flows.
7. Implement progress, supported stop controls, and review protocol.
8. Implement Results and History.
9. Add packaging and platform CI.
10. Complete visual, installer, and interactive acceptance tests.

## Acceptance Criteria

- Existing CLI workflows continue to behave as documented.
- A user can install or diagnose dependencies without reading project source.
- A user can complete the full workflow using only the GUI.
- Mind-map generation shows completed count, total count, elapsed time, and a
  calibrated remaining-time estimate when sufficient data exists.
- Interrupted runs resume without regenerating verified completed artifacts.
- Persian mode has correct RTL layout and English mode has correct LTR layout.
- No core screen overlaps or clips at tested minimum and common desktop sizes.
- The packaged application launches on supported Windows, macOS, and Linux CI
  environments.
- Privileged changes never occur without an immediately preceding confirmation.
- ChatGPT credentials are never requested or logged by the application.

## Runtime and Localization Constraints

- One run lock permits one active pipeline across GUI instances.
- Free space must meet `max(1 GiB, 3 × source size)`; below
  `max(5 GiB, 5 × source size)` requires warning confirmation.
- Drag-and-drop always has native Browse fallback.
- Linux X11/Wayland screenshot and input capability is probed before automation.
- UI locale and index language are independent settings.
- Translation sources are Qt `.ts` files compiled to `.qm`.
- Latin paths and filenames use isolated LTR runs inside Persian layouts.
- Version 1 targets WCAG 2.2 AA contrast and keyboard behavior where applicable.

## Design References

The layout and platform rules are grounded in current official guidance:

- [Qt for Python high-DPI support](https://doc.qt.io/qtforpython-6/overviews/qtdoc-highdpi.html)
- [Qt `QProcess`](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QProcess.html)
- [Qt `pyside6-deploy`](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html)
- [Windows responsive design techniques](https://learn.microsoft.com/en-us/windows/apps/design/layout/responsive-design)
- [Windows screen sizes and breakpoints](https://learn.microsoft.com/en-us/windows/apps/design/layout/screen-sizes-and-breakpoints-for-responsive-design)
- [Apple Human Interface Guidelines: Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Apple Human Interface Guidelines: Designing for macOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-macos)
