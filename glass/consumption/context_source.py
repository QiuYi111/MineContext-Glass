from __future__ import annotations

"""
Adapter utilities that expose Glass timelines to the MineContext consumption layer.

Glass stores multimodal timeline data as ProcessedContext records so that downstream
services can keep operating on familiar primitives. The consumption layer, however,
often needs timeline-aware access patterns (e.g. fetch the most recent segments from
one recording). GlassContextSource consolidates that logic by rebuilding a
ContextEnvelope from persisted metadata and offering convenience helpers that return
ProcessedContext objects or their LLM string representations.
"""

from typing import Iterable, List, Sequence

from opencontext.models.context import ProcessedContext
from opencontext.utils.logging_utils import get_logger

from glass.processing.envelope import ContextEnvelope
from glass.storage import GlassContextRepository, Modality, MultimodalContextItem

logger = get_logger(__name__)


class GlassContextSource:
    """Facade for retrieving timeline-aligned contexts from persistent storage."""

    def __init__(
        self,
        *,
        repository: GlassContextRepository | None = None,
    ) -> None:
        self._repository = repository or GlassContextRepository()

    def fetch_envelope(
        self,
        timeline_id: str,
        *,
        modalities: Sequence[Modality] | None = None,
    ) -> ContextEnvelope | None:
        """
        Load a ContextEnvelope for a timeline.

        Returns None when the timeline has no recorded segments or when none of the
        segments satisfy the requested modality filter.
        """
        try:
            envelope = self._repository.load_envelope(timeline_id, modalities=modalities)
            if envelope and not envelope.items:
                return None
            return envelope
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load Glass envelope for timeline %s", timeline_id)
            return None

    def get_items(
        self,
        timeline_id: str,
        *,
        modalities: Sequence[Modality] | None = None,
    ) -> List[MultimodalContextItem]:
        """Return multimodal items in descending timeline order."""
        envelope = self.fetch_envelope(timeline_id, modalities=modalities)
        if not envelope:
            return []
        return list(envelope.items)

    def get_processed_contexts(
        self,
        timeline_id: str,
        *,
        modalities: Sequence[Modality] | None = None,
    ) -> List[ProcessedContext]:
        """Return ProcessedContext payloads ordered from most recent to oldest."""
        items = self.get_items(timeline_id, modalities=modalities)
        return [item.context for item in items]

    def get_context_strings(
        self,
        timeline_id: str,
        *,
        modalities: Sequence[Modality] | None = None,
    ) -> List[str]:
        """
        Return LLM-ready context strings. Maintains the ordering emitted by
        get_processed_contexts so that consumers see the most recent segments first.
        """
        contexts = self.get_processed_contexts(timeline_id, modalities=modalities)
        strings: List[str] = []
        for context in contexts:
            try:
                strings.append(context.get_llm_context_string())
            except Exception:  # noqa: BLE001
                logger.debug(
                    "Failed to serialise context %s for timeline %s",
                    context.id,
                    timeline_id,
                )
        return strings

    def group_by_context_type(
        self,
        timeline_id: str,
        *,
        modalities: Sequence[Modality] | None = None,
    ) -> dict[str, List[ProcessedContext]]:
        """
        Group contexts by ContextType, matching the structure expected by
        ConsumptionManager utilities.
        """
        grouped: dict[str, List[ProcessedContext]] = {}
        for context in self.get_processed_contexts(timeline_id, modalities=modalities):
            extracted = context.extracted_data
            if not extracted or not extracted.context_type:
                continue
            grouped.setdefault(extracted.context_type.value, []).append(context)
        return grouped

    def iter_context_strings(
        self,
        timeline_id: str,
        *,
        modalities: Sequence[Modality] | None = None,
    ) -> Iterable[str]:
        """Convenience iterator variant of get_context_strings."""
        for context_string in self.get_context_strings(timeline_id, modalities=modalities):
            yield context_string
