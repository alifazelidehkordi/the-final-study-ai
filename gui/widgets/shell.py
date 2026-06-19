"""Application shell with navigation, workspace, and status regions."""

from __future__ import annotations

from pathlib import Path

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
from gui.pipeline.exit_codes import (
    EXIT_PARTIAL,
    EXIT_REVIEW_REQUIRED,
    EXIT_STOPPED_COOPERATIVE,
    EXIT_SUCCESS,
)
from gui.pipeline.process_controller import PipelineProcessController, PipelineRunState
from gui.pipeline.progress_tracker import ProgressSnapshot
from gui.tokens import SPACING, STATUS_MAX_WIDTH, STATUS_MIN_WIDTH, ColorTokens
from gui.widgets.history_page import HistoryPage
from gui.widgets.new_run_page import NewRunPage
from gui.widgets.progress_page import ProgressPage
from gui.widgets.results_page import ResultsPage
from gui.widgets.review_page import ReviewPage
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
        if self._body.text() == "" or "will appear here" in self._body.text().lower():
            self._body.setText(
                self.tr("Pipeline activity and readiness information will appear here.")
            )

    def set_summary(self, text: str) -> None:
        self._body.setText(text)

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
        self._pipeline_controller.run_finished.connect(self._handle_run_finished)

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
                page.event_watcher().snapshot_updated.connect(self._update_status_from_snapshot)
            elif item.destination == NavDestination.RESULTS:
                page = ResultsPage(colors, self._workspace_host)
            elif item.destination == NavDestination.HISTORY:
                page = HistoryPage(colors, self._workspace_host)
                page.open_results_requested.connect(self._open_results_for_manifest)
                page.resume_requested.connect(self._resume_from_manifest)
            else:
                raise ValueError(f"Unhandled destination: {item.destination}")
            self._pages[item.destination] = page
            self._workspace_layout.addWidget(page)
            page.setVisible(item.destination == NavDestination.NEW_RUN)

        self._review_page = ReviewPage(colors, self._pipeline_controller, self._workspace_host)
        self._review_page.review_action_requested.connect(self._on_review_action)
        self._review_page.hide()
        self._workspace_layout.addWidget(self._review_page)

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
        self._review_page.set_colors(colors)

    def layout_state(self) -> LayoutState:
        return layout_state_for_width(self.width())

    def retranslate_ui(self) -> None:
        self.setWindowTitle(self.tr("The Final Study AI"))
        self._navigation.retranslate_ui()
        self._status.retranslate_ui()
        for page in self._pages.values():
            if hasattr(page, "retranslate_ui"):
                page.retranslate_ui()
        self._review_page.retranslate_ui()

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self._apply_layout_state(layout_state_for_width(self.width()))

    def _show_destination(self, destination_value: str) -> None:
        destination = NavDestination(destination_value)
        self._review_page.hide()
        for key, page in self._pages.items():
            page.setVisible(key == destination)
        if destination == NavDestination.HISTORY:
            history = self._pages[NavDestination.HISTORY]
            if isinstance(history, HistoryPage):
                history.refresh_runs()

    def _on_run_started(self, _command: object) -> None:
        self._navigation.select(NavDestination.PROGRESS)
        self._show_destination(NavDestination.PROGRESS.value)

    def _handle_run_finished(self, exit_code: int, state: PipelineRunState | None) -> None:
        history = self._pages.get(NavDestination.HISTORY)
        if isinstance(history, HistoryPage):
            history.refresh_runs()
        if state is None:
            return
        if exit_code == EXIT_REVIEW_REQUIRED:
            self._show_review(state.manifest_file)
            return
        if exit_code in (EXIT_SUCCESS, EXIT_PARTIAL):
            self._open_results_for_manifest(state.manifest_file)
            return
        if exit_code == EXIT_STOPPED_COOPERATIVE:
            self._status.set_summary(self.tr("Run stopped cooperatively at an item boundary."))

    def _show_review(self, manifest_path: Path) -> None:
        for page in self._pages.values():
            page.hide()
        self._review_page.load_manifest(manifest_path)

    def _on_review_action(self, command: object) -> None:
        self._review_page.hide()
        if command is None:
            self._navigation.select(NavDestination.HISTORY)
            self._show_destination(NavDestination.HISTORY.value)
            return
        self._on_run_started(command)

    def _open_results_for_manifest(self, manifest_path: Path) -> None:
        results = self._pages.get(NavDestination.RESULTS)
        if isinstance(results, ResultsPage):
            results.show_run(manifest_path)
        self._navigation.select(NavDestination.RESULTS)
        self._show_destination(NavDestination.RESULTS.value)

    def _resume_from_manifest(self, manifest_path: Path) -> None:
        from gui.pipeline.contracts_bridge import load_run_manifest
        from gui.pipeline.resume_adapter import build_resume_command

        try:
            manifest = load_run_manifest(manifest_path)
            if manifest.get("status") == "awaiting_review":
                self._show_review(manifest_path)
                return
            command = build_resume_command(manifest_path)
            self._pipeline_controller.start(command)
            self._on_run_started(command)
        except (OSError, RuntimeError, ValueError) as exc:
            self._status.set_summary(str(exc))

    def _update_status_from_snapshot(self, snapshot: ProgressSnapshot) -> None:
        if snapshot.item_total:
            items = f"{snapshot.completed_items}/{snapshot.item_total}"
        else:
            items = str(snapshot.completed_items)
        self._status.set_summary(
            f"{snapshot.stage_label}\n{snapshot.current_operation}\n"
            f"{self.tr('Items')}: {items}\n{snapshot.eta_label}"
        )

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
