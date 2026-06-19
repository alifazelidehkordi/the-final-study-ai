# Cross-Platform GUI Design

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
- Pause/stop at supported safe boundaries, retry, and resume.
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

#### Process Controller

Uses `QProcess` to start and monitor external programs without blocking the UI.
Arguments are passed as separate values rather than shell-concatenated strings.
The controller streams standard output and error, reports process state, and
maps exit codes into structured results.

The controller must not execute the full pipeline through a Unix-only shell on
Windows. Platform-neutral Python entry points will be introduced where needed,
while the existing shell scripts remain supported for current CLI users.

#### Progress Parser

Converts pipeline events or recognizable output lines into structured state:

- active stage;
- completed and total items;
- current item;
- elapsed time;
- estimated remaining time;
- warning or failure details;
- output artifacts discovered.

Where current scripts do not expose reliable progress, they will gain a
backward-compatible machine-readable event stream. Plain human-readable output
will remain available.

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

The initial window has a practical laptop-oriented minimum size. Platform
window chrome and text scaling are included in layout testing.

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

The screen also launches the dedicated browser profile so the user can log into
ChatGPT manually. Login state is detected but credentials are never collected.

#### 2. New Run

Contains:

- a large drag-and-drop PDF target with a native Browse action;
- selected-file metadata and validation;
- output-directory selection;
- preset cards;
- a single primary Start action;
- a collapsed Advanced section for granularity, limits, overwrite behavior,
  custom tool paths, and diagnostics.

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
- safe Stop/Pause and Retry actions when applicable.

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

The packaged GUI includes its own Python/Qt runtime. Large external systems,
browser automation assets, and OS-level dependencies are detected and installed
or linked through Setup rather than being silently bundled without validation.

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

- A safe stop asks the current tool to terminate gracefully, waits for a bounded
  period, then offers forced termination with a warning.
- Completed artifacts are retained.
- A run is resumable only at explicit stage or item boundaries.
- Resume skips outputs that pass integrity checks; existence alone is not
  sufficient.
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

### Packaging Tests

Each platform CI job launches the packaged application, checks bundled resource
loading, runs dependency diagnostics, and executes a fixture workflow without
browser automation. Browser automation receives a separate smoke test where a
valid local test profile is available.

### Regression Protection

Existing CLI commands and current test fixtures run before and after GUI-related
core changes. GUI tests may not replace CLI regression tests.

## Delivery Sequence

1. Introduce machine-readable pipeline progress while preserving CLI output.
2. Add run manifests, artifact validation, and resume rules.
3. Build the PySide6 application shell and responsive design tokens.
4. Implement Setup and dependency providers.
5. Implement New Run and process orchestration.
6. Implement Progress and segmentation review.
7. Implement Results and History.
8. Add localization, RTL, theme behavior, and accessibility checks.
9. Add native packaging and platform CI.
10. Complete visual regression, installer, and end-to-end acceptance tests.

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

## Design References

The layout and platform rules are grounded in current official guidance:

- [Qt for Python high-DPI support](https://doc.qt.io/qtforpython-6/overviews/qtdoc-highdpi.html)
- [Qt `QProcess`](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QProcess.html)
- [Qt `pyside6-deploy`](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html)
- [Windows responsive design techniques](https://learn.microsoft.com/en-us/windows/apps/design/layout/responsive-design)
- [Windows screen sizes and breakpoints](https://learn.microsoft.com/en-us/windows/apps/design/layout/screen-sizes-and-breakpoints-for-responsive-design)
- [Apple Human Interface Guidelines: Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Apple Human Interface Guidelines: Designing for macOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-macos)
