from __future__ import annotations

import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from .models import UploadStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class UploadTask:
    """Persisted bookkeeping for an ingestion task."""

    timeline_id: str
    filename: str
    source_path: Path
    status: UploadStatus
    size_bytes: Optional[int] = None
    error: Optional[str] = None
    submitted_at: datetime = _utcnow()
    updated_at: datetime = _utcnow()
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "timeline_id": self.timeline_id,
            "filename": self.filename,
            "source_path": str(self.source_path),
            "status": self.status.value,
            "submitted_at": self.submitted_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if self.size_bytes is not None:
            payload["size_bytes"] = self.size_bytes
        if self.completed_at is not None:
            payload["completed_at"] = self.completed_at.isoformat()
        if self.error:
            payload["error"] = self.error
        return payload


class UploadTaskRepository:
    """SQLite-backed persistence for upload lifecycle state."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._connection = sqlite3.connect(db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._migrate()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def generate_timeline_id(self) -> str:
        return uuid.uuid4().hex

    def create(
        self,
        *,
        timeline_id: str,
        filename: str,
        source_path: Path,
        status: UploadStatus,
        size_bytes: Optional[int] = None,
    ) -> UploadTask:
        now = _utcnow()
        task = UploadTask(
            timeline_id=timeline_id,
            filename=filename,
            source_path=source_path,
            status=status,
            size_bytes=size_bytes,
            submitted_at=now,
            updated_at=now,
        )
        self._insert(task)
        return task

    def upsert(self, task: UploadTask) -> UploadTask:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO upload_tasks (
                    timeline_id,
                    filename,
                    source_path,
                    status,
                    size_bytes,
                    error,
                    submitted_at,
                    updated_at,
                    completed_at
                )
                VALUES (:timeline_id, :filename, :source_path, :status, :size_bytes, :error, :submitted_at, :updated_at, :completed_at)
                ON CONFLICT(timeline_id) DO UPDATE SET
                    filename = excluded.filename,
                    source_path = excluded.source_path,
                    status = excluded.status,
                    size_bytes = excluded.size_bytes,
                    error = excluded.error,
                    submitted_at = excluded.submitted_at,
                    updated_at = excluded.updated_at,
                    completed_at = excluded.completed_at
                """,
                self._serialize(task),
            )
            self._connection.commit()
        return task

    def get(self, timeline_id: str) -> Optional[UploadTask]:
        with self._lock:
            cursor = self._connection.execute(
                """
                SELECT timeline_id, filename, source_path, status, size_bytes, error, submitted_at, updated_at, completed_at
                FROM upload_tasks
                WHERE timeline_id = ?
                """,
                (timeline_id,),
            )
            row = cursor.fetchone()
        if not row:
            return None
        return self._deserialize(row)

    def list(self) -> Iterable[UploadTask]:
        with self._lock:
            cursor = self._connection.execute(
                """
                SELECT timeline_id, filename, source_path, status, size_bytes, error, submitted_at, updated_at, completed_at
                FROM upload_tasks
                ORDER BY submitted_at DESC
                """
            )
            rows = cursor.fetchall()
        for row in rows:
            yield self._deserialize(row)

    def update_status(
        self,
        timeline_id: str,
        status: UploadStatus,
        *,
        error: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> UploadTask:
        now = _utcnow()
        with self._lock:
            cursor = self._connection.execute(
                """
                UPDATE upload_tasks
                SET status = ?,
                    error = ?,
                    updated_at = ?,
                    completed_at = ?
                WHERE timeline_id = ?
                """,
                (
                    status.value,
                    error,
                    self._to_iso(now),
                    self._to_iso(completed_at),
                    timeline_id,
                ),
            )
            if cursor.rowcount == 0:
                raise KeyError(timeline_id)
            cursor = self._connection.execute(
                """
                SELECT timeline_id, filename, source_path, status, size_bytes, error, submitted_at, updated_at, completed_at
                FROM upload_tasks
                WHERE timeline_id = ?
                """,
                (timeline_id,),
            )
            row = cursor.fetchone()
            self._connection.commit()

        return self._deserialize(row)

    def _insert(self, task: UploadTask) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO upload_tasks (
                    timeline_id,
                    filename,
                    source_path,
                    status,
                    size_bytes,
                    error,
                    submitted_at,
                    updated_at,
                    completed_at
                )
                VALUES (:timeline_id, :filename, :source_path, :status, :size_bytes, :error, :submitted_at, :updated_at, :completed_at)
                """,
                self._serialize(task),
            )
            self._connection.commit()

    def _migrate(self) -> None:
        with self._lock:
            self._connection.execute("PRAGMA journal_mode=WAL;")
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS upload_tasks (
                    timeline_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    size_bytes INTEGER,
                    error TEXT,
                    submitted_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_upload_tasks_status
                ON upload_tasks(status)
                """
            )
            self._connection.commit()

    @staticmethod
    def _serialize(task: UploadTask) -> dict[str, object]:
        return {
            "timeline_id": task.timeline_id,
            "filename": task.filename,
            "source_path": str(task.source_path),
            "status": task.status.value,
            "size_bytes": task.size_bytes,
            "error": task.error,
            "submitted_at": UploadTaskRepository._to_iso(task.submitted_at),
            "updated_at": UploadTaskRepository._to_iso(task.updated_at),
            "completed_at": UploadTaskRepository._to_iso(task.completed_at),
        }

    @staticmethod
    def _deserialize(row: sqlite3.Row) -> UploadTask:
        submitted_at = UploadTaskRepository._from_iso(row["submitted_at"])
        updated_at = UploadTaskRepository._from_iso(row["updated_at"])
        completed_at = UploadTaskRepository._from_iso(row["completed_at"])
        return UploadTask(
            timeline_id=row["timeline_id"],
            filename=row["filename"],
            source_path=Path(row["source_path"]),
            status=UploadStatus(row["status"]),
            size_bytes=row["size_bytes"],
            error=row["error"],
            submitted_at=submitted_at,
            updated_at=updated_at or submitted_at,
            completed_at=completed_at,
        )

    @staticmethod
    def _to_iso(value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _from_iso(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        return datetime.fromisoformat(value)
