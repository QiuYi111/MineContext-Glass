from __future__ import annotations

import io
from pathlib import Path

from fastapi.testclient import TestClient

from glass.webui.backend.app import create_app
from glass.webui.backend.config import BackendConfig, UploadLimits


def _make_config(tmp_dir: Path, *, mode: str = "demo") -> BackendConfig:
    config = BackendConfig(
        mode=mode,
        upload_dir=tmp_dir / "uploads",
        state_db_path=tmp_dir / "state.db",
        storage_base_dir=tmp_dir / "storage",
        demo_data_dir=Path(__file__).resolve().parents[1] / "demo_data",
        processing_delay_seconds=0.0,
        upload_limits=UploadLimits(max_size_mb=8, allowed_types=["video/mp4"], max_concurrent=1),
    )
    config.upload_dir.mkdir(parents=True, exist_ok=True)
    config.storage_base_dir.mkdir(parents=True, exist_ok=True)
    return config


def test_demo_seed_is_available(tmp_path: Path) -> None:
    app = create_app(_make_config(tmp_path))
    client = TestClient(app)

    response = client.get("/glass/report/demo-timeline-001")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["timeline_id"] == "demo-timeline-001"
    assert data["highlights"]
    status = client.get("/glass/status/demo-timeline-001")
    assert status.status_code == 200
    assert status.json()["data"]["status"] == "completed"


def test_demo_context_payload_contains_items(tmp_path: Path) -> None:
    app = create_app(_make_config(tmp_path))
    client = TestClient(app)

    response = client.get("/glass/context/demo-timeline-001")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["timeline_id"] == "demo-timeline-001"
    assert payload["items"]
    assert payload["daily_report"]["timeline_id"] == "demo-timeline-001"


def test_demo_mode_blocks_uploads(tmp_path: Path) -> None:
    app = create_app(_make_config(tmp_path))
    client = TestClient(app)

    response = client.post(
        "/glass/upload",
        files={"file": ("sample.mp4", io.BytesIO(b"demo-bytes"), "video/mp4")},
    )
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"]


def test_manual_report_update(tmp_path: Path) -> None:
    app = create_app(_make_config(tmp_path))
    client = TestClient(app)

    timeline_id = "demo-timeline-001"

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

    final_report = client.get(f"/glass/report/{timeline_id}")
    assert final_report.status_code == 200
    payload = final_report.json()["data"]
    assert payload["manual_markdown"] is None
