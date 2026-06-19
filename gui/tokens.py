"""Design tokens shared across light and dark themes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorTokens:
    window: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_muted: str
    danger: str
    nav_active: str
    nav_hover: str


@dataclass(frozen=True)
class SpacingTokens:
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32


@dataclass(frozen=True)
class TypographyTokens:
    app_title_px: int = 20
    section_title_px: int = 16
    body_px: int = 13
    caption_px: int = 11
    font_family: str = "Segoe UI"


LIGHT_COLORS = ColorTokens(
    window="#f3f4f6",
    surface="#ffffff",
    surface_alt="#eef1f5",
    border="#d5dbe3",
    text="#111827",
    text_muted="#5b6472",
    accent="#1f8f5f",
    accent_muted="#d8f3e7",
    danger="#b42318",
    nav_active="#e7f6ef",
    nav_hover="#f8fafc",
)

DARK_COLORS = ColorTokens(
    window="#101218",
    surface="#171b24",
    surface_alt="#1f2430",
    border="#2a3140",
    text="#eef2f7",
    text_muted="#9aa3b2",
    accent="#3ecf8e",
    accent_muted="#173528",
    danger="#f97066",
    nav_active="#1c2b24",
    nav_hover="#202633",
)

SPACING = SpacingTokens()
TYPOGRAPHY = TypographyTokens()

MIN_WINDOW_WIDTH = 1024
MIN_WINDOW_HEIGHT = 700
WIDE_BREAKPOINT = 1280
NAV_RAIL_WIDTH = 88
STATUS_MIN_WIDTH = 240
STATUS_MAX_WIDTH = 320