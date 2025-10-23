from __future__ import annotations

from pathlib import Path

import pytest

from glass.ingestion import IngestionStatus, LocalVideoManager


@pytest.mark.slow
def test_local_video_manager_runs_pipeline(tmp_path: Path) -> None:
    sample_video = Path("videos/22-10/Video Playback.mp4")
    if not sample_video.exists():
        pytest.skip("sample video not available")

    manager = LocalVideoManager(base_dir=tmp_path, frame_rate=0.5)
    manifest = manager.ingest(sample_video)

    assert manifest.timeline_id
    assert manifest.segments, "manifest should contain segments"
    assert any(segment.type.value == "audio" for segment in manifest.segments), "audio segments missing"
    assert any(segment.type.value == "frame" for segment in manifest.segments), "frame segments missing"

    fetched_status = manager.get_status(manifest.timeline_id)
    assert fetched_status is IngestionStatus.COMPLETED

    fetched_manifest = manager.fetch_manifest(manifest.timeline_id)
    assert fetched_manifest.timeline_id == manifest.timeline_id
