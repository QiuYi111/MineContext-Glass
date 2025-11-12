"""
Unified Glass module configuration using GlobalConfig system.

Replaces the separate BackendConfig with a unified approach that:
1. Uses the existing GlobalConfig singleton pattern
2. Maintains backward compatibility with environment variables
3. Provides the same API surface for upload limits and settings
4. Eliminates configuration duplication

This follows Linus Torvalds' principles:
- Single source of truth (GlobalConfig)
- No special cases (unified loading logic)
- Pragmatic solution (reuse existing good infrastructure)
- Never break userspace (maintain API compatibility)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from opencontext.config.global_config import GlobalConfig


@dataclass(slots=True)
class GlassUploadLimits:
    """Runtime configuration for Glass upload validation."""

    max_size_mb: int = 2_048
    allowed_types: List[str] = field(
        default_factory=lambda: ["video/mp4", "video/quicktime", "video/x-matroska"]
    )
    max_concurrent: int = 2


class GlassConfig:
    """
    Unified Glass module configuration.

    Provides a clean API for Glass-specific configuration while using
    the existing GlobalConfig infrastructure internally.
    """

    def __init__(self, global_config: GlobalConfig | None = None) -> None:
        self._global_config = global_config or GlobalConfig.get_instance()

    @property
    def mode(self) -> str:
        """Get Glass operation mode (demo/real)."""
        return self._get_config_value("glass.backend.mode", "demo").lower()

    @property
    def is_demo(self) -> bool:
        """Check if running in demo mode."""
        return self.mode == "demo"

    @property
    def is_real(self) -> bool:
        """Check if running in real mode."""
        return self.mode == "real"

    @property
    def upload_dir(self) -> Path:
        """Get upload directory path."""
        path_str = self._get_config_value("glass.backend.upload_dir", "persist/glass/uploads")
        path = Path(path_str).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def state_db_path(self) -> Path:
        """Get state database path."""
        path_str = self._get_config_value("glass.backend.state_db", "persist/glass/backend_state.db")
        path = Path(path_str).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def storage_base_dir(self) -> Path:
        """Get storage base directory."""
        path_str = self._get_config_value("glass.backend.storage_dir", "persist/glass")
        path = Path(path_str).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def demo_data_dir(self) -> Path:
        """Get demo data directory."""
        path_str = self._get_config_value("glass.backend.demo_dir", "glass/webui/backend/demo_data")
        path = Path(path_str).expanduser().resolve()
        return path

    @property
    def processing_delay_seconds(self) -> float:
        """Get processing delay for demo mode."""
        delay_str = self._get_config_value("glass.backend.processing_delay", "1.5")
        try:
            return float(delay_str)
        except (ValueError, TypeError):
            return 1.5

    @property
    def upload_limits(self) -> GlassUploadLimits:
        """Get upload validation limits."""
        limits = GlassUploadLimits()

        # Override with environment variables for backward compatibility
        max_size = os.getenv("GLASS_UPLOAD_MAX_SIZE_MB")
        if max_size:
            try:
                limits.max_size_mb = int(max_size)
            except ValueError:
                pass

        max_concurrent = os.getenv("GLASS_UPLOAD_MAX_CONCURRENT")
        if max_concurrent:
            try:
                limits.max_concurrent = max(1, int(max_concurrent))
            except ValueError:
                pass

        allowed = os.getenv("GLASS_UPLOAD_ALLOWED_TYPES")
        if allowed:
            values = [entry.strip() for entry in allowed.split(",") if entry.strip()]
            if values:
                limits.allowed_types = values

        # Override with YAML config if available (higher priority than env vars)
        yaml_config = self._global_config.get_config("glass.uploads") or {}
        if isinstance(yaml_config, dict):
            if "max_size_mb" in yaml_config and yaml_config["max_size_mb"] is not None:
                limits.max_size_mb = int(yaml_config["max_size_mb"])
            if "max_concurrent" in yaml_config and yaml_config["max_concurrent"] is not None:
                limits.max_concurrent = max(1, int(yaml_config["max_concurrent"]))
            if "allowed_types" in yaml_config and yaml_config["allowed_types"] is not None:
                limits.allowed_types = list(yaml_config["allowed_types"])

        return limits

    def _get_config_value(self, key: str, default: str) -> str:
        """Get configuration value from GlobalConfig or environment."""
        # Try YAML config first
        yaml_value = self._global_config.get_config(key)
        if yaml_value is not None:
            return str(yaml_value)

        # Fall back to environment variable for backward compatibility
        env_key = key.replace(".", "_").upper()
        return os.getenv(env_key, default)


def create_glass_config() -> GlassConfig:
    """Factory function to create Glass configuration."""
    return GlassConfig()