#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

"""
Batch ingest a day's vlog videos by sampling frames and feeding them into the
existing screenshot processing pipeline, then emit the daily summary report.

Usage (after copying mp4 files into a folder):

    uv run python -m opencontext.tools.daily_vlog_ingest \
        --video-dir data/vlogs/2025-02-26 \
        --date 2025-02-26 \
        --start-time 2025-02-26T08:00:00+08:00
"""

import argparse
import asyncio
import datetime as dt
import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from opencontext.config.global_config import GlobalConfig
from opencontext.context_consumption.generation.generation_report import ReportGenerator
from opencontext.models.context import RawContextProperties
from opencontext.models.enums import ContentFormat, ContextSource
from opencontext.server.opencontext import OpenContext

LOG = logging.getLogger("daily_vlog_ingest")


@dataclass
class FrameRecord:
    """Lightweight metadata for each sampled frame."""
    path: Path
    timestamp: dt.datetime
    video_name: str
    frame_index: int
    relative_seconds: float


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract frames from vlog videos, ingest them, and generate the daily report."
    )
    parser.add_argument(
        "--video-dir",
        required=True,
        help="Directory that contains the mp4 files for the day.",
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Activity date (YYYY-MM-DD) used for organising outputs and report window.",
    )
    parser.add_argument(
        "--start-time",
        help="Optional ISO timestamp (local or with timezone) for the first frame. "
             "Defaults to the start of the provided date in the local timezone.",
    )
    parser.add_argument(
        "--frame-interval",
        type=int,
        default=5,
        help="Seconds between sampled frames (default: 5).",
    )
    parser.add_argument(
        "--output-dir",
        default="persist/vlog_frames",
        help="Destination root for extracted frames (default: persist/vlog_frames).",
    )
    parser.add_argument(
        "--report-dir",
        default="persist/reports",
        help=(
            "Directory to save the generated daily report markdown "
            "(default: persist/reports)."
        ),
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
        "--no-clean",
        action="store_true",
        help="Do not delete the existing frame directory for the day before extraction.",
    )
    parser.add_argument(
        "--max-wait",
        type=int,
        default=900,
        help="Maximum seconds to wait for screenshot processing to finish (default: 900).",
    )
    return parser.parse_args(argv)


def ensure_ffmpeg_available() -> None:
    """Validate that ffmpeg and ffprobe binaries are present."""
    missing = [binary for binary in ("ffmpeg", "ffprobe") if shutil.which(binary) is None]
    if missing:
        raise RuntimeError(
            f"Missing required binaries: {', '.join(missing)}. "
            "Install ffmpeg suite and ensure it is on PATH."
        )


def resolve_project_root() -> Path:
    """Project root is two levels up from this file."""
    return Path(__file__).resolve().parents[2]


def prepare_output_root(base_dir: Path, date_str: str, clean: bool) -> Path:
    """Create (and optionally clear) the folder that holds sampled frames for the day."""
    day_dir = base_dir / date_str
    if clean and day_dir.exists():
        LOG.info("Removing existing frame directory %s", day_dir)
        shutil.rmtree(day_dir)
    day_dir.mkdir(parents=True, exist_ok=True)
    return day_dir


def parse_date(date_str: str) -> dt.date:
    try:
        return dt.date.fromisoformat(date_str)
    except ValueError as exc:
        raise ValueError(f"Invalid date '{date_str}'; expected YYYY-MM-DD") from exc


