from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from opencontext.models.context import ProcessedContext


class Modality(str, Enum):
    """Supported modalities for multimodal context items."""

    AUDIO = "audio"
    FRAME = "frame"
    METADATA = "metadata"
    TEXT = "text"


class MultimodalContextItem(BaseModel):
    """
    Lightweight wrapper that keeps a ProcessedContext aligned with its multimodal origin.

    The MineContext data pipeline continues to operate on ProcessedContext objects. Glass
    extends it with timeline-aware metadata so we can keep track of the original segment
    without adding new branches downstream.
    """

    context: ProcessedContext
    timeline_id: str = Field(..., description="Timeline identifier produced during ingestion.")
    modality: Modality = Field(
        ..., description="Modal channel this context item represents (audio, frame, etc.)."
    )
    content_ref: str = Field(
        ...,
        description=(
            "Reference to the raw artefact (path to frame, inline transcript token, etc.)."
        ),
    )
    embedding_ready: bool = Field(
        False,
        description=(
            "Flag indicating whether the context payload has been vectorised and stored in "
            "the vector backend."
        ),
    )
