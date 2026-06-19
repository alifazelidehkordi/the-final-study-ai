# GUI Source Installation

Use this guide to run **The Final Study AI** desktop GUI from source on Windows,
Ubuntu/Linux, or macOS without a packaged build.

## Requirements

- Python **3.10–3.13** (see `schemas/compatibility-manifest-v1.json`)
- Git
- A working PDF conversion checkout and mind-map project for full pipeline runs
  (the GUI launches without them, but presets will be gated in Setup)

## Locked install

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements/dev-lock.txt
```

Runtime-only install (no linters/tests):

```bash
python -m pip install -r requirements/gui-lock.txt
```

## Launch

```bash
source .venv/bin/activate
export QT_QPA_PLATFORM=offscreen   # optional: headless smoke only
python -m gui
```

Developer quality gates:

```bash
bash scripts/ci/run_quality_gates.sh
```

## Packaging (native host only)

Build on the same operating system you are targeting. Cross-compiling is not
supported.

```bash
source .venv/bin/activate
pyside6-deploy gui/__main__.py \
  -c packaging/pysidedeploy.spec \
  --keep-deployment-files \
  -f
python scripts/ci/record_package_sizes.py
```

Outputs land in `dist/` and `gui/deployment/`. The compressed-size budget is
**≤ 180 MiB** for internal builds. Public Windows/macOS releases require
signing/notarization credentials outside this repository.

## Related docs

- Support matrix: [`SUPPORT_MATRIX.md`](SUPPORT_MATRIX.md)
- Troubleshooting: [`GUI_TROUBLESHOOTING.md`](GUI_TROUBLESHOOTING.md)
- Release notes: [`RELEASE_NOTES_v0.2.0-gui.md`](RELEASE_NOTES_v0.2.0-gui.md)
- Qualification report: [`RELEASE_QUALIFICATION_v0.2.0-gui.md`](RELEASE_QUALIFICATION_v0.2.0-gui.md)

## Notes

- Persian translations ship as `gui/resources/translations/app_fa.qm`.
- Recompile `.ts` files with `pyside6-lrelease gui/resources/translations/app_fa.ts`
  after editing translations.
- Browser automation and mind-map presets remain unavailable until Setup reports
  the corresponding dependencies as Ready.