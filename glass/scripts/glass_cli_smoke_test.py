from __future__ import annotations

"""
Full pipeline regression test for the Glass timeline processor.

This script runs the entire ingestion + processing + report workflow against
all tracked videos found under `videos/<dd-mm>/`. Unlike the original smoke test it
relies on the real ffmpeg tooling, the Glass storage path, and the Doubao AUC
Turbo (火山极速识别) speech service.

Usage (run from repository root):

    uv run python glass/scripts/glass_cli_smoke_test.py --auc-app-key xxx --auc-access-key yyy

Expectations:
1. An isolated `CONTEXT_PATH` workspace is created under `persist/glass_cli_smoke/`.
2. ffmpeg extracts frames/audio from the sample video.
3. Audio is transcribed through AUC Turbo, producing alignment segments.
4. The Glass timeline processor writes multimedia contexts to storage.
5. `opencontext glass report` generates a report scoped to the ingested timeline.
"""

import argparse
import mimetypes
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from opencontext.config.global_config import GlobalConfig
from opencontext.managers.processor_manager import ContextProcessorManager
from opencontext.models.context import RawContextProperties
from opencontext.models.enums import ContentFormat, ContextSource
from opencontext.storage.global_storage import GlobalStorage

from glass.ingestion import AUCTurboConfig, AUCTurboRunner, FFmpegRunner, LocalVideoManager
from glass.processing.chunkers import ManifestChunker
from glass.processing.timeline_processor import GlassTimelineProcessor
from glass.processing.visual_encoder import VisualEncoder
from glass.storage.context_repository import GlassContextRepository

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


def _is_video_file(path: Path) -> bool:
    """Heuristically determine if a path points to a video file."""
    if not path.is_file():
        return False
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type and mime_type.startswith("video/"):
        return True
    return path.suffix.lower() in KNOWN_VIDEO_EXTENSIONS


def _discover_video_paths(repo_root: Path, override: str | None) -> list[Path]:
    """Collect all video files to run through the smoke test."""
    if override:
        candidate = Path(override).expanduser().resolve()
        if not candidate.exists():
            raise FileNotFoundError(f"Video path override missing: {candidate}")
        if candidate.is_file():
            return [candidate]
        videos = sorted(path for path in candidate.rglob("*") if _is_video_file(path))
        if videos:
            return videos
        raise FileNotFoundError(f"No video files found under override directory: {candidate}")

    videos_root = repo_root / "videos"
    if not videos_root.exists():
        raise FileNotFoundError(f"Videos directory missing: {videos_root}")

    videos = sorted(path for path in videos_root.rglob("*") if _is_video_file(path))
    if not videos:
        raise FileNotFoundError(f"No video files found below {videos_root}")
    return videos


def _sanitize_identifier(value: str) -> str:
    """Sanitize strings for safe reuse in run/timeline identifiers."""
    normalized = re.sub(r"[^0-9a-zA-Z]+", "-", value).strip("-")
    return normalized.lower() or "video"


def _derive_run_id(
    base_run_id: str | None,
    sample_video: Path,
    *,
    batch_token: str,
    index: int,
) -> str:
    suffix = f"{index + 1:02d}-{_sanitize_identifier(sample_video.stem)}"
    if base_run_id:
        return f"{base_run_id}-{suffix}"
    return f"{batch_token}-{suffix}"


def _derive_timeline_id(
    base_timeline_id: str | None,
    sample_video: Path,
    *,
    index: int,
) -> str:
    suffix = f"{index + 1:02d}-{_sanitize_identifier(sample_video.stem)}"
    if base_timeline_id:
        return f"{base_timeline_id}-{suffix}"
    return f"smoke-{suffix}"


def _coalesce_numeric_cli_env(
    cli_value: float | None,
    env_name: str,
    default: float,
) -> float:
    """Pick the CLI value, fall back to env var, then default."""
    if cli_value is not None:
        return cli_value
    env_value = os.getenv(env_name)
    if env_value is None:
        return default
    try:
        return float(env_value)
    except ValueError as exc:  # noqa: B904 - want context
        raise ValueError(f"Environment variable {env_name} must be numeric") from exc


def _load_auc_config_from_global() -> AUCTurboConfig:
    """Load the AUC Turbo config from GlobalConfig, falling back to defaults."""
    try:
        global_config = GlobalConfig.get_instance()
        glass_config = global_config.get_config("glass") or {}
        speech_config = glass_config.get("speech_to_text") or {}
        auc_config = speech_config.get("auc_turbo")
        return AUCTurboConfig.from_dict(auc_config)
    except Exception:
        return AUCTurboConfig()


