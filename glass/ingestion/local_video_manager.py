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


class LocalVideoManager(VideoManager):
    """
    Synchronous implementation of the VideoManager contract.

    The manager processes videos on the local machine, emits aligned manifests,
    and persists artifacts below a dedicated base directory without touching the
    existing MineContext storage layout.
    """

    STATUS_FILE = "status.json"
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
        self._speech = speech_runner
        self._frame_rate = frame_rate

        self._base_dir.mkdir(parents=True, exist_ok=True)

    def ingest(self, source: Path | str, *, timeline_id: Optional[str] = None) -> AlignmentManifest:
        source_path = Path(source).expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"video not found: {source_path}")

        timeline = timeline_id or self._generate_timeline_id()
        timeline_dir = self._base_dir / timeline
        timeline_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = timeline_dir / self.MANIFEST_FILE
        if manifest_path.exists():
            logger.info("Manifest already exists for timeline {}, returning cached result", timeline)
            return AlignmentManifest.model_validate_json(manifest_path.read_text())

        logger.info("Starting ingestion for timeline {} from {}", timeline, source_path)
        self._write_status(timeline_dir, IngestionStatus.PROCESSING)

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

            manifest_path.write_text(manifest.to_json())
            self._write_raw_transcription(timeline_dir, transcription)
            self._write_status(timeline_dir, IngestionStatus.COMPLETED)
            logger.info("Finished ingestion for timeline {}", timeline)
            return manifest
        except Exception as exc:  # noqa: BLE001
            logger.exception("Ingestion failed for timeline {}: {}", timeline, exc)
            self._write_status(timeline_dir, IngestionStatus.FAILED)
            raise

    def get_status(self, timeline_id: str) -> IngestionStatus:
        timeline_dir = self._base_dir / timeline_id
        status_path = timeline_dir / self.STATUS_FILE
        if status_path.exists():
            data = json.loads(status_path.read_text())
            return IngestionStatus(data["status"])

        manifest_path = timeline_dir / self.MANIFEST_FILE
        if manifest_path.exists():
            return IngestionStatus.COMPLETED

        raise TimelineNotFoundError(timeline_id)

    def fetch_manifest(self, timeline_id: str) -> AlignmentManifest:
        timeline_dir = self._base_dir / timeline_id
        manifest_path = timeline_dir / self.MANIFEST_FILE
        if not manifest_path.exists():
            raise TimelineNotFoundError(timeline_id)
        return AlignmentManifest.model_validate_json(manifest_path.read_text())

    def _write_status(self, timeline_dir: Path, status: IngestionStatus) -> None:
        payload = {"status": status.value}
        (timeline_dir / self.STATUS_FILE).write_text(json.dumps(payload, indent=2))

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
