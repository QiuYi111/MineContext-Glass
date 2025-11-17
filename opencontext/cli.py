# -*- coding: utf-8 -*-

# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0

"""
Command-line interface - provides the entry point for command-line tools
"""

import argparse
import asyncio
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles
import uvicorn

from glass.commands import GlassBatchRunner, TimelineRunResult, discover_date_videos
from glass.storage.context_repository import GlassContextRepository
from opencontext.models.context import ProcessedContext
from opencontext.server.opencontext import OpenContext
from opencontext.server.api import router as api_router
from opencontext.config.config_manager import ConfigManager
from opencontext.utils.logging_utils import setup_logging, get_logger
from glass.utils.chromadb_manager import preload_chromadb_model

logger = get_logger(__name__)

# Global variables for multi-process support
_config_path = None
_context_lab_instance = None
_capture_enabled = True

def get_or_create_context_lab():
    """Get or create the global OpenContext instance for the current process."""
    global _context_lab_instance, _config_path
    if _context_lab_instance is None:
        _context_lab_instance = _initialize_context_lab(_config_path)
        _context_lab_instance.initialize()
        # Check both global variable and environment variable (for multi-process mode)
        capture_enabled = _capture_enabled and os.getenv("OPENCAPTURE_NO_CAPTURE", "0") != "1"
        if capture_enabled:
            _context_lab_instance.start_capture()
    return _context_lab_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI."""
    # Startup
    if not hasattr(app.state, 'context_lab_instance'):
        app.state.context_lab_instance = get_or_create_context_lab()
    yield
    # Shutdown - cleanup if needed
    pass

app = FastAPI(title="OpenContext", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost",
        "https://www.figma.com",  # Figma web editor
        "https://figma.com",       # Figma desktop
        "file://",                # Figma desktop local files
    ],  # React dev server + Figma
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project root
if hasattr(sys, '_MEIPASS'):
    project_root = Path(sys._MEIPASS)
else:
    project_root = Path(__file__).parent.parent.parent.resolve()

def _get_project_root() -> Path:
    """Get the project root directory."""
    return project_root

def _setup_static_files() -> None:
    """Setup static file mounts for the FastAPI app."""
    # Mount static files
    if hasattr(sys, '_MEIPASS'):
        static_path = Path(sys._MEIPASS) / "opencontext/web/static"
    else:
        static_path = Path(__file__).parent / "web/static"
    
    print(f"Static path: {static_path}")
    print(f"Static path exists: {static_path.exists()}")
    print(f"Static path absolute: {static_path.resolve()}")
    
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        print(f"Mounted static files from: {static_path}")
    else:
        print(f"Static path does not exist: {static_path}")
    
    # Mount screenshots directory
    screenshots_path = Path("./screenshots").resolve()
    if screenshots_path.exists():
        app.mount("/screenshots", StaticFiles(directory=screenshots_path), name="screenshots")

_setup_static_files()

app.include_router(api_router)

def start_web_server(context_lab_instance: OpenContext, host: str, port: int, workers: int = 1, config_path: str = None) -> None:
    """Start the web server with the given opencontext instance.
    
    Args:
        context_lab_instance: The opencontext instance to attach to the app
        host: Host address to bind to
        port: Port number to bind to
        workers: Number of worker processes
        config_path: Configuration file path for multi-process mode
    """
    global _config_path
    _config_path = config_path
    
    if workers > 1:
        logger.info(f"Starting with {workers} worker processes")
        # For multi-process mode, use import string to avoid the warning
        uvicorn.run("opencontext.cli:app", host=host, port=port, log_level="info", workers=workers)
    else:
        # For single process mode, use the existing instance
        app.state.context_lab_instance = context_lab_instance
        uvicorn.run(app, host=host, port=port, log_level="info")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="OpenContext - Context capture, processing, storage and consumption system"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start OpenContext server")
    start_parser.add_argument(
        "--config",
        type=str,
        help="Configuration file path"
    )
    start_parser.add_argument(
        "--host",
        type=str,
        help="Host address (overrides config file)"
    )
    start_parser.add_argument(
        "--port",
        type=int,
        help="Port number (overrides config file)"
    )
    start_parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    start_parser.add_argument(
        "--no-capture",
        action="store_true",
        help="Disable context capture (start server without screenshot/file monitoring)"
    )

    # Glass utilities
    glass_parser = subparsers.add_parser("glass", help="Glass timeline utilities")
    glass_parser.add_argument(
        "--config",
        type=str,
        help="Configuration file path"
    )
    glass_subparsers = glass_parser.add_subparsers(dest="glass_command", help="Glass commands")

    glass_report_parser = glass_subparsers.add_parser(
        "report",
        help="Generate an activity report focused on a Glass timeline"
    )
    glass_report_parser.add_argument(
        "--timeline-id",
        required=True,
        help="Timeline identifier produced during Glass ingestion"
    )
    glass_report_parser.add_argument(
        "--start",
        type=str,
        help="Report start time (ISO8601 string or Unix timestamp seconds)"
    )
    glass_report_parser.add_argument(
        "--end",
        type=str,
        help="Report end time (ISO8601 string or Unix timestamp seconds)"
    )
    glass_report_parser.add_argument(
        "--lookback-minutes",
        type=int,
        default=60,
        help="Fallback lookback window in minutes when start/end are omitted (default: 60)"
    )
    glass_report_parser.add_argument(
        "--output",
        type=str,
        help="Optional path to write the generated report"
    )

    glass_start_parser = glass_subparsers.add_parser(
        "start",
        help="Ingest videos from disk, process timelines, and generate reports",
    )
    glass_start_parser.add_argument(
        "--date",
        required=True,
        help="Date folder under videos/ in format dd-mm (e.g., 22-10)",
    )
    glass_start_parser.add_argument(
        "--config",
        type=str,
        help="Optional configuration path overriding global defaults",
    )
    glass_start_parser.add_argument(
        "--report-output",
        type=str,
        help="Optional directory to write generated reports (defaults to timeline folders)",
    )
    glass_start_parser.add_argument(
        "--frame-rate",
        type=float,
        default=1.0,
        help="Frame sampling rate used during ingestion (default: 1.0 fps)",
    )
    glass_start_parser.add_argument(
        "--lookback-minutes",
        type=int,
        default=120,
        help="Report lookback window in minutes (default: 120)",
    )
    glass_start_parser.add_argument(
        "--timeline-prefix",
        type=str,
        help="Optional prefix applied to generated timeline IDs",
    )
    glass_start_parser.add_argument(
        "--videos-root",
        type=str,
        help="Override the base videos directory (defaults to ./videos)",
    )

    return parser.parse_args()


def _initialize_context_lab(config_path: Optional[str]) -> OpenContext:
    """Initialize the OpenContext instance.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Initialized OpenContext instance

    Raises:
        RuntimeError: If initialization fails
    """
    try:
        # 启动ChromaDB模型预下载
        logger.info("启动ChromaDB模型预下载...")
        def on_preload_complete(success: bool):
            if success:
                logger.info("✅ ChromaDB模型预下载完成")
            else:
                logger.warning("⚠️ ChromaDB模型预下载失败，将在首次使用时下载")

        preload_chromadb_model(callback=on_preload_complete)

        lab_instance = OpenContext(config_path=config_path)
        lab_instance.initialize()
        return lab_instance
    except Exception as e:
        logger.error(f"Failed to initialize OpenContext: {e}")
        raise RuntimeError(f"OpenContext initialization failed: {e}") from e

def _run_headless_mode(lab_instance: OpenContext) -> None:
    """Run in headless mode without web server.
    
    Args:
        lab_instance: The opencontext instance
    """
    try:
        logger.info("Running in headless mode. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        lab_instance.shutdown()

def handle_start(args: argparse.Namespace) -> int:
    """Handle the start command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    global _capture_enabled

    # Set global capture flag based on command line argument
    _capture_enabled = not getattr(args, 'no_capture', False)

    # Set environment variable for multi-process mode
    if getattr(args, 'no_capture', False):
        os.environ["OPENCAPTURE_NO_CAPTURE"] = "1"

    try:
        lab_instance = _initialize_context_lab(args.config)
    except RuntimeError:
        return 1

    logger.info("Starting all modules")
    if _capture_enabled:
        lab_instance.start_capture()
    else:
        logger.info("Context capture disabled (use --no-capture flag to disable screenshot/file monitoring)")

    from opencontext.config.global_config import get_config
    web_config = get_config("web")
    if web_config.get("enabled", True):
        # Command line arguments override config file
        host = args.host if args.host else web_config.get("host", "localhost")
        port = args.port if args.port else web_config.get("port", 8000)

        try:
            logger.info(f"Starting web server on {host}:{port}")
            workers = getattr(args, 'workers', 1)
            start_web_server(lab_instance, host, port, workers, args.config)
        finally:
            logger.info("Web server closed, shutting down capture modules...")
            lab_instance.shutdown()
    else:
        _run_headless_mode(lab_instance)

    return 0


