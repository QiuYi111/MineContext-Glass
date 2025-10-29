from __future__ import annotations

import io
from pathlib import Path

from fastapi.testclient import TestClient

from glass.webui.backend.app import create_app
from glass.webui.backend.config import BackendConfig, UploadLimits


def _make_config(tmp_dir: Path) -> BackendConfig:
    return BackendConfig(
        mode="demo",
        upload_dir=tmp_dir / "uploads",
        demo_data_dir=Path(__file__).resolve().parents[1] / "demo_data",
        processing_delay_seconds=0.0,
        upload_limits=UploadLimits(max_size_mb=8, allowed_types=["video/mp4"], max_concurrent=1),
    )


def test_demo_seed_is_available(tmp_path: Path) -> None:
    app = create_app(_make_config(tmp_path))
    client = TestClient(app)

    response = client.get("/glass/report/demo-timeline-001")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["timeline_id"] == "demo-timeline-001"
    assert data["highlights"]


def test_upload_flow_creates_timeline(tmp_path: Path) -> None:
    app = create_app(_make_config(tmp_path))
    client = TestClient(app)

    response = client.post(
        "/glass/upload",
        files={"file": ("sample.mp4", io.BytesIO(b"demo-bytes"), "video/mp4")},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    timeline_id = payload["timeline_id"]
    assert timeline_id

    status_response = client.get(f"/glass/status/{timeline_id}")
    assert status_response.status_code == 200
    status = status_response.json()["data"]["status"]
    assert status in {"processing", "completed"}

    report_response = client.get(f"/glass/report/{timeline_id}")
    assert report_response.status_code == 200
    report = report_response.json()["data"]
    assert report["timeline_id"] == timeline_id
    assert report["auto_markdown"]


def test_manual_report_update(tmp_path: Path) -> None:
    app = create_app(_make_config(tmp_path))
    client = TestClient(app)

    upload = client.post(
        "/glass/upload",
        files={"file": ("sample.mp4", io.BytesIO(b"data"), "video/mp4")},
    )
    timeline_id = upload.json()["data"]["timeline_id"]

    update = client.put(
        f"/glass/report/{timeline_id}",
        json={
            "manual_markdown": "# Updated\n\n- 手动补充",
            "manual_metadata": {"pinned": True},
        },
    )
    assert update.status_code == 200
    updated = update.json()["data"]
    assert updated["manual_markdown"].startswith("# Updated")
    assert updated["manual_metadata"]["pinned"] is True

    regenerate = client.post(f"/glass/report/{timeline_id}/generate")
    assert regenerate.status_code == 200
    assert regenerate.json()["data"]["status"] == "queued"
