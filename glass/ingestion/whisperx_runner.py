from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import torch
import whisperx
from loguru import logger

from .models import AlignmentSegment, SegmentType


@dataclass(frozen=True)
class TranscriptionResult:
    segments: list[AlignmentSegment]
    raw_response: dict[str, Any]


class WhisperXRunner:
    """
    Encapsulates WhisperX transcription and alignment behavior.

    The runner must normalise WhisperX outputs into AlignmentSegment instances
    so downstream consumers never touch vendor-specific schemas.
    """

    def __init__(
        self,
        *,
        model_size: str = "tiny",
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
    ) -> None:
        resolved_device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        resolved_compute = compute_type or ("float16" if resolved_device.startswith("cuda") else "int8")

        logger.debug(
            "Loading WhisperX model size={}, device={}, compute_type={}",
            model_size,
            resolved_device,
            resolved_compute,
        )
        self._model = whisperx.load_model(
            model_size,
            device=resolved_device,
            compute_type=resolved_compute,
        )

    def transcribe(self, audio_path: Path, *, timeline_id: str) -> TranscriptionResult:
        """Perform speech-to-text on the given audio track."""
        if not audio_path.exists():
            raise FileNotFoundError(f"audio file not found: {audio_path}")

        logger.info("Transcribing audio for timeline {}", timeline_id)
        result = self._model.transcribe(str(audio_path))
        segments = self.build_segments(result)
        return TranscriptionResult(segments=segments, raw_response=result)

    def build_segments(self, whisper_output: dict[str, Any]) -> list[AlignmentSegment]:
        """
        Translate WhisperX native output into alignment segments.

        This helper exists to make unit testing easier without depending on the
        heavy WhisperX runtime.
        """
        results: list[AlignmentSegment] = []
        for item in whisper_output.get("segments", []):
            text = item.get("text", "").strip()
            if not text:
                continue
            results.append(
                AlignmentSegment(
                    start=float(item["start"]),
                    end=float(item["end"]),
                    type=SegmentType.AUDIO,
                    payload=text,
                )
            )
        if not results:
            raise ValueError("whisper output did not contain any segments")
        return results
