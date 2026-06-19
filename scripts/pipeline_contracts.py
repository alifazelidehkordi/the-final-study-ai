"""Versioned event and run-manifest contracts for the pipeline."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

EVENT_SCHEMA = "final-study.event"
EVENT_VERSION = 1
RUN_SCHEMA = "final-study.run"
RUN_VERSION = 1

RUN_STATUSES = {
    "created",
    "running",
    "awaiting_review",
    "stop_requested",
    "stopped",
    "interrupted",
    "partial",
    "failed",
    "completed",
}
PRESETS = {"complete", "markdown_index", "mindmaps_only"}


class ContractError(ValueError):
    """Raised when persisted contract data is invalid or unsupported."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@contextmanager
def exclusive_file_lock(path: Path) -> Iterator[None]:
    """Hold a small cross-platform advisory lock file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as lock_stream:
        lock_stream.seek(0)
        if lock_stream.read(1) == b"":
            lock_stream.write(b"\0")
            lock_stream.flush()
        lock_stream.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(  # type: ignore[attr-defined]
                lock_stream.fileno(),
                msvcrt.LK_LOCK,  # type: ignore[attr-defined]
                1,
            )
            try:
                yield
            finally:
                lock_stream.seek(0)
                msvcrt.locking(  # type: ignore[attr-defined]
                    lock_stream.fileno(),
                    msvcrt.LK_UNLCK,  # type: ignore[attr-defined]
                    1,
                )
        else:
            import fcntl

            fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_stream.fileno(), fcntl.LOCK_UN)


class EventWriter:
    """Append ordered events to a UTF-8 JSON Lines stream."""

    def __init__(self, path: Path | None, run_id: str) -> None:
        self.path = path
        self.run_id = run_id
        self.sequence = 0
        self._thread_lock = Lock()

    def emit(self, event_type: str, stage: str, **data: object) -> dict[str, Any]:
        with self._thread_lock:
            if self.path is not None:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                lock_path = self.path.with_suffix(self.path.suffix + ".lock")
                with (
                    exclusive_file_lock(lock_path),
                    self.path.open("a", encoding="utf-8") as stream,
                ):
                    self.sequence = max(self.sequence, _last_event_sequence(self.path)) + 1
                    payload = self._payload(event_type, stage, data)
                    stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                    return payload
            self.sequence += 1
            return self._payload(event_type, stage, data)

    def _payload(
        self,
        event_type: str,
        stage: str,
        fields: dict[str, object],
    ) -> dict[str, Any]:
        details = dict(fields)
        payload: dict[str, Any] = {
            "schema": EVENT_SCHEMA,
            "version": EVENT_VERSION,
            "run_id": self.run_id,
            "seq": self.sequence,
            "time": utc_now(),
            "type": event_type,
            "stage": stage,
            "data": {},
        }
        for key in ("item", "artifact", "error"):
            if key in details:
                payload[key] = details.pop(key)
        payload["data"] = details
        return payload


def _last_event_sequence(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as stream:
        lines = stream.read().splitlines()
    for line in reversed(lines):
        try:
            event = json.loads(line.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            continue
        sequence = event.get("seq")
        if isinstance(sequence, int):
            return sequence
    return 0


def read_events(path: Path) -> tuple[list[dict[str, Any]], bool]:
    """Read complete event lines and report whether a trailing line was truncated."""
    if not path.exists():
        return [], False
    raw = path.read_bytes()
    truncated = bool(raw) and not raw.endswith(b"\n")
    lines = raw.splitlines()
    if truncated and lines:
        lines = lines[:-1]
    events = [json.loads(line.decode("utf-8")) for line in lines if line.strip()]
    for event in events:
        validate_event(event)
    return events, truncated


def validate_event(event: dict[str, Any]) -> None:
    required = {"schema", "version", "run_id", "seq", "time", "type", "stage", "data"}
    if not required.issubset(event):
        raise ContractError("Event is missing required fields.")
    if event["schema"] != EVENT_SCHEMA or event["version"] != EVENT_VERSION:
        raise ContractError("Unsupported event schema.")
    if not isinstance(event["seq"], int) or event["seq"] < 1:
        raise ContractError("Event sequence must be a positive integer.")


def new_run_manifest(
    *,
    run_id: str,
    preset: str,
    source: dict[str, Any],
    paths: dict[str, str],
    options: dict[str, Any],
) -> dict[str, Any]:
    if preset not in PRESETS:
        raise ContractError(f"Unknown preset: {preset}")
    now = utc_now()
    manifest = {
        "schema": RUN_SCHEMA,
        "version": RUN_VERSION,
        "run_id": run_id,
        "created_at": now,
        "updated_at": now,
        "status": "created",
        "preset": preset,
        "source": source,
        "paths": paths,
        "options": options,
        "tool_versions": {},
        "stages": {},
        "items": {},
        "artifacts": [],
        "last_error": None,
    }
    validate_run_manifest(manifest)
    return manifest


def validate_run_manifest(manifest: dict[str, Any]) -> None:
    required = {
        "schema",
        "version",
        "run_id",
        "created_at",
        "updated_at",
        "status",
        "preset",
        "source",
        "paths",
        "options",
        "tool_versions",
        "stages",
        "items",
        "artifacts",
        "last_error",
    }
    if not required.issubset(manifest):
        raise ContractError("Run manifest is missing required fields.")
    if manifest["schema"] != RUN_SCHEMA or manifest["version"] != RUN_VERSION:
        raise ContractError("Unsupported run manifest schema.")
    if manifest["status"] not in RUN_STATUSES:
        raise ContractError(f"Unknown run status: {manifest['status']}")
    if manifest["preset"] not in PRESETS:
        raise ContractError(f"Unknown preset: {manifest['preset']}")
    if not isinstance(manifest["source"], dict) or not isinstance(manifest["paths"], dict):
        raise ContractError("Run manifest source and paths must be objects.")


def save_run_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = utc_now()
    validate_run_manifest(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(manifest, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_run_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"Could not load run manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ContractError("Run manifest root must be an object.")
    validate_run_manifest(manifest)
    return manifest


def set_run_status(
    path: Path,
    manifest: dict[str, Any],
    status: str,
    *,
    last_error: dict[str, Any] | None = None,
) -> None:
    if status not in RUN_STATUSES:
        raise ContractError(f"Unknown run status: {status}")
    manifest["status"] = status
    manifest["last_error"] = last_error
    save_run_manifest(path, manifest)
