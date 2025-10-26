from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .models import AlignmentManifest, IngestionStatus


class VideoManager(ABC):
    """
    Defines the contract for MineContext Glass ingestion.

    Implementations must keep the pipeline stateless and idempotent for a given
    timeline so that downstream processors never see divergent manifests.
    """

    @abstractmethod
    def ingest(self, source: Path | str, *, timeline_id: Optional[str] = None) -> AlignmentManifest:
        """
        Trigger ingestion for the supplied video.

        Implementations should:
        1. Normalize/validate the source path.
        2. Coordinate ffmpeg frame extraction and speech transcription.
        3. Persist results and return a stable manifest.
        """

        raise NotImplementedError

    @abstractmethod
    def get_status(self, timeline_id: str) -> IngestionStatus:
        """Return the ingestion lifecycle status for a given timeline."""

        raise NotImplementedError

    @abstractmethod
    def fetch_manifest(self, timeline_id: str) -> AlignmentManifest:
        """Load the manifest previously produced for the timeline."""

        raise NotImplementedError


class TimelineNotFoundError(RuntimeError):
    """Raised when the requested timeline cannot be located."""

    def __init__(self, timeline_id: str) -> None:
        super().__init__(f"timeline not found: {timeline_id}")
        self.timeline_id = timeline_id
