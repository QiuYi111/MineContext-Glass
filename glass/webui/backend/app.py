from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import BackendConfig, load_config
from .demo_data import load_demo_timelines
from .repositories import TimelineRepository
from .services import DailyReportBuilder, IngestionCoordinator, MarkdownRenderer


def create_app(config: BackendConfig | None = None) -> FastAPI:
    """Create the standalone FastAPI application serving the Glass API."""

    config = config or load_config()
    repository = TimelineRepository()
    renderer = MarkdownRenderer()
    report_builder = DailyReportBuilder(renderer=renderer)
    coordinator = IngestionCoordinator(repository, config, report_builder)

    if config.is_demo:
        load_demo_timelines(
            config.demo_data_dir,
            repository=repository,
            report_builder=report_builder,
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
    app.state.repository = repository
    app.state.coordinator = coordinator

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
            record = coord.create_upload(
                file.filename,
                file.file,
                content_length=length_value,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            await file.close()

        payload = {"timeline_id": record.timeline_id, "status": record.status.value}
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
            record = coord.get_report(timeline_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="timeline not found") from None
        report = record.build_daily_report().model_dump()
        return {"data": report}

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
            record = coord.save_manual_report(
                timeline_id,
                markdown=markdown or "",
                metadata=metadata,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="timeline not found") from None
        report = record.build_daily_report().model_dump()
        return {"data": report}

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
            record = coord.get_report(timeline_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="timeline not found") from None

        report = record.build_daily_report().model_dump()
        payload = {
            "timeline_id": record.timeline_id,
            "source": record.filename,
            "items": [],
            "daily_report": report,
            "highlights": [highlight.model_dump() for highlight in record.highlights],
            "visual_cards": [card.model_dump() for card in record.visual_cards],
            "auto_markdown": record.auto_markdown,
        }
        return {"data": payload}

    return app


app = create_app()

