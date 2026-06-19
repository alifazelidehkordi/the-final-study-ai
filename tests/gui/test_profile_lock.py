from __future__ import annotations

import pytest

from gui.dependencies.profile_lock import ProfileLockError, acquire_profile_lock, read_lock_status


def test_profile_lock_exclusive_access(tmp_path) -> None:
    lock_path = tmp_path / "profile.lock"
    with acquire_profile_lock("setup", lock_path):
        status = read_lock_status(lock_path)
        assert status.locked is True
        assert status.owner == "setup"
    assert read_lock_status(lock_path).locked is False


def test_profile_lock_rejects_second_holder(tmp_path) -> None:
    lock_path = tmp_path / "profile.lock"
    with acquire_profile_lock("setup", lock_path), pytest.raises(ProfileLockError):
        with acquire_profile_lock("pipeline", lock_path):
            pass