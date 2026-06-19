from __future__ import annotations

import os
from pathlib import Path

import pytest

from gui.layout import LayoutState
from gui.tokens import DARK_COLORS, LIGHT_COLORS
from gui.widgets.shell import MainShell

SCREENSHOT_ROOT = Path(__file__).resolve().parents[2] / "tests" / "gui" / "screenshots"


@pytest.mark.parametrize(
    ("width", "height", "theme_name", "colors", "layout"),
    [
        (1280, 760, "light-wide", LIGHT_COLORS, LayoutState.WIDE),
        (1100, 760, "light-compact", LIGHT_COLORS, LayoutState.COMPACT),
        (960, 760, "light-recovery", LIGHT_COLORS, LayoutState.RECOVERY),
        (1280, 760, "dark-wide", DARK_COLORS, LayoutState.WIDE),
    ],
)
def test_shell_deterministic_screenshot(
    qtbot,
    qapp,
    width: int,
    height: int,
    theme_name: str,
    colors,
    layout: LayoutState,
    request: pytest.FixtureRequest,
) -> None:
    if os.environ.get("GENERATE_GUI_SCREENSHOTS") != "1":
        pytest.skip("Set GENERATE_GUI_SCREENSHOTS=1 to refresh PNG fixtures.")

    window = MainShell(colors)
    qtbot.addWidget(window)
    window.set_colors(colors)
    if layout == LayoutState.RECOVERY:
        window.setMinimumWidth(0)
    window.resize(width, height)
    if layout == LayoutState.RECOVERY:
        window._apply_layout_state(LayoutState.RECOVERY)
    window.show()
    qtbot.waitExposed(window)
    assert window.layout_state() == layout

    output_dir = SCREENSHOT_ROOT / request.node.name
    output_dir.mkdir(parents=True, exist_ok=True)
    image = window.grab()
    image.save(str(output_dir / f"{theme_name}-{width}x{height}.png"))
    assert image.width() == width
    assert image.height() == height


def test_shell_fractional_scale_fixture(qtbot, qapp, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QT_SCALE_FACTOR", "1.25")
    window = MainShell(LIGHT_COLORS)
    qtbot.addWidget(window)
    window.resize(1024, 700)
    window.show()
    qtbot.waitExposed(window)
    assert window.minimumWidth() == 1024
    assert window.minimumHeight() == 700