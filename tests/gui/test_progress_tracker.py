from __future__ import annotations

from gui.pipeline.progress_tracker import ProgressTracker


def test_progress_tracker_computes_eta_after_two_items() -> None:
    tracker = ProgressTracker()
    tracker.ingest_events(
        [
            {
                "seq": 1,
                "type": "run.started",
                "stage": "preflight",
                "time": "2026-06-19T10:00:00Z",
            },
            {
                "seq": 2,
                "type": "item.started",
                "stage": "mindmap_opml",
                "time": "2026-06-19T10:00:00Z",
                "item": {"index": 1, "total": 4, "label": "A"},
            },
            {
                "seq": 3,
                "type": "item.completed",
                "stage": "mindmap_opml",
                "time": "2026-06-19T10:01:00Z",
                "item": {"index": 1, "total": 4, "label": "A"},
            },
            {
                "seq": 4,
                "type": "item.started",
                "stage": "mindmap_opml",
                "time": "2026-06-19T10:01:00Z",
                "item": {"index": 2, "total": 4, "label": "B"},
            },
            {
                "seq": 5,
                "type": "item.completed",
                "stage": "mindmap_opml",
                "time": "2026-06-19T10:03:00Z",
                "item": {"index": 2, "total": 4, "label": "B"},
            },
        ]
    )
    snapshot = tracker.snapshot()
    assert snapshot.completed_items == 2
    assert snapshot.item_total == 4
    assert snapshot.in_mindmap_stage is True
    assert snapshot.eta_seconds is not None
    assert "remaining" in snapshot.eta_label


def test_progress_tracker_marks_review_required() -> None:
    tracker = ProgressTracker()
    tracker.ingest_events(
        [
            {
                "seq": 1,
                "type": "review.required",
                "stage": "review",
                "time": "2026-06-19T10:00:00Z",
            }
        ]
    )
    snapshot = tracker.snapshot()
    assert snapshot.awaiting_review is True