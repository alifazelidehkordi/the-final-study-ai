from __future__ import annotations

from PySide6.QtCore import Qt

from gui.widgets.path_label import PathLabel


def test_path_label_isolates_ltr_text(qtbot, qapp) -> None:
    qapp.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    label = PathLabel()
    qtbot.addWidget(label)
    label.set_path("/home/ali/book work/STUDY_INDEX.pdf")

    assert 'dir="ltr"' in label.text()
    assert "STUDY_INDEX.pdf" in label.text()