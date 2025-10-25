from __future__ import annotations

"""
Command-line smoke test for the Glass pipeline.

This script stitches together the ingestion pipeline, Glass processors, storage,
and the CLI report generation command using the sample video located in the
`videos/` directory. Heavy runtime dependencies (ffmpeg, WhisperX, remote LLMs)
are replaced with lightweight stubs so the end-to-end flow can be validated in
restricted environments.

Usage (run from repository root):

    uv run python glass/scripts/glass_cli_smoke_test.py

The script will:
1. Prepare an isolated `CONTEXT_PATH` workspace under `persist/glass_cli_smoke/`.
2. Stub embedding/vectorization and report generation to avoid network calls.
3. Stub ffmpeg/whisper workloads to emit deterministic frames and transcript
   segments without external binaries.
4. Ingest `videos/22-10/Video Playback.mp4`, run the Glass timeline processor,
   and persist multimodal contexts.
5. Invoke `opencontext glass report` via the CLI and write the resulting report
   to the smoke workspace.
"""

import argparse
import hashlib
import json
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
from opencontext.llm import global_embedding_client, global_vlm_client
from opencontext.managers.processor_manager import ContextProcessorManager
from opencontext.models.context import RawContextProperties, Vectorize
from opencontext.models.enums import ContentFormat, ContextSource
from opencontext.storage.backends import chromadb_backend
from opencontext.storage.global_storage import GlobalStorage

from glass.ingestion import (
    AlignmentSegment,
    LocalVideoManager,
    SegmentType,
    TranscriptionResult,
)
from glass.ingestion.ffmpeg_runner import (
    AudioExtractionResult,
    FrameExtractionResult,
)
from glass.processing.chunkers import ManifestChunker
from glass.processing.timeline_processor import GlassTimelineProcessor
from glass.storage.context_repository import GlassContextRepository


def _hash_to_vector(payload: str | None) -> list[float]:
    """Create a deterministic pseudo-vector from arbitrary input."""
    basis = (payload or "glass-smoke").encode("utf-8", errors="ignore")
    digest = hashlib.sha256(basis).digest()
    vector: list[float] = []
    for index in range(0, 12, 4):
        chunk = int.from_bytes(digest[index : index + 4], "little")
        vector.append(chunk / 2**32)
    return vector


def _install_vectorization_stubs() -> None:
    """Replace heavy embedding + LLM clients with lightweight fallbacks."""

    def _vectorize_stub(vectorize: Vectorize, **_: object) -> list[float]:
        if vectorize.vector:
            return vectorize.vector
        content = vectorize.get_vectorize_content() or vectorize.image_path or ""
        vectorize.vector = _hash_to_vector(str(content))
        return vectorize.vector

    async def _generate_stub(messages: list, **_: object) -> str:
        """Produce a deterministic markdown report from prompt payload."""
        timeline = os.getenv("GLASS_SMOKE_TIMELINE", "unknown")
        user_payload = next((msg.get("content", "") for msg in messages if msg.get("role") == "user"), "")

        range_match = re.search(r"检索范围：(\d+)\s*到\s*(\d+)", user_payload)
        start_ts, end_ts = (range_match.groups() if range_match else ("unknown", "unknown"))

        contexts_block = ""
        marker = "上下文信息："
        if marker in user_payload:
            start_idx = user_payload.index(marker) + len(marker)
            end_marker = "\n\n特别注意："
            end_idx = user_payload.find(end_marker, start_idx)
            if end_idx == -1:
                end_idx = len(user_payload)
            contexts_block = user_payload[start_idx:end_idx].strip()

        try:
            contexts: list[str] = json.loads(contexts_block) if contexts_block else []
        except json.JSONDecodeError:
            contexts = []

        lines: list[str] = [
            "# Glass Timeline Smoke Report",
            f"- timeline: {timeline}",
            f"- window: {start_ts} → {end_ts}",
            f"- context items: {len(contexts)}",
            "",
        ]
        for index, context_str in enumerate(contexts[:8], start=1):
            snippet = (context_str or "").splitlines()[0].strip()
            lines.append(f"{index}. {snippet or 'context snippet unavailable'}")
        if len(contexts) > 8:
            lines.append(f"... {len(contexts) - 8} more segments omitted")
        return "\n".join(lines)

    # Skip eager encoder usage; downstream storage will populate vectors.
    global_embedding_client.is_initialized = lambda: False  # type: ignore[assignment]
    global_embedding_client.do_vectorize = _vectorize_stub  # type: ignore[assignment]
    chromadb_backend.do_vectorize = _vectorize_stub  # type: ignore[assignment]
    global_vlm_client.generate_with_messages_async = _generate_stub  # type: ignore[assignment]


