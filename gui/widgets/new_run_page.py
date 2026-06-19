"""New Run screen with presets, validation, and pipeline launch."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from gui.dependencies.registry import DependencyRegistry
from gui.pipeline.adapter import build_pipeline_command
from gui.pipeline.models import AdvancedOptions, RunPreset, RunRequest
from gui.pipeline.process_controller import PipelineProcessController
from gui.pipeline.validation import ValidationIssue, ValidationSeverity, validate_run_request
from gui.tokens import SPACING, ColorTokens
from gui.widgets.path_label import PathLabel

_PRESET_COPY: dict[RunPreset, tuple[str, str]] = {
    RunPreset.COMPLETE: (
        "Complete Study Pack",
        "PDF to Markdown, segmentation, review gate, and mind maps.",
    ),
    RunPreset.MARKDOWN_INDEX: (
        "Markdown & Index",
        "Convert and segment the PDF, then stop after the study index is ready.",
    ),
    RunPreset.MINDMAPS_ONLY: (
        "Mind Maps Only",
        "Generate OPML and XMind files from an existing segmented work directory.",
    ),
}


class _PresetCard(QFrame):
    def __init__(
        self,
        preset: RunPreset,
        colors: ColorTokens,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.preset = preset
        self._colors = colors
        self.setObjectName(f"presetCard-{preset.value}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.xs)
        self._title = QLabel(self)
        self._title.setObjectName("presetTitle")
        self._description = QLabel(self)
        self._description.setWordWrap(True)
        self._blocker = QLabel(self)
        self._blocker.setWordWrap(True)
        self._blocker.hide()
        layout.addWidget(self._title)
        layout.addWidget(self._description)
        layout.addWidget(self._blocker)
        self.refresh_style()

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self.refresh_style()

    def retranslate_ui(self) -> None:
        title, description = _PRESET_COPY[self.preset]
        self._title.setText(self.tr(title))
        self._description.setText(self.tr(description))

    def set_blocked(self, message: str | None) -> None:
        blocked = bool(message)
        self.setEnabled(not blocked)
        if message:
            self._blocker.setText(message)
            self._blocker.show()
        else:
            self._blocker.hide()

    def refresh_style(self) -> None:
        colors = self._colors
        self.setStyleSheet(
            f"""
            QFrame {{
                border: 1px solid {colors.border};
                border-radius: 12px;
                background: {colors.surface};
            }}
            QFrame:disabled {{
                background: {colors.surface_alt};
            }}
            #presetTitle {{
                font-weight: 600;
                color: {colors.text};
            }}
            """
        )
        self._description.setStyleSheet(f"color: {colors.text_muted};")
        self._blocker.setStyleSheet(f"color: {colors.danger}; font-size: 11px;")


class _DropTarget(QFrame):
    path_selected = Signal(str)

    def __init__(self, colors: ColorTokens, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colors = colors
        self.setAcceptDrops(True)
        self.setObjectName("dropTarget")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.sm)
        self._headline = QLabel(self)
        self._hint = QLabel(self)
        self._hint.setWordWrap(True)
        self._path = PathLabel("", self)
        browse_row = QHBoxLayout()
        self._browse_button = QPushButton(self)
        self._browse_button.clicked.connect(self._browse)
        browse_row.addWidget(self._browse_button)
        browse_row.addStretch(1)
        layout.addWidget(self._headline)
        layout.addWidget(self._hint)
        layout.addWidget(self._path)
        layout.addLayout(browse_row)
        self.refresh_style()
        self.retranslate_ui()

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        self.refresh_style()

    def retranslate_ui(self) -> None:
        self._headline.setText(self.tr("Drop a PDF here"))
        self._hint.setText(self.tr("Or use Browse to choose a file from your computer."))
        self._browse_button.setText(self.tr("Browse…"))

    def set_mode(self, *, pdf: bool) -> None:
        if pdf:
            self._headline.setText(self.tr("Drop a PDF here"))
            self._hint.setText(self.tr("Or use Browse to choose a file from your computer."))
        else:
            self._headline.setText(self.tr("Choose an existing work directory"))
            self._hint.setText(
                self.tr("The folder must already contain parts/ and parts-manifest.json.")
            )

    def set_path(self, path: str) -> None:
        self._path.set_path(path)

    def dragEnterEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        urls = event.mimeData().urls()
        if not urls:
            return
        local = urls[0].toLocalFile()
        if local:
            self.path_selected.emit(local)
            event.acceptProposedAction()

    def _browse(self) -> None:
        self.path_selected.emit("")

    def refresh_style(self) -> None:
        colors = self._colors
        self.setStyleSheet(
            f"""
            #dropTarget {{
                border: 1px dashed {colors.border};
                border-radius: 12px;
                background: {colors.surface_alt};
            }}
            """
        )
        self._headline.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {colors.text};")
        self._hint.setStyleSheet(f"color: {colors.text_muted};")


class NewRunPage(QWidget):
    run_started = Signal(object)

    def __init__(
        self,
        colors: ColorTokens,
        controller: PipelineProcessController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._colors = colors
        self._controller = controller
        self._registry = DependencyRegistry()
        self._preset = RunPreset.COMPLETE
        self._pdf_path: Path | None = None
        self._work_dir: Path | None = None
        self._output_parent: Path | None = None
        self._custom_work_dir_path: Path | None = None
        self.setObjectName("newRunPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)

        self._title = QLabel(self)
        self._title.setObjectName("newRunTitle")
        self._subtitle = QLabel(self)
        self._subtitle.setWordWrap(True)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(SPACING.md)
        self._preset_cards: dict[RunPreset, _PresetCard] = {}
        for preset in RunPreset:
            card = _PresetCard(preset, colors, self)
            card.mousePressEvent = self._make_preset_handler(preset, card.mousePressEvent)  # type: ignore[method-assign]
            self._preset_cards[preset] = card
            preset_row.addWidget(card, stretch=1)
        layout.addLayout(preset_row)

        self._drop_target = _DropTarget(colors, self)
        self._drop_target.path_selected.connect(self._on_source_pick_requested)
        layout.addWidget(self._drop_target)

        output_row = QHBoxLayout()
        self._output_label = QLabel(self)
        self._output_path = PathLabel("", self)
        self._output_button = QPushButton(self)
        self._output_button.clicked.connect(self._choose_output_parent)
        output_row.addWidget(self._output_label)
        output_row.addWidget(self._output_path, stretch=1)
        output_row.addWidget(self._output_button)
        layout.addLayout(output_row)

        self._validation = QLabel(self)
        self._validation.setWordWrap(True)
        self._validation.hide()
        layout.addWidget(self._validation)

        self._advanced = QGroupBox(self)
        advanced_layout = QFormLayout(self._advanced)
        self._granularity = QComboBox(self._advanced)
        self._granularity.addItems(["fine", "normal", "coarse"])
        self._granularity.setCurrentText("normal")
        self._ocr = QComboBox(self._advanced)
        self._ocr.addItems(["off", "auto"])
        self._index_language = QComboBox(self._advanced)
        self._index_language.setEditable(True)
        self._index_language.addItems(["Persian", "English"])
        self._limit = QSpinBox(self._advanced)
        self._limit.setMinimum(0)
        self._limit.setSpecialValueText(self.tr("No limit"))
        self._limit.setValue(0)
        self._overwrite = QCheckBox(self._advanced)
        self._custom_work_dir = PathLabel("", self._advanced)
        self._custom_work_button = QPushButton(self._advanced)
        self._custom_work_button.clicked.connect(self._choose_custom_work_dir)
        custom_row = QHBoxLayout()
        custom_row.addWidget(self._custom_work_dir, stretch=1)
        custom_row.addWidget(self._custom_work_button)
        advanced_layout.addRow(self.tr("Granularity"), self._granularity)
        advanced_layout.addRow(self.tr("OCR"), self._ocr)
        advanced_layout.addRow(self.tr("Index language"), self._index_language)
        advanced_layout.addRow(self.tr("Item limit"), self._limit)
        advanced_layout.addRow(self._overwrite)
        advanced_layout.addRow(self.tr("Custom work directory"), custom_row)
        layout.addWidget(self._advanced)

        action_row = QHBoxLayout()
        self._start_button = QPushButton(self)
        self._start_button.clicked.connect(self._start_run)
        action_row.addStretch(1)
        action_row.addWidget(self._start_button)
        layout.addLayout(action_row)

        self._controller.run_finished.connect(lambda *_: self._refresh_validation())

        self.refresh_style()
        self.retranslate_ui()
        self._select_preset(RunPreset.COMPLETE)
        self.refresh_preset_availability()

    def _make_preset_handler(
        self,
        preset: RunPreset,
        original: Callable[..., None],
    ) -> Callable[..., None]:
        def handler(event) -> None:  # type: ignore[no-untyped-def]
            if self._preset_cards[preset].isEnabled():
                self._select_preset(preset)
            original(event)

        return handler

    def set_colors(self, colors: ColorTokens) -> None:
        self._colors = colors
        for card in self._preset_cards.values():
            card.set_colors(colors)
        self._drop_target.set_colors(colors)
        self.refresh_style()

    def retranslate_ui(self) -> None:
        self._title.setText(self.tr("Start a New Run"))
        self._subtitle.setText(
            self.tr("Choose a PDF, output folder, and preset to begin the study pipeline.")
        )
        for card in self._preset_cards.values():
            card.retranslate_ui()
        self._drop_target.retranslate_ui()
        self._output_label.setText(self.tr("Output folder"))
        self._output_button.setText(self.tr("Browse…"))
        self._advanced.setTitle(self.tr("Advanced"))
        self._overwrite.setText(self.tr("Overwrite existing outputs"))
        self._custom_work_button.setText(self.tr("Browse…"))
        self._start_button.setText(self.tr("Start"))
        self._limit.setSpecialValueText(self.tr("No limit"))
        self._update_source_mode()

    def refresh_preset_availability(self) -> None:
        blocked = self._registry.presets_blocked()
        reports = self._registry.scan_all()
        for preset, card in self._preset_cards.items():
            if preset.value not in blocked:
                card.set_blocked(None)
                continue
            blockers = [
                report.title
                for report in reports
                if preset.value in report.blocks_presets and report.health.value != "ready"
            ]
            message = self.tr("Unavailable: %1").replace("%1", ", ".join(blockers))
            card.set_blocked(message)
        if not self._preset_cards[self._preset].isEnabled():
            for preset in RunPreset:
                if self._preset_cards[preset].isEnabled():
                    self._select_preset(preset)
                    break

    def refresh_style(self) -> None:
        colors = self._colors
        self._title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {colors.text};")
        self._subtitle.setStyleSheet(f"color: {colors.text_muted};")
        self._validation.setStyleSheet(f"color: {colors.danger};")
        self._start_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {colors.accent};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: 600;
            }}
            QPushButton:disabled {{
                background: {colors.border};
            }}
            """
        )

    def _select_preset(self, preset: RunPreset) -> None:
        self._preset = preset
        for item, card in self._preset_cards.items():
            selected = item == preset
            card.setProperty("selected", selected)
            border = self._colors.accent if selected else self._colors.border
            card.setStyleSheet(
                card.styleSheet()
                + f"QFrame#presetCard-{item.value} {{ border: 2px solid {border}; }}"
            )
        self._update_source_mode()
        self._refresh_validation()

    def _update_source_mode(self) -> None:
        mindmaps_only = self._preset == RunPreset.MINDMAPS_ONLY
        self._drop_target.set_mode(pdf=not mindmaps_only)
        self._output_label.setVisible(not mindmaps_only)
        self._output_path.setVisible(not mindmaps_only)
        self._output_button.setVisible(not mindmaps_only)
        self._granularity.setEnabled(not mindmaps_only)
        self._ocr.setEnabled(not mindmaps_only)
        self._index_language.setEnabled(not mindmaps_only)

    def _on_source_pick_requested(self, path: str) -> None:
        if path:
            self._apply_source_path(path)
            self._refresh_validation()
            return
        if self._preset == RunPreset.MINDMAPS_ONLY:
            selected = QFileDialog.getExistingDirectory(self, self.tr("Select work directory"))
            if selected:
                self._apply_source_path(selected)
        else:
            selected, _filter = QFileDialog.getOpenFileName(
                self,
                self.tr("Select PDF"),
                "",
                self.tr("PDF files (*.pdf)"),
            )
            if selected:
                self._apply_source_path(selected)
        self._refresh_validation()

    def _apply_source_path(self, path: str) -> None:
        candidate = Path(path)
        if self._preset == RunPreset.MINDMAPS_ONLY:
            if not candidate.is_dir():
                return
            self._work_dir = candidate
            self._drop_target.set_path(path)
            return
        if not candidate.is_file() or candidate.suffix.lower() != ".pdf":
            return
        self._pdf_path = candidate
        self._drop_target.set_path(path)
        if self._output_parent is None:
            self._output_parent = candidate.parent
            self._output_path.set_path(str(self._output_parent))

    def _choose_output_parent(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, self.tr("Select output folder"))
        if selected:
            self._output_parent = Path(selected)
            self._output_path.set_path(selected)
            self._refresh_validation()

    def _choose_custom_work_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, self.tr("Select work directory"))
        if selected:
            self._custom_work_dir_path = Path(selected)
            self._custom_work_dir.set_path(selected)
            self._refresh_validation()

    def _build_request(self) -> RunRequest:
        limit_value = self._limit.value()
        return RunRequest(
            preset=self._preset,
            pdf_path=self._pdf_path,
            work_dir=self._work_dir,
            output_parent=self._output_parent,
            advanced=AdvancedOptions(
                granularity=self._granularity.currentText(),
                ocr=self._ocr.currentText(),
                index_language=self._index_language.currentText().strip() or "Persian",
                limit=None if limit_value == 0 else limit_value,
                overwrite=self._overwrite.isChecked(),
                custom_work_dir=self._custom_work_dir_path,
            ),
        )

    def _refresh_validation(self) -> None:
        issues = validate_run_request(self._build_request())
        errors = [issue for issue in issues if issue.severity == ValidationSeverity.ERROR]
        if errors:
            self._validation.setText(errors[0].message)
            self._validation.show()
            self._start_button.setEnabled(False)
        else:
            self._validation.hide()
            self._start_button.setEnabled(not self._controller.is_running())

    def _confirm_warnings(self, issues: list[ValidationIssue]) -> bool:
        warnings = [issue for issue in issues if issue.severity == ValidationSeverity.WARNING]
        if not warnings:
            return True
        message = "\n".join(issue.message for issue in warnings)
        answer = QMessageBox.warning(
            self,
            self.tr("Low disk space"),
            message + "\n\n" + self.tr("Continue anyway?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _start_run(self) -> None:
        if self._controller.is_running():
            return
        request = self._build_request()
        issues = validate_run_request(request)
        if any(issue.severity == ValidationSeverity.ERROR for issue in issues):
            self._refresh_validation()
            return
        if not self._confirm_warnings(issues):
            return
        command = build_pipeline_command(request)
        self._controller.start(command)
        self._start_button.setEnabled(False)
        self.run_started.emit(command)