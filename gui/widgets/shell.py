"""Application shell with navigation, workspace, and status regions."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui.layout import LayoutState, layout_state_for_width, minimum_window_size
from gui.navigation import NAV_ITEMS, NavDestination, NavigationRail
from gui.pipeline.process_controller import PipelineProcessController
from gui.tokens import SPACING, STATUS_MAX_WIDTH, STATUS_MIN_WIDTH, ColorTokens
from gui.widgets.new_run_page import NewRunPage
from gui.widgets.path_label import PathLabel
from gui.widgets.progress_page import ProgressPage
from gui.widgets.setup_page import SetupPage

_SCREEN_COPY: dict[NavDestination, tuple[str, str]] = {
    NavDestination.SETUP: (
        "Dependency Setup",
        "Check Python, PDF conversion, browser automation, and mind-map tooling.",
    ),
    NavDestination.NEW_RUN: (
        "Start a New Run",
        "Choose a PDF, output folder, and preset to begin the study pipeline.",
    ),
    NavDestination.PROGRESS: (
        "Run Progress",
        "Track stage status, item counts, and recent pipeline activity.",
    ),
    NavDestination.RESULTS: (
        "Results",
        "Open validated Markdown, index, OPML, and XMind outputs.",
    ),
    NavDestination.HISTORY: (
        "Run History",
        "Review completed, stopped, and resumable runs.",
    ),
}


class _WorkspacePage(QWidget):
    def __init__(
        self,
        destination: NavDestination,
        colors: ColorTokens,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._destination = destination
        self._colors = colors
        self.setObjectName(f"workspace-{destination.value}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)
        self._title = QLabel(self)
        self._title.setObjectName("workspaceTitle")
        self._subtitle = QLabel(self)
        self._subtitle.setObjectName("workspaceSubtitle")
        self._subtitle.setWordWrap(True)
        self._path = PathLabel("/home/student/book_work/STUDY_INDEX.pdf", self)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._path)
        layout.addStretch(1)
        self.refresh_style()
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        title, subtitle = _SCREEN_COPY[self._destination]
        self._title.setText(self.tr(title))
        self._subtitle.setText(self.tr(subtitle))

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self.refresh_style()

    def refresh_style(self) -> None:
        colors = self._colors
        self._title.setStyleSheet(
            f"font-size: 20px; font-weight: 600; color: {colors.text};"
        )
        self._subtitle.setStyleSheet(f"color: {colors.text_muted};")


class _StatusPanel(QFrame):
    def __init__(self, colors: ColorTokens, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colors = colors
        self.setObjectName("statusPanel")
        self.setMinimumWidth(STATUS_MIN_WIDTH)
        self.setMaximumWidth(STATUS_MAX_WIDTH)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.sm)
        self._title = QLabel(self)
        self._title.setObjectName("statusTitle")
        self._body = QLabel(self)
        self._body.setObjectName("statusBody")
        self._body.setWordWrap(True)
        layout.addWidget(self._title)
        layout.addWidget(self._body)
        layout.addStretch(1)
        self.refresh_style()
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self._title.setText(self.tr("Status"))
        self._body.setText(
            self.tr("Pipeline activity and readiness information will appear here.")
        )

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self.refresh_style()

    def refresh_style(self) -> None:
        colors = self._colors
        self.setStyleSheet(
            f"""
            #statusPanel {{
                background: {colors.surface};
                border: 1px solid {colors.border};
                border-radius: 12px;
            }}
            """
        )
        self._title.setStyleSheet(f"font-weight: 600; color: {colors.text};")
        self._body.setStyleSheet(f"color: {colors.text_muted};")


class MainShell(QMainWindow):
    def __init__(self, colors: ColorTokens, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colors = colors
        self.setObjectName("mainShell")
        min_width, min_height = minimum_window_size()
        self.setMinimumSize(min_width, min_height)
        self.resize(1280, 760)

        self._root = QWidget(self)
        self._root_layout = QVBoxLayout(self._root)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        self._content_row = QWidget(self._root)
        self._content_layout = QHBoxLayout(self._content_row)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        self._pipeline_controller = PipelineProcessController(self)

        self._navigation = NavigationRail(colors, self._content_row)
        self._navigation.destination_changed.connect(self._show_destination)

        self._workspace_scroll = QScrollArea(self._content_row)
        self._workspace_scroll.setObjectName("workspaceScroll")
        self._workspace_scroll.setWidgetResizable(True)
        self._workspace_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._workspace_host = QWidget()
        self._workspace_host.setObjectName("workspaceHost")
        self._workspace_layout = QVBoxLayout(self._workspace_host)
        self._workspace_layout.setContentsMargins(0, 0, 0, 0)
        self._workspace_scroll.setWidget(self._workspace_host)

        self._pages: dict[NavDestination, QWidget] = {}
        for item in NAV_ITEMS:
            if item.destination == NavDestination.SETUP:
                page: QWidget = SetupPage(colors, self._workspace_host)
            elif item.destination == NavDestination.NEW_RUN:
                page = NewRunPage(colors, self._pipeline_controller, self._workspace_host)
                page.run_started.connect(self._on_run_started)
            elif item.destination == NavDestination.PROGRESS:
                page = ProgressPage(colors, self._pipeline_controller, self._workspace_host)
            else:
                page = _WorkspacePage(item.destination, colors, self._workspace_host)
            self._pages[item.destination] = page
            self._workspace_layout.addWidget(page)
            page.setVisible(item.destination == NavDestination.NEW_RUN)

        self._status = _StatusPanel(colors, self._content_row)

        self._content_layout.addWidget(self._navigation)
        self._content_layout.addWidget(self._workspace_scroll, stretch=1)
        self._content_layout.addWidget(self._status)

        self._root_layout.addWidget(self._content_row)
        self.setCentralWidget(self._root)
        self._apply_layout_state(layout_state_for_width(self.width()))
        self.retranslate_ui()

    def colors(self) -> ColorTokens:
        return self._colors

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self._navigation.set_colors(colors)
        self._status.set_colors(colors)
        for page in self._pages.values():
            if hasattr(page, "set_colors"):
                page.set_colors(colors)

    def layout_state(self) -> LayoutState:
        return layout_state_for_width(self.width())

    def retranslate_ui(self) -> None:
        self.setWindowTitle(self.tr("The Final Study AI"))
        self._navigation.retranslate_ui()
        self._status.retranslate_ui()
        for page in self._pages.values():
            if hasattr(page, "retranslate_ui"):
                page.retranslate_ui()

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self._apply_layout_state(layout_state_for_width(self.width()))

    def _show_destination(self, destination_value: str) -> None:
        destination = NavDestination(destination_value)
        for key, page in self._pages.items():
            page.setVisible(key == destination)

    def _on_run_started(self, _command: object) -> None:
        self._navigation.select(NavDestination.PROGRESS)
        self._show_destination(NavDestination.PROGRESS.value)

    def _apply_layout_state(self, state: LayoutState) -> None:
        self.setProperty("layoutState", state.value)
        if state == LayoutState.RECOVERY:
            self._content_layout.removeWidget(self._status)
            self._root_layout.removeWidget(self._content_row)
            self._root_layout.addWidget(self._content_row, stretch=1)
            self._root_layout.addWidget(self._status)
            self._status.setMaximumWidth(16777215)
            self._status.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            self._navigation.setMaximumWidth(64)
        else:
            if self._status.parent() is self._root:
                self._root_layout.removeWidget(self._status)
                self._content_layout.addWidget(self._status)
            self._status.setMinimumWidth(STATUS_MIN_WIDTH)
            self._status.setMaximumWidth(STATUS_MAX_WIDTH)
            self._status.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
            nav_width = 88 if state == LayoutState.WIDE else 72
            self._navigation.setFixedWidth(nav_width)