def _build_auc_runner(args: argparse.Namespace) -> AUCTurboRunner:
    """Instantiate an AUC Turbo runner from CLI/env configuration."""
    base = _load_auc_config_from_global()
    app_key = args.auc_app_key or os.getenv("AUC_APP_KEY") or base.app_key
    access_key = args.auc_access_key or os.getenv("AUC_ACCESS_KEY") or base.access_key
    if not app_key or not access_key:
        raise RuntimeError(
            "AUC Turbo credentials missing. Provide --auc-app-key/--auc-access-key "
            "or set AUC_APP_KEY/AUC_ACCESS_KEY."
        )

    config = AUCTurboConfig(
        base_url=args.auc_base_url or os.getenv("AUC_BASE_URL") or base.base_url,
        resource_id=args.auc_resource_id or os.getenv("AUC_RESOURCE_ID") or base.resource_id,
        app_key=app_key,
        access_key=access_key,
        model_name=args.auc_model_name or os.getenv("AUC_MODEL_NAME") or base.model_name,
        request_timeout=_coalesce_numeric_cli_env(
            args.auc_timeout,
            "AUC_REQUEST_TIMEOUT",
            base.request_timeout,
        ),
        max_file_size_mb=_coalesce_numeric_cli_env(
            args.auc_max_size_mb,
            "AUC_MAX_FILE_SIZE_MB",
            base.max_file_size_mb,
        ),
        max_duration_sec=_coalesce_numeric_cli_env(
            args.auc_max_duration_sec,
            "AUC_MAX_DURATION_SEC",
            base.max_duration_sec,
        ),
        endpoint_path=args.auc_endpoint or os.getenv("AUC_ENDPOINT_PATH") or base.endpoint_path,
    )
    return AUCTurboRunner(config=config)


def _prepare_workspace(repo_root: Path, *, override: str | None = None) -> Path:
    """Create an isolated CONTEXT_PATH for the smoke run."""
    workspace_root = repo_root / "persist" / "glass_cli_smoke"
    workspace_root.mkdir(parents=True, exist_ok=True)
    run_id = override or datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    run_dir = workspace_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "persist" / "chromadb").mkdir(parents=True, exist_ok=True)
    (run_dir / "persist" / "sqlite").mkdir(parents=True, exist_ok=True)
    os.environ["CONTEXT_PATH"] = str(run_dir)
    return run_dir


def _initialize_singletons(config_path: Path) -> None:
    """Reset and initialize global singletons with the provided config."""
    GlobalConfig.reset()
    GlobalStorage.reset()
    config = GlobalConfig.get_instance()
    if not config.initialize(str(config_path)):
        raise RuntimeError("GlobalConfig failed to initialize; aborting smoke test")
    storage_manager = GlobalStorage.get_instance()
    storage = storage_manager.get_storage()
    if storage is None:
        raise RuntimeError("UnifiedStorage failed to initialize")


def _build_processor_stack(repository: GlassContextRepository) -> ContextProcessorManager:
    """Instantiate a processor manager configured with the Glass timeline processor."""
    processor_manager = ContextProcessorManager()
    processor = GlassTimelineProcessor(
        repository=repository,
        chunker=ManifestChunker(),
        visual_encoder=VisualEncoder(),
    )
    processor_manager.register_processor(processor)
    return processor_manager


def _ingest_sample_video(
    manager: LocalVideoManager,
    sample_video: Path,
    *,
    timeline_id: str,
) -> str:
    """Run the local ingestion pipeline against the sample video."""
    if not sample_video.exists():
        raise FileNotFoundError(f"Sample video missing: {sample_video}")
    manifest = manager.ingest(sample_video, timeline_id=timeline_id)
    segments = len(manifest.segments)
    if segments == 0:
        raise RuntimeError("Ingestion produced an empty manifest")
    return manifest.to_json()


