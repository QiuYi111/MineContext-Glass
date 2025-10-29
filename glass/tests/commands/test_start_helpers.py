from pathlib import Path

import pytest

from glass.commands import discover_date_videos


def test_discover_date_videos_filters_extensions(tmp_path) -> None:
    video_a = tmp_path / "clip_a.mp4"
    video_a.write_bytes(b"fake")
    (tmp_path / "notes.txt").write_text("skip me", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    video_b = nested / "clip_b.mkv"
    video_b.write_bytes(b"fake")

    videos = discover_date_videos(tmp_path)

    assert [path.name for path in videos] == ["clip_a.mp4", "clip_b.mkv"]


def test_discover_date_videos_raises_when_empty(tmp_path) -> None:
    empty_dir = tmp_path / "2025-01-01"
    empty_dir.mkdir()

    with pytest.raises(FileNotFoundError):
        discover_date_videos(empty_dir)
