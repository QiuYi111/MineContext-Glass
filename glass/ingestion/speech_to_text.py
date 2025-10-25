from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .models import AlignmentSegment


@dataclass(frozen=True)
class TranscriptionResult:
    """Container for normalised transcription output."""

    segments: list[AlignmentSegment]
    raw_response: dict[str, Any]


class SpeechToTextRunner(Protocol):
    """Protocol implemented by all speech-to-text backends."""

    def transcribe(self, audio_path: Path, *, timeline_id: str) -> TranscriptionResult:
        ...
