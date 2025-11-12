#!/usr/bin/env python3
"""Debug script for speech fallback mechanism."""

from glass.ingestion.speech_fallback import FallbackSpeechToTextRunner
from glass.ingestion.speech_to_text import TranscriptionResult
from glass.ingestion.models import AlignmentSegment


class MockFailingSpeechRunner:
    """Mock speech runner that always fails."""

    def transcribe(self, audio_path: str, *, timeline_id: str) -> TranscriptionResult:
        print(f"MockFailingSpeechRunner: Raising exception for {audio_path}")
        raise RuntimeError("AUC Turbo service unavailable")


def test_simple_fallback():
    """Test simple fallback case."""
    print("=== Debug Speech Fallback ===")

    # Test 1: Fallback enabled (should work)
    print("\n--- Test 1: Fallback ENABLED ---")
    failing_runner = MockFailingSpeechRunner()
    fallback_runner = FallbackSpeechToTextRunner(
        base_runner=failing_runner,
        fallback_enabled=True,
        log_failures=True,
    )

    try:
        result = fallback_runner.transcribe("/tmp/test_audio.wav", timeline_id="test_timeline")
        print(f"✅ Fallback worked: {len(result.segments)} segments")
        return True
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
        return False


def test_fallback_disabled():
    """Test fallback disabled case."""
    print("\n--- Test 2: Fallback DISABLED ---")
    failing_runner = MockFailingSpeechRunner()
    fallback_runner = FallbackSpeechToTextRunner(
        base_runner=failing_runner,
        fallback_enabled=False,  # Disabled
        log_failures=True,
    )

    try:
        result = fallback_runner.transcribe("/tmp/test_audio.wav", timeline_id="test_timeline")
        print(f"❌ Should have raised exception but got result: {result}")
        return False
    except RuntimeError as e:
        print(f"✅ Correctly raised exception: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected exception: {e}")
        return False


if __name__ == "__main__":
    success1 = test_simple_fallback()
    success2 = test_fallback_disabled()

    overall_success = success1 and success2
    exit(0 if overall_success else 1)