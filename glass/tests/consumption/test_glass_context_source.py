from __future__ import annotations

import datetime
import sqlite3
import uuid

from glass.consumption import GlassContextSource
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

    def batch_upsert_processed_context(self, contexts: list[ProcessedContext]):
        for context in contexts:
            self.contexts[(context.extracted_data.context_type.value, context.id)] = context
        return [context.id for context in contexts]

    def get_processed_context(self, context_id: str, context_type: str):
        return self.contexts.get((context_type, context_id))


def _make_repo(connection: sqlite3.Connection) -> GlassContextRepository:
    storage = _StubStorage()
    connection.row_factory = sqlite3.Row
    _bootstrap_schema(connection)
    return GlassContextRepository(storage=storage, connection=connection)


def test_context_source_returns_timeline_strings_sorted_by_segment() -> None:
    connection = sqlite3.connect(":memory:")
    repo = _make_repo(connection)

    base_time = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)

    early = _make_context(
        text="first",
        context_type=ContextType.ACTIVITY_CONTEXT,
        metadata={
            "segment_start": 0.0,
            "segment_end": 5.0,
            "source_video": "videos/demo.mp4",
        },
        create_time=base_time,
    )
    late = _make_context(
        text="second",
        context_type=ContextType.STATE_CONTEXT,
        metadata={
            "segment_start": 5.0,
            "segment_end": 12.0,
            "source_video": "videos/demo.mp4",
        },
        create_time=base_time + datetime.timedelta(seconds=1),
    )

    repo.upsert_aligned_segments(
        [
            MultimodalContextItem(
                context=early,
                timeline_id="timeline-77",
                modality=Modality.AUDIO,
                content_ref="a.txt",
                embedding_ready=True,
            ),
            MultimodalContextItem(
                context=late,
                timeline_id="timeline-77",
                modality=Modality.FRAME,
                content_ref="frame.png",
                embedding_ready=True,
            ),
        ]
    )

    source = GlassContextSource(repository=repo)
    strings = source.get_context_strings("timeline-77")

    assert len(strings) == 2
    assert "\"segment_end\": 12.0" in strings[0]
    assert "\"segment_end\": 5.0" in strings[1]


def test_group_by_context_type_uses_timeline_ordering() -> None:
    connection = sqlite3.connect(":memory:")
    repo = _make_repo(connection)

    base_time = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)

    contexts = [
        _make_context(
            text="first",
            context_type=ContextType.ACTIVITY_CONTEXT,
            metadata={"segment_start": 0.0, "segment_end": 2.0},
            create_time=base_time,
        ),
        _make_context(
            text="second",
            context_type=ContextType.ACTIVITY_CONTEXT,
            metadata={"segment_start": 2.0, "segment_end": 4.0},
            create_time=base_time + datetime.timedelta(seconds=1),
        ),
    ]

    repo.upsert_aligned_segments(
        [
            MultimodalContextItem(
                context=context,
                timeline_id="timeline-88",
                modality=Modality.AUDIO,
                content_ref=f"segment-{index}",
                embedding_ready=True,
            )
            for index, context in enumerate(contexts)
        ]
    )

    source = GlassContextSource(repository=repo)
    grouped = source.group_by_context_type("timeline-88")

    assert set(grouped.keys()) == {ContextType.ACTIVITY_CONTEXT.value}
    ordered_ids = [context.id for context in grouped[ContextType.ACTIVITY_CONTEXT.value]]
    # Should be sorted from latest to earliest
    assert ordered_ids == [contexts[1].id, contexts[0].id]
