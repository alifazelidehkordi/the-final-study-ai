"""Primary navigation rail and destination registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QPushButton, QVBoxLayout, QWidget

from gui.tokens import SPACING, ColorTokens


class NavDestination(str, Enum):
    SETUP = "setup"
    NEW_RUN = "new_run"
    PROGRESS = "progress"
    RESULTS = "results"
    HISTORY = "history"


@dataclass(frozen=True)
class NavItem:
    destination: NavDestination
    label: str


NAV_ITEMS: tuple[NavItem, ...] = (
    NavItem(NavDestination.SETUP, "Setup"),
    NavItem(NavDestination.NEW_RUN, "New Run"),
    NavItem(NavDestination.PROGRESS, "Progress"),
    NavItem(NavDestination.RESULTS, "Results"),
    NavItem(NavDestination.HISTORY, "History"),
)


class NavigationRail(QWidget):
    destination_changed = Signal(str)

    def __init__(self, colors: ColorTokens, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colors = colors
        self.setObjectName("navigationRail")
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[NavDestination, QPushButton] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.lg, SPACING.sm, SPACING.lg)
        layout.setSpacing(SPACING.sm)
        for item in NAV_ITEMS:
            button = QPushButton(self)
            button.setObjectName(f"nav-{item.destination.value}")
            button.setCheckable(True)
            button.setProperty("nav_label", item.label)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked, dest=item.destination: self._on_click(dest))
            self._group.addButton(button)
            self._buttons[item.destination] = button
            layout.addWidget(button)
        layout.addStretch(1)
        self._buttons[NavDestination.NEW_RUN].setChecked(True)
        self.retranslate_ui()
        self.refresh_style()

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self.refresh_style()

    def retranslate_ui(self) -> None:
        for button in self._buttons.values():
            label = button.property("nav_label")
            if isinstance(label, str):
                button.setText(self.tr(label))

    def select(self, destination: NavDestination) -> None:
        button = self._buttons[destination]
        button.setChecked(True)

    def _on_click(self, destination: NavDestination) -> None:
        self.destination_changed.emit(destination.value)

    def refresh_style(self) -> None:
        colors = self._colors
        self.setStyleSheet(
            f"""
            #navigationRail {{
                background: {colors.surface};
                border-right: 1px solid {colors.border};
            }}
            QPushButton {{
                text-align: left;
                padding: {SPACING.md}px {SPACING.lg}px;
                border: 1px solid transparent;
                border-radius: 8px;
                background: transparent;
                color: {colors.text};
            }}
            QPushButton:hover {{
                background: {colors.nav_hover};
            }}
            QPushButton:checked {{
                background: {colors.nav_active};
                border-color: {colors.accent};
                color: {colors.text};
            }}
            """
        )