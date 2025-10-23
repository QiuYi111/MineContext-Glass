"""
Processing utilities for MineContext Glass.

The module exposes selectors for the main processing primitives while deferring
their imports to avoid circular dependencies with OpenContext's processor
factory.
"""

from importlib import import_module
from typing import Any

__all__ = (
    "ContextEnvelope",
    "GlassTimelineProcessor",
    "ManifestChunker",
    "VisualEncoder",
    "build_context_items",
)

_EXPORT_MAP = {
    "ManifestChunker": ("glass.processing.chunkers", "ManifestChunker"),
    "build_context_items": ("glass.processing.chunkers", "build_context_items"),
    "ContextEnvelope": ("glass.processing.envelope", "ContextEnvelope"),
    "GlassTimelineProcessor": ("glass.processing.timeline_processor", "GlassTimelineProcessor"),
    "VisualEncoder": ("glass.processing.visual_encoder", "VisualEncoder"),
}


def __getattr__(name: str) -> Any:
    module_path, symbol = _EXPORT_MAP.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'glass.processing' has no attribute '{name}'")  # noqa: TRY003
    module = import_module(module_path)
    return getattr(module, symbol)