def _parse_time_argument(value: Optional[str]) -> Optional[int]:
    """Parse timestamp arguments accepting Unix seconds or ISO8601 strings."""
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        pass

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid time format '{value}'. Use ISO8601 or Unix timestamp.") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def _resolve_report_window(args: argparse.Namespace) -> tuple[int, int]:
    """Resolve start/end timestamps for Glass report generation."""
    start_ts = _parse_time_argument(getattr(args, "start", None))
    end_ts = _parse_time_argument(getattr(args, "end", None))

    if start_ts is None or end_ts is None:
        now_ts = int(datetime.now(tz=timezone.utc).timestamp())
        end_ts = end_ts or now_ts
        lookback_minutes = max(getattr(args, "lookback_minutes", 60), 1)
        start_ts = start_ts or end_ts - lookback_minutes * 60

    if end_ts <= start_ts:
        raise ValueError("End time must be greater than start time.")

    return start_ts, end_ts


def _ensure_storage_initialized() -> None:
    """Ensure storage layers are initialised for CLI commands."""
    from opencontext.storage.global_storage import get_global_storage

    storage_manager = get_global_storage()
    if not storage_manager.is_initialized():
        storage = storage_manager.get_storage()
        if storage is None:
            raise RuntimeError("Storage is not initialized; check configuration.")


