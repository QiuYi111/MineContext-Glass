from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from glass.processing.envelope import ContextEnvelope
from glass.reports.models import DailyReport
from glass.storage.context_repository import DailyReportRecord
from glass.storage.models import Modality, MultimodalContextItem

from .models import UploadStatus
from .state import UploadTask, UploadTaskRepository


@dataclass(slots=True)
class SnapshotTimeline:
    """Materialised representation of a timeline stored in a demo snapshot."""

    timeline_id: str
    filename: str
    source_path: Path
    status: UploadStatus
    submitted_at: Optional[datetime]
    completed_at: Optional[datetime]
    envelope: ContextEnvelope
    report: DailyReport

    def clone_envelope(self, *, modalities: Sequence[Modality] | None = None) -> Optional[ContextEnvelope]:
        if not modalities:
            return self.envelope

        allowed = {modality for modality in modalities}
        # Filter items using the same semantics as GlassContextRepository
        filtered: List[MultimodalContextItem] = [
            item for item in self.envelope.items if item.modality in allowed
        ]
        if not filtered:
            return None
        return ContextEnvelope.from_items(
            timeline_id=self.envelope.timeline_id,
            source=self.envelope.source,
            items=filtered,
        )


class SnapshotContextRepository:
    """Read/write facade over snapshot timelines mimicking GlassContextRepository."""

    def __init__(self, timelines: Dict[str, SnapshotTimeline]) -> None:
        self._timelines = timelines

    def load_envelope(
        self,
        timeline_id: str,
        *,
        modalities: Sequence[Modality] | None = None,
    ):
        timeline = self._timelines.get(timeline_id)
        if not timeline:
            return None
        return timeline.clone_envelope(modalities=modalities)

    def load_daily_report_record(self, timeline_id: str) -> DailyReportRecord | None:
        timeline = self._timelines.get(timeline_id)
        if not timeline:
            return None
        report = timeline.report
        manual_metadata = report.manual_metadata or {}
        updated_at = report.updated_at
        return DailyReportRecord(
            timeline_id=timeline_id,
            manual_markdown=report.manual_markdown,
            manual_metadata=manual_metadata,
            rendered_html=report.rendered_html,
            updated_at=updated_at,
        )

    def upsert_daily_report(
        self,
        *,
        timeline_id: str,
        manual_markdown: str | None,
        manual_metadata: dict | None = None,
        rendered_html: str | None = None,
    ) -> DailyReportRecord:
        timeline = self._timelines.get(timeline_id)
        if not timeline:
            raise RuntimeError(f"unknown timeline {timeline_id}")

        report = timeline.report
        report.manual_markdown = manual_markdown
        report.manual_metadata = manual_metadata or {}
        report.rendered_html = rendered_html
        report.updated_at = datetime.now(timezone.utc)
        return DailyReportRecord(
            timeline_id=timeline_id,
            manual_markdown=report.manual_markdown,
            manual_metadata=report.manual_metadata,
            rendered_html=report.rendered_html,
            updated_at=report.updated_at,
        )

    def clear_daily_report(self, timeline_id: str) -> None:
        timeline = self._timelines.get(timeline_id)
        if not timeline:
            return
        report = timeline.report
        report.manual_markdown = None
        report.manual_metadata = {}
        report.rendered_html = None
        report.updated_at = datetime.now(timezone.utc)


def load_snapshot(directory: Path) -> Dict[str, SnapshotTimeline]:
    """Load snapshot JSON payloads from the provided directory."""
    timelines: Dict[str, SnapshotTimeline] = {}
    if not directory.exists():
        return timelines

    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        for entry in _iter_timelines(payload):
            timeline = _build_timeline(entry)
            timelines[timeline.timeline_id] = timeline

    return timelines


def seed_upload_tasks(tasks: UploadTaskRepository, timelines: Iterable[SnapshotTimeline]) -> None:
    """Populate the upload task repository from snapshot metadata."""
    now = datetime.now(timezone.utc)
    for timeline in timelines:
        submitted_at = timeline.submitted_at or now
        completed_at = timeline.completed_at
        tasks.upsert(
            UploadTask(
                timeline_id=timeline.timeline_id,
                filename=timeline.filename,
                source_path=timeline.source_path,
                status=timeline.status,
                submitted_at=submitted_at,
                updated_at=completed_at or submitted_at,
                completed_at=completed_at,
            )
        )


def _iter_timelines(payload: object) -> Iterable[dict]:
    if isinstance(payload, dict):
        entries = payload.get("timelines") or []
    else:
        entries = payload or []
    for entry in entries:
        if isinstance(entry, dict):
            yield entry


def _build_timeline(entry: dict) -> SnapshotTimeline:
    timeline_id = entry.get("timeline_id")
    if not timeline_id:
        raise ValueError("timeline entry missing timeline_id")

    status_value = entry.get("status", UploadStatus.COMPLETED.value)
    status = UploadStatus(status_value)

    source_path = entry.get("source_path") or entry.get("filename") or timeline_id
    filename = entry.get("filename") or Path(source_path).name

    envelope_payload = entry.get("envelope")
    if not envelope_payload:
        raise ValueError(f"timeline {timeline_id} missing envelope payload")
    envelope = ContextEnvelope.model_validate(envelope_payload)

    report_payload = entry.get("report")
    if not report_payload:
        raise ValueError(f"timeline {timeline_id} missing report payload")
    report = DailyReport.model_validate(report_payload)

    submitted_at = _parse_datetime(entry.get("submitted_at"))
    completed_at = _parse_datetime(entry.get("completed_at"))

    return SnapshotTimeline(
        timeline_id=timeline_id,
        filename=filename,
        source_path=Path(source_path),
        status=status,
        submitted_at=submitted_at,
        completed_at=completed_at,
        envelope=envelope,
        report=report,
    )


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(value.replace(" ", "T"))
        except Exception:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
