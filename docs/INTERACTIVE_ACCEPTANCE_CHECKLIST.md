# Interactive Browser-Automation Acceptance Checklist

Use this checklist before enabling **Complete Study Pack** and **Mind Maps Only**
for public release on a given OS. Hosted CI cannot perform these steps.

**Fixture PDF:** small study PDF with valid `parts/` after segmentation  
**Mind-map project:** `chatgpt-mindmap-to-xmind` @ `feature/pipeline-events`

## Preconditions

- [ ] Setup reports Ready: Python, PySide6, PDF conversion, mind-map project, packages, Chrome, profile/login
- [ ] Linux only: X11 session (`echo $DISPLAY`, `echo $XDG_SESSION_TYPE=x11`)
- [ ] macOS only: Accessibility + Screen Recording granted to terminal/app
- [ ] Visible login probe succeeds from Setup

## Windows

- [ ] Launch `python -m gui` on a logged-in desktop session
- [ ] Complete Study Pack: segmentation review appears (exit `20`)
- [ ] Approve review → mind-map stage shows item progress
- [ ] Stop After Current Item stops at part boundary (exit `21`)
- [ ] Results open OPML and XMind natively
- [ ] History lists the run with correct status

## Linux (X11)

- [ ] Same as Windows on Ubuntu/X11 or XWayland with `DISPLAY` set
- [ ] `scrot` capture works during mind-map stage
- [ ] Profile lock prevents overlapping Setup probe and active run

## Linux (Wayland) — expected rejection

- [ ] GUI launches
- [ ] Complete and Mind Maps Only presets remain blocked in New Run
- [ ] Markdown & Index preset still works

## macOS — expected rejection until pass

- [ ] GUI launches and Markdown & Index works
- [ ] Complete / Mind Maps Only remain blocked until all macOS rows below pass
- [ ] Selenium launches with app-managed profile
- [ ] PyAutoGUI input works with granted permissions
- [ ] Full Complete preset completes one limited mind-map part

## Sign-off

| OS | Tester | Date | Result |
|---|---|---|---|
| Windows | | | |
| Linux X11 | | | |
| Linux Wayland | | | N/A — automation blocked |
| macOS | | | |