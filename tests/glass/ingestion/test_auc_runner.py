from __future__ import annotations

import wave
from pathlib import Path
from unittest import mock

import pytest

from glass.ingestion.auc_runner import AUCTurboConfig, AUCTurboRunner
from glass.ingestion.models import SegmentType


def _write_silence_wav(path: Path, duration: float = 0.5, sample_rate: int = 16000) -> None:
    frames = int(duration * sample_rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frames)


def test_auc_runner_transcribe_success(tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.wav"
    _write_silence_wav(audio_path)

    mock_session = mock.Mock()
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.headers = {"X-Api-Status-Code": "20000000"}
    mock_response.json.return_value = {
        "result": {
            "utterances": [
                {"start_time": 0, "end_time": 1.5, "text": "hello world"},
            ]
        }
    }
    mock_session.post.return_value = mock_response

    runner = AUCTurboRunner(
        config=AUCTurboConfig(app_key="app", access_key="key"),
        session=mock_session,
    )
    result = runner.transcribe(audio_path, timeline_id="abc123")

    assert len(result.segments) == 1
    assert result.segments[0].payload == "hello world"
    assert result.segments[0].type is SegmentType.AUDIO
    mock_session.post.assert_called_once()


def test_auc_runner_rejects_large_file(tmp_path: Path) -> None:
    audio_path = tmp_path / "oversize.wav"
    audio_path.write_bytes(b"x" * 1024 * 1024)  # 1 MB

    runner = AUCTurboRunner(
        config=AUCTurboConfig(
            app_key="app",
            access_key="key",
            max_file_size_mb=0.1,
        )
    )

    with pytest.raises(ValueError):
        runner.transcribe(audio_path, timeline_id="oversize")
