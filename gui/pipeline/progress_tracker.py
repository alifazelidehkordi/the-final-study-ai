"""Derive live progress snapshots from JSONL pipeline events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import median
from typing import Any

STAGE_LABELS = {
    "preflight": "Preflight",
    "pdf_to_markdown": "PDF to Markdown",
    "segmentation": "Segmentation",
    "review": "Segmentation review",
    "mindmap_opml": "Mind maps (OPML)",
    "opml_to_xmind": "OPML to XMind",
    "finalize": "Finalizing",
}

MINDMAP_STAGES = {"mindmap_opml", "opml_to_xmind"}


@dataclass
class ProgressSnapshot:
    stage: str
    stage_label: str
    current_operation: str
    item_index: int | None = None
    item_total: int | None = None
    item_label: str | None = None
    completed_items: int = 0
    elapsed_seconds: float = 0.0
    eta_seconds: float | None = None
    eta_label: str = "Calculating estimate"
    recent_activity: list[str] = field(default_factory=list)
    artifact_counts: dict[str, int] = field(default_factory=dict)
    in_mindmap_stage: bool = False
    awaiting_review: bool = False
    run_failed: bool = False


def _parse_time(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


class ProgressTracker:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []
        self._seen_sequences: set[int] = set()
        self._started_at: datetime | None = None
        self._last_item_started_at: datetime | None = None
        self._item_durations: list[float] = []
        self._stage = "preflight"
        self._current_operation = "Starting…"
        self._item_index: int | None = None
        self._item_total: int | None = None
        self._item_label: str | None = None
        self._completed_items = 0
        self._artifact_counts: dict[str, int] = {}
        self._recent_activity: list[str] = []
        self._awaiting_review = False
        self._run_failed = False

    def reset(self) -> None:
        self._events = []
        self._seen_sequences = set()
        self._started_at = None
        self._last_item_started_at = None
        self._item_durations = []
        self._stage = "preflight"
        self._current_operation = "Starting…"
        self._item_index = None
        self._item_total = None
        self._item_label = None
        self._completed_items = 0
        self._artifact_counts = {}
        self._recent_activity = []
        self._awaiting_review = False
        self._run_failed = False

    @property
    def ingested_event_count(self) -> int:
        return len(self._seen_sequences)

    def ingest_events(self, events: list[dict[str, Any]]) -> None:
        for event in events:
            sequence = event.get("seq")
            if not isinstance(sequence, int) or sequence in self._seen_sequences:
                continue
            self._seen_sequences.add(sequence)
            self._apply_event(event)

    def snapshot(self, *, now: datetime | None = None) -> ProgressSnapshot:
        moment = now or datetime.now(timezone.utc)
        elapsed = 0.0
        if self._started_at is not None:
            elapsed = max(0.0, (moment - self._started_at).total_seconds())
        eta_seconds, eta_label = self._estimate_remaining()
        return ProgressSnapshot(
            stage=self._stage,
            stage_label=STAGE_LABELS.get(self._stage, self._stage),
            current_operation=self._current_operation,
            item_index=self._item_index,
            item_total=self._item_total,
            item_label=self._item_label,
            completed_items=self._completed_items,
            elapsed_seconds=elapsed,
            eta_seconds=eta_seconds,
            eta_label=eta_label,
            recent_activity=list(self._recent_activity[-8:]),
            artifact_counts=dict(self._artifact_counts),
            in_mindmap_stage=self._stage in MINDMAP_STAGES,
            awaiting_review=self._awaiting_review,
            run_failed=self._run_failed,
        )

    def _estimate_remaining(self) -> tuple[float | None, str]:
        if self._item_total is None or self._item_total <= 0:
            return None, "Calculating estimate"
        remaining = max(0, self._item_total - self._completed_items)
        if remaining == 0:
            return 0.0, "Almost done"
        if len(self._item_durations) < 2:
            return None, "Calculating estimate"
        sample = self._item_durations[-5:]
        estimate = median(sample) * remaining
        return estimate, f"~{self._format_duration(estimate)} remaining (approx.)"

    def _apply_event(self, event: dict[str, Any]) -> None:
        self._events.append(event)
        event_type = str(event.get("type", ""))
        stage = str(event.get("stage", ""))
        if stage:
            self._stage = stage

        item = event.get("item")
        if isinstance(item, dict):
            index = item.get("index")
            total = item.get("total")
            label = item.get("label")
            if isinstance(index, int):
                self._item_index = index
            if isinstance(total, int):
                self._item_total = total
            if isinstance(label, str):
                self._item_label = label

        data = event.get("data")
        if isinstance(data, dict):
            completed = data.get("completed")
            total = data.get("total")
            if isinstance(completed, int):
                self._completed_items = completed
            if isinstance(total, int):
                self._item_total = total

        if event_type == "run.started":
            timestamp = event.get("time")
            if isinstance(timestamp, str):
                self._started_at = _parse_time(timestamp)
            self._current_operation = "Pipeline started"
            self._push_activity("Run started")
        elif event_type == "stage.started":
            self._current_operation = STAGE_LABELS.get(stage, stage)
            self._push_activity(f"Stage started: {self._current_operation}")
        elif event_type == "stage.progress":
            completed = self._completed_items
            total = self._item_total
            if total:
                self._current_operation = f"{completed} of {total} items"
            self._push_activity(self._current_operation)
        elif event_type == "item.started":
            timestamp = event.get("time")
            if isinstance(timestamp, str):
                self._last_item_started_at = _parse_time(timestamp)
            label = self._item_label or "item"
            self._current_operation = f"Working on {label}"
            if self._item_index is not None and self._item_total is not None:
                self._current_operation = f"{self._item_index} of {self._item_total}: {label}"
            self._push_activity(self._current_operation)
        elif event_type == "item.completed":
            self._completed_items += 1
            self._record_item_duration(event.get("time"))
            artifact = event.get("artifact")
            if isinstance(artifact, dict):
                kind = artifact.get("kind")
                if isinstance(kind, str):
                    self._artifact_counts[kind] = self._artifact_counts.get(kind, 0) + 1
            label = self._item_label or "item"
            self._push_activity(f"Completed {label}")
        elif event_type == "item.failed":
            label = self._item_label or "item"
            self._push_activity(f"Failed {label}")
        elif event_type == "review.required":
            self._awaiting_review = True
            self._current_operation = "Segmentation review required"
            self._push_activity("Review required before mind maps")
        elif event_type in {"run.failed", "stage.failed"}:
            self._run_failed = True
            self._current_operation = "Run failed"
            self._push_activity("Run failed")
        elif event_type == "run.stopped":
            self._current_operation = "Run stopped"
            self._push_activity("Run stopped")
        elif event_type == "run.completed":
            self._current_operation = "Run completed"
            self._push_activity("Run completed")

    def _record_item_duration(self, finished_time: object) -> None:
        if self._last_item_started_at is None or not isinstance(finished_time, str):
            return
        finished = _parse_time(finished_time)
        duration = max(0.0, (finished - self._last_item_started_at).total_seconds())
        self._item_durations.append(duration)
        self._last_item_started_at = None

    def _push_activity(self, message: str) -> None:
        self._recent_activity.append(message)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        total = int(seconds)
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours}h {minutes}m"
        if minutes:
            return f"{minutes}m {secs}s"
        return f"{secs}s"