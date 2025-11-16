from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence, Optional
import sys
import platform

import shutil
import subprocess

from loguru import logger


class FFmpegNotFoundError(Exception):
    """FFmpeg未找到异常"""
    def __init__(self, message: str, install_guide: str = None):
        super().__init__(message)
        self.install_guide = install_guide


def get_ffmpeg_path() -> str:
    """
    获取FFmpeg路径的智能检测策略

    Returns:
        str: FFmpeg可执行文件路径

    Raises:
        FFmpegNotFoundError: 如果找不到FFmpeg
    """
    # 1. 检查app内捆绑版本（打包后）
    if getattr(sys, '_MEIPASS', None):
        bundled_ffmpeg = Path(sys._MEIPASS) / "bin" / "ffmpeg"
        if bundled_ffmpeg.exists():
            logger.info(f"使用捆绑的FFmpeg: {bundled_ffmpeg}")
            return str(bundled_ffmpeg)

    # 2. 检查Homebrew安装路径（macOS优先）
    if platform.system() == "Darwin":
        # Apple Silicon
        homebrew_arm = Path("/opt/homebrew/bin/ffmpeg")
        if homebrew_arm.exists():
            logger.info(f"使用Homebrew (ARM) FFmpeg: {homebrew_arm}")
            return str(homebrew_arm)

        # Intel Mac
        homebrew_intel = Path("/usr/local/bin/ffmpeg")
        if homebrew_intel.exists():
            logger.info(f"使用Homebrew (Intel) FFmpeg: {homebrew_intel}")
            return str(homebrew_intel)

    # 3. 检查系统PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        logger.info(f"使用系统PATH中的FFmpeg: {system_ffmpeg}")
        return system_ffmpeg

    # 4. 都没找到，提供安装指导
    install_guide = _get_install_guide()
    error_msg = f"FFmpeg not found. {install_guide}"
    logger.error(error_msg)

    raise FFmpegNotFoundError(
        "FFmpeg not found. Please install FFmpeg to continue.",
        install_guide=install_guide
    )


def _get_install_guide() -> str:
    """获取FFmpeg安装指导"""
    system = platform.system()

    if system == "Darwin":  # macOS
        return (
            "Install using Homebrew:\n"
            "  brew install ffmpeg\n"
            "Or download from: https://ffmpeg.org/download.html"
        )
    elif system == "Linux":
        return (
            "Install using your package manager:\n"
            "  Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  CentOS/RHEL: sudo yum install ffmpeg\n"
            "  Fedora: sudo dnf install ffmpeg"
        )
    elif system == "Windows":
        return (
            "Download from: https://ffmpeg.org/download.html\n"
            "and add to your PATH environment variable"
        )
    else:
        return "Download from: https://ffmpeg.org/download.html"


def _ensure_executable(path: str | None = None, default: str = "ffmpeg") -> str:
    """
    确保FFmpeg可执行文件可用

    Args:
        path: 指定的FFmpeg路径
        default: 默认的可执行文件名

    Returns:
        str: FFmpeg可执行文件路径

    Raises:
        FFmpegNotFoundError: 如果找不到FFmpeg
    """
    if path:
        if Path(path).exists():
            return path
        else:
            raise FFmpegNotFoundError(f"指定的FFmpeg路径不存在: {path}")

    return get_ffmpeg_path()


def verify_ffmpeg_installation() -> dict:
    """验证FFmpeg安装和功能"""
    result = {
        "available": False,
        "version": None,
        "codecs": [],
        "error": None
    }

    try:
        ffmpeg_path = get_ffmpeg_path()

        # 获取版本信息
        version_result = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if version_result.returncode == 0:
            first_line = version_result.stdout.split('\n')[0]
            result["version"] = first_line
            result["available"] = True

            # 获取支持的编解码器
            codecs_result = subprocess.run(
                [ffmpeg_path, "-codecs"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if codecs_result.returncode == 0:
                # 提取常用编解码器
                important_codecs = ["h264", "h265", "aac", "mp3", "vp9"]
                for codec in important_codecs:
                    if codec.lower() in codecs_result.stdout.lower():
                        result["codecs"].append(codec)

        logger.info(f"FFmpeg验证成功: {result['version']}")

    except subprocess.TimeoutExpired:
        result["error"] = "FFmpeg命令超时"
        logger.error("FFmpeg验证超时")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"FFmpeg验证失败: {e}")

    return result

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
