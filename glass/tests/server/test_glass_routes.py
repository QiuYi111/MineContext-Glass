from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from glass.ingestion import IngestionStatus, TimelineNotFoundError
from glass.processing.envelope import ContextEnvelope
from glass.storage.context_repository import DailyReportRecord
from glass.storage.models import Modality, MultimodalContextItem
from opencontext.models.context import (
    ContextProperties,
    ExtractedData,
    ProcessedContext,
    Vectorize,
)
from opencontext.models.enums import ContentFormat, ContextType
from opencontext.server.routes import glass as glass_routes


class _StubIngestionService:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._counter = 0
        self.status: dict[str, IngestionStatus] = {}
        self.destinations: list[Path] = []

    def allocate_upload_path(self, filename: str) -> Path:
        return self._base_dir / filename

    def submit(self, destination: Path) -> str:
        self.destinations.append(destination)
        self._counter += 1
        timeline_id = f"timeline-{self._counter}"
        self.status[timeline_id] = IngestionStatus.PROCESSING
        return timeline_id

    def get_status(self, timeline_id: str) -> IngestionStatus:
        if timeline_id not in self.status:
            raise TimelineNotFoundError(timeline_id)
        return self.status[timeline_id]


class _StubRepository:
    def __init__(self, envelopes: dict[str, ContextEnvelope]):
        self._envelopes = envelopes
        self._reports: dict[str, DailyReportRecord] = {}

    def load_envelope(self, timeline_id: str) -> ContextEnvelope | None:
        return self._envelopes.get(timeline_id)

    def load_daily_report_record(self, timeline_id: str) -> DailyReportRecord | None:
        return self._reports.get(timeline_id)

    def upsert_daily_report(
        self,
        *,
        timeline_id: str,
        manual_markdown: str | None,
        manual_metadata: dict | None = None,
        rendered_html: str | None = None,
    ) -> DailyReportRecord:
        record = DailyReportRecord(
            timeline_id=timeline_id,
            manual_markdown=manual_markdown,
            manual_metadata=manual_metadata or {},
            rendered_html=rendered_html,
            updated_at=dt.datetime.now(dt.timezone.utc),
        )
        self._reports[timeline_id] = record
        return record


def _make_fastapi_app(ingestion_service: Any, repository: Any | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(glass_routes.router)
    app.dependency_overrides[glass_routes._get_ingestion_service] = lambda: ingestion_service
    if repository is not None:
        app.dependency_overrides[glass_routes._get_repository] = lambda: repository
    return TestClient(app)


def test_upload_endpoint_persists_file(tmp_path: Path) -> None:
    service = _StubIngestionService(tmp_path)
    client = _make_fastapi_app(service)

    response = client.post(
        "/glass/upload",
        files={"file": ("demo.mp4", b"fake-bytes", "video/mp4")},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    timeline_id = payload["timeline_id"]
    assert timeline_id in service.status
    assert (tmp_path / "demo.mp4").exists()
    assert payload["status"] == IngestionStatus.PROCESSING.value


def test_status_endpoint_returns_not_found(tmp_path: Path) -> None:
    service = _StubIngestionService(tmp_path)
    client = _make_fastapi_app(service)

    response = client.get("/glass/status/unknown-timeline")
    assert response.status_code == 404


def test_upload_limits_endpoint_returns_defaults(tmp_path: Path) -> None:
    service = _StubIngestionService(tmp_path)
    client = _make_fastapi_app(service)

    response = client.get("/glass/uploads/limits")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["max_size_mb"] > 0
    assert "allowed_types" in data


def test_context_endpoint_serializes_envelope(tmp_path: Path) -> None:
    service = _StubIngestionService(tmp_path)
    timeline_id = service.submit(tmp_path / "unused.mp4")
    service.status[timeline_id] = IngestionStatus.COMPLETED

    now = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    properties = ContextProperties(
        create_time=now,
        event_time=now,
        update_time=now,
    )
    extracted = ExtractedData(
        summary="Example summary",
        context_type=ContextType.ACTIVITY_CONTEXT,
    )
    vectorize = Vectorize(
        content_format=ContentFormat.TEXT,
        text="hello world",
    )
    processed = ProcessedContext(
        properties=properties,
        extracted_data=extracted,
        vectorize=vectorize,
    )
    processed.metadata = {"segment_start": 0.0, "segment_end": 2.5}

    item = MultimodalContextItem(
        context=processed,
        timeline_id=timeline_id,
        modality=Modality.AUDIO,
        content_ref="audio.wav",
        embedding_ready=True,
    )
    envelope = ContextEnvelope.from_items(
        timeline_id=timeline_id,
        source="video.mp4",
        items=[item],
    )
    repository = _StubRepository({timeline_id: envelope})

    client = _make_fastapi_app(service, repository)
    response = client.get(f"/glass/context/{timeline_id}")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["timeline_id"] == timeline_id
    assert data["items"][0]["modality"] == Modality.AUDIO.value
    assert "daily_report" in data
    assert data["highlights"], "highlights should be derived from contexts"
    assert data["daily_report"]["auto_markdown"]
    assert data["summary"], "summary should provide a condensed view"
    assert "thumbnail_url" in data["highlights"][0]


def test_report_endpoints_support_manual_updates(tmp_path: Path) -> None:
    service = _StubIngestionService(tmp_path)
    timeline_id = service.submit(tmp_path / "unused.mp4")
    service.status[timeline_id] = IngestionStatus.COMPLETED

    now = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    properties = ContextProperties(
        create_time=now,
        event_time=now,
        update_time=now,
    )
    extracted = ExtractedData(
        summary="Auto summary",
        context_type=ContextType.ACTIVITY_CONTEXT,
    )
    vectorize = Vectorize(
        content_format=ContentFormat.TEXT,
        text="text",
    )
    processed = ProcessedContext(
        properties=properties,
        extracted_data=extracted,
        vectorize=vectorize,
    )
    processed.metadata = {"segment_start": 5.0, "segment_end": 8.0}

    item = MultimodalContextItem(
        context=processed,
        timeline_id=timeline_id,
        modality=Modality.AUDIO,
        content_ref="audio.wav",
        embedding_ready=True,
    )
    envelope = ContextEnvelope.from_items(
        timeline_id=timeline_id,
        source="video.mp4",
        items=[item],
    )
    repository = _StubRepository({timeline_id: envelope})
    client = _make_fastapi_app(service, repository)

    initial = client.get(f"/glass/report/{timeline_id}")
    assert initial.status_code == 200
    initial_data = initial.json()["data"]
    assert initial_data["auto_markdown"]
    assert initial_data["manual_markdown"] is None

    updated = client.put(
        f"/glass/report/{timeline_id}",
        json={
            "manual_markdown": "# My Report\n\nUpdated content.",
            "manual_metadata": {"pinned": True},
        },
    )
    assert updated.status_code == 200
    updated_data = updated.json()["data"]
    assert "# My Report" in updated_data["manual_markdown"]
    assert updated_data["manual_metadata"]["pinned"] is True

    follow_up = client.get(f"/glass/report/{timeline_id}")
    assert follow_up.status_code == 200
    follow_data = follow_up.json()["data"]
    assert follow_data["manual_markdown"].startswith("# My Report")
