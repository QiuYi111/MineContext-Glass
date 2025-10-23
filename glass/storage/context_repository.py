from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterable, List, Optional, Sequence, Tuple

from opencontext.storage.base_storage import StorageType
from opencontext.storage.global_storage import get_global_storage
from opencontext.storage.unified_storage import UnifiedStorage
from opencontext.utils.logging_utils import get_logger

from .models import Modality, MultimodalContextItem

logger = get_logger(__name__)


class GlassContextRepository:
    """
    Persists Glass multimodal context bookkeeping alongside the existing MineContext storage.

    Vector embeddings continue to live in the global storage; this repository only tracks
    timeline metadata in SQLite. The intent is to keep data flow identical for downstream
    consumers while providing a single insertion point for Phase 2.
    """

    def __init__(
        self,
        storage: Optional[UnifiedStorage] = None,
        connection: Optional[sqlite3.Connection] = None,
    ) -> None:
        self._storage = storage or self._resolve_storage()
        self._connection = connection or self._resolve_connection(self._storage)

    def upsert_aligned_segments(self, items: Sequence[MultimodalContextItem]) -> List[str]:
        """
        Upsert a batch of aligned segments.

        Steps:
          1. Write ProcessedContext payloads to the vector backend (batch preferred).
          2. Record the multimodal metadata in SQLite so downstream jobs can fetch by timeline.
        """
        if not items:
            logger.debug("upsert_aligned_segments called with empty payload")
            return []

        contexts = [item.context for item in items]
        upserted_ids = self._storage.batch_upsert_processed_context(contexts)
        if not upserted_ids:
            # Fallback: vector backend may return None while still persisting the records;
            # fall back to ProcessedContext ids to maintain reference continuity.
            upserted_ids = [context.id for context in contexts]

        if len(upserted_ids) != len(items):
            raise ValueError(
                "Vector backend returned unexpected number of IDs; "
                f"expected {len(items)}, got {len(upserted_ids)}"
            )

        records = []
        for item, context_id in zip(items, upserted_ids):
            context_type = None
            if item.context and item.context.extracted_data:
                context_type = item.context.extracted_data.context_type.value
            records.append(
                {
                    "timeline_id": item.timeline_id,
                    "context_id": context_id,
                    "modality": item.modality.value,
                    "content_ref": item.content_ref,
                    "embedding_ready": 1 if item.embedding_ready else 0,
                    "context_type": context_type,
                }
            )

        with self._transaction() as cursor:
            cursor.executemany(
                """
                INSERT INTO glass_multimodal_context (
                    timeline_id,
                    context_id,
                    modality,
                    content_ref,
                    embedding_ready,
                    context_type,
                    created_at,
                    updated_at
                )
                VALUES (
                    :timeline_id,
                    :context_id,
                    :modality,
                    :content_ref,
                    :embedding_ready,
                    :context_type,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT(context_id) DO UPDATE SET
                    timeline_id = excluded.timeline_id,
                    modality = excluded.modality,
                    content_ref = excluded.content_ref,
                    embedding_ready = excluded.embedding_ready,
                    context_type = excluded.context_type,
                    updated_at = CURRENT_TIMESTAMP
                """,
                records,
            )

        return upserted_ids

    def fetch_by_timeline(self, timeline_id: str) -> List[sqlite3.Row]:
        """Fetch raw rows for a timeline. Primarily intended for validation and tests."""
        with self._transaction(readonly=True) as cursor:
            cursor.execute(
                """
                SELECT timeline_id, context_id, modality, content_ref, embedding_ready, context_type
                FROM glass_multimodal_context
                WHERE timeline_id = ?
                ORDER BY context_id
                """,
                (timeline_id,),
            )
            return cursor.fetchall()

    def load_envelope(
        self,
        timeline_id: str,
        *,
        modalities: Sequence[Modality] | None = None,
    ):
        """
        Load a ContextEnvelope for the specified timeline.

        Returns None when no multimodal items are recorded or when the underlying
        ProcessedContext records cannot be reconstructed.
        """
        rows = self.fetch_by_timeline(timeline_id)
        if not rows:
            return None

        allowed_modalities = {modality for modality in modalities} if modalities else None
        items: List[MultimodalContextItem] = []
        for row in rows:
            try:
                modality = Modality(row["modality"])
            except ValueError:
                logger.debug(
                    "Skipping multimodal row with unsupported modality '%s' for timeline %s",
                    row["modality"],
                    timeline_id,
                )
                continue

            if allowed_modalities and modality not in allowed_modalities:
                continue

            context_type = row["context_type"]
            if not context_type:
                logger.debug(
                    "Multimodal row %s for timeline %s missing context_type metadata",
                    row["context_id"],
                    timeline_id,
                )
                continue

            context = self._storage.get_processed_context(row["context_id"], context_type)
            if not context:
                logger.debug(
                    "Processed context %s (%s) not found for timeline %s",
                    row["context_id"],
                    context_type,
                    timeline_id,
                )
                continue

            item = MultimodalContextItem(
                context=context,
                timeline_id=timeline_id,
                modality=modality,
                content_ref=row["content_ref"],
                embedding_ready=bool(row["embedding_ready"]),
            )
            items.append(item)

        if not items:
            return None

        items.sort(key=_sort_envelope_item, reverse=True)
        source = _resolve_source_from_items(items) or timeline_id

        from glass.processing.envelope import ContextEnvelope  # local import to avoid cycle

        return ContextEnvelope.from_items(
            timeline_id=timeline_id,
            source=source,
            items=items,
        )

    def _resolve_storage(self) -> UnifiedStorage:
        storage = get_global_storage().get_storage()
        if not storage:
            raise RuntimeError("Unified storage is not initialised; run storage.initialize() first")
        return storage

    def _resolve_connection(self, storage: UnifiedStorage) -> sqlite3.Connection:
        backend = storage.get_default_backend(StorageType.DOCUMENT_DB)
        if backend is None:
            raise RuntimeError("Document backend is not configured; cannot persist multimodal metadata")

        connection = getattr(backend, "connection", None)
        if connection is None:
            raise RuntimeError("Configured document backend does not expose a SQLite connection")

        # Ensure we surface rows as dictionaries for convenience.
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _transaction(self, readonly: bool = False) -> Iterable[sqlite3.Cursor]:
        cursor = self._connection.cursor()
        try:
            yield cursor
            if not readonly:
                self._connection.commit()
        except Exception:
            logger.exception("SQLite operation failed; rolling back transaction")
            if not readonly:
                self._connection.rollback()
            raise
        finally:
            cursor.close()


def _sort_envelope_item(item: MultimodalContextItem) -> Tuple[float, float]:
    """
    Sort envelope items by segment_end (fallback to segment_start) and creation time.

    Returns a tuple so that Python can compare consistently even when metadata is missing.
    """
    metadata = item.context.metadata or {}
    segment_end = metadata.get("segment_end")
    segment_start = metadata.get("segment_start")

    end_val = float(segment_end) if segment_end is not None else float(segment_start or 0.0)
    create_time = item.context.properties.create_time
    create_ts = create_time.timestamp() if create_time else 0.0
    return end_val, create_ts


def _resolve_source_from_items(items: Sequence[MultimodalContextItem]) -> Optional[str]:
    for item in items:
        metadata = item.context.metadata or {}
        source = metadata.get("source_video")
        if source:
            return str(source)
    return None
