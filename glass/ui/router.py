from __future__ import annotations

# -*- coding: utf-8 -*-

# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

"""MineContext Glass web UI routes."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

router = APIRouter(prefix="/glass", tags=["glass-ui"])

_templates_root = Path(__file__).parent / "templates"
_base_templates = Path(__file__).resolve().parents[2] / "opencontext" / "web" / "templates"

templates = Jinja2Templates(directory=str(_templates_root))
templates.env.loader = ChoiceLoader([
    FileSystemLoader(str(_templates_root)),
    templates.env.loader,
    FileSystemLoader(str(_base_templates)),
])


@router.get("", response_class=HTMLResponse, include_in_schema=False)
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def glass_dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "glass_dashboard.html",
        {
            "request": request,
            "title": "Glass Timeline",
        },
    )
