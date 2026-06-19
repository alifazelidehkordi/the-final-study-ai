from __future__ import annotations

import sys
from pathlib import Path

from gui.pipeline.adapter import build_pipeline_command
from gui.pipeline.models import RunPreset, RunRequest
from gui.pipeline.process_controller import PipelineProcessController


def test_process_controller_runs_helper_script(qtbot, qapp, tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF")
    helper = tmp_path / "helper.py"
    helper.write_text(
        "import sys\nprint('hello-from-helper')\nraise SystemExit(0)\n",
        encoding="utf-8",
    )
    request = RunRequest(preset=RunPreset.COMPLETE, pdf_path=pdf, output_parent=tmp_path)
    command = build_pipeline_command(request, run_id="controller-test")
    argv = (sys.executable, str(helper))
    replaced = command.__class__(
        run_id=command.run_id,
        argv=argv,
        work_dir=command.work_dir,
        event_file=command.event_file,
        manifest_file=command.manifest_file,
        log_file=command.log_file,
        stop_file=command.stop_file,
    )

    controller = PipelineProcessController()
    lines: list[str] = []
    finished: list[tuple[int, object]] = []
    controller.output_line.connect(lines.append)
    controller.run_finished.connect(lambda code, state: finished.append((code, state)))
    controller.start(replaced)

    assert controller.is_running()
    qtbot.waitUntil(lambda: len(finished) > 0, timeout=10_000)
    assert finished[0][0] == 0
    assert "hello-from-helper" in lines