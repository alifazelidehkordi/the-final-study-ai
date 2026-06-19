"""Integrity validators used for safe pipeline resume."""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from defusedxml import ElementTree

PAGE_MARKER = re.compile(r"^<!-- Page \d+ -->\s*$", re.MULTILINE)


class ArtifactValidationError(ValueError):
    """Raised when a generated artifact is incomplete or malformed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_nonempty_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise ArtifactValidationError(f"Artifact is missing or empty: {path}")


def validate_markdown(path: Path, *, require_page_marker: bool = True) -> str:
    require_nonempty_file(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise ArtifactValidationError(f"Markdown is not UTF-8: {path}") from exc
    if not text.strip():
        raise ArtifactValidationError(f"Markdown contains no content: {path}")
    if require_page_marker and PAGE_MARKER.search(text) is None:
        raise ArtifactValidationError(f"Markdown has no source page marker: {path}")
    return sha256_file(path)


def validate_parts_manifest(path: Path) -> dict[str, Any]:
    require_nonempty_file(path)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactValidationError(f"Parts manifest is invalid JSON: {path}") from exc
    if not isinstance(manifest, dict):
        raise ArtifactValidationError("Parts manifest root must be an object.")
    if manifest.get("schema") != "final-study.parts" or manifest.get("version") != 1:
        raise ArtifactValidationError("Unsupported parts manifest schema.")
    parts = manifest.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ArtifactValidationError("Parts manifest contains no parts.")
    parts_dir = path.parent / "parts"
    for part in parts:
        if not isinstance(part, dict):
            raise ArtifactValidationError("Parts manifest entry must be an object.")
        filename = part.get("filename")
        expected_hash = part.get("sha256")
        if not isinstance(filename, str) or not isinstance(expected_hash, str):
            raise ArtifactValidationError("Part entry is missing filename or hash.")
        part_path = parts_dir / filename
        validate_markdown(part_path, require_page_marker=False)
        if sha256_file(part_path) != expected_hash:
            raise ArtifactValidationError(f"Part hash mismatch: {part_path}")
    return manifest


def validate_index_markdown(path: Path, *, expected_parts: int) -> str:
    digest = validate_markdown(path, require_page_marker=False)
    text = path.read_text(encoding="utf-8")
    if text.count("(parts/") < expected_parts:
        raise ArtifactValidationError("Study index does not reference every expected part.")
    return digest


def validate_index_pdf(path: Path) -> str:
    require_nonempty_file(path)
    try:
        fitz = importlib.import_module("fitz")
        document = fitz.open(path)
    except (ImportError, RuntimeError, ValueError) as exc:
        raise ArtifactValidationError(f"Study index PDF cannot be opened: {path}") from exc
    try:
        if document.page_count < 1:
            raise ArtifactValidationError("Study index PDF contains no pages.")
    finally:
        document.close()
    return sha256_file(path)


def validate_opml(path: Path) -> str:
    require_nonempty_file(path)
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise ArtifactValidationError(f"OPML is invalid XML: {path}") from exc
    if root is None:
        raise ArtifactValidationError("OPML document contains no root element.")
    if root.tag.lower() != "opml":
        raise ArtifactValidationError("OPML root element is missing.")
    body = root.find("body")
    if body is None or body.find("outline") is None:
        raise ArtifactValidationError("OPML body contains no root outline.")
    return sha256_file(path)


def validate_xmind(path: Path) -> str:
    require_nonempty_file(path)
    required = {"content.json", "metadata.json", "manifest.json"}
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ArtifactValidationError("XMind ZIP contains a corrupt member.")
            if not required.issubset(archive.namelist()):
                raise ArtifactValidationError("XMind ZIP is missing required JSON files.")
            content = json.loads(archive.read("content.json"))
            json.loads(archive.read("metadata.json"))
            json.loads(archive.read("manifest.json"))
    except (OSError, zipfile.BadZipFile, UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactValidationError(f"XMind archive is invalid: {path}") from exc
    if not isinstance(content, list) or not content:
        raise ArtifactValidationError("XMind content contains no sheets.")
    first_sheet = content[0]
    if not isinstance(first_sheet, dict) or not isinstance(first_sheet.get("rootTopic"), dict):
        raise ArtifactValidationError("XMind content contains no root topic.")
    return sha256_file(path)
