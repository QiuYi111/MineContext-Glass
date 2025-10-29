from __future__ import annotations

import asyncio
import datetime as dt
from pathlib import Path
from typing import BinaryIO, Dict, Optional

from loguru import logger

from ..config import BackendConfig
from ..models import TimelineRecord, UploadStatus
from ..repositories import TimelineRepository
from .reports import DailyReportBuilder


class IngestionCoordinator:
    """Coordinate uploads and lightweight processing for the standalone backend."""

    def __init__(
        self,
        repository: TimelineRepository,
        config: BackendConfig,
        report_builder: DailyReportBuilder,
    ) -> None:
        self._repository = repository
        self._config = config
        self._report_builder = report_builder
        self._tasks: Dict[str, asyncio.Task] = {}

    @property
    def limits(self):
        return self._config.upload_limits

    def create_upload(self, filename: str, file_obj: BinaryIO, *, content_length: Optional[int] = None) -> TimelineRecord:
        """Persist an upload to disk and register a new timeline."""
        self._validate_upload(filename=filename, content_length=content_length)
        destination = self._resolve_destination(filename)
        self._write_stream(file_obj, destination)

        record = self._repository.create(filename=filename, source_path=destination)
        record.status = UploadStatus.PROCESSING
        record.completed_at = None
        self._repository.upsert(record)
        logger.info("Registered new timeline %s for upload %s", record.timeline_id, filename)
        self.enqueue_processing(record.timeline_id)
        return record

    def get_status(self, timeline_id: str) -> UploadStatus:
        record = self._repository.get(timeline_id)
        if not record:
            raise KeyError(timeline_id)
        return record.status

    def get_report(self, timeline_id: str) -> TimelineRecord:
        record = self._repository.get(timeline_id)
        if not record:
            raise KeyError(timeline_id)
        if record.status is not UploadStatus.COMPLETED:
            logger.debug("Timeline %s not completed yet; generating report inline for demo mode", timeline_id)
            record.status = UploadStatus.COMPLETED
            report = self._report_builder.build_auto_report(record)
            record.rendered_html = report.rendered_html
            record.completed_at = record.completed_at or dt.datetime.now(dt.timezone.utc)
            self._repository.upsert(record)
        return record

    def save_manual_report(self, timeline_id: str, *, markdown: str, metadata: dict[str, object]) -> TimelineRecord:
        record = self._repository.save_manual_report(
            timeline_id,
            manual_markdown=markdown,
            manual_metadata=metadata,
        )
        record.rendered_html = self._report_builder.renderer.render(record.manual_markdown or record.auto_markdown)
        record.completed_at = dt.datetime.now(dt.timezone.utc)
        self._repository.upsert(record)
        return record

    def regenerate_report(self, timeline_id: str) -> TimelineRecord:
        record = self._repository.get(timeline_id)
        if not record:
            raise KeyError(timeline_id)
        self.enqueue_processing(timeline_id, force=True)
        return record

    def enqueue_processing(self, timeline_id: str, *, force: bool = False) -> None:
        """Schedule background processing for the supplied timeline."""
        if timeline_id in self._tasks and not self._tasks[timeline_id].done() and not force:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop (likely during tests); execute synchronously.
            asyncio.run(self._process_pipeline(timeline_id))
            return
        task = loop.create_task(self._process_pipeline(timeline_id))
        self._tasks[timeline_id] = task

    async def _process_pipeline(self, timeline_id: str) -> None:
        record = self._repository.get(timeline_id)
        if not record:
            logger.warning("Processing requested for unknown timeline %s", timeline_id)
            return
        logger.info("Starting lightweight processing for timeline %s", timeline_id)
        self._repository.update_status(timeline_id, UploadStatus.PROCESSING)

        if self._config.processing_delay_seconds > 0:
            await asyncio.sleep(self._config.processing_delay_seconds)

        record.status = UploadStatus.COMPLETED
        report = self._report_builder.build_auto_report(record)
        record.rendered_html = report.rendered_html
        record.completed_at = dt.datetime.now(dt.timezone.utc)
        self._repository.upsert(record)
        logger.info("Timeline %s marked as completed", timeline_id)

    def _validate_upload(self, *, filename: str, content_length: Optional[int]) -> None:
        if not filename:
            raise ValueError("filename is required")

        suffix = Path(filename).suffix.lower()
        allowed_suffixes = {".mp4", ".mov", ".mkv", ".avi"}
        if suffix and suffix not in allowed_suffixes:
            logger.debug("Upload %s uses suffix %s outside allowlist", filename, suffix)

        limits = self._config.upload_limits
        if content_length and content_length > limits.max_size_mb * 1024 * 1024:
            raise ValueError("file too large")

    def _resolve_destination(self, filename: str) -> Path:
        safe_name = Path(filename).name or "upload.bin"
        destination = self._config.upload_dir / safe_name
        counter = 1
        while destination.exists():
            destination = self._config.upload_dir / f"{counter}_{safe_name}"
            counter += 1
        return destination

    @staticmethod
    def _write_stream(source: BinaryIO, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as handle:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
