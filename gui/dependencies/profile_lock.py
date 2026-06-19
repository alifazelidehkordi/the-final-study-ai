"""Exclusive browser-profile lock shared by Setup and pipeline runs."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from gui.paths import profile_lock_path


@dataclass(frozen=True)
class ProfileLockStatus:
    locked: bool
    owner: str | None = None
    since: str | None = None


class ProfileLockError(RuntimeError):
    """Raised when the browser profile is already in use."""


def _lock_meta_path(lock_file: Path) -> Path:
    return lock_file.with_name(f"{lock_file.name}.meta")


def read_lock_status(path: Path | None = None) -> ProfileLockStatus:
    lock_file = path or profile_lock_path()
    if not lock_file.exists():
        return ProfileLockStatus(locked=False)
    meta_file = _lock_meta_path(lock_file)
    if not meta_file.exists():
        return ProfileLockStatus(locked=True)
    try:
        payload = meta_file.read_text(encoding="utf-8").strip().splitlines()
    except OSError:
        return ProfileLockStatus(locked=True)
    owner = payload[0] if payload else None
    since = payload[1] if len(payload) > 1 else None
    return ProfileLockStatus(locked=True, owner=owner, since=since)


@contextmanager
def acquire_profile_lock(owner: str, path: Path | None = None) -> Iterator[None]:
    from scripts.file_lock import try_lock_exclusive, unlock

    lock_file = path or profile_lock_path()
    meta_file = _lock_meta_path(lock_file)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with lock_file.open("a+b") as stream:
        stream.seek(0)
        if stream.read(1) == b"":
            stream.write(b"\0")
            stream.flush()
        stream.seek(0)
        try:
            try_lock_exclusive(stream)
        except (BlockingIOError, OSError) as exc:
            status = read_lock_status(lock_file)
            holder = status.owner or owner
            raise ProfileLockError(f"Browser profile is already locked: {holder}") from exc
        try:
            meta_file.write_text(
                f"{owner}\n{datetime.now(timezone.utc).isoformat()}\n",
                encoding="utf-8",
            )
            yield
        finally:
            unlock(stream)
            meta_file.unlink(missing_ok=True)
    lock_file.unlink(missing_ok=True)