def _invoke_cli_report(
    timeline_id: str,
    *,
    report_path: Path,
    lookback_minutes: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Call the CLI report command via a subprocess."""
    env = os.environ.copy()
    env["GLASS_SMOKE_TIMELINE"] = timeline_id
    command = [
        sys.executable,
        "-m",
        "opencontext.cli",
        "glass",
        "report",
        "--timeline-id",
        timeline_id,
        "--lookback-minutes",
        str(lookback_minutes),
        "--output",
        str(report_path),
    ]
    return subprocess.run(
        command,
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )


def _summarize_repository(repo: GlassContextRepository, timeline_id: str) -> int:
    """Return the number of multimodal records persisted for the timeline."""
    return len(repo.fetch_by_timeline(timeline_id))


def run_smoke_test(
    args: argparse.Namespace,
    sample_video: Path,
    *,
    run_id: str | None = None,
    timeline_id: str | None = None,
) -> Path:
    """Execute the end-to-end smoke workflow and return the report path."""
    repo_root = Path(__file__).resolve().parents[2]
    run_dir = _prepare_workspace(repo_root, override=run_id or args.run_id)
    _initialize_singletons(repo_root / "config" / "config.yaml")

    repository = GlassContextRepository()
    processor_manager = _build_processor_stack(repository)

    ffmpeg_runner = FFmpegRunner(ffmpeg_executable=args.ffmpeg_bin)
    speech_runner = _build_auc_runner(args)
    ingestion_dir = run_dir / "ingestion"
    video_manager = LocalVideoManager(
        base_dir=ingestion_dir,
        frame_rate=args.frame_rate,
        ffmpeg_runner=ffmpeg_runner,
        speech_runner=speech_runner,
    )

    timeline_identifier = timeline_id or args.timeline_id or f"smoke-{int(time.time())}"
    manifest_json = _ingest_sample_video(
        video_manager,
        sample_video,
        timeline_id=timeline_identifier,
    )

    raw_context = RawContextProperties(
        content_format=ContentFormat.VIDEO,
        source=ContextSource.VIDEO,
        create_time=datetime.now(timezone.utc),
        additional_info={
            "timeline_id": timeline_identifier,
            "alignment_manifest": manifest_json,
        },
    )
    processed_contexts = processor_manager.process(raw_context)
    if not processed_contexts:
        raise RuntimeError("Glass timeline processor did not emit any processed contexts.")

    if _summarize_repository(repository, timeline_identifier) == 0:
        raise RuntimeError("Glass context repository has no records for the timeline.")

    report_path = run_dir / "glass_report.md"
    result = _invoke_cli_report(
        timeline_identifier,
        report_path=report_path,
        lookback_minutes=args.lookback_minutes,
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())

    if not report_path.exists() or report_path.stat().st_size == 0:
        raise RuntimeError("CLI did not produce a report file.")

    return report_path


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke-test Glass CLI report generation.")
    parser.add_argument(
        "--timeline-id",
        help="Optional fixed timeline identifier to reuse across runs.",
    )
    parser.add_argument(
        "--run-id",
        help="Optional run directory name under persist/glass_cli_smoke/.",
    )
    parser.add_argument(
        "--frame-rate",
        type=float,
        default=1.0,
        help="Frame sampling rate used while extracting frames via ffmpeg.",
    )
    parser.add_argument(
        "--lookback-minutes",
        type=int,
        default=120,
        help="Lookback window passed to the CLI report command.",
    )
    parser.add_argument(
        "--video-path",
        help="Override the default videos/ tree. Accepts a single file or a directory.",
    )
    parser.add_argument(
        "--ffmpeg-bin",
        help="Explicit path to ffmpeg; defaults to resolving ffmpeg from PATH.",
    )
    parser.add_argument(
        "--auc-app-key",
        help="AUC Turbo App Key. Defaults to environment variable AUC_APP_KEY.",
    )
    parser.add_argument(
        "--auc-access-key",
        help="AUC Turbo Access Key. Defaults to environment variable AUC_ACCESS_KEY.",
    )
    parser.add_argument(
        "--auc-base-url",
        help="Override the AUC Turbo base URL.",
    )
    parser.add_argument(
        "--auc-resource-id",
        help="Override the AUC Turbo resource id (default volc.bigasr.auc_turbo).",
    )
    parser.add_argument(
        "--auc-model-name",
        help="Override the AUC Turbo model name (default bigmodel).",
    )
    parser.add_argument(
        "--auc-timeout",
        type=float,
        help="HTTP timeout for AUC Turbo requests (seconds).",
    )
    parser.add_argument(
        "--auc-max-size-mb",
        type=float,
        help="Reject audio files above this size before calling AUC Turbo.",
    )
    parser.add_argument(
        "--auc-max-duration-sec",
        type=float,
        help="Reject audio files above this duration before calling AUC Turbo.",
    )
    parser.add_argument(
        "--auc-endpoint",
        help="Custom endpoint path appended to the base URL.",
    )
    return parser


def main() -> None:
    parser = _build_argument_parser()
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    batch_token = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    videos = _discover_video_paths(repo_root, args.video_path)

    for index, sample_video in enumerate(videos):
        run_id = _derive_run_id(args.run_id, sample_video, batch_token=batch_token, index=index)
        timeline_id = _derive_timeline_id(args.timeline_id, sample_video, index=index)
        try:
            report_path = run_smoke_test(
                args,
                sample_video,
                run_id=run_id,
                timeline_id=timeline_id,
            )
        except subprocess.CalledProcessError as exc:
            if exc.stdout:
                print(exc.stdout, file=sys.stderr)
            if exc.stderr:
                print(exc.stderr, file=sys.stderr)
            raise
        print(f"Smoke test completed for {sample_video}. Report written to {report_path}")


if __name__ == "__main__":
    main()
