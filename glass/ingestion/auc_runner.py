from __future__ import annotations

import base64
import uuid
import wave
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Mapping, Optional

import requests
from loguru import logger

from .models import AlignmentSegment, SegmentType
from .speech_to_text import SpeechToTextRunner, TranscriptionResult


class AUCTurboError(RuntimeError):
    """Raised when the AUC Turbo API returns an error response."""


@dataclass(frozen=True)
class AUCTurboConfig:
    """Configuration required to call the AUC Turbo API."""

    base_url: str = "https://openspeech.bytedance.com/api/v3"
    resource_id: str = "volc.bigasr.auc_turbo"
    app_key: str = ""
    access_key: str = ""
    model_name: str = "bigmodel"
    request_timeout: float = 120.0
    max_file_size_mb: float = 100.0
    max_duration_sec: float = 7200.0
    endpoint_path: str = "/auc/bigmodel/recognize/flash"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "AUCTurboConfig":
        """Create an instance from a mapping loaded out of config."""
        if data is None:
            data = {}
        allowed = {field.name for field in fields(cls)}
        kwargs = {key: data[key] for key in allowed & data.keys()}
        return cls(**kwargs)

    def build_url(self) -> str:
        return f"{self.base_url.rstrip('/')}{self.endpoint_path}"


class AUCTurboRunner(SpeechToTextRunner):
    """Speech-to-text runner backed by Volcano Engine's AUC Turbo API."""

    def __init__(
        self,
        config: AUCTurboConfig,
        *,
        session: Optional[requests.Session] = None,
    ) -> None:
        if not config.app_key or not config.access_key:
            raise ValueError("AUC Turbo app_key and access_key must be configured")
        self._config = config
        self._session = session or requests.Session()

    def transcribe(self, audio_path: Path, *, timeline_id: str) -> TranscriptionResult:
        if not audio_path.exists():
            raise FileNotFoundError(f"audio file not found: {audio_path}")

        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self._config.max_file_size_mb:
            raise ValueError(
                f"audio file {audio_path} exceeds max size "
                f"{self._config.max_file_size_mb} MB (got {file_size_mb:.2f} MB)"
            )

        duration_sec = self._calculate_duration(audio_path)
        if duration_sec is not None and duration_sec > self._config.max_duration_sec:
            raise ValueError(
                f"audio duration {duration_sec:.2f}s exceeds limit "
                f"{self._config.max_duration_sec}s"
            )

        payload = self._build_payload(audio_path)
        headers = self._build_headers()
        request_id = headers["X-Api-Request-Id"]
        try:
            response = self._session.post(
                self._config.build_url(),
                headers=headers,
                json=payload,
                timeout=self._config.request_timeout,
            )
        except requests.RequestException as exc:  # noqa: PERF203 - clarity matters
            logger.error("AUC Turbo request failed for timeline {}: {}", timeline_id, exc)
            raise AUCTurboError("AUC Turbo request failed") from exc

        if response.status_code != 200:
            raise AUCTurboError(
                f"AUC Turbo returned HTTP {response.status_code} "
                f"(request_id={request_id})"
            )

        status_code = response.headers.get("X-Api-Status-Code")
        if status_code and status_code != "20000000":
            raise AUCTurboError(
                f"AUC Turbo status={status_code} "
                f"(request_id={request_id}, message={response.headers.get('X-Api-Message')})"
            )

        data = response.json()
        segments = self._parse_segments(data)
        if not segments:
            raise ValueError("AUC Turbo response did not contain utterances")

        logger.info("AUC Turbo transcription completed for timeline {}", timeline_id)
        return TranscriptionResult(segments=segments, raw_response=data)

    def _build_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Api-App-Key": self._config.app_key,
            "X-Api-Access-Key": self._config.access_key,
            "X-Api-Resource-Id": self._config.resource_id,
            "X-Api-Request-Id": uuid.uuid4().hex,
            "X-Api-Sequence": "-1",
        }

    def _build_payload(self, audio_path: Path) -> dict[str, Any]:
        encoded_audio = base64.b64encode(audio_path.read_bytes()).decode("ascii")
        return {
            "user": {"uid": self._config.app_key},
            "audio": {"data": encoded_audio},
            "request": {"model_name": self._config.model_name},
        }

    def _parse_segments(self, payload: dict[str, Any]) -> list[AlignmentSegment]:
        result = payload.get("result") or {}
        utterances = result.get("utterances") or []
        segments: list[AlignmentSegment] = []
        for item in utterances:
            text = (item.get("text") or "").strip()
            if not text:
                continue
            try:
                start = float(item["start_time"])
                end = float(item["end_time"])
            except (KeyError, TypeError, ValueError) as exc:
                logger.debug("Skipping utterance with invalid timestamps: {}", exc)
                continue
            segments.append(
                AlignmentSegment(
                    start=start,
                    end=end,
                    type=SegmentType.AUDIO,
                    payload=text,
                )
            )
        return segments

    @staticmethod
    def _calculate_duration(audio_path: Path) -> Optional[float]:
        try:
            with wave.open(str(audio_path), "rb") as handle:
                frames = handle.getnframes()
                frame_rate = handle.getframerate() or 1
                return frames / float(frame_rate)
        except (wave.Error, OSError):
            return None
