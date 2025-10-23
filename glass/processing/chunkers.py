from __future__ import annotations

"""
Utilities for converting an AlignmentManifest into MineContext-friendly
ProcessedContext payloads.

We deliberately reuse the core data models from opencontext.models.context so
that downstream services can keep operating on familiar types without learning
about video timelines or bespoke payload formats.
"""

import datetime as _dt
from dataclasses import dataclass
from typing import Callable, List, Sequence

from opencontext.context_processing.chunker.simple_text_chunker import SimpleTextChunker
from opencontext.models.context import (
    ContextProperties,
    ContextType,
    ExtractedData,
    ProcessedContext,
    RawContextProperties,
    Vectorize,
)
from opencontext.models.enums import ContentFormat, ContextSource
from opencontext.utils.logging_utils import get_logger

from glass.ingestion.models import AlignmentManifest, AlignmentSegment, SegmentType
from glass.storage.models import Modality, MultimodalContextItem

logger = get_logger(__name__)


@dataclass(frozen=True)
class SegmentContextSpec:
    """Lightweight descriptor produced by ManifestChunker for a single segment."""

    manifest: AlignmentManifest
    segment: AlignmentSegment
    modality: Modality
    unique_suffix: str


class ManifestChunker:
    """
    Translate AlignmentManifest segments into ProcessedContext payloads.

    Audio segments become text chunks; frame segments become image contexts that
    can later be vectorised by the Glass visual encoder. The chunker keeps the
    metadata surface compatible with the existing MineContext pipeline to honour
    the reuse contract described in docs/reuse_reference.md.
    """

    def __init__(
        self,
        *,
        text_chunker: SimpleTextChunker | None = None,
        clock: Callable[[], _dt.datetime] | None = None,
    ) -> None:
        self._text_chunker = text_chunker or SimpleTextChunker()
        self._clock = clock or (lambda: _dt.datetime.now(tz=_dt.timezone.utc))

    def build_items(self, manifest: AlignmentManifest) -> List[MultimodalContextItem]:
        """
        Convert a manifest into a list of MultimodalContextItem objects.
        """
        items: List[MultimodalContextItem] = []
        for index, segment in enumerate(manifest.iter_segments()):
            if segment.type is SegmentType.AUDIO:
                spec = SegmentContextSpec(
                    manifest=manifest,
                    segment=segment,
                    modality=Modality.AUDIO,
                    unique_suffix=f"audio-{index:04d}",
                )
                items.extend(self._build_audio_items(spec))
            elif segment.type is SegmentType.FRAME:
                spec = SegmentContextSpec(
                    manifest=manifest,
                    segment=segment,
                    modality=Modality.FRAME,
                    unique_suffix=f"frame-{index:04d}",
                )
                item = self._build_frame_item(spec)
                if item:
                    items.append(item)
            else:
                logger.debug(
                    "Skipping unsupported segment type '%s' in timeline %s",
                    segment.type,
                    manifest.timeline_id,
                )
        return items

    def _build_audio_items(self, spec: SegmentContextSpec) -> List[MultimodalContextItem]:
        """Create one or more context items from an audio transcript segment."""
        segment_text = spec.segment.payload.strip()
        if not segment_text:
            logger.debug(
                "Ignoring empty audio payload for segment %s on timeline %s",
                spec.unique_suffix,
                spec.manifest.timeline_id,
            )
            return []

        raw = self._build_raw_context(
            object_id=f"{spec.manifest.timeline_id}-{spec.unique_suffix}",
            text=segment_text,
            spec=spec,
        )

        chunks = list(self._text_chunker.chunk(raw))
        if not chunks:
            logger.debug(
                "Text chunker returned no chunks for segment %s on timeline %s",
                spec.unique_suffix,
                spec.manifest.timeline_id,
            )
            return []

        items: List[MultimodalContextItem] = []
        for chunk in chunks:
            processed_context = self._build_processed_context(
                raw=raw,
                spec=spec,
                chunk_text=chunk.text or "",
                chunk_index=chunk.chunk_index,
                context_type=ContextType.ACTIVITY_CONTEXT,
                vectorize_format=ContentFormat.TEXT,
                vectorize_text=chunk.text or "",
                summary_hint=chunk.summary,
            )
            items.append(
                MultimodalContextItem(
                    context=processed_context,
                    timeline_id=spec.manifest.timeline_id,
                    modality=spec.modality,
                    content_ref=segment_text,
                )
            )
        return items

    def _build_frame_item(self, spec: SegmentContextSpec) -> MultimodalContextItem | None:
        """Create an image context for a frame segment."""
        frame_path = spec.segment.payload.strip()
        if not frame_path:
            logger.debug(
                "Ignoring frame segment with empty payload on timeline %s",
                spec.manifest.timeline_id,
            )
            return None

        raw = self._build_raw_context(
            object_id=f"{spec.manifest.timeline_id}-{spec.unique_suffix}",
            text="",
            spec=spec,
            content_path=frame_path,
        )

        processed_context = self._build_processed_context(
            raw=raw,
            spec=spec,
            chunk_text=f"Frame captured at {spec.segment.start:.2f}s",
            chunk_index=0,
            context_type=ContextType.STATE_CONTEXT,
            vectorize_format=ContentFormat.IMAGE,
            vectorize_text=None,
            vectorize_image=frame_path,
            summary_hint=None,
        )
        return MultimodalContextItem(
            context=processed_context,
            timeline_id=spec.manifest.timeline_id,
            modality=spec.modality,
            content_ref=frame_path,
        )

    def _build_raw_context(
        self,
        *,
        object_id: str,
        spec: SegmentContextSpec,
        text: str,
        content_path: str | None = None,
    ) -> RawContextProperties:
        """Construct a RawContextProperties instance capturing manifest metadata."""
        additional_info = {
            "timeline_id": spec.manifest.timeline_id,
            "segment_start": spec.segment.start,
            "segment_end": spec.segment.end,
            "segment_type": spec.segment.type.value,
            "source_video": spec.manifest.source,
        }

        return RawContextProperties(
            content_format=ContentFormat.TEXT if text else ContentFormat.IMAGE,
            source=ContextSource.VIDEO,
            create_time=self._clock(),
            object_id=object_id,
            content_text=text or None,
            content_path=content_path,
            additional_info=additional_info,
            enable_merge=False,
        )

    def _build_processed_context(
        self,
        *,
        raw: RawContextProperties,
        spec: SegmentContextSpec,
        chunk_text: str,
        chunk_index: int,
        context_type: ContextType,
        vectorize_format: ContentFormat,
        vectorize_text: str | None,
        summary_hint: str | None,
        vectorize_image: str | None = None,
    ) -> ProcessedContext:
        """Build a ProcessedContext sharing metadata with MineContext models."""
        summary = summary_hint or chunk_text
        extracted = ExtractedData(
            title=None,
            summary=summary,
            context_type=context_type,
            confidence=10,
            importance=5,
        )

        properties = ContextProperties(
            raw_properties=[raw],
            create_time=raw.create_time,
            event_time=raw.create_time,
            update_time=raw.create_time,
            enable_merge=False,
            duration_count=1,
        )

        vectorize = Vectorize(
            content_format=vectorize_format,
            text=vectorize_text,
            image_path=vectorize_image,
        )

        metadata = {
            "timeline_id": spec.manifest.timeline_id,
            "segment_start": spec.segment.start,
            "segment_end": spec.segment.end,
            "segment_type": spec.segment.type.value,
            "chunk_index": chunk_index,
            "source_video": spec.manifest.source,
        }

        return ProcessedContext(
            id=f"{raw.object_id}-chunk-{chunk_index}",
            properties=properties,
            extracted_data=extracted,
            vectorize=vectorize,
            metadata=metadata,
        )


def build_context_items(manifest: AlignmentManifest) -> Sequence[MultimodalContextItem]:
    """
    Functional helper around ManifestChunker for callers that do not need to
    manage the chunker lifecycle explicitly.
    """
    chunker = ManifestChunker()
    return chunker.build_items(manifest)
