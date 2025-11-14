from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Iterable, List

from glass.ingestion import AlignmentManifest, AlignmentSegment, SegmentType
from glass.processing.chunkers import ManifestChunker
from glass.processing.timeline_processor import GlassTimelineProcessor
from glass.storage.models import Modality, MultimodalContextItem
from opencontext.models.context import RawContextProperties
from opencontext.models.enums import ContentFormat, ContextSource


def _fixed_clock() -> dt.datetime:
    return dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)


def _build_manifest(frame_path: Path) -> AlignmentManifest:
    return AlignmentManifest(
        timeline_id="timeline-001",
        source="videos/sample.mp4",
        segments=[
            AlignmentSegment(start=0.0, end=2.5, type=SegmentType.AUDIO, payload="Hello from the timeline."),
            AlignmentSegment(start=2.5, end=5.0, type=SegmentType.FRAME, payload=str(frame_path)),
        ],
    )


def test_manifest_chunker_builds_audio_and_frame_items(tmp_path: Path) -> None:
    frame_path = tmp_path / "frame_0001.png"
    frame_path.write_text("fake-image-bytes")

    manifest = _build_manifest(frame_path)
    chunker = ManifestChunker(clock=_fixed_clock)

    items = chunker.build_items(manifest)
    assert len(items) == 2

    audio_item = next(item for item in items if item.modality is Modality.AUDIO)
    assert audio_item.context.vectorize.content_format is ContentFormat.TEXT
    assert audio_item.context.vectorize.text == "Hello from the timeline."
    assert audio_item.context.metadata["timeline_id"] == manifest.timeline_id

    frame_item = next(item for item in items if item.modality is Modality.FRAME)
    assert frame_item.content_ref == str(frame_path)
    assert frame_item.context.vectorize.content_format is ContentFormat.IMAGE
    assert frame_item.context.metadata["segment_type"] == SegmentType.FRAME.value


class _StubRepository:
    def __init__(self) -> None:
        self.items: List[MultimodalContextItem] = []

    def upsert_aligned_segments(self, items: Iterable[MultimodalContextItem]) -> List[str]:
        self.items = list(items)
        return [item.context.id for item in self.items]


class _StubVisualEncoder:
    def encode(self, image_path: str):
        from opencontext.models.context import Vectorize
        from opencontext.models.enums import ContentFormat

        return Vectorize(
            content_format=ContentFormat.IMAGE,
            image_path=image_path,
            vector=[0.1, 0.2, 0.3],
        )


def test_timeline_processor_persists_contexts(tmp_path: Path) -> None:
    frame_path = tmp_path / "frame_0001.png"
    frame_path.write_text("fake-image")

    manifest = _build_manifest(frame_path)
    manifest_path = tmp_path / "alignment_manifest.json"
    manifest_path.write_text(manifest.to_json())

    repository = _StubRepository()
    processor = GlassTimelineProcessor(
        repository=repository,
        chunker=ManifestChunker(clock=_fixed_clock),
        visual_encoder=_StubVisualEncoder(),
    )

    raw_context = RawContextProperties(
        content_format=ContentFormat.VIDEO,
        source=ContextSource.VIDEO,
        create_time=_fixed_clock(),
        content_path=str(manifest_path),
        additional_info={"timeline_id": manifest.timeline_id},
    )

    assert processor.can_process(raw_context) is True

    processed_contexts = processor.process(raw_context)
    assert processed_contexts, "Processor should return generated contexts"
    assert len(processed_contexts) == len(repository.items)

    # Visual encoder should mark frame items as embedding ready
    frame_item = next(item for item in repository.items if item.modality is Modality.FRAME)
    assert frame_item.embedding_ready is True
    assert processor.last_envelope is not None
    assert processor.last_envelope.timeline_id == manifest.timeline_id
