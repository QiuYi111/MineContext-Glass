from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from glass.reports.models import TimelineHighlight, VisualCard

from .models import TimelineRecord, UploadStatus
from .repositories import TimelineRepository
from .services.reports import DailyReportBuilder


def load_demo_timelines(
    directory: Path,
    *,
    repository: TimelineRepository,
    report_builder: DailyReportBuilder,
) -> None:
    """Seed the repository with demo timelines defined in JSON files."""
    if not directory.exists():
        return

    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"[glass.webui.backend] Failed to load demo data {path}: {exc}")
            continue

        for entry in _iter_timelines(payload):
            record = _build_record(entry)
            repository.upsert(record)
            if record.status is UploadStatus.COMPLETED:
                report_builder.build_auto_report(record)
                repository.upsert(record)


def _iter_timelines(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, dict):
        entries = payload.get("timelines") or []
    else:
        entries = payload or []
    for entry in entries:
        if isinstance(entry, dict):
            yield entry


def _build_record(data: dict[str, Any]) -> TimelineRecord:
    timeline_id = data.get("timeline_id") or data.get("id") or "demo-timeline"
    filename = data.get("filename") or data.get("source") or "demo.mp4"
    source_path = Path(data.get("source_path") or filename)

    submitted_at = _parse_datetime(data.get("submitted_at")) or datetime.now(timezone.utc)
    completed_at = _parse_datetime(data.get("completed_at"))

    highlights = [TimelineHighlight(**entry) for entry in data.get("highlights", []) if isinstance(entry, dict)]
    visual_cards = [VisualCard(**entry) for entry in data.get("visual_cards", []) if isinstance(entry, dict)]

    status_value = data.get("status") or "completed"
    try:
        status = UploadStatus(status_value)
    except ValueError:
        status = UploadStatus.COMPLETED

    return TimelineRecord(
        timeline_id=timeline_id,
        filename=filename,
        source_path=source_path,
        status=status,
        submitted_at=submitted_at,
        completed_at=completed_at,
        auto_markdown=data.get("auto_markdown"),
        manual_markdown=data.get("manual_markdown"),
        manual_metadata=data.get("manual_metadata") or {},
        highlights=highlights,
        visual_cards=visual_cards,
        rendered_html=data.get("rendered_html"),
    )


def _parse_datetime(value: Any):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except Exception:  # noqa: BLE001
        return None

