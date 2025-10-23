from __future__ import annotations

"""
Lightweight wrapper around the global embedding client for handling Glass frame
vectorisation. The encoder is intentionally defensive: if the embedding client
is not configured it will simply return the Vectorize object untouched so the
caller can decide when to retry.
"""

from opencontext.llm import global_embedding_client
from opencontext.models.context import Vectorize
from opencontext.models.enums import ContentFormat
from opencontext.utils.logging_utils import get_logger

logger = get_logger(__name__)


class VisualEncoder:
    """Encode frame images into vector representations when possible."""

    def encode(self, image_path: str) -> Vectorize:
        vectorize = Vectorize(content_format=ContentFormat.IMAGE, image_path=image_path)
        return self._maybe_vectorize(vectorize)

    def _maybe_vectorize(self, vectorize: Vectorize) -> Vectorize:
        if not global_embedding_client.is_initialized():
            logger.debug("Embedding client not initialised; skipping eager vectorisation for %s", vectorize.image_path)
            return vectorize

        try:
            global_embedding_client.do_vectorize(vectorize)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Visual encoder failed to vectorise %s: %s", vectorize.image_path, exc)
        return vectorize
