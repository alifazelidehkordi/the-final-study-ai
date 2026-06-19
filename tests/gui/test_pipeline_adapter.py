from __future__ import annotations

from pathlib import Path

from gui.pipeline.adapter import build_pipeline_command
from gui.pipeline.models import AdvancedOptions, RunPreset, RunRequest


def test_complete_preset_builds_canonical_argv(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF-1.4 sample")
    request = RunRequest(
        preset=RunPreset.COMPLETE,
        pdf_path=pdf,
        output_parent=tmp_path,
        advanced=AdvancedOptions(granularity="fine", ocr="auto", index_language="English"),
    )

    command = build_pipeline_command(request, run_id="run-123")

    assert command.run_id == "run-123"
    assert str(pdf) in command.argv
    assert "--work-dir" in command.argv
    assert command.work_dir == (tmp_path / "book_work").resolve()
    assert "--granularity" in command.argv
    assert "fine" in command.argv
    assert "--index-language" in command.argv
    assert "English" in command.argv
    assert "--ocr" in command.argv
    assert "auto" in command.argv
    assert "--stop-after" not in command.argv
    assert "--event-file" in command.argv
    assert "--manifest-file" in command.argv
    assert "--log-file" in command.argv
    assert "--run-id" in command.argv
    assert "run-123" in command.argv
    assert "--stop-file" in command.argv


def test_markdown_index_preset_stops_after_segmentation(tmp_path: Path) -> None:
    pdf = tmp_path / "notes.pdf"
    pdf.write_bytes(b"%PDF sample")
    request = RunRequest(preset=RunPreset.MARKDOWN_INDEX, pdf_path=pdf)

    command = build_pipeline_command(request, run_id="md-run")

    assert "--stop-after" in command.argv
    assert command.argv[command.argv.index("--stop-after") + 1] == "segmentation"


def test_mindmaps_only_preset_uses_work_dir_and_flags(tmp_path: Path) -> None:
    work = tmp_path / "book_work"
    (work / "parts").mkdir(parents=True)
    (work / "parts-manifest.json").write_text("{}", encoding="utf-8")
    request = RunRequest(preset=RunPreset.MINDMAPS_ONLY, work_dir=work, advanced=AdvancedOptions(limit=3))

    command = build_pipeline_command(request, run_id="mm-run")

    assert str(work.resolve()) in command.argv
    assert "--mindmap-only" in command.argv
    assert "--require-valid-parts" in command.argv
    assert "--limit" in command.argv
    assert "3" in command.argv
    assert command.argv[0].endswith("python") or "python" in command.argv[0]