"""Cross-platform advisory file locks for manifests and browser profiles."""

from __future__ import annotations

import sys
from typing import IO


def lock_exclusive_blocking(stream: IO[bytes]) -> None:
    """Acquire an exclusive lock, blocking until it is available."""
    if sys.platform == "win32":
        import msvcrt

        msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        return
    import fcntl

    fcntl.flock(stream.fileno(), fcntl.LOCK_EX)


def try_lock_exclusive(stream: IO[bytes]) -> None:
    """Acquire an exclusive lock or raise BlockingIOError / OSError."""
    if sys.platform == "win32":
        import msvcrt

        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        return
    import fcntl

    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def unlock(stream: IO[bytes]) -> None:
    """Release an advisory lock on the stream."""
    if sys.platform == "win32":
        import msvcrt

        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)