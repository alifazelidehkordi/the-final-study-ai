from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts.artifact_validators import (
    ArtifactValidationError,
    sha256_file,
    validate_markdown,
    validate_opml,
    validate_parts_manifest,
    validate_xmind,
)


def test_validate_markdown_requires_page_marker(tmp_path: Path) -> None:
    path = tmp_path / "book.md"
    path.write_text("# Topic\nBody\n", encoding="utf-8")

    with pytest.raises(ArtifactValidationError, match="page marker"):
        validate_markdown(path)

    path.write_text("<!-- Page 1 -->\n# Topic\nBody\n", encoding="utf-8")
    assert validate_markdown(path) == sha256_file(path)


def test_validate_parts_manifest_rejects_changed_part(tmp_path: Path) -> None:
    parts = tmp_path / "parts"
    parts.mkdir()
    part = parts / "01_Topic.md"
    part.write_text("# Topic\nBody\n", encoding="utf-8")
    manifest_path = tmp_path / "parts-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "final-study.parts",
                "version": 1,
                "parts": [
                    {
                        "id": "part-001",
                        "filename": part.name,
                        "sha256": sha256_file(part),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    validate_parts_manifest(manifest_path)

    part.write_text("# Changed\n", encoding="utf-8")
    with pytest.raises(ArtifactValidationError, match="hash mismatch"):
        validate_parts_manifest(manifest_path)


def test_validate_opml_and_xmind(tmp_path: Path) -> None:
    opml = tmp_path / "map.opml"
    opml.write_text(
        '<opml version="2.0"><body><outline text="Root"/></body></opml>',
        encoding="utf-8",
    )
    assert validate_opml(opml) == sha256_file(opml)

    xmind = tmp_path / "map.xmind"
    with zipfile.ZipFile(xmind, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("content.json", json.dumps([{"rootTopic": {"title": "Root"}}]))
        archive.writestr("metadata.json", "{}")
        archive.writestr("manifest.json", "{}")
    assert validate_xmind(xmind) == sha256_file(xmind)


def test_validate_xmind_rejects_plain_zip(tmp_path: Path) -> None:
    xmind = tmp_path / "broken.xmind"
    with zipfile.ZipFile(xmind, "w") as archive:
        archive.writestr("other.txt", "not xmind")

    with pytest.raises(ArtifactValidationError, match="required JSON"):
        validate_xmind(xmind)
