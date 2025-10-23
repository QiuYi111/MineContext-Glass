from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from glass.ui.router import router as ui_router


def test_glass_dashboard_contains_upload_hooks() -> None:
    app = FastAPI()
    app.include_router(ui_router)
    client = TestClient(app)

    response = client.get("/glass")
    assert response.status_code == 200
    html = response.text

    assert 'id="glass-dropzone"' in html
    assert 'id="glass-file-input"' in html
    assert "fetch('/glass/upload'" in html
