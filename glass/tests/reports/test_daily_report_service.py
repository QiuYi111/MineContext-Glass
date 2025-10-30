from __future__ import annotations

import datetime as dt
from typing import Optional

from glass.processing.envelope import ContextEnvelope
from glass.reports import DailyReportService
from glass.storage import DailyReportRecord, Modality, MultimodalContextItem
from opencontext.models.context import (
    ContextProperties,
    ContextType,
    ExtractedData,
    ProcessedContext,
    RawContextProperties,
    Vectorize,
)
from opencontext.models.enums import ContentFormat, ContextSource


def _make_text_context(
    *,
    summary: str,
    start: float,
    end: float,
    context_id: str,
) -> ProcessedContext:
    now = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    raw = RawContextProperties(
        content_format=ContentFormat.TEXT,
        source=ContextSource.VIDEO,
        create_time=now,
        content_text=summary,
    )
    properties = ContextProperties(
        raw_properties=[raw],
        create_time=now,
        event_time=now,
        update_time=now,
    )
    extracted = ExtractedData(
        title="",
        summary=summary,
        keywords=[],
        entities=[],
        tags=[],
        context_type=ContextType.ACTIVITY_CONTEXT,
        confidence=5,
        importance=3,
    )
    vectorize = Vectorize(content_format=ContentFormat.TEXT, text=summary)
    metadata = {
        "segment_start": start,
        "segment_end": end,
        "source_video": "videos/demo.mp4",
    }
    return ProcessedContext(
        id=context_id,
        properties=properties,
        extracted_data=extracted,
        vectorize=vectorize,
        metadata=metadata,
    )


class _StubRepository:
    def __init__(self, envelope: ContextEnvelope) -> None:
        self._envelope = envelope
        self._record: Optional[DailyReportRecord] = None

    def load_envelope(self, timeline_id: str) -> ContextEnvelope | None:
        return self._envelope if timeline_id == self._envelope.timeline_id else None

    def load_daily_report_record(self, timeline_id: str) -> DailyReportRecord | None:
        return self._record if self._envelope.timeline_id == timeline_id else None

    def upsert_daily_report(
        self,
        *,
        timeline_id: str,
        manual_markdown: str | None,
        manual_metadata: dict | None = None,
        rendered_html: str | None = None,
    ) -> DailyReportRecord:
        self._record = DailyReportRecord(
            timeline_id=timeline_id,
            manual_markdown=manual_markdown,
            manual_metadata=manual_metadata or {},
            rendered_html=rendered_html,
            updated_at=dt.datetime.now(dt.timezone.utc),
        )
        return self._record


def test_service_builds_auto_report() -> None:
    context = _make_text_context(summary="Segment summary", start=0.0, end=3.0, context_id="ctx-1")
    item = MultimodalContextItem(
        context=context,
        timeline_id="timeline-1",
        modality=Modality.AUDIO,
        content_ref="segment-one",
        embedding_ready=True,
    )
    envelope = ContextEnvelope.from_items(
        timeline_id="timeline-1",
        source="videos/demo.mp4",
        items=[item],
    )
    repo = _StubRepository(envelope)
    service = DailyReportService(repository=repo)

    report = service.get_report("timeline-1")

    assert "Glass Timeline Daily Report" in report.auto_markdown
    assert report.highlights, "Highlights should be derived from context summaries"
    assert report.visual_cards == []
    assert report.rendered_html and "<h1>" in report.rendered_html


def test_service_sanitises_manual_markdown() -> None:
    context = _make_text_context(summary="Segment summary", start=0.0, end=3.0, context_id="ctx-1")
    item = MultimodalContextItem(
        context=context,
        timeline_id="timeline-2",
        modality=Modality.AUDIO,
        content_ref="segment-one",
        embedding_ready=True,
    )
    envelope = ContextEnvelope.from_items(
        timeline_id="timeline-2",
        source="videos/demo.mp4",
        items=[item],
    )
    repo = _StubRepository(envelope)
    service = DailyReportService(repository=repo)

    report = service.save_manual_report(
        timeline_id="timeline-2",
        manual_markdown="# Title\n\n<script>alert('x');</script>",
        manual_metadata={"foo": "bar"},
        envelope=envelope,
    )

    assert report.manual_markdown.startswith("# Title")
    assert "<script>" not in report.rendered_html
    assert report.manual_metadata == {"foo": "bar"}
    assert repo._record is not None and "<script>" not in (repo._record.rendered_html or "")


def test_highlight_includes_thumbnail_for_frames() -> None:
    context = _make_text_context(summary="Frame summary", start=10.0, end=13.0, context_id="ctx-frame")
    item = MultimodalContextItem(
        context=context,
        timeline_id="timeline-frame",
        modality=Modality.FRAME,
        content_ref="frames/frame-001.png",
        embedding_ready=True,
    )
    envelope = ContextEnvelope.from_items(
        timeline_id="timeline-frame",
        source="videos/demo.mp4",
        items=[item],
    )
    repo = _StubRepository(envelope)
    service = DailyReportService(repository=repo)

    report = service.get_report("timeline-frame")

    assert report.highlights, "Frame highlight should be generated"
    assert report.highlights[0].thumbnail_url == "frames/frame-001.png"
