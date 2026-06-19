"""Dependency detection, install plans, and health registry."""

from gui.dependencies.models import DependencyHealth, DependencyId, DependencyReport, InstallPlan
from gui.dependencies.registry import DependencyRegistry

__all__ = [
    "DependencyHealth",
    "DependencyId",
    "DependencyReport",
    "DependencyRegistry",
    "InstallPlan",
]