"""Launch and monitor run_pipeline.py through QProcess."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal

from gui.paths import project_root
from gui.pipeline.adapter import PipelineCommand


@dataclass(frozen=True)
class PipelineRunState:
    run_id: str
    work_dir: Path
    event_file: Path
    manifest_file: Path
    log_file: Path
    stop_file: Path


class PipelineProcessController(QObject):
    run_started = Signal(object)
    output_line = Signal(str)
    run_finished = Signal(int, object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._process: QProcess | None = None
        self._state: PipelineRunState | None = None

    def is_running(self) -> bool:
        if self._process is None:
            return False
        return self._process.state() != QProcess.ProcessState.NotRunning

    def current_state(self) -> PipelineRunState | None:
        return self._state

    def start(self, command: PipelineCommand) -> None:
        if self.is_running():
            raise RuntimeError("A pipeline run is already active.")
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(self._emit_output)
        process.finished.connect(self._on_finished)
        process.setWorkingDirectory(str(self.working_directory()))
        process.start(command.argv[0], list(command.argv[1:]))
        if not process.waitForStarted(10_000):
            raise RuntimeError("Could not start the pipeline process.")
        self._process = process
        self._state = PipelineRunState(
            run_id=command.run_id,
            work_dir=command.work_dir,
            event_file=command.event_file,
            manifest_file=command.manifest_file,
            log_file=command.log_file,
            stop_file=command.stop_file,
        )
        self.run_started.emit(self._state)

    def stop_now(self) -> None:
        if self._process is None:
            return
        self._process.kill()

    def request_cooperative_stop(self) -> None:
        if self._state is None:
            return
        self._state.stop_file.parent.mkdir(parents=True, exist_ok=True)
        self._state.stop_file.write_text("requested\n", encoding="utf-8")

    def working_directory(self) -> Path:
        return project_root()

    def _emit_output(self) -> None:
        if self._process is None:
            return
        raw = self._process.readAllStandardOutput().data()
        if isinstance(raw, (bytes, bytearray)):
            payload = raw.decode("utf-8", errors="replace")
        else:
            payload = bytes(raw).decode("utf-8", errors="replace")
        for line in payload.splitlines():
            if line:
                self.output_line.emit(line)

    def _on_finished(self, exit_code: int, _status: QProcess.ExitStatus) -> None:
        state = self._state
        self._process = None
        self._state = None
        self.run_finished.emit(exit_code, state)