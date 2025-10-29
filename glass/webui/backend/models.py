from __future__ import annotations

import datetime as dt
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from glass.reports.models import DailyReport, TimelineHighlight, VisualCard


class UploadStatus(str, Enum):
    """Lifecycle states for timeline ingestion."""

    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TimelineRecord(BaseModel):
    """Internal representation of an uploaded timeline."""

    timeline_id: str
    filename: str
    source_path: Path
    status: UploadStatus = UploadStatus.PENDING
    submitted_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    completed_at: Optional[dt.datetime] = None
    auto_markdown: Optional[str] = None
    manual_markdown: Optional[str] = None
    manual_metadata: Dict[str, object] = Field(default_factory=dict)
    highlights: List[TimelineHighlight] = Field(default_factory=list)
    visual_cards: List[VisualCard] = Field(default_factory=list)
    rendered_html: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def build_daily_report(self) -> DailyReport:
        return DailyReport(
            timeline_id=self.timeline_id,
            source=self.filename,
            auto_markdown=self.auto_markdown,
            manual_markdown=self.manual_markdown,
            rendered_html=self.rendered_html,
            highlights=self.highlights,
            visual_cards=self.visual_cards,
            manual_metadata=self.manual_metadata,
            updated_at=self.completed_at,
        )
