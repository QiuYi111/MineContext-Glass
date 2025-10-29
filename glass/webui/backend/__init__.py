from __future__ import annotations

"""
Standalone backend for the Glass WebUI.

Expose ``create_app`` so callers can run ``uvicorn glass.webui.backend.app:app``.
"""

from .app import app, create_app

__all__ = ["app", "create_app"]

