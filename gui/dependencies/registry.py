"""Aggregate dependency probes and attach install plans."""

from __future__ import annotations

from gui.dependencies import probes
from gui.dependencies.manifest import CompatibilityManifest, load_compatibility_manifest
from gui.dependencies.models import DependencyHealth, DependencyId, DependencyReport
from gui.dependencies.providers import install_plan_for
from gui.dependencies.tool_paths import ToolPaths, default_tool_paths
from gui.paths import browser_profile_dir
from gui.settings import AppSettings


class DependencyRegistry:
    def __init__(
        self,
        *,
        settings: AppSettings | None = None,
        manifest: CompatibilityManifest | None = None,
        tool_paths: ToolPaths | None = None,
    ) -> None:
        self.settings = settings or AppSettings.load()
        self.manifest = manifest or load_compatibility_manifest()
        self.tool_paths = tool_paths or default_tool_paths(browser_profile_dir=browser_profile_dir())

    def scan_all(self) -> list[DependencyReport]:
        raw_reports = [
            probes.probe_python(self.manifest),
            probes.probe_pyside6(self.manifest),
            probes.probe_pdf_conversion(self.tool_paths, self.manifest),
            probes.probe_ocr(),
            probes.probe_mindmap_project(self.tool_paths, self.manifest),
            probes.probe_mindmap_packages(self.tool_paths, self.manifest),
            probes.probe_chrome(self.tool_paths),
            probes.probe_linux_desktop(),
            probes.probe_profile_login(self.tool_paths, self.settings),
        ]
        return [self._attach_plan(report) for report in raw_reports]

    def report_for(self, dependency_id: DependencyId) -> DependencyReport:
        for report in self.scan_all():
            if report.dependency_id == dependency_id:
                return report
        raise KeyError(dependency_id)

    def presets_blocked(self) -> set[str]:
        blocked: set[str] = set()
        for report in self.scan_all():
            if report.health != DependencyHealth.READY:
                blocked.update(report.blocks_presets)
        return blocked

    def _attach_plan(self, report: DependencyReport) -> DependencyReport:
        if report.health not in (DependencyHealth.MISSING, DependencyHealth.REPAIRABLE):
            return report
        plan = install_plan_for(
            report.dependency_id,
            manifest=self.manifest,
            tool_paths=self.tool_paths,
        )
        if plan is None:
            return report
        return DependencyReport(
            dependency_id=report.dependency_id,
            title=report.title,
            purpose=report.purpose,
            health=report.health,
            detected_version=report.detected_version,
            detected_path=report.detected_path,
            detail=report.detail,
            install_plan=plan,
            blocks_presets=report.blocks_presets,
        )