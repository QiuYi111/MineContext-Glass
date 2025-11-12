from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Optional

from loguru import logger

from .ffmpeg_runner import FFmpegRunner
from .models import AlignmentManifest, AlignmentSegment, IngestionStatus, SegmentType
from .video_manager import TimelineNotFoundError, VideoManager
from .speech_to_text import SpeechToTextRunner, TranscriptionResult
from .state_manager import AtomicStateManager, StateError, create_state_manager
from .speech_fallback import FallbackSpeechToTextRunner, with_speech_fallback


class LocalVideoManager(VideoManager):
    """
    Synchronous implementation of the VideoManager contract.

    The manager processes videos on the local machine, emits aligned manifests,
    and persists artifacts below a dedicated base directory without touching the
    existing MineContext storage layout.
    """

    MANIFEST_FILE = "alignment_manifest.json"
    RAW_TRANSCRIPT_FILE = "transcription_raw.json"

    def __init__(
        self,
        *,
        base_dir: Path | None = None,
        ffmpeg_runner: FFmpegRunner | None = None,
        speech_runner: SpeechToTextRunner | None = None,
        frame_rate: float = 1.0,
    ) -> None:
        if frame_rate <= 0:
            raise ValueError("frame_rate must be positive")
        if speech_runner is None:
            raise ValueError("speech_runner is required for LocalVideoManager")

        self._base_dir = (base_dir or Path("persist") / "glass").resolve()
        self._ffmpeg = ffmpeg_runner or FFmpegRunner()
        self._speech = FallbackSpeechToTextRunner(
            base_runner=speech_runner,
            fallback_enabled=True,
            log_failures=True,
        )
        self._frame_rate = frame_rate
        self._state_manager = create_state_manager(self._base_dir)

        self._base_dir.mkdir(parents=True, exist_ok=True)

    def ingest(self, source: Path | str, *, timeline_id: Optional[str] = None) -> AlignmentManifest:
        source_path = Path(source).expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"video not found: {source_path}")

        timeline = timeline_id or self._generate_timeline_id()

        # Check if already completed (atomic check)
        try:
            state = self._state_manager.get_state(timeline)
            if state.status == IngestionStatus.COMPLETED:
                # Return cached result without reprocessing
                timeline_dir = self._base_dir / timeline
                manifest_path = timeline_dir / self.MANIFEST_FILE
                if manifest_path.exists():
                    logger.info("Manifest already exists for timeline {}, returning cached result", timeline)
                    return AlignmentManifest.model_validate_json(manifest_path.read_text())
        except StateError:
            # Timeline doesn't exist yet, create it
            pass

        # Create timeline with atomic state management
        try:
            state = self._state_manager.create_timeline(timeline)
            logger.info("Starting ingestion for timeline {} from {}", timeline, source_path)
            self._state_manager.update_status(timeline, IngestionStatus.PROCESSING)
        except StateError as exc:
            logger.error("Failed to create timeline {}: {}", timeline, exc)
            raise RuntimeError(f"Failed to initialize timeline {timeline}") from exc

        timeline_dir = self._base_dir / timeline
        copied_source = timeline_dir / source_path.name
        if not copied_source.exists():
            shutil.copy2(source_path, copied_source)

        frames_dir = timeline_dir / "frames"
        audio_path = timeline_dir / "audio.wav"

        try:
            frame_result = self._ffmpeg.extract_frames(
                copied_source,
                fps=self._frame_rate,
                output_dir=frames_dir,
            )

            audio_result = self._ffmpeg.extract_audio(
                copied_source,
                output_path=audio_path,
            )

            transcription = self._speech.transcribe(audio_result.audio_path, timeline_id=timeline)

            manifest = self._build_manifest(
                timeline_id=timeline,
                source=copied_source,
                frames=frame_result.frame_paths,
                transcription=transcription,
            )

            manifest_path = timeline_dir / self.MANIFEST_FILE
            manifest_path.write_text(manifest.to_json())
            self._write_raw_transcription(timeline_dir, transcription)

            # Atomically update to completed status
            self._state_manager.update_status(timeline, IngestionStatus.COMPLETED)
            logger.info("Finished ingestion for timeline {}", timeline)
            return manifest

        except Exception as exc:  # noqa: BLE001
            logger.exception("Ingestion failed for timeline {}: {}", timeline, exc)
            # Atomically update to failed status with error message
            self._state_manager.update_status(timeline, IngestionStatus.FAILED, error_message=str(exc))
            raise

    def get_status(self, timeline_id: str) -> IngestionStatus:
        """
        Get ingestion status for timeline using atomic state management.

        This eliminates the race conditions present in the original implementation
        by using file locking and maintaining a single source of truth.
        """
        try:
            state = self._state_manager.get_state(timeline_id)
            return state.status
        except StateError as exc:
            # Convert StateError to TimelineNotFoundError for API compatibility
            raise TimelineNotFoundError(timeline_id) from exc

    def fetch_manifest(self, timeline_id: str) -> AlignmentManifest:
        timeline_dir = self._base_dir / timeline_id
        manifest_path = timeline_dir / self.MANIFEST_FILE
        if not manifest_path.exists():
            raise TimelineNotFoundError(timeline_id)
        return AlignmentManifest.model_validate_json(manifest_path.read_text())


    def _write_raw_transcription(self, timeline_dir: Path, transcription: TranscriptionResult) -> None:
        raw_path = timeline_dir / self.RAW_TRANSCRIPT_FILE
        raw_path.write_text(json.dumps(transcription.raw_response, indent=2))

    def _build_manifest(
        self,
        *,
        timeline_id: str,
        source: Path,
        frames: list[Path],
        transcription: TranscriptionResult,
    ) -> AlignmentManifest:
        frame_segments = self._build_frame_segments(frames)
        segments = frame_segments + transcription.segments
        return AlignmentManifest(
            timeline_id=timeline_id,
            source=str(source),
            segments=segments,
        )

    def _build_frame_segments(self, frames: list[Path]) -> list[AlignmentSegment]:
        segments: list[AlignmentSegment] = []
        for index, frame_path in enumerate(frames):
            start = index / self._frame_rate
            end = (index + 1) / self._frame_rate
            segments.append(
                AlignmentSegment(
                    start=start,
                    end=end,
                    type=SegmentType.FRAME,
                    payload=str(frame_path),
                )
            )
        return segments

    @staticmethod
    def _generate_timeline_id() -> str:
        return uuid.uuid4().hex
