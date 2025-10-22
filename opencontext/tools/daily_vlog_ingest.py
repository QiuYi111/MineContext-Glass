#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

"""
Batch ingest a day's vlog videos by sampling frames and feeding them into the
existing screenshot processing pipeline, then emit the daily summary report.

Usage (after copying the day's mp4 files into videos/DD-MM/):

    uv run python -m opencontext.tools.daily_vlog_ingest
"""

import argparse
import asyncio
import datetime as dt
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

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


def parse_day_folder(date_token: str, year_override: Optional[int]) -> dt.date:
    """Parse a date token that may be 'YYYY-MM-DD' or 'DD-MM'/'MM-DD'."""
    now = dt.datetime.now().astimezone()
    if not date_token:
        return now.date()

    try:
        return dt.date.fromisoformat(date_token)
    except ValueError:
        pass

    parts = [p for p in re.split(r'[-_/]', date_token) if p]
    if len(parts) != 2:
        raise ValueError(f"Unsupported date format '{date_token}'. Use YYYY-MM-DD or DD-MM.")

    first, second = map(int, parts)
    # Try to infer ordering (prefer DD-MM as user example suggests)
    day, month = first, second
    if day > 31 or month > 12:
        # swap if likely MM-DD
        day, month = month, day
    elif day <= 12 and month <= 12:
        # ambiguous, prefer DD-MM but allow override by year flag
        pass

    year = year_override or now.year
    return dt.date(year, month, day)


def build_folder_candidates(date_val: dt.date, original_token: Optional[str]) -> List[str]:
    """Return possible folder names to search for the videos."""
    candidates = []
    if original_token:
        candidates.append(original_token)
    candidates.extend([
        f"{date_val.day:02d}-{date_val.month:02d}",
        date_val.isoformat(),
    ])
    # Deduplicate while preserving order
    seen = set()
    ordered = []
    for item in candidates:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


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


def parse_video_start_time(stem: str, day_start: dt.datetime) -> Optional[dt.datetime]:
    """Parse video filename (e.g., '12-13.mp4' or '09_30-10_00') to derive start timestamp."""
    # First try compact forms: 1230, 12h30, 12:30, 12_30
    compact_match = re.match(r'(?P<hour>\d{1,2})(?:[:h_]?)(?P<minute>\d{2})?', stem)
    if compact_match:
        hour = int(compact_match.group("hour"))
        minute = compact_match.group("minute")
        minute_val = int(minute) if minute else 0
        if 0 <= hour < 24 and 0 <= minute_val < 60:
            return day_start.replace(hour=hour, minute=minute_val)

    # Fallback for range-like patterns: 12-13, 08-09-30, etc.
    tokens = [t for t in re.split(r'[^0-9]', stem) if t]
    if not tokens:
        return None

    first = tokens[0]
    if len(first) in (1, 2):
        hour = int(first)
        if hour < 24:
            return day_start.replace(hour=hour, minute=0)
    elif len(first) == 4:
        hour = int(first[:2])
        minute = int(first[2:])
        if hour < 24 and minute < 60:
            return day_start.replace(hour=hour, minute=minute)

    return None


