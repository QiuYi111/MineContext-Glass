from __future__ import annotations

from enum import Enum
from typing import Iterable

from pydantic import BaseModel, Field, model_validator


class SegmentType(str, Enum):
    """Modalities supported in an alignment manifest."""

    AUDIO = "audio"
    FRAME = "frame"
    METADATA = "metadata"


class AlignmentSegment(BaseModel):
    """Represents a single aligned fragment on the timeline."""

    start: float = Field(ge=0, description="Segment start timestamp in seconds.")
    end: float = Field(ge=0, description="Segment end timestamp in seconds.")
    type: SegmentType
    payload: str = Field(
        ...,
        description="Reference to the underlying data (file path, inline text, etc.).",
    )

    @model_validator(mode="after")
    def validate_range(self) -> "AlignmentSegment":
        if self.end < self.start:
            raise ValueError("end timestamp must be >= start timestamp")
        return self


class AlignmentManifest(BaseModel):
    """
    Describes aligned multimodal segments for a video timeline.

    The manifest is the contract between ingestion and downstream processors; every
    consumer reads the same immutable structure instead of branching on ad-hoc flags.
    """

    timeline_id: str
    source: str = Field(..., description="Original source of the ingested video.")
    segments: list[AlignmentSegment] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_ordered_segments(self) -> "AlignmentManifest":
        if not self.segments:
            raise ValueError("alignment manifest requires at least one segment")

        ordered = sorted(self.segments, key=lambda segment: segment.start)
        if ordered != self.segments:
            self.segments = ordered
        return self

    def iter_segments(self, segment_type: SegmentType | None = None) -> Iterable[AlignmentSegment]:
        """Iterate over segments, optionally filtered by modality."""
        if segment_type is None:
            yield from self.segments
            return

        for segment in self.segments:
            if segment.type is segment_type:
                yield segment

    def to_json(self) -> str:
        """Serialize the manifest in a stable JSON form suitable for persistence."""
        return self.model_dump_json(indent=2, exclude_none=True, by_alias=True)


class IngestionStatus(str, Enum):
    """Lifecycle states for a timeline ingestion task."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
