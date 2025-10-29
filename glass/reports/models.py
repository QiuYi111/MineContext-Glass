from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TimelineHighlight(BaseModel):
    """Concise representation of a noteworthy segment within the timeline."""

    title: str = Field(..., description="Short human readable highlight title.")
    summary: Optional[str] = Field(None, description="Expanded summary for the highlight.")
    modality: str = Field(..., description="Underlying modality for the highlight (audio/frame/text/etc).")
    timestamp: Optional[float] = Field(
        None,
        description="Primary timestamp in seconds associated with the highlight.",
    )
    segment_start: Optional[float] = Field(None, description="Segment start in seconds.")
    segment_end: Optional[float] = Field(None, description="Segment end in seconds.")
    context_id: Optional[str] = Field(None, description="ProcessedContext identifier backing the highlight.")


class VisualCard(BaseModel):
    """Visual element extracted from the timeline for quick scanning."""

    image_url: str = Field(..., description="Path or URL to the representative frame image.")
    caption: Optional[str] = Field(None, description="Optional caption describing the frame.")
    segment_start: Optional[float] = Field(None, description="Frame start timestamp.")
    segment_end: Optional[float] = Field(None, description="Frame end timestamp.")


class DailyReport(BaseModel):
    """Payload returned to the WebUI describing the auto and manual report state."""

    timeline_id: str = Field(..., description="Timeline identifier.")
    source: Optional[str] = Field(None, description="Original video source reference.")
    auto_markdown: Optional[str] = Field(
        None,
        description="System generated Markdown summary derived from the timeline.",
    )
    manual_markdown: Optional[str] = Field(
        None,
        description="User supplied Markdown overrides.",
    )
    rendered_html: Optional[str] = Field(
        None,
        description="Sanitised HTML rendering of the manual/auto Markdown.",
    )
    highlights: List[TimelineHighlight] = Field(default_factory=list)
    visual_cards: List[VisualCard] = Field(default_factory=list)
    manual_metadata: Dict[str, Any] = Field(default_factory=dict)
    updated_at: Optional[_dt.datetime] = Field(
        None,
        description="Last modification timestamp for the manual report content.",
    )
