from __future__ import annotations

from pathlib import Path
from typing import Optional

from .snapshot import SnapshotContextRepository, load_snapshot, seed_upload_tasks
from .state import UploadTaskRepository


def load_demo_snapshot(
    directory: Path,
    *,
    tasks: Optional[UploadTaskRepository] = None,
) -> SnapshotContextRepository:
    """
    Load pre-exported snapshot payloads for demo mode.

    The snapshot is expected to resemble the output of scripts/export_glass_snapshot.py.
    """
    timelines = load_snapshot(directory)
    repository = SnapshotContextRepository(timelines)
    if tasks:
        seed_upload_tasks(tasks, timelines.values())
    return repository
