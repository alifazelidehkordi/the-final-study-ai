"""Exclusive browser-profile lock shared by Setup and pipeline runs."""

from __future__ import annotations

import os
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


def read_lock_status(path: Path | None = None) -> ProfileLockStatus:
    lock_file = path or profile_lock_path()
    if not lock_file.exists():
        return ProfileLockStatus(locked=False)
    try:
        payload = lock_file.read_text(encoding="utf-8").strip().splitlines()
    except OSError:
        return ProfileLockStatus(locked=True)
    owner = payload[0] if payload else None
    since = payload[1] if len(payload) > 1 else None
    return ProfileLockStatus(locked=True, owner=owner, since=since)


@contextmanager
def acquire_profile_lock(owner: str, path: Path | None = None) -> Iterator[None]:
    lock_file = path or profile_lock_path()
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with lock_file.open("a+b") as stream:
        stream.seek(0)
        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined]
            except OSError as exc:
                raise ProfileLockError(f"Browser profile is already locked: {owner}") from exc
            try:
                stream.seek(0)
                stream.truncate(0)
                stream.write(f"{owner}\n{datetime.now(timezone.utc).isoformat()}\n".encode())
                stream.flush()
                yield
            finally:
                stream.seek(0)
                stream.truncate(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
        else:
            import fcntl

            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                status = read_lock_status(lock_file)
                raise ProfileLockError(
                    f"Browser profile is already locked: {status.owner or 'unknown'}"
                ) from exc
            try:
                stream.seek(0)
                stream.truncate(0)
                stream.write(f"{owner}\n{datetime.now(timezone.utc).isoformat()}\n".encode())
                stream.flush()
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    lock_file.unlink(missing_ok=True)