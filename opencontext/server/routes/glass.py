from __future__ import annotations

# -*- coding: utf-8 -*-

# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

"""Glass-specific API endpoints."""

from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from glass.reports import DailyReportService
from opencontext.utils.logging_utils import get_logger

from glass.ingestion import (
    IngestionStatus,
    LocalVideoManager,
    TimelineNotFoundError,
    build_speech_to_text_runner_from_config,
)
from glass.ingestion.service import GlassIngestionService
from glass.storage.context_repository import GlassContextRepository
from opencontext.config.global_config import GlobalConfig
from opencontext.config.glass_config import GlassConfig, create_glass_config
from opencontext.server.opencontext import OpenContext
from opencontext.server.utils import convert_resp, get_context_lab

router = APIRouter(prefix="/glass", tags=["glass"])
logger = get_logger(__name__)


class ManualReportRequest(BaseModel):
    manual_markdown: str = Field(..., description="User provided Markdown content for the daily report.")
    manual_metadata: Dict[str, Any] | None = Field(
        default=None,
        description="Optional structured metadata describing layout or pinned highlights.",
    )


def _get_ingestion_service(request: Request, context_lab: OpenContext = Depends(get_context_lab)) -> GlassIngestionService:
    service = getattr(request.app.state, "glass_ingestion_service", None)
    if service is None:
        speech_runner = build_speech_to_text_runner_from_config()
        manager = LocalVideoManager(speech_runner=speech_runner)
        service = GlassIngestionService(manager, context_lab.processor_manager)
        setattr(request.app.state, "glass_ingestion_service", service)
    return service


def _get_repository(request: Request) -> GlassContextRepository:
    repository = getattr(request.app.state, "glass_context_repository", None)
    if repository is None:
        repository = GlassContextRepository()
        setattr(request.app.state, "glass_context_repository", repository)
    return repository


def _get_report_service(
    request: Request,
    repository: GlassContextRepository = Depends(_get_repository),
) -> DailyReportService:
    service = getattr(request.app.state, "glass_report_service", None)
    if service is None:
        service = DailyReportService(repository=repository)
        setattr(request.app.state, "glass_report_service", service)
    return service


def _load_upload_limits() -> dict[str, Any]:
    """Load upload limits using unified Glass configuration."""
    glass_config = create_glass_config()
    limits = glass_config.upload_limits

    return {
        "max_size_mb": limits.max_size_mb,
        "allowed_types": limits.allowed_types,
        "max_concurrent": limits.max_concurrent,
    }


async def _persist_upload(file: UploadFile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)


@router.post("/upload")
async def upload_video(
    request: Request,
    file: UploadFile = File(...),
    ingestion: GlassIngestionService = Depends(_get_ingestion_service),
) -> dict:
    if file.filename is None or file.filename.strip() == "":
        raise HTTPException(status_code=400, detail="filename is required")

    if file.content_type and not file.content_type.startswith("video/"):
        raise HTTPException(status_code=415, detail="only video uploads are supported")

    destination = ingestion.allocate_upload_path(file.filename)
    await _persist_upload(file, destination)
    await file.close()

    timeline_id = ingestion.submit(destination)
    status = _safe_status_lookup(ingestion, timeline_id)

    payload = {
        "timeline_id": timeline_id,
        "status": status.value,
    }
    return convert_resp(payload)


@router.get("/uploads/limits")
def get_upload_limits() -> dict:
    return convert_resp(_load_upload_limits())


@router.get("/timelines")
def get_all_timelines(
    repository: GlassContextRepository = Depends(_get_repository)
) -> dict:
    """Get all available timelines with basic metadata."""
    timelines = repository.get_all_timelines()
    return convert_resp(timelines)


@router.get("/status/{timeline_id}")
def get_status(
    timeline_id: str,
    ingestion: GlassIngestionService = Depends(_get_ingestion_service),
    repository: GlassContextRepository = Depends(_get_repository),
    report_service: DailyReportService = Depends(_get_report_service),
) -> dict:
    try:
        # Get basic status
        status = ingestion.get_status(timeline_id)

        # Enhanced status with progress details
        response_data = {
            "timeline_id": timeline_id,
            "status": status.value,
            "progress": 0,
            "current_step": "准备中...",
            "total_steps": 4,
            "message": ""
        }

        # Map status to progress details
        if status.value == "pending":
            response_data.update({
                "progress": 0,
                "current_step": "等待开始处理...",
                "message": "任务已提交，等待开始处理"
            })
        elif status.value == "processing":
            response_data.update({
                "progress": 50,  # Estimate 50% during processing
                "current_step": "正在处理视频内容...",
                "message": "正在提取视频帧和转录语音"
            })
        elif status.value == "completed":
            # Check if data is actually ready for consumption
            envelope = repository.load_envelope(timeline_id)
            if envelope is not None:
                response_data.update({
                    "progress": 100,
                    "current_step": "处理完成",
                    "message": "视频处理完成，数据已准备就绪",
                    "status": "ready"  # Use different status to indicate data is ready
                })
            else:
                # Ingestion completed but data not yet processed
                response_data.update({
                    "progress": 85,
                    "current_step": "正在处理时间线数据...",
                    "message": "视频处理完成，正在生成时间线上下文",
                    "status": "finalizing"  # New intermediate status
                })
        elif status.value == "failed":
            response_data.update({
                "progress": 0,
                "current_step": "处理失败",
                "message": "视频处理过程中出现错误"
            })

    except TimelineNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return convert_resp(response_data)


