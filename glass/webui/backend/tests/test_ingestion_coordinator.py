from __future__ import annotations

import datetime as dt
from pathlib import Path

from glass.ingestion.models import IngestionStatus
from glass.reports.models import DailyReport
from glass.reports.service import DailyReportService
from glass.storage.context_repository import DailyReportRecord
from glass.storage.models import Modality, MultimodalContextItem
from opencontext.models.context import (
    ContextProperties,
    ExtractedData,
    ProcessedContext,
    Vectorize,
)
from opencontext.models.enums import ContentFormat, ContextType

from glass.webui.backend.config import BackendConfig
from glass.webui.backend.models import UploadStatus
from glass.webui.backend.services.ingestion import IngestionCoordinator, ReportNotReadyError
from glass.webui.backend.state import UploadTaskRepository


class _StubIngestionService:
    def __init__(self) -> None:
        self._tasks = {}

    def get_status(self, timeline_id: str) -> IngestionStatus:
        return IngestionStatus.COMPLETED


class _StubContextRepository:
    def __init__(self, envelope) -> None:
        self._envelope = envelope
        self._manual: DailyReportRecord | None = None
        self.cleared = False

    def load_envelope(self, timeline_id: str, *, modalities=None):
        if timeline_id != self._envelope.timeline_id:
            return None
        return self._envelope

    def load_daily_report_record(self, timeline_id: str) -> DailyReportRecord | None:
        if timeline_id != self._envelope.timeline_id:
            return None
        return self._manual

    def upsert_daily_report(
        self,
        *,
        timeline_id: str,
        manual_markdown: str | None,
        manual_metadata: dict | None = None,
        rendered_html: str | None = None,
    ) -> DailyReportRecord:
        if timeline_id != self._envelope.timeline_id:
            raise RuntimeError("unknown timeline")
        record = DailyReportRecord(
            timeline_id=timeline_id,
            manual_markdown=manual_markdown,
            manual_metadata=manual_metadata or {},
            rendered_html=rendered_html,
            updated_at=dt.datetime.now(dt.timezone.utc),
        )
        self._manual = record
        return record

    def clear_daily_report(self, timeline_id: str) -> None:
        if timeline_id != self._envelope.timeline_id:
            return
        self._manual = None
        self.cleared = True


def _make_envelope(timeline_id: str) -> tuple:
    now = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    properties = ContextProperties(create_time=now, event_time=now, update_time=now)
    extracted = ExtractedData(summary="Auto highlight", context_type=ContextType.ACTIVITY_CONTEXT)
    vectorize = Vectorize(content_format=ContentFormat.TEXT, text="hello world")

    processed_audio = ProcessedContext(
        properties=properties,
        extracted_data=extracted,
        vectorize=vectorize,
    )
    processed_audio.metadata = {
        "segment_start": 0.0,
        "segment_end": 5.0,
        "thumbnail_url": "thumb-a.png",
    }

    processed_frame = ProcessedContext(
        properties=properties,
        extracted_data=extracted,
        vectorize=vectorize,
    )
    processed_frame.metadata = {
        "segment_start": 5.0,
        "segment_end": 10.0,
        "thumbnail_url": "thumb-b.png",
    }

    audio_item = MultimodalContextItem(
        context=processed_audio,
        timeline_id=timeline_id,
        modality=Modality.AUDIO,
        content_ref="audio.wav",
        embedding_ready=True,
    )
    frame_item = MultimodalContextItem(
        context=processed_frame,
        timeline_id=timeline_id,
        modality=Modality.FRAME,
        content_ref="frame.png",
        embedding_ready=True,
    )

    from glass.processing.envelope import ContextEnvelope

    envelope = ContextEnvelope.from_items(
        timeline_id=timeline_id,
        source="video.mp4",
        items=[audio_item, frame_item],
    )

    report = DailyReport(
        timeline_id=timeline_id,
        source="video.mp4",
        auto_markdown="# Auto report\n\n- Item",
        manual_markdown=None,
        rendered_html="<h1>Auto</h1>",
        highlights=[],
        visual_cards=[],
        manual_metadata={},
        updated_at=now,
    )
    return envelope, report


