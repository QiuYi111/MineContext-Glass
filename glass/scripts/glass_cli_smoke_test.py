from __future__ import annotations

"""
Full pipeline regression test for the Glass timeline processor.

This script runs the entire ingestion + processing + report workflow against
the tracked video in `videos/25-10/6-22.mp4`. Unlike the original smoke test it
relies on the real ffmpeg tooling, the Glass storage path, and the Doubao AUC
Turbo (火山极速识别) speech service instead of WhisperX stubs.

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
import os
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


def _resolve_video_path(repo_root: Path, override: str | None) -> Path:
    """Return the sample video path, optionally overridden by CLI."""
    if override:
        candidate = Path(override).expanduser()
    else:
        candidate = repo_root / "videos" / "25-10" / "6-22.mp4"
    candidate = candidate.resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"Sample video missing: {candidate}")
    return candidate


def _build_auc_runner(args: argparse.Namespace) -> AUCTurboRunner:
    """Instantiate an AUC Turbo runner from CLI/env configuration."""
    base = AUCTurboConfig()
    app_key = args.auc_app_key or os.getenv("AUC_APP_KEY")
    access_key = args.auc_access_key or os.getenv("AUC_ACCESS_KEY")
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


def run_smoke_test(args: argparse.Namespace) -> Path:
    """Execute the end-to-end smoke workflow and return the report path."""
    repo_root = Path(__file__).resolve().parents[2]
    run_dir = _prepare_workspace(repo_root, override=args.run_id)
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

    sample_video = _resolve_video_path(repo_root, args.video_path)
    timeline_id = args.timeline_id or f"smoke-{int(time.time())}"
    manifest_json = _ingest_sample_video(
        video_manager,
        sample_video,
        timeline_id=timeline_id,
    )

    raw_context = RawContextProperties(
        content_format=ContentFormat.VIDEO,
        source=ContextSource.VIDEO,
        create_time=datetime.now(timezone.utc),
        additional_info={
            "timeline_id": timeline_id,
            "alignment_manifest": manifest_json,
        },
    )
    processed_contexts = processor_manager.process(raw_context)
    if not processed_contexts:
        raise RuntimeError("Glass timeline processor did not emit any processed contexts.")

    if _summarize_repository(repository, timeline_id) == 0:
        raise RuntimeError("Glass context repository has no records for the timeline.")

    report_path = run_dir / "glass_report.md"
    result = _invoke_cli_report(
        timeline_id,
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
        help="Override the default videos/25-10/6-22.mp4 sample with a custom path.",
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
    try:
        report_path = run_smoke_test(args)
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout, file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        raise
    print(f"Smoke test completed. Report written to {report_path}")


if __name__ == "__main__":
    main()
