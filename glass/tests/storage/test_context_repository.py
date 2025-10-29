from __future__ import annotations

import datetime
import sqlite3
import uuid
from collections import defaultdict

import pytest

from glass.storage import GlassContextRepository, Modality, MultimodalContextItem
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
            auto_summary_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE glass_daily_reports (
            timeline_id TEXT PRIMARY KEY,
            manual_markdown TEXT,
            manual_metadata TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _make_context(
    text: str,
    context_id: str | None = None,
    *,
    context_type: ContextType = ContextType.SEMANTIC_CONTEXT,
    metadata: dict | None = None,
    create_time: datetime.datetime | None = None,
) -> ProcessedContext:
    now = create_time or datetime.datetime.now(datetime.timezone.utc)
    raw = RawContextProperties(
        content_format=ContentFormat.TEXT,
        source=ContextSource.OTHER,
        create_time=now,
        content_text=text,
    )
    properties = ContextProperties(
        raw_properties=[raw],
        create_time=now,
        event_time=now,
        update_time=now,
    )
    extracted = ExtractedData(
        title="",
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
        id=context_id or str(uuid.uuid4()),
        properties=properties,
        extracted_data=extracted,
        vectorize=vectorize,
        metadata=metadata or {},
    )


class _FakeStorage:
    def __init__(self) -> None:
        self.contexts: dict[tuple[str, str], ProcessedContext] = {}

    def batch_upsert_processed_context(self, contexts: list[ProcessedContext]):
        buckets: dict[str, list[ProcessedContext]] = defaultdict(list)
        for context in contexts:
            context_type = context.extracted_data.context_type.value
            key = (context_type, context.id)
            self.contexts[key] = context
            buckets[context_type].append(context)

        ordered_ids: list[str] = []
        for bucket in buckets.values():
            ordered_ids.extend([ctx.id for ctx in bucket])
        return ordered_ids

    def get_processed_context(self, context_id: str, context_type: str):
        return self.contexts.get((context_type, context_id))


def _make_repo(connection: sqlite3.Connection, storage: _FakeStorage | None = None) -> GlassContextRepository:
    storage = storage or _FakeStorage()
    connection.row_factory = sqlite3.Row
    _bootstrap_schema(connection)
    return GlassContextRepository(storage=storage, connection=connection)


def test_upsert_persists_and_fetches_segments() -> None:
    connection = sqlite3.connect(":memory:")
    storage = _FakeStorage()
    repo = _make_repo(connection, storage)

    context = _make_context("hello world")
    item = MultimodalContextItem(
        context=context,
        timeline_id="timeline-1",
        modality=Modality.AUDIO,
        content_ref="segment-001",
        embedding_ready=True,
    )

    ids = repo.upsert_aligned_segments([item])
    assert ids == [context.id]
    assert list(storage.contexts.values()) == [context]

    rows = repo.fetch_by_timeline("timeline-1")
    assert len(rows) == 1
    row = rows[0]
    assert row["context_id"] == context.id
    assert row["embedding_ready"] == 1
    assert row["content_ref"] == "segment-001"
    assert row["context_type"] == context.extracted_data.context_type.value


def test_upsert_preserves_context_type_alignment_when_backend_reorders_ids() -> None:
    connection = sqlite3.connect(":memory:")
    storage = _FakeStorage()
    repo = _make_repo(connection, storage)

    base_time = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
    items: list[MultimodalContextItem] = []
    for index, (text, ctx_type, modality) in enumerate(
        [
            ("audio-a", ContextType.ACTIVITY_CONTEXT, Modality.AUDIO),
            ("frame-a", ContextType.STATE_CONTEXT, Modality.FRAME),
            ("audio-b", ContextType.ACTIVITY_CONTEXT, Modality.AUDIO),
            ("frame-b", ContextType.STATE_CONTEXT, Modality.FRAME),
        ]
    ):
        context = _make_context(
            text=text,
            context_type=ctx_type,
            create_time=base_time + datetime.timedelta(seconds=index),
        )
        items.append(
            MultimodalContextItem(
                context=context,
                timeline_id="timeline-mixed",
                modality=modality,
                content_ref=f"segment-{index}",
                embedding_ready=True,
            )
        )

    persisted_ids = repo.upsert_aligned_segments(items)
    assert persisted_ids and len(persisted_ids) == len(items)

    rows = repo.fetch_by_timeline("timeline-mixed")
    expected_mapping = {
        item.context.id: item.context.extracted_data.context_type.value for item in items
    }
    for row in rows:
        context_id = row["context_id"]
        assert context_id in expected_mapping
        assert row["context_type"] == expected_mapping[context_id]


def test_upsert_updates_existing_record() -> None:
    connection = sqlite3.connect(":memory:")
    storage = _FakeStorage()
    repo = _make_repo(connection, storage)

    context_id = "ctx-123"
    first_context = _make_context("first", context_id=context_id)
    first_item = MultimodalContextItem(
        context=first_context,
        timeline_id="timeline-2",
        modality=Modality.FRAME,
        content_ref="frame-a.png",
        embedding_ready=False,
    )
    repo.upsert_aligned_segments([first_item])

    updated_context = _make_context("second update", context_id=context_id)
    updated_item = MultimodalContextItem(
        context=updated_context,
        timeline_id="timeline-2",
        modality=Modality.FRAME,
        content_ref="frame-b.png",
        embedding_ready=True,
    )
    repo.upsert_aligned_segments([updated_item])

    rows = repo.fetch_by_timeline("timeline-2")
    assert len(rows) == 1
    row = rows[0]
    assert row["context_id"] == context_id
    assert row["content_ref"] == "frame-b.png"
    assert row["embedding_ready"] == 1
    assert row["context_type"] == updated_context.extracted_data.context_type.value


def test_upsert_rolls_back_on_failure() -> None:
    connection = sqlite3.connect(":memory:")
    storage = _FakeStorage()
    repo = _make_repo(connection, storage)

    # Drop table to trigger failure inside the transaction.
    connection.execute("DROP TABLE glass_multimodal_context")

    context = _make_context("boom")
    item = MultimodalContextItem(
        context=context,
        timeline_id="timeline-3",
        modality=Modality.METADATA,
        content_ref="meta.json",
        embedding_ready=False,
    )

    with pytest.raises(sqlite3.OperationalError):
        repo.upsert_aligned_segments([item])

    # Ensure transaction is cleaned up and no lingering state remains.
    assert not connection.in_transaction


def test_load_envelope_recovers_contexts_sorted_by_segment() -> None:
    connection = sqlite3.connect(":memory:")
    storage = _FakeStorage()
    repo = _make_repo(connection, storage)

    base_time = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)

    audio_context = _make_context(
        "audio",
        context_type=ContextType.ACTIVITY_CONTEXT,
        metadata={
            "segment_start": 0.0,
            "segment_end": 5.0,
            "source_video": "videos/sample.mp4",
        },
        create_time=base_time,
    )
    frame_context = _make_context(
        "frame",
        context_type=ContextType.STATE_CONTEXT,
        metadata={
            "segment_start": 5.0,
            "segment_end": 10.0,
            "source_video": "videos/sample.mp4",
        },
        create_time=base_time + datetime.timedelta(seconds=1),
    )

    repo.upsert_aligned_segments(
        [
            MultimodalContextItem(
                context=audio_context,
                timeline_id="timeline-42",
                modality=Modality.AUDIO,
                content_ref="segment-a",
                embedding_ready=True,
            ),
            MultimodalContextItem(
                context=frame_context,
                timeline_id="timeline-42",
                modality=Modality.FRAME,
                content_ref="frame-b.png",
                embedding_ready=True,
            ),
        ]
    )

    envelope = repo.load_envelope("timeline-42")
    assert envelope is not None
    assert envelope.timeline_id == "timeline-42"
    assert envelope.source == "videos/sample.mp4"
    assert [item.context.id for item in envelope.items] == [frame_context.id, audio_context.id]


def test_daily_report_roundtrip() -> None:
    connection = sqlite3.connect(":memory:")
    storage = _FakeStorage()
    repo = _make_repo(connection, storage)

    timeline_id = "timeline-daily-report"
    assert repo.load_daily_report_record(timeline_id) is None

    record = repo.upsert_daily_report(
        timeline_id=timeline_id,
        manual_markdown="# Report\n\nSummary.",
        manual_metadata={"pinned": ["ctx-1"]},
    )
    assert record.manual_markdown.startswith("# Report")
    assert record.manual_metadata["pinned"] == ["ctx-1"]
    assert record.updated_at is not None

    fetched = repo.load_daily_report_record(timeline_id)
    assert fetched is not None
    assert fetched.manual_markdown == record.manual_markdown
    assert fetched.manual_metadata == record.manual_metadata
