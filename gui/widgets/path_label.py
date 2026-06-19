"""Display filesystem paths with isolated LTR rendering in RTL layouts."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget


class PathLabel(QLabel):
    def __init__(self, path: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pathLabel")
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setWordWrap(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.set_path(path)

    def set_path(self, path: str) -> None:
        escaped = (
            path.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        self.setText(
            f'<span dir="ltr" style="unicode-bidi: isolate;">{escaped}</span>'
        )
        self.setTextFormat(Qt.TextFormat.RichText)