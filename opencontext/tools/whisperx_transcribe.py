#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

"""
Transcribe video/audio files with WhisperX and ingest transcripts into OpenContext.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING

try:
    import torch
except ImportError:
    torch = None  # type: ignore[assignment]

try:  # pragma: no cover - runtime import
    import whisperx  # type: ignore[assignment]
    from whisperx.diarize import DiarizationPipeline  # type: ignore[assignment]
except ImportError:  # pragma: no cover - handled at runtime
    whisperx = None  # type: ignore[assignment]
    DiarizationPipeline = None  # type: ignore[assignment]

if TYPE_CHECKING:  # pragma: no cover - typing helpers
    import whisperx as whisperx_module  # noqa: F401
    from whisperx.diarize import DiarizationPipeline as DiarizationPipelineType  # noqa: F401

from opencontext.config.global_config import GlobalConfig
from opencontext.models.context import RawContextProperties
from opencontext.models.enums import ContentFormat, ContextSource
from opencontext.server.opencontext import OpenContext
from opencontext.utils.logging_utils import get_logger

logger = get_logger(__name__)

DEFAULT_TRANSCRIPT_DIR = Path("persist/transcripts")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe video/audio files with WhisperX and enqueue transcripts for OpenContext."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Video/audio files or directories containing media to transcribe.",
    )
    parser.add_argument(
        "--model",
        default="large-v2",
        help="WhisperX ASR model name (default: large-v2).",
    )
    parser.add_argument(
        "--device",
        default=default_device(),
        help="Device to run WhisperX on (default: auto-detected).",
    )
    parser.add_argument(
        "--compute-type",
        default=None,
        help="Compute type for WhisperX (default: float16 on CUDA, int8 on CPU).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for transcription (default: 16).",
    )
    parser.add_argument(
        "--no-align",
        dest="align",
        action="store_false",
        help="Disable alignment and keep original Whisper timestamps.",
    )
    parser.set_defaults(align=True)
    parser.add_argument(
        "--diarize",
        action="store_true",
        help="Enable speaker diarization (requires HuggingFace token).",
    )
    parser.add_argument(
        "--hf-token",
        help="HuggingFace token required for diarization models.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_TRANSCRIPT_DIR,
        help="Directory to store JSON transcripts (default: persist/transcripts).",
    )
    parser.add_argument(
        "--save-output",
        action="store_true",
        help="Write transcript JSON files in addition to ingestion.",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip sending transcripts into OpenContext (only save files).",
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to OpenContext configuration file (default: config/config.yaml).",
    )
    return parser.parse_args(argv)


def default_device() -> str:
    if torch and torch.cuda.is_available():
        return "cuda"
    return "cpu"


def default_compute_type(device: str) -> str:
    if device.startswith("cuda"):
        return "float16"
    return "int8"


def find_media_files(inputs: Iterable[str]) -> List[Path]:
    supported_suffixes = {".mp4", ".m4v", ".mov", ".avi", ".mkv", ".wav", ".mp3", ".flac"}
    results: List[Path] = []
    for item in inputs:
        path = Path(item).expanduser().resolve()
        if path.is_file():
            if path.suffix.lower() in supported_suffixes:
                results.append(path)
            else:
                logger.warning("Skipping unsupported file %s", path)
        elif path.is_dir():
            for candidate in sorted(path.rglob("*")):
                if candidate.is_file() and candidate.suffix.lower() in supported_suffixes:
                    results.append(candidate)
        else:
            logger.warning("Path not found: %s", path)
    return results


def ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required by WhisperX but was not found on PATH.")


def format_timestamp(seconds: Optional[float]) -> str:
    if seconds is None:
        return "--:--:--.---"
    millis = int(round(seconds * 1000))
    remainder = millis % 1000
    total_seconds = millis // 1000
    sec = total_seconds % 60
    minutes = (total_seconds // 60) % 60
    hours = total_seconds // 3600
    return f"{hours:02d}:{minutes:02d}:{sec:02d}.{remainder:03d}"


def build_transcript_text(segments: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = format_timestamp(seg.get("start"))
        end = format_timestamp(seg.get("end"))
        speaker = seg.get("speaker")
        if speaker:
            lines.append(f"[{start} - {end}] {speaker}: {text}")
        else:
            lines.append(f"[{start} - {end}] {text}")
    return "\n".join(lines)


def transcribe_media(
    media_path: Path,
    model_name: str,
    device: str,
    compute_type: str,
    batch_size: int,
    align: bool,
    diarize: bool,
    hf_token: Optional[str],
) -> Dict[str, Any]:
    if whisperx is None:
        raise RuntimeError("WhisperX is not installed.")

    logger.info("Transcribing %s", media_path)
    audio = whisperx.load_audio(str(media_path))

    model = whisperx.load_model(model_name, device=device, compute_type=compute_type)
    try:
        result = model.transcribe(audio, batch_size=batch_size,language="zh")
    finally:
        del model
        gc.collect()

    language = result.get("language")
    segments = result.get("segments", [])
    alignment_model = None

    if align and language:
        logger.info("Running alignment for %s (language=%s)", media_path.name, language)
        model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
        try:
            result = whisperx.align(
                segments,
                model_a,
                metadata,
                audio,
                device,
                return_char_alignments=False,
            )
        finally:
            del model_a
            gc.collect()

        segments = result.get("segments", segments)
        alignment_model = metadata.get("model_name") if isinstance(metadata, dict) else None

    diarization_segments: Optional[List[Dict[str, Any]]] = None
    if diarize:
        if not hf_token:
            logger.warning("Diarization requested but --hf-token not provided; skipping diarization.")
        elif DiarizationPipeline is None:
            logger.error("DiarizationPipeline unavailable because WhisperX dependencies are missing.")
        else:
            logger.info("Running speaker diarization for %s", media_path.name)
            diarize_model = DiarizationPipeline(use_auth_token=hf_token, device=device)
            try:
                raw_diarization = diarize_model(audio)
                diarization_segments = [
                    {
                        "speaker": speaker,
                        "start": float(segment.start),
                        "end": float(segment.end),
                    }
                    for segment, _, speaker in raw_diarization.itertracks(yield_label=True)
                ]
                result = whisperx.assign_word_speakers(raw_diarization, {"segments": segments})
            finally:
                del diarize_model
                gc.collect()
            segments = result.get("segments", segments)

    transcript_text = build_transcript_text(segments)
    logger.info("Transcription complete for %s (%d segments)", media_path.name, len(segments))

    return {
        "language": language,
        "segments": segments,
        "text": transcript_text,
        "alignment_model": alignment_model,
        "diarization_segments": diarization_segments,
    }


def save_transcript(output_dir: Path, media_path: Path, payload: Dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{media_path.stem}.json"
    serializable = {
        "video_path": str(media_path),
        "language": payload.get("language"),
        "text": payload.get("text"),
        "segments": payload.get("segments"),
        "alignment_model": payload.get("alignment_model"),
    }
    if payload.get("diarization_segments") is not None:
        serializable["diarization_segments"] = payload["diarization_segments"]
    output_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def ingest_transcript(
    context_lab: OpenContext,
    media_path: Path,
    payload: Dict[str, Any],
) -> bool:
    try:
        stat = media_path.stat()
        create_dt = dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc)
    except FileNotFoundError:
        create_dt = dt.datetime.now(dt.timezone.utc)

    raw = RawContextProperties(
        content_format=ContentFormat.TEXT,
        source=ContextSource.TEXT,
        create_time=create_dt,
        content_text=payload.get("text") or "",
        additional_info={
            "origin": "whisperx_transcribe",
            "video_path": str(media_path),
            "language": payload.get("language"),
            "alignment_model": payload.get("alignment_model"),
            "has_diarization": payload.get("diarization_segments") is not None,
            "segments": payload.get("segments"),
            "diarization_segments": payload.get("diarization_segments"),
        },
    )
    success = context_lab.add_context(raw)
    if not success:
        logger.error("Failed to enqueue transcript for %s", media_path)
    else:
        logger.info("Transcript enqueued for %s", media_path)
    return success


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)

    if whisperx is None:
        logger.error("WhisperX is not installed. Run `uv add whisperx` (or pip install whisperx) first.")
        return 1

    ensure_ffmpeg()
    media_files = find_media_files(args.inputs)
    if not media_files:
        logger.error("No supported media files found.")
        return 1

    compute_type = args.compute_type or default_compute_type(args.device)

    project_root = Path(__file__).resolve().parents[2]
    os.environ.setdefault("CONTEXT_PATH", str(project_root))

    context_lab: Optional[OpenContext] = None
    if not args.skip_ingest:
        GlobalConfig().initialize(args.config)
        context_lab = OpenContext()
        context_lab.initialize()

    exit_code = 0

    try:
        for media_path in media_files:
            try:
                payload = transcribe_media(
                    media_path=media_path,
                    model_name=args.model,
                    device=args.device,
                    compute_type=compute_type,
                    batch_size=args.batch_size,
                    align=args.align,
                    diarize=args.diarize,
                    hf_token=args.hf_token,
                )
            except Exception as exc:  # pragma: no cover - runtime errors
                logger.exception("Transcription failed for %s: %s", media_path, exc)
                exit_code = 1
                continue

            if args.save_output:
                output_path = save_transcript(args.output_dir, media_path, payload)
                logger.info("Transcript saved to %s", output_path)

            if context_lab and not ingest_transcript(context_lab, media_path, payload):
                exit_code = 1
    finally:
        if context_lab:
            context_lab.shutdown(graceful=True)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