def _handle_glass_report(args: argparse.Namespace) -> int:
    """Handle `opencontext glass report` command."""
    from glass.consumption import GlassContextSource
    from opencontext.context_consumption.generation.generation_report import ReportGenerator

    try:
        _ensure_storage_initialized()
        start_ts, end_ts = _resolve_report_window(args)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to prepare Glass report parameters: %s", exc)
        return 1

    generator = ReportGenerator(glass_source=GlassContextSource())
    try:
        report = asyncio.run(
            generator.generate_report(
                start_ts,
                end_ts,
                timeline_id=args.timeline_id,
            )
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to generate Glass report: %s", exc)
        return 1

    output_path = getattr(args, "output", None)
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report or "", encoding="utf-8")
        logger.info("Report written to %s", path)
    else:
        if report:
            print(report)
        else:
            logger.info("Report generation returned empty content.")

    return 0


def _handle_glass_start(args: argparse.Namespace) -> int:
    """Handle `opencontext glass start` command."""
    try:
        _ensure_storage_initialized()
    except Exception as exc:  # noqa: BLE001
        logger.error("Storage initialisation failed: %s", exc)
        return 1

    repo_root = Path.cwd()
    videos_root = (
        Path(args.videos_root).expanduser().resolve()
        if getattr(args, "videos_root", None)
        else repo_root / "videos"
    )
    date_token = args.date
    date_dir = (videos_root / date_token).resolve()

    try:
        video_paths = discover_date_videos(date_dir)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to discover videos under %s: %s", date_dir, exc)
        return 1

    report_dir = (
        Path(args.report_output).expanduser().resolve()
        if getattr(args, "report_output", None)
        else (repo_root / "persist" / "reports" / date_token)
    )

    try:
        runner = GlassBatchRunner(
            frame_rate=args.frame_rate,
        )
        results = runner.run(
            date_token=date_token,
            video_paths=video_paths,
            timeline_prefix=args.timeline_prefix,
            report_dir=report_dir,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Glass start workflow failed: %s", exc)
        return 1

    if not results:
        logger.warning("No video files processed for %s", date_token)
        return 0

    try:
        context_strings, start_ts, end_ts = _collect_daily_contexts(
            results,
            runner.repository,
            lookback_minutes=getattr(args, "lookback_minutes", None),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to gather contexts for daily report: %s", exc)
        context_strings = []
        now_ts = int(datetime.now(timezone.utc).timestamp())
        start_ts = end_ts = now_ts

    daily_report = ""
    if context_strings:
        try:
            daily_report = _generate_daily_report_content(
                context_strings,
                start_ts=start_ts,
                end_ts=end_ts,
                repository=runner.repository,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to generate aggregated daily report: %s", exc)
    else:
        logger.warning("No processed contexts available to compose daily report for %s", date_token)

    try:
        aggregate_path = _write_daily_report(
            report_content=daily_report,
            report_dir=report_dir,
            date_token=date_token,
            results=results,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to write daily report: %s", exc)
        aggregate_path = None

    for result in results:
        logger.info(
            "Timeline %s processed (%s contexts) from %s",
            result.timeline_id,
            result.processed_contexts,
            result.video_path,
        )

    if aggregate_path:
        logger.info("Daily report saved to %s", aggregate_path)
    return 0


def _collect_daily_contexts(
    results: Sequence[TimelineRunResult],
    repository: GlassContextRepository,
    lookback_minutes: Optional[int] = None,
) -> tuple[list[str], int, int]:
    """Collect context strings and their time bounds for all processed timelines."""
    from glass.consumption import GlassContextSource

    source = GlassContextSource(repository=repository)
    context_strings: list[str] = []
    timestamps: list[int] = []
    cutoff_ts: Optional[int] = None
    if lookback_minutes and lookback_minutes > 0:
        cutoff_ts = int(datetime.now(timezone.utc).timestamp()) - lookback_minutes * 60

    for result in results:
        contexts = source.get_processed_contexts(result.timeline_id)
        for context in contexts:
            timestamp = _context_timestamp(context)
            if cutoff_ts is not None and timestamp is not None and timestamp < cutoff_ts:
                continue
            if timestamp is not None:
                timestamps.append(timestamp)
            try:
                context_strings.append(context.get_llm_context_string())
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "Failed to serialise context %s for timeline %s: %s",
                    getattr(context, "id", "unknown"),
                    result.timeline_id,
                    exc,
                )

    now_ts = int(datetime.now(timezone.utc).timestamp())
    start_ts = min(timestamps) if timestamps else now_ts
    end_ts = max(timestamps) if timestamps else now_ts
    return context_strings, start_ts, end_ts


def _context_timestamp(context: ProcessedContext) -> Optional[int]:
    """Extract a UTC timestamp from a ProcessedContext."""
    try:
        create_time = context.properties.create_time
        if not create_time:
            return None
        if create_time.tzinfo is None:
            create_time = create_time.replace(tzinfo=timezone.utc)
        else:
            create_time = create_time.astimezone(timezone.utc)
        return int(create_time.timestamp())
    except Exception:  # noqa: BLE001
        return None


def _generate_daily_report_content(
    context_strings: Sequence[str],
    *,
    start_ts: int,
    end_ts: int,
    repository: GlassContextRepository,
) -> str:
    """Generate a single daily report with all collected contexts."""
    from glass.consumption import GlassContextSource
    from opencontext.context_consumption.generation.generation_report import ReportGenerator

    if not context_strings:
        return ""

    generator = ReportGenerator(glass_source=GlassContextSource(repository=repository))
    return asyncio.run(
        generator.generate_report_from_contexts(
            list(context_strings),
            start_ts,
            end_ts,
        )
    )


def _write_daily_report(
    results: Sequence[TimelineRunResult],
    report_dir: Path,
    date_token: str,
    *,
    report_content: str,
) -> Path:
    """Persist the aggregated daily report to disk."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    lines = [
        f"# Glass Daily Report - {date_token}",
        "",
        f"_Generated at {timestamp}_",
        "",
    ]

    if report_content:
        lines.append(report_content.strip())
        lines.append("")
    else:
        lines.append("_No report content produced for this date._")
        lines.append("")

    lines.append("## Processed Timelines")
    for result in results:
        lines.append(f"- `{result.timeline_id}` from `{result.video_path.name}` ({result.processed_contexts} contexts)")
    lines.append("")

    report_dir.mkdir(parents=True, exist_ok=True)
    aggregate_path = report_dir / f"{date_token}-daily.md"
    aggregate_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return aggregate_path


def handle_glass(args: argparse.Namespace) -> int:
    """Dispatch Glass sub-commands."""
    if not getattr(args, "glass_command", None):
        logger.error("No Glass sub-command specified. Use 'opencontext glass --help' for details.")
        return 1

    if args.glass_command == "report":
        return _handle_glass_report(args)
    if args.glass_command == "start":
        return _handle_glass_start(args)

    logger.error("Unknown Glass sub-command: %s", args.glass_command)
    return 1


def _setup_logging(config_path: Optional[str]) -> None:
    """Setup logging configuration.
    
    Args:
        config_path: Optional path to configuration file
    """
    from opencontext.config.global_config import GlobalConfig
    GlobalConfig.get_instance().initialize(config_path)

    setup_logging(GlobalConfig.get_instance().get_config('logging'))

def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_args()

    # Setup logging first
    _setup_logging(getattr(args, 'config', None))

    logger.debug(f"Command line arguments: {args}")

    if not args.command:
        logger.error("No command specified. Use 'opencontext start' or 'opencontext --help' for usage.")
        return 1

    if args.command == "start":
        return handle_start(args)
    if args.command == "glass":
        return handle_glass(args)

    logger.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
