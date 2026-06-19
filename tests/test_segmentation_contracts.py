from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import jsonschema

from scripts.pipeline_contracts import read_events

ROOT = Path(__file__).resolve().parents[1]
SEGMENTER = ROOT / "scripts" / "segment_markdown_study_parts.py"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_segmentation_writes_valid_hashed_manifest_and_events(tmp_path: Path) -> None:
    markdown = tmp_path / "کتاب test.md"
    markdown.write_text(
        "<!-- Page 1 -->\n## Topic One\nBody\n"
        "<!-- Page 2 -->\n## Topic Two\nMore body\n",
        encoding="utf-8",
    )
    output = tmp_path / "work dir"
    events_path = tmp_path / "events.jsonl"

    result = subprocess.run(
        [
            sys.executable,
            str(SEGMENTER),
            "--input",
            str(markdown),
            "--output-dir",
            str(output),
            "--no-pdf",
            "--event-file",
            str(events_path),
            "--run-id",
            "run-segment",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    manifest_path = output / "parts-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (ROOT / "schemas/parts-manifest-v1.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(schema).validate(manifest)
    assert manifest["source"]["markdown_sha256"] == sha256_file(markdown)
    assert manifest["parts"]
    for part in manifest["parts"]:
        part_path = output / "parts" / part["filename"]
        assert part["sha256"] == sha256_file(part_path)

    events, truncated = read_events(events_path)
    assert truncated is False
    assert [event["seq"] for event in events] == list(range(1, len(events) + 1))
    assert any(event["type"] == "item.completed" for event in events)
    assert events[-1]["type"] == "artifact.validated"
