#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

"""
End-to-end vlog pipeline that combines frame ingestion, WhisperX transcription,
and daily report generation.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import os
import time
from pathlib import Path
from typing import Iterable, List, Optional

from opencontext.config.global_config import GlobalConfig
from opencontext.server.opencontext import OpenContext
from opencontext.utils.logging_utils import get_logger, setup_logging

logger = get_logger(__name__)

logger.info("Loaded context tool module.")
from opencontext.tools import daily_vlog_ingest as vlog_ingest
logger.info("Loaded vlog ingest module.")
from opencontext.tools import whisperx_transcribe as whisper_tool
logger.info("Loaded whisperx tool module.")

def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the full MineContext vlog pipeline: extract video frames, "
            "transcribe audio with WhisperX, and generate the daily report."
        )
    )
    parser.add_argument(
        "--date",
        help="Activity date. Accepts YYYY-MM-DD or DD-MM. Defaults to today.",
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Override year if using DD-MM folder naming (defaults to current year).",
    )
    parser.add_argument(
        "--frame-interval",
        type=int,
        default=5,
        help="Seconds between sampled frames (default: 5).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("persist/vlog_frames"),
        help="Destination root for extracted frames (default: persist/vlog_frames).",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("persist/reports"),
        help="Directory to save the generated daily report (default: persist/reports).",
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to the OpenContext configuration file (default: config/config.yaml).",
    )
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="Skip frame extraction and reuse existing images under output-dir/date.",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip frame ingestion and reuse contexts already stored in the database.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not delete the existing frame directory for the day before extraction.",
    )
    parser.add_argument(
        "--max-wait",
        type=int,
        default=900,
        help="Maximum seconds to wait for processors to drain their queues (default: 900).",
    )

    # WhisperX options
    parser.add_argument(
        "--no-transcribe",
        dest="transcribe",
        action="store_false",
        help="Disable WhisperX transcription step.",
    )
    parser.set_defaults(transcribe=True)
    parser.add_argument(
        "--whisper-model",
        default="large-v2",
        help="WhisperX ASR model name (default: large-v2).",
    )
    parser.add_argument(
        "--cpu-only",
        action="store_true",
        help="Force WhisperX to run on CPU and use int8 compute type when unspecified.",
    )
    parser.add_argument(
        "--device",
        default=whisper_tool.default_device(),
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
        help="Batch size for WhisperX transcription (default: 16).",
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
        "--save-transcripts",
        action="store_true",
        help="Save transcript JSON files in addition to ingestion.",
    )
    parser.add_argument(
        "--transcript-dir",
        type=Path,
        default=Path("persist/transcripts"),
        help="Directory to store transcript JSON (default: persist/transcripts).",
    )
    parser.add_argument(
        "--no-transcript-ingest",
        action="store_true",
        help="Do not enqueue transcripts into OpenContext (only save files when enabled).",
    )

    return parser.parse_args(argv)


def wait_for_processor(context_lab: OpenContext, processor_name: str, max_wait: int) -> None:
    """Wait until the specified processor drains its queue or timeout."""
    processor = context_lab.processor_manager.get_processor(processor_name)
    if processor is None:
        logger.debug(f"Processor {processor_name} not registered; skipping wait.")
        return

    poll_interval = 5
    waited = 0
    consecutive_idle = 0
    last_reported_size: Optional[int] = None

    while waited < max_wait:
        queue_obj = getattr(processor, "_input_queue", None)
        processing_thread = getattr(processor, "_processing_task", None)
        remaining = queue_obj.qsize() if queue_obj is not None else 0

        if remaining != last_reported_size:
            plural_suffix = "s" if remaining != 1 else ""
            logger.info(f"{processor_name} queue backlog: {remaining} item{plural_suffix} remaining")
            last_reported_size = remaining

        if remaining == 0:
            consecutive_idle += 1
            if consecutive_idle >= 3:
                logger.info(f"{processor_name} queue is idle.")
                break
        else:
            consecutive_idle = 0

        if processing_thread and not processing_thread.is_alive():
            logger.info(f"{processor_name} background thread has exited.")
            break

        time.sleep(poll_interval)
        waited += poll_interval
    else:
        logger.warning(f"Timed out after {max_wait} seconds waiting for {processor_name}.")


def resolve_videos_for_date(date_val: dt.date, original_token: Optional[str]) -> Optional[Path]:
    """Locate the directory that holds videos for the given day."""
    folder_candidates = vlog_ingest.build_folder_candidates(date_val, original_token)
    video_root = vlog_ingest.resolve_project_root() / "videos"
    for candidate in folder_candidates:
        candidate_path = video_root / candidate
        if candidate_path.exists():
            return candidate_path
    tried_paths = ", ".join(str(video_root / c) for c in folder_candidates)
    logger.error(f"Could not find videos for {date_val.isoformat()}. Tried: {tried_paths}")
    return None


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)

    project_root = vlog_ingest.resolve_project_root()
    os.environ.setdefault("CONTEXT_PATH", str(project_root))

    global_config = GlobalConfig.get_instance()
    global_config.initialize(args.config)
    setup_logging(global_config.get_config("logging") or {})
    logger.info("Initialized logging for vlog pipeline.")

    try:
        vlog_ingest.ensure_ffmpeg()
    except RuntimeError as exc:
        logger.error(str(exc))
        return 1

    if args.transcribe:
        if whisper_tool.whisperx is None:
            logger.error("WhisperX is not installed. Run `uv add whisperx` or re-run with --no-transcribe.")
            return 1
        # WhisperX also requires ffmpeg; reuse the same check to provide clearer errors.
        try:
            whisper_tool.ensure_ffmpeg()
            logger.debug("WhisperX dependencies are satisfied.")
        except RuntimeError as exc:
            logger.error(str(exc))
            return 1

    local_tz = dt.datetime.now().astimezone().tzinfo
    date_token = args.date or ""
    try:
        date_val = vlog_ingest.parse_day_folder(date_token, args.year)
    except ValueError as exc:
        logger.error(str(exc))
        return 1

    video_dir = resolve_videos_for_date(date_val, date_token if date_token else None)
    if video_dir is None:
        return 1

    videos = sorted(
        path
        for path in video_dir.iterdir()
        if path.is_file() and path.suffix.lower() in vlog_ingest.SUPPORTED_VIDEO_EXTENSIONS
    )
    logger.info(f"Found {len(videos)} video files under {video_dir}")
    if not videos:
        extensions = ", ".join(vlog_ingest.SUPPORTED_VIDEO_EXTENSIONS)
        logger.error(f"No supported video files found under {video_dir} (extensions: {extensions})")
        return 1

    day_start = dt.datetime.combine(date_val, dt.time.min)
    if local_tz:
        day_start = day_start.replace(tzinfo=local_tz)

    video_start_times: dict[Path, dt.datetime] = {}
    for video_path in videos:
        start_dt = vlog_ingest.parse_video_start_time(video_path.stem, day_start)
        if start_dt:
            video_start_times[video_path] = start_dt

    GlobalConfig().initialize(args.config)
    context_lab = OpenContext()
    context_lab.initialize()

    if not video_start_times:
        logger.warning("Failed to infer start times from filenames; frames will be ordered sequentially.")

    device = "cpu" if args.cpu_only else args.device
    if args.cpu_only and args.device != "cpu":
        logger.info("Overriding device to CPU due to --cpu-only flag.")
    compute_type = args.compute_type or whisper_tool.default_compute_type(device)
    transcript_outputs: List[Path] = []
    exit_code = 0

    try:
        if args.transcribe:
            for media_path in videos:
                try:
                    payload = whisper_tool.transcribe_media(
                        media_path=media_path,
                        model_name=args.whisper_model,
                        device=device,
                        compute_type=compute_type,
                        batch_size=args.batch_size,
                        align=args.align,
                        diarize=args.diarize,
                        hf_token=args.hf_token,
                    )
                except Exception as exc:  # pragma: no cover - runtime errors
                    logger.exception(f"Transcription failed for {media_path}: {exc}")
                    exit_code = 1
                    continue

                if args.save_transcripts:
                    output_path = whisper_tool.save_transcript(
                        args.transcript_dir.expanduser().resolve(),
                        media_path,
                        payload,
                    )
                    transcript_outputs.append(output_path)
                    logger.info(f"Transcript saved to {output_path}")

                if not args.no_transcript_ingest:
                    whisper_tool.ingest_transcript(context_lab, media_path, payload)

            wait_for_processor(context_lab, "document_processor", args.max_wait)
        else:
            logger.info("Skipping transcription step.")

        if args.skip_ingest:
            logger.info("Skipping frame ingestion; assuming frames already ingested.")
        else:
            frame_root = args.output_dir.expanduser().resolve()
            day_folder_name = video_dir.name
            day_output_dir = vlog_ingest.prepare_output_root(
                frame_root,
                day_folder_name,
                clean=(not args.no_clean and not args.skip_extract),
            )

            logger.info(f"Starting frame extraction for {date_val.isoformat()}")
            records = vlog_ingest.collect_frames(
                videos=videos,
                day_output_dir=day_output_dir,
                interval=args.frame_interval,
                video_start_times=video_start_times,
                reuse_existing=args.skip_extract,
                day_start=day_start,
                clean_existing=not args.no_clean,
            )

            if not records:
                logger.error("No frames available for ingestion. Aborting.")
                return 1

            vlog_ingest.ingest_frames(context_lab, records)
            wait_for_processor(context_lab, "screenshot_processor", args.max_wait)

        day_end = day_start + dt.timedelta(days=1)
        report_date_str = date_val.isoformat()
        logger.info(f"Generating daily report for {report_date_str}")
        report = asyncio.run(
            vlog_ingest.generate_daily_report(
                int(day_start.timestamp()),
                int(day_end.timestamp()),
            )
        )
        output_path = vlog_ingest.write_report(
            report,
            args.report_dir.expanduser().resolve(),
            report_date_str,
        )
        logger.info(f"Daily report saved to {output_path}")

        if transcript_outputs:
            logger.info(f"Saved {len(transcript_outputs)} transcript files under {args.transcript_dir}")
    finally:
        context_lab.shutdown(graceful=True)

    return exit_code


if __name__ == "__main__":
    main()
