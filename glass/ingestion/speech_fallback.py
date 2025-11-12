"""
Speech recognition fallback mechanism.

Implements graceful degradation when speech-to-text services fail.
Allows video processing to continue without audio transcription.
"""

from __future__ import annotations

import functools
import logging
from typing import Callable, Optional, Any

from .models import AlignmentSegment
from .speech_to_text import SpeechToTextRunner, TranscriptionResult

logger = logging.getLogger(__name__)


class SpeechFallbackError(RuntimeError):
    """Raised when speech recognition fails and fallback is not available."""


def create_fallback_transcription(duration_seconds: float = 0.0) -> TranscriptionResult:
    """
    Create a fallback transcription result when speech recognition fails.

    Args:
        duration_seconds: Estimated duration of the audio in seconds

    Returns:
        TranscriptionResult with empty segments and fallback flag
    """
    return TranscriptionResult(
        segments=[],
        raw_response={
            "fallback": True,
            "reason": "speech_recognition_failed",
            "duration_seconds": duration_seconds,
        }
    )


def with_speech_fallback(
    *,
    enabled: bool = True,
    log_failures: bool = True,
    create_dummy_segments: bool = True,
) -> Callable:
    """
    Decorator that provides speech recognition fallback.

    When speech recognition fails, returns a fallback result instead of raising
    an exception. This allows video processing to continue without audio transcription.

    Args:
        enabled: Whether fallback is enabled (default: True)
        log_failures: Whether to log speech recognition failures (default: True)
        create_dummy_segments: Whether to create dummy segments for video alignment (default: True)

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not enabled:
                return func(*args, **kwargs)

            try:
                result = func(*args, **kwargs)

                # Validate result
                if isinstance(result, TranscriptionResult):
                    if not result.segments and create_dummy_segments:
                        # Empty transcription, add dummy segment for video alignment
                        logger.info("Speech recognition returned empty result, adding dummy segment for video alignment")
                        result.segments.append(AlignmentSegment(
                            start=0.0,
                            end=1.0,
                            type="audio",  # Use audio type for fallback
                            payload="[Audio transcription unavailable]",
                        ))

                return result

            except Exception as exc:
                # Log the failure if requested
                if log_failures:
                    logger.warning(
                        "Speech recognition failed with error: %s. ",
                        exc,
                        exc_info=True,
                    )

                # Estimate duration from kwargs if possible
                duration = 0.0
                audio_path = kwargs.get('audio_path') or (args[0] if args else None)
                if audio_path:
                    # Try to estimate duration from file size or other heuristics
                    try:
                        import os
                        if os.path.exists(audio_path):
                            # Rough estimate: ~1 second per 16KB for 16kHz mono WAV
                            file_size = os.path.getsize(audio_path)
                            duration = max(1.0, file_size / (16 * 1024))
                    except Exception:
                        duration = 0.0

                # Create fallback result
                fallback_result = create_fallback_transcription(duration)

                if create_dummy_segments:
                    # Always create at least one dummy segment for video alignment
                    segment_duration = max(1.0, min(30.0, duration))  # Min 1s, max 30s
                    fallback_result.segments.append(AlignmentSegment(
                        start=0.0,
                        end=segment_duration,
                        type="audio",  # Use audio type for fallback
                        payload="[Speech recognition failed - video only processing]",
                    ))

                logger.info(
                    "Using speech fallback: duration=%.1fs, segments=%d",
                    duration,
                    len(fallback_result.segments),
                )

                return fallback_result

        return wrapper
    return decorator


class FallbackSpeechToTextRunner(SpeechToTextRunner):
    """
    Speech-to-text runner with automatic fallback on failures.

    Wraps another SpeechToTextRunner and provides fallback behavior
    when the underlying service fails.
    """

    def __init__(
        self,
        *,
        base_runner: SpeechToTextRunner,
        fallback_enabled: bool = True,
        log_failures: bool = True,
    ) -> None:
        self._base_runner = base_runner
        self._fallback_enabled = fallback_enabled
        self._log_failures = log_failures

    def transcribe(self, audio_path: str, *, timeline_id: Optional[str] = None) -> TranscriptionResult:
        """
        Transcribe audio with automatic fallback on failure.

        Args:
            audio_path: Path to audio file
            timeline_id: Optional timeline identifier

        Returns:
            TranscriptionResult (either real or fallback)
        """
        if not self._fallback_enabled:
            # No fallback, just call the base runner directly
            return self._base_runner.transcribe(audio_path, timeline_id=timeline_id)

        # Use fallback decorator logic
        return self._transcribe_with_fallback(audio_path, timeline_id=timeline_id)

    @with_speech_fallback(enabled=True, log_failures=True, create_dummy_segments=True)
    def _transcribe_with_fallback(self, audio_path: str, *, timeline_id: Optional[str] = None) -> TranscriptionResult:
        """Internal method with fallback decorator applied."""
        return self._base_runner.transcribe(audio_path, timeline_id=timeline_id)

    def __repr__(self) -> str:
        return f"FallbackSpeechToTextRunner(base={self._base_runner!r})"