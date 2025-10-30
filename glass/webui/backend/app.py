from __future__ import annotations

import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from glass.ingestion import FFmpegRunner, LocalVideoManager, build_speech_to_text_runner_from_config
from glass.ingestion.models import AlignmentManifest, AlignmentSegment, IngestionStatus, SegmentType
from glass.ingestion.service import GlassIngestionService
from glass.ingestion.video_manager import TimelineNotFoundError, VideoManager
from glass.processing.chunkers import ManifestChunker
from glass.processing.timeline_processor import GlassTimelineProcessor
from glass.processing.visual_encoder import VisualEncoder
from glass.reports.service import DailyReportService
from glass.storage.context_repository import GlassContextRepository
from opencontext.managers.processor_manager import ContextProcessorManager

from .config import BackendConfig, load_config
from .demo_data import load_demo_timelines
from .repositories import TimelineRepository
from .services import DailyReportBuilder, IngestionCoordinator, MarkdownRenderer
from .services.ingestion import ReportNotReadyError
from .state import UploadTaskRepository


def create_app(
    config: BackendConfig | None = None,
    *,
    ingestion_service: GlassIngestionService | None = None,
    tasks_repository: UploadTaskRepository | None = None,
    context_repository: GlassContextRepository | None = None,
    report_service: DailyReportService | None = None,
) -> FastAPI:
    """Create the standalone FastAPI application serving the Glass API."""

    config = config or load_config()
    tasks = tasks_repository or UploadTaskRepository(config.state_db_path)
    context_repo = context_repository or GlassContextRepository()
    report_srv = report_service or DailyReportService(repository=context_repo)
    legacy_repository = TimelineRepository()
    renderer = MarkdownRenderer()
    report_builder = DailyReportBuilder(renderer=renderer)

    ingestion = ingestion_service or _build_ingestion_service(config, context_repo)

    coordinator = IngestionCoordinator(
        config=config,
        tasks=tasks,
        ingestion_service=ingestion,
        context_repository=context_repo,
        report_service=report_srv,
        legacy_repository=legacy_repository,
        legacy_report_builder=report_builder,
    )

    if config.is_demo:
        load_demo_timelines(
            config.demo_data_dir,
            repository=legacy_repository,
            report_builder=report_builder,
            tasks=tasks,
        )

    app = FastAPI(
        title="Glass WebUI Backend",
        version="0.1.0",
        description="Lightweight backend serving the Glass WebUI without OpenContext dependencies.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.config = config
    app.state.repository = legacy_repository
    app.state.tasks = tasks
    app.state.coordinator = coordinator
    app.state.ingestion_service = ingestion

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        try:
            tasks.close()
        except Exception:  # noqa: BLE001
            pass

    def get_coordinator() -> IngestionCoordinator:
        return app.state.coordinator  # type: ignore[return-value]

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/glass/uploads/limits")
    async def get_upload_limits(coord: IngestionCoordinator = Depends(get_coordinator)) -> dict[str, Any]:
        return {"data": asdict(coord.limits)}

    @app.post("/glass/upload")
    async def upload_video(
        request: Request,
        file: UploadFile = File(...),
        coord: IngestionCoordinator = Depends(get_coordinator),
    ) -> dict[str, Any]:
        if not file.filename:
            raise HTTPException(status_code=400, detail="filename is required")

        content_length = request.headers.get("content-length")
        length_value: int | None = None
        if content_length:
            try:
                length_value = int(content_length)
            except ValueError:
                length_value = None

        try:
            task = coord.create_upload(
                file.filename,
                file.file,
                content_length=length_value,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TimelineNotFoundError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            await file.close()

        payload = {"timeline_id": task.timeline_id, "status": task.status.value}
        return {"data": payload}

    @app.get("/glass/status/{timeline_id}")
    async def get_status(
        timeline_id: str,
        coord: IngestionCoordinator = Depends(get_coordinator),
    ) -> dict[str, Any]:
        try:
            status = coord.get_status(timeline_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="timeline not found") from None
        return {"data": {"timeline_id": timeline_id, "status": status.value}}

    @app.get("/glass/report/{timeline_id}")
    async def get_daily_report(
        timeline_id: str,
        coord: IngestionCoordinator = Depends(get_coordinator),
    ) -> dict[str, Any]:
        try:
            report = coord.get_daily_report(timeline_id)
        except ReportNotReadyError as exc:
            detail = str(exc) or "timeline is still processing"
            raise HTTPException(status_code=409, detail=detail) from None
        except KeyError:
            raise HTTPException(status_code=404, detail="timeline not found") from None
        return {"data": report.model_dump()}

    @app.put("/glass/report/{timeline_id}")
    async def update_daily_report(
        timeline_id: str,
        payload: dict[str, Any],
        coord: IngestionCoordinator = Depends(get_coordinator),
    ) -> dict[str, Any]:
        markdown = payload.get("manual_markdown")
        metadata = payload.get("manual_metadata") or {}
        if metadata and not isinstance(metadata, dict):
            raise HTTPException(status_code=400, detail="manual_metadata must be an object")
        try:
            report = coord.save_manual_report(
                timeline_id,
                markdown=markdown or "",
                metadata=metadata,
            )
        except ReportNotReadyError as exc:
            detail = str(exc) or "timeline is still processing"
            raise HTTPException(status_code=409, detail=detail) from None
        except KeyError:
            raise HTTPException(status_code=404, detail="timeline not found") from None
        return {"data": report.model_dump()}

    @app.post("/glass/report/{timeline_id}/generate")
    async def regenerate_daily_report(
        timeline_id: str,
        coord: IngestionCoordinator = Depends(get_coordinator),
    ) -> dict[str, Any]:
        try:
            coord.regenerate_report(timeline_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="timeline not found") from None
        return {"data": {"timeline_id": timeline_id, "status": "queued"}}

    @app.get("/glass/context/{timeline_id}")
    async def get_context(
        timeline_id: str,
        coord: IngestionCoordinator = Depends(get_coordinator),
    ) -> dict[str, Any]:
        try:
            payload = coord.build_context_payload(timeline_id)
        except ReportNotReadyError as exc:
            detail = str(exc) or "timeline is still processing"
            raise HTTPException(status_code=409, detail=detail) from None
        except KeyError:
            raise HTTPException(status_code=404, detail="timeline not found") from None
        return {"data": payload}

    return app


def _build_ingestion_service(config: BackendConfig, repository: GlassContextRepository) -> GlassIngestionService:
    processor_manager = _build_processor_manager(repository)
    video_manager = _build_video_manager(config)
    return GlassIngestionService(
        video_manager=video_manager,
        processor_manager=processor_manager,
        upload_dir=config.upload_dir,
    )


def _build_processor_manager(repository: GlassContextRepository) -> ContextProcessorManager:
    manager = ContextProcessorManager()
    processor = GlassTimelineProcessor(
        repository=repository,
        chunker=ManifestChunker(),
        visual_encoder=VisualEncoder(),
    )
    manager.register_processor(processor)
    return manager


def _build_video_manager(config: BackendConfig) -> VideoManager:
    if config.is_demo:
        return _DemoVideoManager(base_dir=config.storage_base_dir / "demo")

    try:
        speech_runner = build_speech_to_text_runner_from_config()
        ffmpeg_runner = FFmpegRunner()
        return LocalVideoManager(
            base_dir=config.storage_base_dir,
            speech_runner=speech_runner,
            ffmpeg_runner=ffmpeg_runner,
        )
    except Exception as exc:  # noqa: BLE001
        try:
            from loguru import logger

            logger.warning("Falling back to demo video manager: {}", exc)
        except Exception:
            pass
        return _DemoVideoManager(base_dir=config.storage_base_dir / "fallback")


class _DemoVideoManager(VideoManager):
    """Minimal VideoManager used for demo mode and tests."""

    def __init__(self, *, base_dir: Path | None = None) -> None:
        self._base_dir = (base_dir or Path("persist") / "glass" / "demo").resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._manifests: dict[str, AlignmentManifest] = {}
        self._statuses: dict[str, IngestionStatus] = {}

    def ingest(self, source: Path | str, *, timeline_id: Optional[str] = None) -> AlignmentManifest:
        timeline = timeline_id or uuid.uuid4().hex
        self._statuses[timeline] = IngestionStatus.PROCESSING
        source_path = Path(source).resolve()
        manifest = AlignmentManifest(
            timeline_id=timeline,
            source=str(source_path),
            segments=[
                AlignmentSegment(
                    start=0.0,
                    end=10.0,
                    type=SegmentType.AUDIO,
                    payload=f"Auto-generated summary for {timeline}",
                )
            ],
        )
        self._manifests[timeline] = manifest
        self._statuses[timeline] = IngestionStatus.COMPLETED
        return manifest

    def get_status(self, timeline_id: str) -> IngestionStatus:
        if timeline_id not in self._statuses:
            raise TimelineNotFoundError(timeline_id)
        return self._statuses[timeline_id]

    def fetch_manifest(self, timeline_id: str) -> AlignmentManifest:
        manifest = self._manifests.get(timeline_id)
        if not manifest:
            raise TimelineNotFoundError(timeline_id)
        return manifest


app = create_app()
