from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from scripts.pipeline_contracts import (
    ContractError,
    EventWriter,
    load_run_manifest,
    new_run_manifest,
    read_events,
    save_run_manifest,
    set_run_status,
)

ROOT = Path(__file__).resolve().parents[1]


def example_manifest() -> dict:
    return new_run_manifest(
        run_id="run-1",
        preset="complete",
        source={"kind": "pdf", "path": "/data/book.pdf"},
        paths={
            "work_dir": "/data/book_work",
            "event_file": "/data/events.jsonl",
            "log_file": "/data/run.log",
        },
        options={
            "granularity": "normal",
            "ocr": "off",
            "index_language": "Persian",
            "overwrite": False,
            "limit": None,
        },
    )


def test_event_writer_orders_events_and_reader_ignores_truncated_tail(
    tmp_path: Path,
) -> None:
    path = tmp_path / "events.jsonl"
    writer = EventWriter(path, "run-1")
    first = writer.emit("run.started", "preflight")
    second = writer.emit("stage.started", "segmentation")
    with path.open("ab") as stream:
        stream.write(b'{"schema":"final-study.event"')

    events, truncated = read_events(path)

    assert truncated is True
    assert [event["seq"] for event in events] == [1, 2]
    assert first["seq"] == 1
    assert second["seq"] == 2


def test_manifest_round_trip_and_status_update_are_atomic(tmp_path: Path) -> None:
    path = tmp_path / "runs" / "run.json"
    manifest = example_manifest()

    save_run_manifest(path, manifest)
    set_run_status(path, manifest, "awaiting_review")
    loaded = load_run_manifest(path)

    assert loaded["status"] == "awaiting_review"
    assert loaded["run_id"] == "run-1"
    assert not list(path.parent.glob("*.tmp"))


def test_manifest_rejects_newer_versions(tmp_path: Path) -> None:
    path = tmp_path / "run.json"
    manifest = example_manifest()
    manifest["version"] = 2
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ContractError, match="Unsupported"):
        load_run_manifest(path)


@pytest.mark.parametrize(
    ("schema_name", "instance"),
    (
        (
            "event-v1.schema.json",
            {
                "schema": "final-study.event",
                "version": 1,
                "run_id": "run-1",
                "seq": 1,
                "time": "2026-06-19T12:00:00Z",
                "type": "run.started",
                "stage": "preflight",
                "data": {},
            },
        ),
        ("run-manifest-v1.schema.json", example_manifest()),
        (
            "parts-manifest-v1.schema.json",
            {
                "schema": "final-study.parts",
                "version": 1,
                "source": {"path": "/data/book.md"},
                "granularity": "normal",
                "index_language": "Persian",
                "parts": [
                    {
                        "id": "part-1",
                        "filename": "01_Topic.md",
                        "sha256": "a" * 64,
                        "start_page": 1,
                        "end_page": 2,
                    }
                ],
            },
        ),
    ),
)
def test_json_schemas_accept_contract_examples(
    schema_name: str,
    instance: dict,
) -> None:
    schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(instance)
