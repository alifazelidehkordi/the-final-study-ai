"""Watch a JSONL event file and emit newly parsed events."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer, Signal

from gui.pipeline.contracts_bridge import read_events
from gui.pipeline.progress_tracker import ProgressSnapshot, ProgressTracker


class EventWatcher(QObject):
    events_updated = Signal(list)
    snapshot_updated = Signal(object)
    truncated_warning = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._path: Path | None = None
        self._tracker = ProgressTracker()
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._reload)
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._reload)

    def tracker(self) -> ProgressTracker:
        return self._tracker

    def watch(self, path: Path) -> None:
        self.stop()
        self._path = path
        self._tracker.reset()
        if path.exists():
            self._watcher.addPath(str(path))
        self._reload()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        if self._path is not None and self._watcher.files():
            self._watcher.removePath(str(self._path))
        self._path = None

    def snapshot(self) -> ProgressSnapshot:
        return self._tracker.snapshot()

    def _reload(self) -> None:
        if self._path is None:
            return
        if not self._path.exists():
            return
        events, truncated = read_events(self._path)
        previous_count = self._tracker.ingested_event_count
        self._tracker.ingest_events(events)
        if truncated:
            self.truncated_warning.emit()
        if self._tracker.ingested_event_count != previous_count:
            self.events_updated.emit(events)
        self.snapshot_updated.emit(self._tracker.snapshot())
        if self._path.exists() and str(self._path) not in self._watcher.files():
            self._watcher.addPath(str(self._path))