#!/usr/bin/env python3
"""Test just the working speech recognition."""

from glass.ingestion.speech_fallback import FallbackSpeechToTextRunner
from glass.ingestion.speech_to_text import TranscriptionResult
from glass.ingestion.models import AlignmentSegment


class MockWorkingSpeechRunner:
    """Mock speech runner that works normally."""

    def transcribe(self, audio_path: str, *, timeline_id: str) -> TranscriptionResult:
        return TranscriptionResult(
            segments=[
                AlignmentSegment(
                    start=0.0,
                    end=5.0,
                    type="audio",
                    payload="This is a test transcription",
                )
            ],
            raw_response={"test": "success"},
        )


def test_working_speech_recognition():
    """Test that normal speech recognition still works."""
    print("🧪 Testing normal speech recognition...")

    working_runner = MockWorkingSpeechRunner()
    fallback_runner = FallbackSpeechToTextRunner(
        base_runner=working_runner,
        fallback_enabled=True,
        log_failures=True,
    )

    audio_path = "/tmp/test_audio.wav"
    result = fallback_runner.transcribe(audio_path, timeline_id="test_timeline")

    print(f"Result: {result}")
    print(f"Segments: {len(result.segments)}")
    if result.segments:
        print(f"First segment payload: '{result.segments[0].payload}'")
        print(f"Expected: 'This is a test transcription'")
        print(f"Match: {result.segments[0].payload == 'This is a test transcription'}")

    # Should get the original result, not fallback
    assert result is not None
    assert len(result.segments) == 1, f"Expected 1 segment, got {len(result.segments)}"
    assert result.segments[0].payload == "This is a test transcription"
    assert result.raw_response.get("fallback") is None  # Not a fallback result

    print("✅ Normal transcription works correctly")


if __name__ == "__main__":
    test_working_speech_recognition()