@router.get("/context/{timeline_id}")
def get_context(
    timeline_id: str,
    repository: GlassContextRepository = Depends(_get_repository),
    report_service: DailyReportService = Depends(_get_report_service),
) -> dict:
    envelope = repository.load_envelope(timeline_id)
    if envelope is None:
        raise HTTPException(status_code=404, detail="context not ready for timeline")
    try:
        report = report_service.get_report(timeline_id, envelope=envelope)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    payload = envelope.model_dump()
    payload["summary"] = report_service.build_summary(report)
    payload["daily_report"] = report
    payload["highlights"] = report.highlights
    payload["visual_cards"] = report.visual_cards
    payload["auto_markdown"] = report.auto_markdown
    return convert_resp(payload)


@router.get("/report/{timeline_id}")
def get_daily_report(
    timeline_id: str,
    repository: GlassContextRepository = Depends(_get_repository),
    report_service: DailyReportService = Depends(_get_report_service),
) -> dict:
    envelope = repository.load_envelope(timeline_id)
    if envelope is None:
        raise HTTPException(status_code=404, detail="timeline not ready")
    try:
        report = report_service.get_report(timeline_id, envelope=envelope)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return convert_resp(report)


@router.put("/report/{timeline_id}")
def update_daily_report(
    timeline_id: str,
    payload: ManualReportRequest,
    repository: GlassContextRepository = Depends(_get_repository),
    report_service: DailyReportService = Depends(_get_report_service),
) -> dict:
    envelope = repository.load_envelope(timeline_id)
    if envelope is None:
        raise HTTPException(status_code=404, detail="timeline not ready")
    try:
        report = report_service.save_manual_report(
            timeline_id=timeline_id,
            manual_markdown=payload.manual_markdown,
            manual_metadata=payload.manual_metadata or {},
            envelope=envelope,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return convert_resp(report)


@router.post("/report/{timeline_id}/generate")
def regenerate_daily_report(
    timeline_id: str,
    repository: GlassContextRepository = Depends(_get_repository),
    report_service: DailyReportService = Depends(_get_report_service),
) -> dict:
    """Regenerate the daily report for a timeline using intelligent LLM analysis."""
    envelope = repository.load_envelope(timeline_id)
    if envelope is None:
        raise HTTPException(status_code=404, detail="timeline not ready")

    try:
        # Use CLI's ReportGenerator for intelligent report generation
        import asyncio
        from opencontext.context_consumption.generation.generation_report import ReportGenerator
        from glass.consumption import GlassContextSource

        # Get timeline time range
        if envelope.items:
            timestamps = []
            for item in envelope.items:
                metadata = item.context.metadata or {}
                start_time = metadata.get("segment_start")
                end_time = metadata.get("segment_end")
                if end_time:
                    timestamps.append(float(end_time))
                elif start_time:
                    timestamps.append(float(start_time))

            if timestamps:
                start_time = int(min(timestamps))
                end_time = int(max(timestamps))
            else:
                # Fallback to current time if no timestamps found
                import time
                current_time = int(time.time())
                start_time = current_time - 3600  # 1 hour ago
                end_time = current_time
        else:
            raise HTTPException(status_code=404, detail="no content found in timeline")

        # Generate intelligent report
        async def generate_report():
            generator = ReportGenerator(glass_source=GlassContextSource())
            return await generator.generate_report(
                start_time,
                end_time,
                timeline_id=timeline_id,
            )

        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            intelligent_report = loop.run_until_complete(generate_report())
        finally:
            loop.close()

        if intelligent_report:
            # Save the intelligent report as auto_markdown with a special marker
            repository.upsert_daily_report(
                timeline_id=timeline_id,
                manual_markdown=intelligent_report,  # Store in manual_markdown for persistence
                manual_metadata={"generation_method": "intelligent_llm"},
                rendered_html="",
            )

            return convert_resp({
                "timeline_id": timeline_id,
                "status": "completed"
            })
        else:
            raise HTTPException(status_code=500, detail="Report generation returned empty content")

    except Exception as exc:
        logger.exception(f"Failed to generate intelligent report: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to regenerate report: {exc}") from exc


def _safe_status_lookup(ingestion: GlassIngestionService, timeline_id: str) -> IngestionStatus:
    try:
        return ingestion.get_status(timeline_id)
    except TimelineNotFoundError:
        return IngestionStatus.PENDING
