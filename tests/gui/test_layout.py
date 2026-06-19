from __future__ import annotations

from gui.layout import LayoutState, layout_state_for_width, minimum_window_size


def test_minimum_window_size_matches_contract() -> None:
    assert minimum_window_size() == (1024, 700)


def test_layout_state_breakpoints() -> None:
    assert layout_state_for_width(1400) == LayoutState.WIDE
    assert layout_state_for_width(1280) == LayoutState.WIDE
    assert layout_state_for_width(1100) == LayoutState.COMPACT
    assert layout_state_for_width(1024) == LayoutState.COMPACT
    assert layout_state_for_width(900) == LayoutState.RECOVERY