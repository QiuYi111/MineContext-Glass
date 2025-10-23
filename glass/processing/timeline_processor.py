from __future__ import annotations

"""
Glass timeline processor.

This processor plugs Glass manifests into the existing MineContext processing
manager by translating AlignmentManifest payloads into ProcessedContext objects
and storing them through GlassContextRepository.
"""

from pathlib import Path
from typing import Iterable, List, Optional

from opencontext.context_processing.processor.base_processor import BaseContextProcessor
from opencontext.models.context import ProcessedContext, RawContextProperties
from opencontext.utils.logging_utils import get_logger

from glass.ingestion.models import AlignmentManifest
from glass.processing.chunkers import ManifestChunker
from glass.processing.envelope import ContextEnvelope
from glass.processing.visual_encoder import VisualEncoder
from glass.storage.context_repository import GlassContextRepository
from glass.storage.models import Modality, MultimodalContextItem

logger = get_logger(__name__)


class GlassTimelineProcessor(BaseContextProcessor):
    """Route timeline manifests into the MineContext processing pipeline."""

    def __init__(
        self,
        *,
        repository: Optional[GlassContextRepository] = None,
        chunker: Optional[ManifestChunker] = None,
        visual_encoder: Optional[VisualEncoder] = None,
    ) -> None:
        from opencontext.config.global_config import get_config

        config = get_config("processing.glass_timeline_processor") or {}
        super().__init__(config=config)

        self._repository = repository or GlassContextRepository()
        self._chunker = chunker or ManifestChunker()
        self._visual_encoder = visual_encoder or VisualEncoder()
        self._last_envelope: Optional[ContextEnvelope] = None

    def get_name(self) -> str:
        return "glass_timeline_processor"

    def get_description(self) -> str:
        return "Process Glass alignment manifests into multimodal contexts."

    def get_version(self) -> str:
        return "0.1.0"

    def can_process(self, context: RawContextProperties) -> bool:
        if not isinstance(context, RawContextProperties):
            return False
        additional = context.additional_info or {}
        timeline_id = additional.get("timeline_id")
        if not timeline_id:
            return False
        if context.content_path and Path(context.content_path).exists():
            return True
        if additional.get("alignment_manifest"):
            return True
        logger.debug(
            "Timeline context %s missing manifest payload", timeline_id
        )
        return False

    def process(self, context: RawContextProperties) -> List[ProcessedContext]:
        try:
            manifest = self._load_manifest(context)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load manifest for context %s: %s", context.object_id, exc)
            self._processing_stats["error_count"] += 1
            return []

        items = self._chunker.build_items(manifest)
        if not items:
            logger.warning("Manifest for timeline %s produced no context items", manifest.timeline_id)
            return []

        self._ensure_visual_embeddings(items)
        envelope = ContextEnvelope.from_items(
            timeline_id=manifest.timeline_id,
            source=manifest.source,
            items=items,
        )
        self._last_envelope = envelope

        try:
            self._repository.upsert_aligned_segments(items)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to persist contexts for timeline %s: %s", manifest.timeline_id, exc)
            self._processing_stats["error_count"] += 1
            return []

        processed_contexts = [item.context for item in items]
        self._processing_stats["processed_count"] += 1
        self._processing_stats["contexts_generated_count"] += len(processed_contexts)

        if self._callback:
            try:
                self._callback(processed_contexts)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Timeline processor callback raised: %s", exc)

        return processed_contexts

    def shutdown(self, graceful: bool = False) -> bool:
        logger.info("Shutting down GlassTimelineProcessor (graceful=%s)", graceful)
        return True

    @property
    def last_envelope(self) -> Optional[ContextEnvelope]:
        return self._last_envelope

    def _load_manifest(self, context: RawContextProperties) -> AlignmentManifest:
        additional = context.additional_info or {}
        if context.content_path:
            manifest_path = Path(context.content_path)
            if not manifest_path.exists():
                raise FileNotFoundError(f"alignment manifest not found: {manifest_path}")
            return AlignmentManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))

        manifest_payload = additional.get("alignment_manifest")
        if isinstance(manifest_payload, str):
            return AlignmentManifest.model_validate_json(manifest_payload)
        if isinstance(manifest_payload, dict):
            return AlignmentManifest.model_validate(manifest_payload)

        raise ValueError("No manifest payload supplied for timeline context")

    def _ensure_visual_embeddings(self, items: Iterable[MultimodalContextItem]) -> None:
        for item in items:
            if item.modality is Modality.FRAME and item.context.vectorize:
                if item.context.vectorize.vector:
                    item.embedding_ready = True
                    continue

                vectorize = self._visual_encoder.encode(item.content_ref)
                item.context.vectorize = vectorize
                item.embedding_ready = bool(vectorize.vector)