def parse_start_datetime(date_val: dt.date, start_time: Optional[str]) -> dt.datetime:
    if start_time:
        try:
            parsed = dt.datetime.fromisoformat(start_time)
        except ValueError as exc:
            raise ValueError(f"Invalid --start-time '{start_time}': {exc}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
        return parsed

    local_tz = dt.datetime.now().astimezone().tzinfo
    return dt.datetime.combine(date_val, dt.time.min).replace(tzinfo=local_tz)


def run_ffmpeg_extract(video_path: Path, output_dir: Path, interval: int) -> None:
    """Invoke ffmpeg to sample frames for a single video."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pattern = output_dir / "frame_%06d.jpg"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video_path),
        "-vf",
        f"fps=1/{interval}",
        "-q:v",
        "2",
        str(pattern),
    ]
    LOG.debug("Running ffmpeg: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def probe_duration(video_path: Path) -> Optional[float]:
    """Return the video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=nokey=1:noprint_wrappers=1",
        str(video_path),
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        LOG.warning("Unable to determine duration for %s; falling back to frame count.", video_path)
        return None


def extract_frames_for_day(
    videos: List[Path],
    day_output_dir: Path,
    interval: int,
    clean_each_video: bool,
) -> List[FrameRecord]:
    """Extract frames for every video and collect metadata for ingestion."""
    records: List[FrameRecord] = []
    baseline = dt.datetime.now().astimezone()
    elapsed = 0.0

    for video_path in videos:
        video_output_dir = day_output_dir / video_path.stem
        if clean_each_video and video_output_dir.exists():
            shutil.rmtree(video_output_dir)

        LOG.info("Sampling frames from %s", video_path)
        run_ffmpeg_extract(video_path, video_output_dir, interval)

        frames = sorted(video_output_dir.glob("frame_*.jpg"))
        if not frames:
            LOG.warning("No frames extracted from %s; skipping.", video_path)
            continue

        duration = probe_duration(video_path)
        for idx, frame_path in enumerate(frames):
            relative_seconds = elapsed + idx * interval
            records.append(
                FrameRecord(
                    path=frame_path,
                    timestamp=baseline + dt.timedelta(seconds=relative_seconds),
                    video_name=video_path.stem,
                    frame_index=idx,
                    relative_seconds=relative_seconds,
                )
            )

        if duration:
            elapsed += duration
        else:
            elapsed += len(frames) * interval

    return records


def reuse_existing_frames(
    videos: List[Path],
    day_output_dir: Path,
    interval: int,
) -> List[FrameRecord]:
    """Collect metadata for already extracted frames without running ffmpeg."""
    records: List[FrameRecord] = []
    elapsed = 0.0
    baseline = dt.datetime.now().astimezone()

    for video_path in videos:
        video_output_dir = day_output_dir / video_path.stem
        frames = sorted(video_output_dir.glob("frame_*.jpg"))
        if not frames:
            LOG.warning("No frames found under %s; skipping.", video_output_dir)
            continue

        duration = probe_duration(video_path)
        for idx, frame_path in enumerate(frames):
            relative_seconds = elapsed + idx * interval
            records.append(
                FrameRecord(
                    path=frame_path,
                    timestamp=baseline + dt.timedelta(seconds=relative_seconds),
                    video_name=video_path.stem,
                    frame_index=idx,
                    relative_seconds=relative_seconds,
                )
            )

        if duration:
            elapsed += duration
        else:
            elapsed += len(frames) * interval

    return records


def remap_timestamps(records: List[FrameRecord], start_dt: dt.datetime) -> None:
    """Shift sampled frames so that the first frame aligns to start_dt."""
    if not records:
        return
    base_ts = records[0].relative_seconds
    for rec in records:
        offset = rec.relative_seconds - base_ts
        rec.timestamp = start_dt + dt.timedelta(seconds=offset)


def ingest_frames(context_lab: OpenContext, records: List[FrameRecord]) -> None:
    LOG.info("Ingesting %d frames into the screenshot pipeline.", len(records))
    for idx, rec in enumerate(records, start=1):
        raw = RawContextProperties(
            content_format=ContentFormat.IMAGE,
            source=ContextSource.SCREENSHOT,
            create_time=rec.timestamp,
            content_path=str(rec.path),
            additional_info={
                "origin": "daily_vlog_ingest",
                "video_name": rec.video_name,
                "frame_index": rec.frame_index,
                "relative_seconds": rec.relative_seconds,
            },
        )
        success = context_lab.add_context(raw)
        if not success:
            LOG.warning("Failed to enqueue frame %s", rec.path)
        if idx % 50 == 0:
            LOG.info("Queued %d/%d frames", idx, len(records))


def wait_for_processing(context_lab: OpenContext, max_wait: int) -> None:
    """Wait until the screenshot processor drains its queue or timeout."""
    processor = context_lab.processor_manager.get_processor("screenshot_processor")
    if processor is None:
        return

    poll_interval = 5
    waited = 0
    consecutive_idle = 0

    while waited < max_wait:
        queue_obj = getattr(processor, "_input_queue", None)
        processing_thread = getattr(processor, "_processing_task", None)
        remaining = queue_obj.qsize() if queue_obj is not None else 0

        if remaining == 0:
            consecutive_idle += 1
            if consecutive_idle >= 3:
                LOG.info("Screenshot processor queue is idle.")
                break
        else:
            consecutive_idle = 0

        if processing_thread and not processing_thread.is_alive():
            LOG.info("Screenshot processor background thread has exited.")
            break

        time.sleep(poll_interval)
        waited += poll_interval
    else:
        LOG.warning("Timed out after %s seconds waiting for screenshot processing.", max_wait)


async def generate_daily_report(start_ts: int, end_ts: int) -> str:
    generator = ReportGenerator()
    return await generator.generate_report(start_ts, end_ts)


def write_report(report: str, report_dir: Path, date_str: str) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    output_path = report_dir / f"{date_str}.md"
    output_path.write_text(report or "", encoding="utf-8")
    return output_path


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    ensure_ffmpeg_available()

    video_dir = Path(args.video_dir).expanduser().resolve()
    if not video_dir.exists():
        LOG.error("Video directory %s does not exist.", video_dir)
        return 1

    videos = sorted(video_dir.glob("*.mp4"))
    if not videos:
        LOG.error("No mp4 files found under %s", video_dir)
        return 1

    date_val = parse_date(args.date)
    start_dt = parse_start_datetime(date_val, args.start_time)

    project_root = resolve_project_root()
    os.environ.setdefault("CONTEXT_PATH", str(project_root))

    frame_root = Path(args.output_dir).expanduser().resolve()
    day_output_dir = prepare_output_root(frame_root, args.date, clean=not args.no_clean and not args.skip_extract)

    if args.skip_extract:
        records = reuse_existing_frames(videos, day_output_dir, args.frame_interval)
    else:
        records = extract_frames_for_day(
            videos,
            day_output_dir,
            args.frame_interval,
            clean_each_video=True,
        )

    if not records:
        LOG.error("No frames available for ingestion. Aborting.")
        return 1

    remap_timestamps(records, start_dt)

    global_config = GlobalConfig()
    global_config.initialize(args.config)
    context_lab = OpenContext()
    context_lab.initialize()

    ingest_frames(context_lab, records)
    wait_for_processing(context_lab, max_wait=args.max_wait)

    day_start = dt.datetime.combine(date_val, dt.time.min)
    if start_dt.tzinfo:
        day_start = day_start.replace(tzinfo=start_dt.tzinfo)
    day_end = day_start + dt.timedelta(days=1)

    LOG.info("Generating daily report for %s", args.date)
    report = asyncio.run(generate_daily_report(int(day_start.timestamp()), int(day_end.timestamp())))
    output_path = write_report(report, Path(args.report_dir).expanduser().resolve(), args.date)
    LOG.info("Daily report saved to %s", output_path)

    context_lab.shutdown(graceful=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
