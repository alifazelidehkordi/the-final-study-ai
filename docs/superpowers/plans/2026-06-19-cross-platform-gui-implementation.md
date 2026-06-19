# Cross-Platform GUI Implementation Plan

## Approach

Build the cross-platform execution contracts before the visual shell, then
connect the PySide6 application only to stable JSONL events, manifests, and
validated artifacts. Preserve the existing CLI through compatibility wrappers
and enable each operating system only after its release gate passes.

## Scope

- In:
  - Cross-platform Python orchestration and legacy CLI compatibility.
  - Versioned progress events, run manifests, integrity validation, and resume.
  - Required event/stop support in `chatgpt-mindmap-to-xmind`.
  - PySide6 GUI with Setup, New Run, Progress, Review, Results, and History.
  - Persian/English localization, RTL/LTR, high-DPI, themes, and accessibility.
  - Dependency management and interactive ChatGPT login/profile checks.
  - Windows, Linux, and macOS packaging and release validation.
- Out:
  - Multiple-PDF queues, cloud sync, embedded editors, mobile/web clients.
  - macOS mind-map support before its interactive automation gate passes.
  - Silent privileged installation or storage of ChatGPT credentials.

## Action Items

- [ ] 1. Add the cross-platform orchestration foundation.
  - Create `scripts/run_pipeline.py` with canonical presets, stages, exit codes,
    `--event-file`, `--start-at`, `--stop-after`, `--rerun`, and `--resume`.
  - Convert `scripts/run_pipeline.sh` into a backward-compatible wrapper and add
    a Windows wrapper only if useful for direct CLI users.
  - Add tests for legacy-flag mapping, paths containing spaces/non-ASCII text,
    environment discovery, and review exit code `20`.

- [ ] 2. Implement shared contracts and durable state.
  - Add focused modules for JSONL event writing/reading, Run Manifest v1,
    atomic persistence, stable error codes, tool-version fingerprints, and run
    locking.
  - Add JSON Schema files for events, run manifests, and
    `parts-manifest.json`.
  - Test truncated event lines, sequence ordering, incompatible schema versions,
    crash recovery, and concurrent-run rejection.

- [ ] 3. Make conversion and segmentation resumable and observable.
  - Add event emission and artifact hashing around PDF conversion.
  - Extend `segment_markdown_study_parts.py` to emit events and atomically write
    `parts-manifest.json` with ordered parts, page ranges, options, and hashes.
  - Implement Markdown, parts, index Markdown, and index PDF validators.
  - Preserve existing human CLI output and existing segmentation behavior.

- [ ] 4. Upgrade the mind-map dependency contract.
  - Add compatible `--event-file`, run ID, and stop-file support to
    `chatgpt-mindmap-to-xmind/scripts/pipeline.py`, `batch_pdf.py`,
    `batch_markdown.py`, and `convert_opml_batch.py`.
  - Emit item start/retry/skip/complete/failure events only after OPML/XMind
    validation.
  - Check cooperative stop immediately before each new item and retain immediate
    process-tree termination as the fallback.
  - Add OPML and XMind validators plus tests for partial download, invalid ZIP,
    retry, stop-after-item, and resume.

- [ ] 5. Build the PySide6 application foundation.
  - Create the `gui/` package with application bootstrap, settings, navigation,
    design tokens, system/light/dark themes, and responsive layout states.
  - Add Qt `.ts`/`.qm` localization from the first screen and implement true
    Persian RTL with isolated LTR paths and filenames.
  - Add `pytest-qt` coverage and deterministic screenshots for `1024×700`,
    compact, and wide layouts at normal and fractional scale factors.

- [ ] 6. Implement Setup and dependency management.
  - Add platform providers for Python/tool environments, PDF conversion, OCR,
    mind-map checkout/packages, Chrome/Chromium, and Linux desktop capability.
  - Add app-managed tool directories, pinned-version installation plans,
    license disclosure, explicit privilege confirmation, repair, and manual
    fallback instructions.
  - Implement the exclusive browser-profile lock and visible Selenium login
    probe without cookie inspection.

- [ ] 7. Implement New Run and process orchestration.
  - Build PDF drag-and-drop/native Browse, output selection, preset cards,
    validation, free-space checks, and Advanced options.
  - Give Mind Maps Only its distinct existing-work-directory source flow.
  - Connect `QProcess` to `run_pipeline.py` using argument arrays and expose only
    presets supported by current dependency/platform health.

- [ ] 8. Implement operational screens and recovery.
  - Build Progress from JSONL events with stage/item counts, elapsed time,
    robust ETA, recent activity, logs, Stop Now, and conditional Stop After
    Current Item.
  - Build Segmentation Review around exit `20`, including approve,
    finer/coarser regeneration, and explicit replacement impact.
  - Build Results and History from validated manifests, including retry,
    compatible resume, changed-artifact warnings, and native open actions.

- [ ] 9. Complete cross-platform packaging and CI.
  - Add locked source-install instructions and `pyside6-deploy` configuration.
  - Add Windows, Ubuntu, and macOS CI jobs for linting, unit/integration/UI tests,
    packaging, launch smoke tests, resource loading, and fixture workflows.
  - Record artifact sizes; require Windows signing and macOS
    signing/notarization only for public production releases.

- [ ] 10. Run release qualification and documentation.
  - Execute existing CLI regression tests plus full GUI tests on all platforms.
  - Perform interactive browser-automation acceptance on supported Windows and
    Linux sessions; test X11 and explicitly qualify or reject Wayland.
  - Keep macOS mind-map presets unavailable until permissions and complete
    interactive automation pass.
  - Update English/Persian README files, setup/troubleshooting documentation,
    release notes, and final support matrix.

## Validation

- Existing v0.1.0 CLI commands retain documented behavior.
- JSONL events and manifests validate against versioned schemas.
- Review, partial failure, cooperative stop, immediate interruption, and resume
  are covered by integration fixtures.
- Artifact validators reject malformed Markdown, OPML, index PDF, and XMind.
- Core screens pass interaction, keyboard, RTL/LTR, theme, high-DPI, and visual
  regression tests without clipping or overlap.
- Packaged applications launch on all CI platforms; browser automation is
  enabled only after the corresponding interactive release gate passes.

## Open Questions

- None blocking. Exact pinned commits and package hashes will be selected during
  implementation and recorded in the compatibility manifest.
