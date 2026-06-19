"""Responsive layout states derived from window width."""

from __future__ import annotations

from enum import Enum

from gui.tokens import MIN_WINDOW_HEIGHT, MIN_WINDOW_WIDTH, WIDE_BREAKPOINT


class LayoutState(str, Enum):
    WIDE = "wide"
    COMPACT = "compact"
    RECOVERY = "recovery"


def layout_state_for_width(width: int) -> LayoutState:
    if width >= WIDE_BREAKPOINT:
        return LayoutState.WIDE
    if width >= MIN_WINDOW_WIDTH:
        return LayoutState.COMPACT
    return LayoutState.RECOVERY


def minimum_window_size() -> tuple[int, int]:
    return MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT