from __future__ import annotations

import datetime
import sqlite3
import uuid

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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _make_context(text: str, context_id: str | None = None) -> ProcessedContext:
    now = datetime.datetime.now(datetime.timezone.utc)
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
        context_type=ContextType.SEMANTIC_CONTEXT,
        confidence=1,
        importance=1,
    )
    vectorize = Vectorize(content_format=ContentFormat.TEXT, text=text)
    return ProcessedContext(
        id=context_id or str(uuid.uuid4()),
        properties=properties,
        extracted_data=extracted,
        vectorize=vectorize,
    )


class _FakeStorage:
    def __init__(self) -> None:
        self.contexts: list[ProcessedContext] = []

    def batch_upsert_processed_context(self, contexts: list[ProcessedContext]):
        self.contexts.extend(contexts)
        return [context.id for context in contexts]


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
    assert storage.contexts == [context]

    rows = repo.fetch_by_timeline("timeline-1")
    assert len(rows) == 1
    row = rows[0]
    assert row["context_id"] == context.id
    assert row["embedding_ready"] == 1
    assert row["content_ref"] == "segment-001"


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
