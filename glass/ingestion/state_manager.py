"""
Atomic state management for video ingestion pipeline.

Implements Linus Torvalds' principles:
- Single source of truth
- No special cases
- Atomic operations
- Simple, reliable state transitions
"""

from __future__ import annotations

import fcntl
import json
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from loguru import logger

from .models import IngestionStatus


class StateError(RuntimeError):
    """Raised when state operations fail."""


@dataclass
class TimelineState:
    """Atomic state representation for a timeline."""

    timeline_id: str
    status: IngestionStatus
    created_at: float
    updated_at: float
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timeline_id": self.timeline_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TimelineState:
        return cls(
            timeline_id=data["timeline_id"],
            status=IngestionStatus(data["status"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            error_message=data.get("error_message"),
        )


class AtomicStateManager:
    """
    Atomic state manager that eliminates race conditions.

    Uses file locking to ensure atomic read-modify-write operations.
    Maintains single source of truth in a single state file.
    """

    STATE_FILE = "timeline_state.json"
    LOCK_FILE = "timeline_state.lock"
    LOCK_TIMEOUT = 30.0  # seconds

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir.resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _get_timeline_dir(self, timeline_id: str) -> Path:
        return self._base_dir / timeline_id

    def _acquire_lock(self, timeline_dir: Path) -> Path:
        """Acquire exclusive lock for timeline state operations."""
        lock_path = timeline_dir / self.LOCK_FILE
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        # Open lock file
        lock_fd = lock_path.open('w')

        # Try to acquire exclusive lock with timeout
        start_time = time.time()
        while time.time() - start_time < self.LOCK_TIMEOUT:
            try:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return lock_fd
            except BlockingIOError:
                time.sleep(0.1)
                continue

        lock_fd.close()
        raise StateError(f"Failed to acquire lock for timeline {timeline_dir.name} within {self.LOCK_TIMEOUT}s")

    def _release_lock(self, lock_fd: Path) -> None:
        """Release the lock."""
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()
        except Exception:
            pass  # Best effort cleanup

    def create_timeline(self, timeline_id: str) -> TimelineState:
        """Create a new timeline with PENDING status."""
        timeline_dir = self._get_timeline_dir(timeline_id)
        timeline_dir.mkdir(parents=True, exist_ok=True)

        lock_fd = self._acquire_lock(timeline_dir)
        try:
            state = TimelineState(
                timeline_id=timeline_id,
                status=IngestionStatus.PENDING,
                created_at=time.time(),
                updated_at=time.time(),
            )
            self._write_state(timeline_dir, state)
            return state
        finally:
            self._release_lock(lock_fd)

    def get_state(self, timeline_id: str) -> TimelineState:
        """
        Get current state for timeline.

        Raises:
            StateError: If timeline doesn't exist
        """
        timeline_dir = self._get_timeline_dir(timeline_id)
        if not timeline_dir.exists():
            raise StateError(f"Timeline {timeline_id} not found")

        lock_fd = self._acquire_lock(timeline_dir)
        try:
            return self._read_state(timeline_dir)
        finally:
            self._release_lock(lock_fd)

    def update_status(self, timeline_id: str, status: IngestionStatus, error_message: Optional[str] = None) -> TimelineState:
        """Update timeline status atomically."""
        timeline_dir = self._get_timeline_dir(timeline_id)
        if not timeline_dir.exists():
            raise StateError(f"Timeline {timeline_id} not found")

        lock_fd = self._acquire_lock(timeline_dir)
        try:
            state = self._read_state(timeline_dir)
            state.status = status
            state.updated_at = time.time()
            state.error_message = error_message
            self._write_state(timeline_dir, state)
            return state
        finally:
            self._release_lock(lock_fd)

    def _read_state(self, timeline_dir: Path) -> TimelineState:
        """Read state from file. Must be called with lock held."""
        state_path = timeline_dir / self.STATE_FILE
        if not state_path.exists():
            raise StateError(f"State file not found for timeline {timeline_dir.name}")

        try:
            data = json.loads(state_path.read_text())
            return TimelineState.from_dict(data)
        except (json.JSONDecodeError, KeyError) as exc:
            raise StateError(f"Invalid state file format for timeline {timeline_dir.name}: {exc}") from exc

    def _write_state(self, timeline_dir: Path, state: TimelineState) -> None:
        """Write state to file. Must be called with lock held."""
        state_path = timeline_dir / self.STATE_FILE
        state_path.write_text(json.dumps(state.to_dict(), indent=2))

    def cleanup_timeline(self, timeline_id: str) -> None:
        """Clean up timeline state files."""
        timeline_dir = self._get_timeline_dir(timeline_id)
        if not timeline_dir.exists():
            return

        lock_fd = self._acquire_lock(timeline_dir)
        try:
            # Remove state files but keep timeline directory and content
            state_path = timeline_dir / self.STATE_FILE
            lock_path = timeline_dir / self.LOCK_FILE

            if state_path.exists():
                state_path.unlink()
            if lock_path.exists():
                lock_path.unlink()
        finally:
            self._release_lock(lock_fd)


def create_state_manager(base_dir: Path | None = None) -> AtomicStateManager:
    """Factory function to create state manager."""
    base = base_dir or Path("persist") / "glass"
    return AtomicStateManager(base)