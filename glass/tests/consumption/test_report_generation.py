from __future__ import annotations

import asyncio
import datetime
import sqlite3
import uuid

from glass.consumption import GlassContextSource
from glass.storage import GlassContextRepository, Modality, MultimodalContextItem
from opencontext.context_consumption.generation.generation_report import ReportGenerator
from opencontext.models.context import (
    ContextProperties,
    ExtractedData,
    ProcessedContext,
    RawContextProperties,
    Vectorize,
)
from opencontext.models.enums import ContentFormat, ContextSource, ContextType


def _bootstrap_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE glass_multimodal_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timeline_id TEXT NOT NULL,
            context_id TEXT NOT NULL UNIQUE,
            modality TEXT NOT NULL,
            content_ref TEXT NOT NULL,
            embedding_ready BOOLEAN DEFAULT 0,
            context_type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _make_context(
    *,
    text: str,
    context_type: ContextType,
    metadata: dict,
    create_time: datetime.datetime,
) -> ProcessedContext:
    raw = RawContextProperties(
        content_format=ContentFormat.TEXT,
        source=ContextSource.VIDEO,
        create_time=create_time,
        content_text=text,
    )
    properties = ContextProperties(
        raw_properties=[raw],
        create_time=create_time,
        event_time=create_time,
        update_time=create_time,
    )
    extracted = ExtractedData(
        title=text,
        summary=text,
        keywords=[],
        entities=[],
        tags=[],
        context_type=context_type,
        confidence=1,
        importance=1,
    )
    vectorize = Vectorize(content_format=ContentFormat.TEXT, text=text)
    return ProcessedContext(
        id=str(uuid.uuid4()),
        properties=properties,
        extracted_data=extracted,
        vectorize=vectorize,
        metadata=metadata,
    )


class _StubStorage:
    def __init__(self) -> None:
        self.contexts: dict[tuple[str, str], ProcessedContext] = {}
        self.reports: list[dict[str, str]] = []

    def batch_upsert_processed_context(self, contexts: list[ProcessedContext]):
        for context in contexts:
            key = (context.extracted_data.context_type.value, context.id)
            self.contexts[key] = context
        return [context.id for context in contexts]

    def get_processed_context(self, context_id: str, context_type: str):
        return self.contexts.get((context_type, context_id))

    def get_all_processed_contexts(self, *args, **kwargs):  # pragma: no cover - should not be used here
        raise AssertionError("Timeline-aware fetching should avoid general context queries")

    def insert_vaults(self, title: str, summary: str, content: str, document_type: str):
        self.reports.append({"title": title, "content": content, "document_type": document_type})
        return len(self.reports)


def test_report_generator_prefers_glass_timeline(monkeypatch) -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    _bootstrap_schema(connection)

    storage = _StubStorage()
    repo = GlassContextRepository(storage=storage, connection=connection)
    source = GlassContextSource(repository=repo)

    base_time = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
    contexts = [
        _make_context(
            text="segment-one",
            context_type=ContextType.ACTIVITY_CONTEXT,
            metadata={
                "segment_start": 0.0,
                "segment_end": 4.0,
                "source_video": "videos/demo.mp4",
            },
            create_time=base_time,
        ),
        _make_context(
            text="segment-two",
            context_type=ContextType.ACTIVITY_CONTEXT,
            metadata={
                "segment_start": 4.0,
                "segment_end": 8.0,
                "source_video": "videos/demo.mp4",
            },
            create_time=base_time + datetime.timedelta(seconds=1),
        ),
    ]

    repo.upsert_aligned_segments(
        [
            MultimodalContextItem(
                context=context,
                timeline_id="timeline-consume",
                modality=Modality.AUDIO,
                content_ref=f"segment-{index}",
                embedding_ready=True,
            )
            for index, context in enumerate(contexts)
        ]
    )

    captured_messages: dict[str, list] = {}

    async def _fake_generate(messages, **_kwargs):
        captured_messages["messages"] = messages
        return "Generated report"

    def _fake_get_storage():
        return storage

    def _fake_publish_event(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        "opencontext.context_consumption.generation.generation_report.generate_with_messages_async",
        _fake_generate,
    )
    monkeypatch.setattr(
        "opencontext.storage.global_storage.get_storage",
        _fake_get_storage,
    )
    monkeypatch.setattr(
        "opencontext.managers.event_manager.publish_event",
        _fake_publish_event,
    )

    generator = ReportGenerator(glass_source=source)

    start_ts = int(base_time.timestamp()) - 1
    end_ts = int((base_time + datetime.timedelta(seconds=5)).timestamp())
    report = asyncio.run(generator.generate_report(start_ts, end_ts, timeline_id="timeline-consume"))

    assert report == "Generated report"
    assert storage.reports, "Report content should be persisted"
    assert "messages" in captured_messages
    user_message = captured_messages["messages"][1]["content"]
    assert "segment-two" in user_message
    assert "segment-one" in user_message
    assert "Z" in user_message
