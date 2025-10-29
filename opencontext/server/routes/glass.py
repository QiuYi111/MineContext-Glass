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

from glass.ingestion import (
    IngestionStatus,
    LocalVideoManager,
    TimelineNotFoundError,
    build_speech_to_text_runner_from_config,
)
from glass.ingestion.service import GlassIngestionService
from glass.storage.context_repository import GlassContextRepository
from opencontext.config.global_config import GlobalConfig
from opencontext.server.opencontext import OpenContext
from opencontext.server.utils import convert_resp, get_context_lab

router = APIRouter(prefix="/glass", tags=["glass"])


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
    defaults = {
        "max_size_mb": 2_048,
        "allowed_types": ["video/mp4", "video/quicktime", "video/x-matroska"],
        "max_concurrent": 2,
    }
    try:
        config = GlobalConfig.get_instance().get_config("glass.uploads") or {}
    except Exception:  # noqa: BLE001
        return defaults

    merged = defaults.copy()
    for key, value in config.items():
        if value is not None:
            merged[key] = value
    return merged


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


@router.get("/status/{timeline_id}")
def get_status(
    timeline_id: str,
    ingestion: GlassIngestionService = Depends(_get_ingestion_service),
) -> dict:
    try:
        status = ingestion.get_status(timeline_id)
    except TimelineNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return convert_resp({"timeline_id": timeline_id, "status": status.value})


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


def _safe_status_lookup(ingestion: GlassIngestionService, timeline_id: str) -> IngestionStatus:
    try:
        return ingestion.get_status(timeline_id)
    except TimelineNotFoundError:
        return IngestionStatus.PENDING