class _StubFFmpegRunner:
    """Produce deterministic frame/audio artefacts without invoking ffmpeg."""

    def __init__(self, *, frame_count: int = 6) -> None:
        self._frame_count = max(frame_count, 1)

    def extract_frames(
        self,
        video_path: Path,
        *,
        fps: float,
        output_dir: Path,
        image_pattern: str = "frame_%05d.png",
    ) -> FrameExtractionResult:
        del video_path, fps  # Unused in stub
        output_dir.mkdir(parents=True, exist_ok=True)
        frame_paths: list[Path] = []
        for index in range(self._frame_count):
            frame_path = output_dir / image_pattern.replace("%05d", f"{index:05d}")
            frame_path.write_text(f"stub-frame-{index}", encoding="utf-8")
            frame_paths.append(frame_path)
        return FrameExtractionResult(frames_dir=output_dir, frame_paths=frame_paths)

    def extract_audio(self, video_path: Path, *, output_path: Path) -> AudioExtractionResult:
        del video_path  # Unused
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"stub-audio")
        return AudioExtractionResult(audio_path=output_path)


class _StubWhisperXRunner:
    """Emit canned transcript segments instead of running WhisperX."""

    def __init__(self, *, segment_count: int = 3) -> None:
        self._segment_count = max(segment_count, 1)

    def transcribe(self, audio_path: Path, *, timeline_id: str) -> TranscriptionResult:
        if not audio_path.exists():
            raise FileNotFoundError(f"audio stub missing: {audio_path}")
        segments: list[AlignmentSegment] = []
        for index in range(self._segment_count):
            start = float(index * 8)
            end = start + 4.0
            text = f"Stub transcript line {index + 1} recorded on timeline {timeline_id}"
            segments.append(
                AlignmentSegment(start=start, end=end, type=SegmentType.AUDIO, payload=text)
            )
        raw_response = {
            "segments": [
                {"start": seg.start, "end": seg.end, "text": seg.payload} for seg in segments
            ]
        }
        return TranscriptionResult(segments=segments, raw_response=raw_response)


class _StubVisualEncoder:
    """Provide deterministic image vectors without hitting external services."""

    def encode(self, image_path: str) -> Vectorize:
        vector = _hash_to_vector(image_path)
        return Vectorize(
            content_format=ContentFormat.IMAGE,
            image_path=image_path,
            vector=vector,
        )


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
        visual_encoder=_StubVisualEncoder(),
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
    _install_vectorization_stubs()
    _initialize_singletons(repo_root / "config" / "config.yaml")

    repository = GlassContextRepository()
    processor_manager = _build_processor_stack(repository)

    ffmpeg_stub = _StubFFmpegRunner(frame_count=args.frame_count)
    whisper_stub = _StubWhisperXRunner(segment_count=args.segment_count)
    ingestion_dir = run_dir / "ingestion"
    video_manager = LocalVideoManager(
        base_dir=ingestion_dir,
        frame_rate=args.frame_rate,
        ffmpeg_runner=ffmpeg_stub,
        speech_runner=whisper_stub,
    )

    timeline_id = args.timeline_id or f"smoke-{int(time.time())}"
    manifest_json = _ingest_sample_video(
        video_manager,
        repo_root / "videos" / "22-10" / "Video Playback.mp4",
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
        "--frame-count",
        type=int,
        default=6,
        help="Number of synthetic frames generated by the ffmpeg stub.",
    )
    parser.add_argument(
        "--segment-count",
        type=int,
        default=3,
        help="Number of synthetic transcript segments produced by the whisper stub.",
    )
    parser.add_argument(
        "--frame-rate",
        type=float,
        default=1.0,
        help="Frame sampling rate used by the ingestion stub.",
    )
    parser.add_argument(
        "--lookback-minutes",
        type=int,
        default=120,
        help="Lookback window passed to the CLI report command.",
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
