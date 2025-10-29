from __future__ import annotations

import datetime as dt
import threading
import uuid
from pathlib import Path
from typing import Dict, Iterable, Optional

from .models import TimelineRecord, UploadStatus


class TimelineRepository:
    """In-memory timeline store with coarse locking suitable for the demo backend."""

    def __init__(self) -> None:
        self._records: Dict[str, TimelineRecord] = {}
        self._lock = threading.RLock()

    def generate_timeline_id(self) -> str:
        return uuid.uuid4().hex

    def upsert(self, record: TimelineRecord) -> TimelineRecord:
        with self._lock:
            self._records[record.timeline_id] = record
        return record

    def create(self, *, filename: str, source_path: Path) -> TimelineRecord:
        timeline_id = self.generate_timeline_id()
        record = TimelineRecord(
            timeline_id=timeline_id,
            filename=filename,
            source_path=source_path,
            status=UploadStatus.UPLOADING,
        )
        return self.upsert(record)

    def get(self, timeline_id: str) -> Optional[TimelineRecord]:
        with self._lock:
            return self._records.get(timeline_id)

    def all(self) -> Iterable[TimelineRecord]:
        with self._lock:
            return tuple(self._records.values())

    def update_status(self, timeline_id: str, status: UploadStatus) -> TimelineRecord:
        with self._lock:
            record = self._records.get(timeline_id)
            if record is None:
                raise KeyError(timeline_id)
            record.status = status
            if status is UploadStatus.COMPLETED:
                record.completed_at = dt.datetime.now(dt.timezone.utc)
            elif status is UploadStatus.FAILED:
                record.completed_at = None
            self._records[timeline_id] = record
            return record

    def save_manual_report(
        self,
        timeline_id: str,
        *,
        manual_markdown: str,
        manual_metadata: dict,
    ) -> TimelineRecord:
        with self._lock:
            record = self._records.get(timeline_id)
            if record is None:
                raise KeyError(timeline_id)
            record.manual_markdown = manual_markdown
            record.manual_metadata = manual_metadata
            self._records[timeline_id] = record
            return record

