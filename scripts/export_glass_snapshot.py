from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from glass.reports.service import DailyReportService
from glass.storage.context_repository import GlassContextRepository
from opencontext.config.global_config import get_global_config
from opencontext.storage.global_storage import get_global_storage


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export MineContext Glass timelines into a demo snapshot."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the JSON file that will receive the snapshot.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print the JSON payload (indent=2).",
    )
    return parser.parse_args()


def _ensure_infrastructure_ready() -> None:
    """Best-effort initialization for config and storage layers."""
    config = get_global_config()
    if not config.is_initialized():
        config.initialize("config/config.yaml")

    storage_manager = get_global_storage()
    storage = storage_manager.get_storage()
    if storage is None:
        raise RuntimeError(
            "Unified storage is not initialized. Run the Glass pipeline once or "
            "ensure config/config.yaml declares working storage.backends."
        )


def _normalise_timestamp(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace(" ", "T"))
    except ValueError:
        return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _resolve_time_bounds(repository: GlassContextRepository, timeline_id: str) -> Dict[str, Optional[str]]:
    cursor = repository._connection.execute(  # type: ignore[attr-defined]
        """
        SELECT
            MIN(created_at) AS submitted_at,
            MAX(updated_at) AS completed_at
        FROM glass_multimodal_context
        WHERE timeline_id = ?
        """,
        (timeline_id,),
    )
    row = cursor.fetchone()
    if not row:
        return {"submitted_at": None, "completed_at": None}
    submitted = _normalise_timestamp(row["submitted_at"])
    completed = _normalise_timestamp(row["completed_at"])
    return {"submitted_at": submitted, "completed_at": completed}


def _export_timelines(repository: GlassContextRepository, report_service: DailyReportService) -> List[Dict[str, Any]]:
    cursor = repository._connection.execute(  # type: ignore[attr-defined]
        "SELECT DISTINCT timeline_id FROM glass_multimodal_context ORDER BY timeline_id"
    )
    timeline_ids = [row["timeline_id"] for row in cursor.fetchall()]

    exported: List[Dict[str, Any]] = []
    for timeline_id in timeline_ids:
        envelope = repository.load_envelope(timeline_id)
        if envelope is None:
            continue

        try:
            report = report_service.get_report(timeline_id, envelope=envelope)
        except ValueError:
            # Contexts exist but report generation failed; skip to keep snapshot clean.
            continue

        time_bounds = _resolve_time_bounds(repository, timeline_id)
        source_path = report.source or envelope.source
        filename = Path(source_path).name if source_path else f"{timeline_id}.mp4"
        exported.append(
            {
                "timeline_id": timeline_id,
                "status": "completed",
                "filename": filename,
                "source_path": source_path,
                "submitted_at": time_bounds["submitted_at"],
                "completed_at": time_bounds["completed_at"],
                "envelope": envelope.model_dump(mode="json"),
                "report": report.model_dump(mode="json"),
            }
        )

    return exported


def main() -> int:
    args = _parse_args()

    try:
        _ensure_infrastructure_ready()
    except Exception as exc:  # noqa: BLE001
        print(f"[snapshot] Failed to initialise infrastructure: {exc}", file=sys.stderr)
        return 1

    try:
        repository = GlassContextRepository()
        report_service = DailyReportService(repository=repository)
    except Exception as exc:  # noqa: BLE001
        print(f"[snapshot] Failed to initialise repositories: {exc}", file=sys.stderr)
        return 1

    timelines = _export_timelines(repository, report_service)
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "timeline_count": len(timelines),
        "timelines": timelines,
    }

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if args.pretty:
            output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        else:
            output_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print(f"[snapshot] Failed to write snapshot {output_path}: {exc}", file=sys.stderr)
        return 1

    print(f"[snapshot] Exported {len(timelines)} timeline(s) to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
