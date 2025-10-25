from __future__ import annotations

# -*- coding: utf-8 -*-

# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

"""Glass-specific API endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from glass.ingestion import (
    IngestionStatus,
    LocalVideoManager,
    TimelineNotFoundError,
    build_speech_to_text_runner_from_config,
)
from glass.ingestion.service import GlassIngestionService
from glass.storage.context_repository import GlassContextRepository
from opencontext.server.opencontext import OpenContext
from opencontext.server.utils import convert_resp, get_context_lab

router = APIRouter(prefix="/glass", tags=["glass"])


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
) -> dict:
    envelope = repository.load_envelope(timeline_id)
    if envelope is None:
        raise HTTPException(status_code=404, detail="context not ready for timeline")
    return convert_resp(envelope)


def _safe_status_lookup(ingestion: GlassIngestionService, timeline_id: str) -> IngestionStatus:
    try:
        return ingestion.get_status(timeline_id)
    except TimelineNotFoundError:
        return IngestionStatus.PENDING
