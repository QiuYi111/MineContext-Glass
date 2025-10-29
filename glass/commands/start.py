from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence

from loguru import logger

from glass.consumption import GlassContextSource
from glass.ingestion import (
    FFmpegRunner,
    LocalVideoManager,
    SpeechToTextRunner,
    build_speech_to_text_runner_from_config,
)
from glass.processing.chunkers import ManifestChunker
from glass.processing.timeline_processor import GlassTimelineProcessor
from glass.processing.visual_encoder import VisualEncoder
from glass.storage.context_repository import GlassContextRepository
from opencontext.context_consumption.generation.generation_report import ReportGenerator
from opencontext.managers.processor_manager import ContextProcessorManager
from opencontext.models.context import RawContextProperties
from opencontext.models.enums import ContentFormat, ContextSource

KNOWN_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".webm",
    ".mpg",
    ".mpeg",
    ".m4v",
    ".wmv",
    ".flv",
    ".ts",
    ".mp2",
}


def _sanitize_identifier(value: str) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z]+", "-", value).strip("-")
    return normalized.lower() or "video"


def _is_video_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in KNOWN_VIDEO_EXTENSIONS


def discover_date_videos(date_dir: Path) -> List[Path]:
    """
    Discover videos under the provided date directory.
    """
    if not date_dir.exists():
        raise FileNotFoundError(f"Videos directory not found: {date_dir}")
    if not date_dir.is_dir():
        raise NotADirectoryError(f"Video path is not a directory: {date_dir}")

    videos = sorted(
        path for path in date_dir.rglob("*") if _is_video_file(path)
    )
    if not videos:
        raise FileNotFoundError(f"No video files found under {date_dir}")
    return videos


@dataclass(frozen=True)
class TimelineRunResult:
    timeline_id: str
    video_path: Path
    processed_contexts: int
    report_path: Optional[Path]


class GlassBatchRunner:
    """
    Drive ingestion → processing → reporting for a batch of videos.
    """

    def __init__(
        self,
        *,
        frame_rate: float = 1.0,
        repository: Optional[GlassContextRepository] = None,
        speech_runner: Optional[SpeechToTextRunner] = None,
        ffmpeg_runner: Optional[FFmpegRunner] = None,
        processor_manager: Optional[ContextProcessorManager] = None,
        report_lookback_minutes: int = 120,
    ) -> None:
        if frame_rate <= 0:
            raise ValueError("frame_rate must be positive")

        self._repository = repository or GlassContextRepository()
        self._speech_runner = speech_runner or build_speech_to_text_runner_from_config()
        self._ffmpeg_runner = ffmpeg_runner or FFmpegRunner()
        self._video_manager = LocalVideoManager(
            ffmpeg_runner=self._ffmpeg_runner,
            speech_runner=self._speech_runner,
            frame_rate=frame_rate,
        )
        self._processor_manager = processor_manager or self._build_processor_manager(self._repository)
        self._report_generator = ReportGenerator(
            glass_source=GlassContextSource(repository=self._repository)
        )
        self._report_lookback = max(report_lookback_minutes, 1)

    def run(
        self,
        *,
        date_token: str,
        video_paths: Sequence[Path],
        timeline_prefix: Optional[str] = None,
        report_dir: Optional[Path] = None,
    ) -> List[TimelineRunResult]:
        if not video_paths:
            return []

        report_dir = report_dir.resolve() if report_dir else None
        if report_dir:
            report_dir.mkdir(parents=True, exist_ok=True)

        results: List[TimelineRunResult] = []
        for index, video_path in enumerate(video_paths):
            timeline_id = self._build_timeline_id(
                date_token=date_token,
                video_path=video_path,
                index=index,
                prefix=timeline_prefix,
            )
            logger.info("Processing %s as timeline %s", video_path, timeline_id)
            manifest_json = self._ingest(video_path, timeline_id)
            processed_contexts = self._process_manifest(
                timeline_id=timeline_id,
                manifest_json=manifest_json,
            )
            report_path = self._maybe_generate_report(
                timeline_id=timeline_id,
                report_dir=report_dir,
            )
            results.append(
                TimelineRunResult(
                    timeline_id=timeline_id,
                    video_path=video_path,
                    processed_contexts=processed_contexts,
                    report_path=report_path,
                )
            )
        return results

    def _build_timeline_id(
        self,
        *,
        date_token: str,
        video_path: Path,
        index: int,
        prefix: Optional[str],
    ) -> str:
        slug = _sanitize_identifier(video_path.stem)
        base = prefix or date_token
        return f"{base}-{index + 1:02d}-{slug}"

    def _ingest(self, video_path: Path, timeline_id: str) -> str:
        manifest = self._video_manager.ingest(video_path, timeline_id=timeline_id)
        segments = len(manifest.segments)
        if segments == 0:
            raise RuntimeError(f"Ingestion produced an empty manifest for {timeline_id}")
        return manifest.to_json()

    def _process_manifest(self, *, timeline_id: str, manifest_json: str) -> int:
        raw_context = RawContextProperties(
            content_format=ContentFormat.VIDEO,
            source=ContextSource.VIDEO,
            create_time=datetime.now(timezone.utc),
            additional_info={
                "timeline_id": timeline_id,
                "alignment_manifest": manifest_json,
            },
        )
        processed_contexts = self._processor_manager.process(raw_context)
        if not processed_contexts:
            raise RuntimeError(f"Timeline processor emitted no contexts for {timeline_id}")
        return len(processed_contexts)

    def _maybe_generate_report(
        self,
        *,
        timeline_id: str,
        report_dir: Optional[Path],
    ) -> Optional[Path]:
        if not report_dir:
            return None

        end_ts = int(datetime.now(timezone.utc).timestamp())
        start_ts = end_ts - self._report_lookback * 60
        try:
            report = asyncio.run(
                self._report_generator.generate_report(
                    start_ts,
                    end_ts,
                    timeline_id=timeline_id,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to generate report for timeline %s: %s", timeline_id, exc)
            return None

        if not report:
            logger.info("Report generator returned empty content for %s", timeline_id)
            return None

        output_path = report_dir / f"{timeline_id}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        logger.info("Report written to %s", output_path)
        return output_path

    @staticmethod
    def _build_processor_manager(repository: GlassContextRepository) -> ContextProcessorManager:
        manager = ContextProcessorManager()
        processor = GlassTimelineProcessor(
            repository=repository,
            chunker=ManifestChunker(),
            visual_encoder=VisualEncoder(),
        )
        manager.register_processor(processor)
        return manager
