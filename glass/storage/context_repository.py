from __future__ import annotations

import datetime as _dt
import json
import sqlite3
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from opencontext.storage.base_storage import StorageType
from opencontext.storage.global_storage import get_global_storage
from opencontext.storage.unified_storage import UnifiedStorage
from opencontext.utils.logging_utils import get_logger

from .models import Modality, MultimodalContextItem

logger = get_logger(__name__)


@dataclass(frozen=True)
class DailyReportRecord:
    timeline_id: str
    manual_markdown: str | None
    manual_metadata: dict | None
    rendered_html: str | None
    updated_at: _dt.datetime | None


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

        # Persist per-context-type batches so we can reliably map returned IDs back to the original items.
        indexed_by_type: dict[str, list[tuple[int, MultimodalContextItem]]] = defaultdict(list)
        for index, item in enumerate(items):
            context = item.context
            if not context or not context.extracted_data or not context.extracted_data.context_type:
                raise ValueError("Each context item must carry an extracted context_type")
            context_type_value = context.extracted_data.context_type.value
            indexed_by_type[context_type_value].append((index, item))

        persisted_ids: list[str | None] = [None] * len(items)
        for context_type, indexed_items in indexed_by_type.items():
            contexts = [item.context for _, item in indexed_items]
            try:
                upserted_ids = self._storage.batch_upsert_processed_context(contexts) or []
            except Exception:
                logger.exception("Failed to persist contexts for type %s", context_type)
                raise

            if len(upserted_ids) != len(contexts):
                logger.debug(
                    "Vector backend returned %s IDs for %s contexts (type=%s); "
                    "falling back to intrinsic context IDs.",
                    len(upserted_ids),
                    len(contexts),
                    context_type,
                )
                upserted_ids = [context.id for context in contexts]

            for (index, item), context_id in zip(indexed_items, upserted_ids):
                persisted_ids[index] = context_id

        records = []
        for index, item in enumerate(items):
            context_id = persisted_ids[index] or item.context.id
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
                    "auto_summary_json": None,
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
                    auto_summary_json,
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
                    :auto_summary_json,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT(context_id) DO UPDATE SET
                    timeline_id = excluded.timeline_id,
                    modality = excluded.modality,
                    content_ref = excluded.content_ref,
                    embedding_ready = excluded.embedding_ready,
                    context_type = excluded.context_type,
                    auto_summary_json = excluded.auto_summary_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                records,
            )

        return [persisted_id or item.context.id for persisted_id, item in zip(persisted_ids, items)]

    def fetch_by_timeline(self, timeline_id: str) -> List[sqlite3.Row]:
        """Fetch raw rows for a timeline. Primarily intended for validation and tests."""
        with self._transaction(readonly=True) as cursor:
            cursor.execute(
                """
                SELECT timeline_id, context_id, modality, content_ref, embedding_ready, context_type, auto_summary_json
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

    def load_daily_report_record(self, timeline_id: str) -> DailyReportRecord | None:
        """Return the persisted manual report metadata for a timeline, if any."""
        with self._transaction(readonly=True) as cursor:
            cursor.execute(
                """
                SELECT timeline_id, manual_markdown, manual_metadata, rendered_html, updated_at
                FROM glass_daily_reports
                WHERE timeline_id = ?
                """,
                (timeline_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        manual_metadata: dict | None = None
        metadata_payload = row["manual_metadata"]
        if metadata_payload:
            try:
                manual_metadata = json.loads(metadata_payload)
            except json.JSONDecodeError:
                logger.debug("Failed to decode manual_metadata for timeline %s", timeline_id)
        if manual_metadata is None:
            manual_metadata = {}

        updated_at = _parse_sqlite_timestamp(row["updated_at"])
        return DailyReportRecord(
            timeline_id=row["timeline_id"],
            manual_markdown=row["manual_markdown"],
            manual_metadata=manual_metadata,
            rendered_html=row["rendered_html"],
            updated_at=updated_at,
        )

    def upsert_daily_report(
        self,
        *,
        timeline_id: str,
        manual_markdown: str | None,
        manual_metadata: dict | None = None,
        rendered_html: str | None = None,
    ) -> DailyReportRecord:
        """Persist manual report content for a timeline."""
        metadata_payload = json.dumps(manual_metadata) if manual_metadata else None
        with self._transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO glass_daily_reports (timeline_id, manual_markdown, manual_metadata, rendered_html, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(timeline_id) DO UPDATE SET
                    manual_markdown = excluded.manual_markdown,
                    manual_metadata = excluded.manual_metadata,
                    rendered_html = excluded.rendered_html,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (timeline_id, manual_markdown, metadata_payload, rendered_html),
            )

        record = self.load_daily_report_record(timeline_id)
        if not record:
            raise RuntimeError(f"Failed to persist daily report for timeline {timeline_id}")
        return record

    def clear_daily_report(self, timeline_id: str) -> None:
        """Remove any manual report overrides for a timeline."""
        with self._transaction() as cursor:
            cursor.execute(
                "DELETE FROM glass_daily_reports WHERE timeline_id = ?",
                (timeline_id,),
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


def _parse_sqlite_timestamp(value: object) -> Optional[_dt.datetime]:
    if not value:
        return None
    if isinstance(value, _dt.datetime):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return _dt.datetime.strptime(value, fmt).replace(tzinfo=_dt.timezone.utc)
            except ValueError:
                continue
    return None
