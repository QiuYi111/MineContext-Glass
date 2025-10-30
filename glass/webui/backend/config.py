from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass(slots=True)
class UploadLimits:
    """Runtime configuration for upload validation."""

    max_size_mb: int = 2_048
    allowed_types: List[str] = field(
        default_factory=lambda: ["video/mp4", "video/quicktime", "video/x-matroska"]
    )
    max_concurrent: int = 2


@dataclass(slots=True)
class BackendConfig:
    """Configuration values consumed by the standalone backend."""

    mode: str = "demo"
    upload_dir: Path = Path("persist/glass/uploads")
    state_db_path: Path = Path("persist/glass/backend_state.db")
    storage_base_dir: Path = Path("persist/glass")
    demo_data_dir: Path = Path("glass/webui/backend/demo_data")
    processing_delay_seconds: float = 1.5
    upload_limits: UploadLimits = field(default_factory=UploadLimits)

    @property
    def is_demo(self) -> bool:
        return self.mode == "demo"

    @property
    def is_real(self) -> bool:
        return self.mode == "real"


def _parse_upload_limits(prefix: str = "GLASS_UPLOAD_") -> UploadLimits:
    limits = UploadLimits()
    max_size = os.getenv(f"{prefix}MAX_SIZE_MB")
    if max_size:
        try:
            limits.max_size_mb = int(max_size)
        except ValueError:
            pass

    max_concurrent = os.getenv(f"{prefix}MAX_CONCURRENT")
    if max_concurrent:
        try:
            limits.max_concurrent = max(1, int(max_concurrent))
        except ValueError:
            pass

    allowed = os.getenv(f"{prefix}ALLOWED_TYPES")
    if allowed:
        values = [entry.strip() for entry in allowed.split(",") if entry.strip()]
        if values:
            limits.allowed_types = values

    return limits


def load_config() -> BackendConfig:
    """Load backend configuration from environment variables."""

    mode = os.getenv("GLASS_BACKEND_MODE", "demo").strip().lower()
    upload_dir = Path(os.getenv("GLASS_BACKEND_UPLOAD_DIR", "persist/glass/uploads")).expanduser()
    demo_dir = Path(os.getenv("GLASS_BACKEND_DEMO_DIR", "glass/webui/backend/demo_data")).expanduser()
    state_db = Path(os.getenv("GLASS_BACKEND_STATE_DB", "persist/glass/backend_state.db")).expanduser()
    storage_base = Path(os.getenv("GLASS_BACKEND_STORAGE_DIR", "persist/glass")).expanduser()

    processing_delay = os.getenv("GLASS_BACKEND_PROCESSING_DELAY")
    delay_value = 1.5
    if processing_delay:
        try:
            delay_value = float(processing_delay)
        except ValueError:
            pass

    config = BackendConfig(
        mode=mode,
        upload_dir=upload_dir,
        state_db_path=state_db,
        storage_base_dir=storage_base,
        demo_data_dir=demo_dir,
        processing_delay_seconds=delay_value,
        upload_limits=_parse_upload_limits(),
    )
    config.upload_dir.mkdir(parents=True, exist_ok=True)
    config.state_db_path.parent.mkdir(parents=True, exist_ok=True)
    config.storage_base_dir.mkdir(parents=True, exist_ok=True)
    return config
