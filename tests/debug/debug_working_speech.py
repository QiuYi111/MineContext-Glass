#!/usr/bin/env python3
"""Debug working speech recognition."""

from glass.ingestion.speech_fallback import FallbackSpeechToTextRunner
from glass.ingestion.speech_to_text import TranscriptionResult
from glass.ingestion.models import AlignmentSegment


class MockWorkingSpeechRunner:
    """Mock speech runner that works normally."""

    def transcribe(self, audio_path: str, *, timeline_id: str) -> TranscriptionResult:
        print(f"MockWorkingSpeechRunner: Creating successful transcription")
        result = TranscriptionResult(
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
        print(f"  Created result: {len(result.segments)} segments")
        print(f"  First segment: {result.segments[0].payload}")
        return result


def test_working_speech():
    """Test working speech recognition."""
    print("=== Debug Working Speech ===")

    working_runner = MockWorkingSpeechRunner()
    fallback_runner = FallbackSpeechToTextRunner(
        base_runner=working_runner,
        fallback_enabled=True,
        log_failures=True,
    )

    print(f"Fallback runner created: {fallback_runner}")

    result = fallback_runner.transcribe("/tmp/test_audio.wav", timeline_id="test_timeline")

    print(f"Final result: {len(result.segments)} segments")
    print(f"First segment: {result.segments[0].payload}")
    print(f"Raw response: {result.raw_response}")


if __name__ == "__main__":
    test_working_speech()