def test_build_context_payload_uses_real_envelope(tmp_path) -> None:
    timeline_id = "timeline-real"
    envelope, _ = _make_envelope(timeline_id)
    repository = _StubContextRepository(envelope)
    report_service = DailyReportService(repository=repository)
    config = BackendConfig(
        mode="real",
        upload_dir=tmp_path / "uploads",
        state_db_path=tmp_path / "state.db",
        storage_base_dir=tmp_path / "storage",
    )
    ingestion = _StubIngestionService()
    tasks = UploadTaskRepository(config.state_db_path)
    tasks.create(
        timeline_id=timeline_id,
        filename="video.mp4",
        source_path=Path("video.mp4"),
        status=UploadStatus.COMPLETED,
    )

    coordinator = IngestionCoordinator(
        config=config,
        tasks=tasks,
        ingestion_service=ingestion,
        context_repository=repository,
        report_service=report_service,
    )

    payload = coordinator.build_context_payload(timeline_id)
    assert payload["timeline_id"] == timeline_id
    assert payload["source"] == "video.mp4"
    assert payload["daily_report"]["timeline_id"] == timeline_id
    assert payload["items"][0]["context_id"]
    assert "summary" in payload
    assert payload["visual_cards"]
    assert payload["visual_cards"][0]["image_url"] == "frame.png"


def test_save_manual_report_requires_envelope(tmp_path) -> None:
    timeline_id = "timeline-real"
    envelope, _ = _make_envelope(timeline_id)
    repository = _StubContextRepository(envelope)
    report_service = DailyReportService(repository=repository)
    config = BackendConfig(
        mode="real",
        upload_dir=tmp_path / "uploads",
        state_db_path=tmp_path / "state.db",
        storage_base_dir=tmp_path / "storage",
    )
    ingestion = _StubIngestionService()
    tasks = UploadTaskRepository(config.state_db_path)
    tasks.create(
        timeline_id=timeline_id,
        filename="video.mp4",
        source_path=Path("video.mp4"),
        status=UploadStatus.COMPLETED,
    )

    coordinator = IngestionCoordinator(
        config=config,
        tasks=tasks,
        ingestion_service=ingestion,
        context_repository=repository,
        report_service=report_service,
    )

    updated = coordinator.save_manual_report(
        timeline_id,
        markdown="# Manual report",
        metadata={"pinned": ["ctx-1"]},
    )
    assert updated.manual_markdown == "# Manual report"
    assert repository.load_daily_report_record(timeline_id) is not None

    repository.clear_daily_report(timeline_id)
    assert repository.cleared is True

    result = coordinator.regenerate_report(timeline_id)
    assert result.timeline_id == timeline_id
    assert repository.cleared is True


def test_build_context_payload_blocks_when_missing_envelope(tmp_path) -> None:
    timeline_id = "timeline-missing"
    envelope, _ = _make_envelope("other-timeline")
    repository = _StubContextRepository(envelope)
    report_service = DailyReportService(repository=repository)
    config = BackendConfig(
        mode="real",
        upload_dir=tmp_path / "uploads",
        state_db_path=tmp_path / "state.db",
        storage_base_dir=tmp_path / "storage",
    )
    ingestion = _StubIngestionService()
    tasks = UploadTaskRepository(config.state_db_path)
    tasks.create(
        timeline_id=timeline_id,
        filename="video.mp4",
        source_path=Path("video.mp4"),
        status=UploadStatus.PROCESSING,
    )

    coordinator = IngestionCoordinator(
        config=config,
        tasks=tasks,
        ingestion_service=ingestion,
        context_repository=repository,
        report_service=report_service,
    )

    try:
        coordinator.build_context_payload(timeline_id)
    except ReportNotReadyError:
        pass
    else:
        raise AssertionError("expected ReportNotReadyError")
