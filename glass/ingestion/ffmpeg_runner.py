from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import shutil
import subprocess

from loguru import logger


def _ensure_executable(path: str | None, /, default: str) -> str:
    if path:
        return path
    resolved = shutil.which(default)
    if not resolved:
        raise FileNotFoundError(f"{default} executable not found in PATH")
    return resolved

@dataclass(frozen=True)
class FrameExtractionResult:
    frames_dir: Path
    frame_paths: list[Path]


@dataclass(frozen=True)
class AudioExtractionResult:
    audio_path: Path


class FFmpegRunner:
    """
    Thin wrapper around ffmpeg operations required for MineContext Glass.

    A dedicated class keeps subprocess orchestration isolated so that higher-level
    managers do not accumulate special-case logic.
    """

    def __init__(self, ffmpeg_executable: str | None = None) -> None:
        self._ffmpeg = _ensure_executable(ffmpeg_executable, "ffmpeg")

    def _run(self, args: Sequence[str]) -> None:
        logger.debug("Running ffmpeg command: {}", " ".join(args))
        subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def extract_frames(
        self,
        video_path: Path,
        *,
        fps: float,
        output_dir: Path,
        image_pattern: str = "frame_%05d.png",
    ) -> FrameExtractionResult:
        """Extract frames to a temporary directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        frame_template = output_dir / image_pattern
        command = [
            self._ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video_path),
            "-vf",
            f"fps={fps}",
            str(frame_template),
        ]
        self._run(command)

        frame_paths = sorted(output_dir.glob("frame_*.png"))
        if not frame_paths:
            raise RuntimeError(f"ffmpeg did not produce any frames in {output_dir}")

        return FrameExtractionResult(frames_dir=output_dir, frame_paths=frame_paths)

    def extract_audio(self, video_path: Path, *, output_path: Path) -> AudioExtractionResult:
        """Extract the audio track as a standalone file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            self._ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(output_path),
        ]
        self._run(command)
        if not output_path.exists():
            raise RuntimeError(f"ffmpeg did not produce audio file at {output_path}")
        return AudioExtractionResult(audio_path=output_path)

    def cleanup(self, paths: Iterable[Path]) -> None:
        """Clean up temporary artifacts created during processing."""
        for path in paths:
            if not path.exists():
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
