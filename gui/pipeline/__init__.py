"""Pipeline orchestration helpers for the desktop GUI."""

from gui.pipeline.adapter import build_pipeline_command
from gui.pipeline.exit_codes import (
    EXIT_PARTIAL,
    EXIT_REVIEW_REQUIRED,
    EXIT_STOPPED_COOPERATIVE,
    EXIT_SUCCESS,
)
from gui.pipeline.models import AdvancedOptions, RunPreset, RunRequest
from gui.pipeline.process_controller import PipelineProcessController, PipelineRunState
from gui.pipeline.progress_tracker import ProgressSnapshot, ProgressTracker
from gui.pipeline.resume_adapter import (
    build_approve_command,
    build_regenerate_command,
    build_resume_command,
)
from gui.pipeline.run_store import RunSummary, list_runs
from gui.pipeline.validation import DiskSpaceCheck, ValidationIssue, validate_run_request

__all__ = [
    "AdvancedOptions",
    "DiskSpaceCheck",
    "EXIT_PARTIAL",
    "EXIT_REVIEW_REQUIRED",
    "EXIT_STOPPED_COOPERATIVE",
    "EXIT_SUCCESS",
    "PipelineProcessController",
    "PipelineRunState",
    "ProgressSnapshot",
    "ProgressTracker",
    "RunPreset",
    "RunRequest",
    "RunSummary",
    "ValidationIssue",
    "build_approve_command",
    "build_pipeline_command",
    "build_regenerate_command",
    "build_resume_command",
    "list_runs",
    "validate_run_request",
]