def collect_frames(
    videos: List[Path],
    day_output_dir: Path,
    interval: int,
    video_start_times: Dict[Path, dt.datetime],
    reuse_existing: bool,
    day_start: dt.datetime,
    clean_existing: bool,
) -> List[FrameRecord]:
    """Extract (or reuse) frames for every video and collect metadata for ingestion."""
    records: List[FrameRecord] = []

    for video_path in videos:
        start_dt = video_start_times.get(video_path)
        if start_dt is None:
            LOG.warning(
                "Unable to parse start time from filename '%s'; fallback to sequential ordering.",
                video_path.name,
            )
            start_dt = day_start + dt.timedelta(seconds=len(records) * interval)

        video_output_dir = day_output_dir / video_path.stem

        if not reuse_existing:
            if clean_existing and video_output_dir.exists():
                shutil.rmtree(video_output_dir)

            LOG.info("Sampling frames from %s", video_path)
            run_ffmpeg_extract(video_path, video_output_dir, interval)
        else:
            if not video_output_dir.exists():
                LOG.warning("Frame directory %s is missing; switching to extraction.", video_output_dir)
                LOG.info("Sampling frames from %s", video_path)
                run_ffmpeg_extract(video_path, video_output_dir, interval)

        frames = sorted(video_output_dir.glob("frame_*.jpg"))
        if not frames:
            LOG.warning("No frames available for %s; skipping.", video_path)
            continue

        for idx, frame_path in enumerate(frames):
            frame_timestamp = start_dt + dt.timedelta(seconds=idx * interval)
            relative_seconds = max(0.0, (frame_timestamp - day_start).total_seconds())
            records.append(
                FrameRecord(
                    path=frame_path,
                    timestamp=frame_timestamp,
                    video_name=video_path.stem,
                    frame_index=idx,
                    relative_seconds=relative_seconds,
                )
            )

    # Sort records by timestamp to ensure chronological ingestion
    records.sort(key=lambda record: record.timestamp)
    return records


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

    project_root = resolve_project_root()
    os.environ.setdefault("CONTEXT_PATH", str(project_root))

    local_tz = dt.datetime.now().astimezone().tzinfo
    date_token = args.date
    try:
        date_val = parse_day_folder(date_token or "", args.year)
    except ValueError as exc:
        LOG.error(str(exc))
        return 1

    folder_candidates = build_folder_candidates(date_val, date_token)
    video_root = project_root / "videos"
    video_dir = None
    for candidate in folder_candidates:
        candidate_path = video_root / candidate
        if candidate_path.exists():
            video_dir = candidate_path
            break

    if video_dir is None:
        LOG.error(
            "Could not find videos for %s. Tried: %s",
            date_val.isoformat(),
            ", ".join(str(video_root / c) for c in folder_candidates),
        )
        return 1

    LOG.info("Using video directory: %s", video_dir)

    videos = sorted(video_dir.glob("*.mp4"))
    if not videos:
        LOG.error("No mp4 files found under %s", video_dir)
        return 1

    if args.skip_extract:
        LOG.info("Reusing existing frames under %s", args.output_dir)

    frame_root = Path(args.output_dir).expanduser().resolve()
    day_folder_name = video_dir.name
    day_output_dir = prepare_output_root(
        frame_root,
        day_folder_name,
        clean=(not args.no_clean and not args.skip_extract),
    )

    day_start = dt.datetime.combine(date_val, dt.time.min)
    if local_tz:
        day_start = day_start.replace(tzinfo=local_tz)

    video_start_times: Dict[Path, dt.datetime] = {}
    for video_path in videos:
        start_dt = parse_video_start_time(video_path.stem, day_start)
        if start_dt:
            video_start_times[video_path] = start_dt

    if not video_start_times:
        LOG.warning("Failed to infer start times from filenames; frames will be ordered sequentially.")

    records = collect_frames(
        videos=videos,
        day_output_dir=day_output_dir,
        interval=args.frame_interval,
        video_start_times=video_start_times,
        reuse_existing=args.skip_extract,
        day_start=day_start,
        clean_existing=not args.no_clean,
    )

    if not records:
        LOG.error("No frames available for ingestion. Aborting.")
        return 1

    global_config = GlobalConfig()
    global_config.initialize(args.config)
    context_lab = OpenContext()
    context_lab.initialize()

    ingest_frames(context_lab, records)
    wait_for_processing(context_lab, max_wait=args.max_wait)

    day_end = day_start + dt.timedelta(days=1)

    report_date_str = date_val.isoformat()
    LOG.info("Generating daily report for %s", report_date_str)
    report = asyncio.run(generate_daily_report(int(day_start.timestamp()), int(day_end.timestamp())))
    output_path = write_report(report, Path(args.report_dir).expanduser().resolve(), report_date_str)
    LOG.info("Daily report saved to %s", output_path)

    context_lab.shutdown(graceful=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
