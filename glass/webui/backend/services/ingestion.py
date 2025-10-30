from __future__ import annotations

import threading
from datetime import datetime, timezone
from concurrent.futures import Future
from pathlib import Path
from typing import Any, BinaryIO, Optional

from loguru import logger

from glass.ingestion.models import IngestionStatus
from glass.ingestion.service import GlassIngestionService
from glass.ingestion.video_manager import TimelineNotFoundError
from glass.reports.service import DailyReportService
from glass.storage.context_repository import GlassContextRepository

from ..config import BackendConfig
from ..models import TimelineRecord, UploadStatus
from ..repositories import TimelineRepository
from ..state import UploadTask, UploadTaskRepository
from .reports import DailyReportBuilder

CHUNK_SIZE = 1024 * 1024


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ReportNotReadyError(RuntimeError):
    """Raised when a consumer requests a report before contexts are available."""


class IngestionCoordinator:
    """Coordinate uploads and pipe them through the Glass ingestion service."""

    def __init__(
        self,
        *,
        config: BackendConfig,
        tasks: UploadTaskRepository,
        ingestion_service: GlassIngestionService,
        context_repository: GlassContextRepository | None = None,
        report_service: DailyReportService | None = None,
        legacy_repository: TimelineRepository | None = None,
        legacy_report_builder: DailyReportBuilder | None = None,
    ) -> None:
        self._config = config
        self._tasks = tasks
        self._ingestion = ingestion_service
        self._context_repository = context_repository
        self._report_service = report_service
        self._legacy_repository = legacy_repository
        self._legacy_report_builder = legacy_report_builder
        self._lock = threading.RLock()
        self._futures: dict[str, Future[None]] = {}

    @property
    def limits(self):
        return self._config.upload_limits

    def create_upload(
        self,
        filename: str,
        file_obj: BinaryIO,
        *,
        content_length: Optional[int] = None,
    ) -> UploadTask:
        """Persist an upload to disk and register a new ingestion task."""
        self._validate_upload(filename=filename, content_length=content_length)
        destination = self._allocate_destination(filename)
        size = self._write_stream(file_obj, destination)

        timeline_id = self._tasks.generate_timeline_id()
        task = self._tasks.create(
            timeline_id=timeline_id,
            filename=filename,
            source_path=destination,
            status=UploadStatus.PROCESSING,
            size_bytes=size,
        )
        if self._config.is_demo:
            self._seed_legacy_record(task)

        try:
            submitted_id = self._ingestion.submit(destination, timeline_id=timeline_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to submit ingestion for %s: %s", timeline_id, exc)
            self._tasks.update_status(timeline_id, UploadStatus.FAILED, error=str(exc))
            raise

        if submitted_id != timeline_id:
            logger.warning(
                "Ingestion service returned timeline id %s different from allocated %s",
                submitted_id,
                timeline_id,
            )
            timeline_id = submitted_id

        self._register_future(timeline_id)
        return self._tasks.get(timeline_id) or task

    def get_status(self, timeline_id: str) -> UploadStatus:
        task = self._tasks.get(timeline_id)
        if task is None:
            raise KeyError(timeline_id)

        if task.status in (UploadStatus.COMPLETED, UploadStatus.FAILED):
            return task.status

        try:
            ingestion_status = self._ingestion.get_status(timeline_id)
        except TimelineNotFoundError:
            return task.status

        mapped = self._map_status(ingestion_status)
        if mapped != task.status:
            completed_at = task.completed_at
            if mapped is UploadStatus.COMPLETED:
                completed_at = _now()
            task = self._tasks.update_status(
                timeline_id,
                mapped,
                completed_at=completed_at if mapped is UploadStatus.COMPLETED else None,
            )
        return task.status

    def get_daily_report(self, timeline_id: str):
        envelope = self._load_envelope(timeline_id)
        if envelope is not None and self._report_service:
            try:
                report = self._report_service.get_report(timeline_id, envelope=envelope)
            except ValueError as exc:  # envelope exists but contexts not ready
                raise ReportNotReadyError(str(exc)) from exc
            if self._config.is_demo:
                self._sync_legacy_auto_report(timeline_id, report=report)
            return report

        if self._config.is_demo:
            record = self._get_legacy_record(timeline_id)
            if record is not None:
                if record.status is not UploadStatus.COMPLETED and self._legacy_report_builder:
                    record.status = UploadStatus.COMPLETED
                    report = self._legacy_report_builder.build_auto_report(record)
                    record.rendered_html = report.rendered_html
                    self._legacy_repository.upsert(record)
                return record.build_daily_report()

        task = self._tasks.get(timeline_id)
        if task and task.status is not UploadStatus.COMPLETED:
            raise ReportNotReadyError(timeline_id)
        raise KeyError(timeline_id)

    def save_manual_report(self, timeline_id: str, *, markdown: str, metadata: dict[str, object]):
        envelope = self._load_envelope(timeline_id)
        if envelope is None or not self._report_service:
            if self._config.is_demo:
                return self._save_legacy_manual_report(timeline_id, markdown=markdown, metadata=metadata)
            raise ReportNotReadyError(timeline_id)

        try:
            report = self._report_service.save_manual_report(
                timeline_id=timeline_id,
                manual_markdown=markdown,
                manual_metadata=metadata,
                envelope=envelope,
            )
        except ValueError as exc:
            raise ReportNotReadyError(str(exc)) from exc

        if self._config.is_demo:
            self._sync_legacy_manual_report(timeline_id, markdown=markdown, metadata=metadata)
        return report

    def regenerate_report(self, timeline_id: str) -> TimelineRecord:
        if self._context_repository and not self._config.is_demo:
            task = self._tasks.get(timeline_id)
            if task is None:
                raise KeyError(timeline_id)
            # In real mode we do not re-run ingestion yet; clearing manual overrides keeps responses consistent.
            self._clear_manual_report(timeline_id)
            return TimelineRecord(
                timeline_id=timeline_id,
                filename=task.filename,
                source_path=task.source_path,
                status=self.get_status(timeline_id),
            )

        if not self._legacy_repository:
            raise KeyError(timeline_id)
        record = self._legacy_repository.get(timeline_id)
        if not record:
            raise KeyError(timeline_id)
        self._register_future(timeline_id)
        return record

    def build_context_payload(self, timeline_id: str) -> dict[str, Any]:
        task = self._tasks.get(timeline_id)
        if task is None:
            raise KeyError(timeline_id)

        envelope = self._load_envelope(timeline_id)
        if envelope is None:
            if self._config.is_demo:
                legacy = self._get_legacy_record(timeline_id)
                if legacy and legacy.status is UploadStatus.COMPLETED:
                    return self._build_legacy_context_payload(timeline_id, legacy)
            raise ReportNotReadyError(timeline_id)

        if not self._report_service:
            raise ReportNotReadyError(timeline_id)

        try:
            report = self._report_service.get_report(timeline_id, envelope=envelope)
        except ValueError as exc:
            raise ReportNotReadyError(str(exc)) from exc

        summary = self._report_service.build_summary(report)

        items: list[dict[str, Any]] = []
        for item in envelope.items:
            metadata = (item.context.metadata or {}).copy()
            summary_text = ""
            if item.context.extracted_data and item.context.extracted_data.summary:
                summary_text = item.context.extracted_data.summary
            items.append(
                {
                    "context_id": item.context.id,
                    "modality": item.modality.value,
                    "content_ref": item.content_ref,
                    "summary": summary_text,
                    "metadata": metadata,
                }
            )

        return {
            "timeline_id": timeline_id,
            "source": envelope.source,
            "items": items,
            "daily_report": report.model_dump(),
            "summary": summary,
            "highlights": [highlight.model_dump() for highlight in report.highlights],
            "visual_cards": [card.model_dump() for card in report.visual_cards],
            "auto_markdown": report.auto_markdown,
        }

    def _register_future(self, timeline_id: str) -> None:
        tasks_map = getattr(self._ingestion, "_tasks", None)
        if not isinstance(tasks_map, dict):
            return
        future = tasks_map.get(timeline_id)
        if not isinstance(future, Future):
            return

        with self._lock:
            self._futures[timeline_id] = future

        def _callback(done: Future[None], *, task_id: str = timeline_id) -> None:
            try:
                done.result()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Ingestion task failed for %s: %s", task_id, exc)
                self._tasks.update_status(task_id, UploadStatus.FAILED, error=str(exc))
                return
            logger.info("Ingestion task completed for timeline %s", task_id)
            self._tasks.update_status(task_id, UploadStatus.COMPLETED, completed_at=_now())

        future.add_done_callback(_callback)

    def _seed_legacy_record(self, task: UploadTask) -> None:
        if not self._legacy_repository:
            return

        record = TimelineRecord(
            timeline_id=task.timeline_id,
            filename=task.filename,
            source_path=task.source_path,
            status=UploadStatus.PROCESSING,
        )
        self._legacy_repository.upsert(record)

    def _sync_legacy_manual_report(self, timeline_id: str, *, markdown: str, metadata: dict[str, object]) -> None:
        if not self._legacy_repository:
            return
        record = self._legacy_repository.save_manual_report(
            timeline_id,
            manual_markdown=markdown,
            manual_metadata=metadata,
        )
        if self._legacy_report_builder:
            record.rendered_html = self._legacy_report_builder.renderer.render(markdown)
            self._legacy_repository.upsert(record)

    def _get_legacy_record(self, timeline_id: str) -> TimelineRecord | None:
        if not self._legacy_repository:
            return None
        return self._legacy_repository.get(timeline_id)

    def _load_envelope(self, timeline_id: str):
        if not self._context_repository:
            return None
        return self._context_repository.load_envelope(timeline_id)

    def _sync_legacy_auto_report(self, timeline_id: str, *, report) -> None:
        if not self._legacy_repository or not self._legacy_report_builder:
            return
        record = self._legacy_repository.get(timeline_id)
        if record is None:
            record = TimelineRecord(
                timeline_id=timeline_id,
                filename=report.source,
                source_path=Path(report.source),
                status=UploadStatus.COMPLETED,
            )
        record.auto_markdown = report.auto_markdown
        record.manual_markdown = report.manual_markdown
        record.manual_metadata = report.manual_metadata
        record.highlights = report.highlights
        record.visual_cards = report.visual_cards
        record.rendered_html = report.rendered_html
        record.status = UploadStatus.COMPLETED
        self._legacy_repository.upsert(record)

    def _save_legacy_manual_report(self, timeline_id: str, *, markdown: str, metadata: dict[str, object]):
        record = self._legacy_repository.save_manual_report(
            timeline_id,
            manual_markdown=markdown,
            manual_metadata=metadata,
        )
        if self._legacy_report_builder:
            record.rendered_html = self._legacy_report_builder.renderer.render(
                record.manual_markdown or record.auto_markdown
            )
            self._legacy_repository.upsert(record)
        return record.build_daily_report()

    def _build_legacy_context_payload(self, timeline_id: str, record: TimelineRecord) -> dict[str, Any]:
        daily_report = record.build_daily_report()
        items: list[dict[str, Any]] = []
        for highlight in daily_report.highlights:
            items.append(
                {
                    "context_id": highlight.context_id,
                    "modality": highlight.modality,
                    "content_ref": highlight.thumbnail_url,
                    "summary": (highlight.summary or highlight.title or ""),
                    "metadata": {
                        "segment_start": highlight.segment_start,
                        "segment_end": highlight.segment_end,
                    },
                }
            )
        return {
            "timeline_id": timeline_id,
            "source": record.filename,
            "items": items,
            "daily_report": daily_report.model_dump(),
            "summary": "",
            "highlights": [highlight.model_dump() for highlight in daily_report.highlights],
            "visual_cards": [card.model_dump() for card in daily_report.visual_cards],
            "auto_markdown": daily_report.auto_markdown,
        }

    def _clear_manual_report(self, timeline_id: str) -> None:
        if not self._context_repository:
            return
        try:
            repository = self._context_repository
            if hasattr(repository, "clear_daily_report"):
                repository.clear_daily_report(timeline_id)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to clear manual report for %s: %s", timeline_id, exc)

    def _map_status(self, status: IngestionStatus) -> UploadStatus:
        if status is IngestionStatus.PENDING:
            return UploadStatus.PENDING
        if status is IngestionStatus.PROCESSING:
            return UploadStatus.PROCESSING
        if status is IngestionStatus.COMPLETED:
            return UploadStatus.COMPLETED
        if status is IngestionStatus.FAILED:
            return UploadStatus.FAILED
        return UploadStatus.PROCESSING

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

    def _allocate_destination(self, filename: str) -> Path:
        try:
            return self._ingestion.allocate_upload_path(filename)
        except AttributeError:
            safe_name = Path(filename).name or "upload.bin"
            destination = self._config.upload_dir / safe_name
            counter = 1
            while destination.exists():
                destination = self._config.upload_dir / f"{counter}_{safe_name}"
                counter += 1
            return destination

    @staticmethod
    def _write_stream(source: BinaryIO, destination: Path) -> int:
        destination.parent.mkdir(parents=True, exist_ok=True)
        total = 0
        with destination.open("wb") as handle:
            while True:
                chunk = source.read(CHUNK_SIZE)
                if not chunk:
                    break
                handle.write(chunk)
                total += len(chunk)
        return total
