from __future__ import annotations

import hashlib
import importlib.util
import json
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_pipeline.py"
SPEC = importlib.util.spec_from_file_location("run_pipeline", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
pipeline = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pipeline
SPEC.loader.exec_module(pipeline)


def executable_script(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def test_mindmap_cooperative_stop_propagates_exit_21(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = tmp_path / "work"
    parts = work / "parts"
    parts.mkdir(parents=True)
    part = parts / "01_Topic.md"
    part.write_text("# Topic\nBody\n", encoding="utf-8")
    (work / "parts-manifest.json").write_text(
        json.dumps(
            {
                "schema": "final-study.parts",
                "version": 1,
                "parts": [
                    {
                        "id": "part-001",
                        "filename": part.name,
                        "sha256": hashlib.sha256(part.read_bytes()).hexdigest(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    project = tmp_path / "mindmap"
    python_path = project / ".venv/bin/python"
    python_path.parent.mkdir(parents=True)
    python_path.symlink_to(sys.executable)
    pipeline_script = executable_script(
        project / "scripts/pipeline.py",
        "import sys\nraise SystemExit(21)\n",
    )
    prompt = project / "prompts/prompt-mind-map.md"
    prompt.parent.mkdir(parents=True)
    prompt.write_text("prompt", encoding="utf-8")
    events = tmp_path / "events.jsonl"
    monkeypatch.setenv("MINDMAP_PROJECT", str(project))

    code = pipeline.main(
        (
            "--work-dir",
            str(work),
            "--mindmap-only",
            "--require-valid-parts",
            "--approve-segmentation",
            "--event-file",
            str(events),
            "--run-id",
            "run-stop",
        )
    )

    assert code == pipeline.EXIT_STOPPED_COOPERATIVE
    payloads = [json.loads(line) for line in events.read_text().splitlines()]
    assert payloads[-1]["type"] == "run.stopped"
    assert pipeline_script.is_file()