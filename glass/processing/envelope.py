from __future__ import annotations

"""
Context envelope for Glass timelines.

The envelope gives downstream consumers a stable structure that bundles the
multimodal context items derived from a timeline. This avoids coupling clients
to intermediate storage schemas or manifest internals.
"""

from typing import List, Sequence

from pydantic import BaseModel, Field

from glass.storage.models import MultimodalContextItem


class ContextEnvelope(BaseModel):
    """Bundle of multimodal context items derived from a single timeline."""

    timeline_id: str = Field(..., description="Timeline identifier that produced the items.")
    source: str = Field(..., description="Original video source associated with the timeline.")
    items: List[MultimodalContextItem] = Field(default_factory=list)

    @classmethod
    def from_items(
        cls,
        *,
        timeline_id: str,
        source: str,
        items: Sequence[MultimodalContextItem],
    ) -> "ContextEnvelope":
        return cls(timeline_id=timeline_id, source=source, items=list(items))

    def __len__(self) -> int:
        return len(self.items)
