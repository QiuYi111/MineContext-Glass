from __future__ import annotations

"""
Asynchronous orchestration for Glass timeline ingestion.

The upload service coordinates LocalVideoManager ingestion runs and bridges the
resulting manifests into the standard MineContext processing pipeline without
blocking FastAPI request handlers.
"""

import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from loguru import logger

from .models import IngestionStatus
from .video_manager import TimelineNotFoundError, VideoManager
from opencontext.managers.processor_manager import ContextProcessorManager
from opencontext.models.context import RawContextProperties
from opencontext.models.enums import ContentFormat, ContextSource


class GlassIngestionService:
    """Manage asynchronous ingestion tasks for MineContext Glass uploads."""

    def __init__(
        self,
        video_manager: VideoManager,
        processor_manager: ContextProcessorManager,
        *,
        upload_dir: Path | None = None,
        executor: ThreadPoolExecutor | None = None,
    ) -> None:
        self._video_manager = video_manager
        self._processor_manager = processor_manager
        self._upload_dir = (upload_dir or Path("persist") / "glass" / "uploads").resolve()
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        self._executor = executor or ThreadPoolExecutor(max_workers=2)
        self._tasks: Dict[str, Future[None]] = {}
        self._lock = threading.Lock()

    @property
    def upload_dir(self) -> Path:
        return self._upload_dir

    def allocate_upload_path(self, filename: str) -> Path:
        """Return a unique, sanitized path for an incoming upload."""
        safe_name = Path(filename).name or "upload.bin"
        unique_name = f"{uuid.uuid4().hex}_{safe_name}"
        return self._upload_dir / unique_name

    def submit(self, source_path: Path, *, timeline_id: Optional[str] = None) -> str:
        """Schedule ingestion for the supplied source video."""
        if not source_path.exists():
            raise FileNotFoundError(f"upload source not found: {source_path}")

        timeline = timeline_id or uuid.uuid4().hex
        with self._lock:
            future = self._executor.submit(self._ingest_and_process, timeline, source_path)
            self._tasks[timeline] = future
            future.add_done_callback(lambda _: self._tasks.pop(timeline, None))
        return timeline

    def get_status(self, timeline_id: str) -> IngestionStatus:
        """Return the current ingestion status, falling back to pending for queued tasks."""
        try:
            return self._video_manager.get_status(timeline_id)
        except TimelineNotFoundError:
            with self._lock:
                if timeline_id in self._tasks:
                    return IngestionStatus.PENDING
            raise

    def fetch_manifest(self, timeline_id: str):
        """Delegates to the underlying VideoManager."""
        return self._video_manager.fetch_manifest(timeline_id)

    def _ingest_and_process(self, timeline_id: str, source_path: Path) -> None:
        """Run ingestion through the VideoManager and bridge results into processing."""
        logger.info("Starting Glass ingestion task for timeline %s", timeline_id)
        try:
            manifest = self._video_manager.ingest(source_path, timeline_id=timeline_id)
            self._bridge_manifest(manifest)
            logger.info("Completed Glass ingestion task for timeline %s", timeline_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Glass ingestion task failed for timeline %s: %s", timeline_id, exc)
            raise
        finally:
            self._cleanup_source(source_path)

    def _bridge_manifest(self, manifest) -> None:
        raw_context = RawContextProperties(
            content_format=ContentFormat.VIDEO,
            source=ContextSource.VIDEO,
            create_time=datetime.now(timezone.utc),
            additional_info={
                "timeline_id": manifest.timeline_id,
                "alignment_manifest": manifest.to_json(),
            },
        )
        self._processor_manager.process(raw_context)

    @staticmethod
    def _cleanup_source(source_path: Path) -> None:
        try:
            source_path.unlink(missing_ok=True)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to remove uploaded source %s: %s", source_path, exc)
