from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from glass.ingestion import IngestionStatus, TimelineNotFoundError
from glass.processing.envelope import ContextEnvelope
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

    def load_envelope(self, timeline_id: str) -> ContextEnvelope | None:
        return self._envelopes.get(timeline_id)


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
