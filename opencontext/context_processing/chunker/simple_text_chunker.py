#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple chunker for plain text payloads such as speech transcripts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional

from opencontext.context_processing.chunker.chunkers import BaseChunker, ChunkingConfig
from opencontext.models.context import Chunk, RawContextProperties
from opencontext.utils.logging_utils import get_logger

logger = get_logger(__name__)


class SimpleTextChunker(BaseChunker):
    """Lightweight chunker that splits plain text into paragraph-sized chunks."""

    def __init__(self, config: Optional[ChunkingConfig] = None):
        super().__init__(config=config)

    def chunk(self, context: RawContextProperties) -> Iterator[Chunk]:
        text = self._load_text(context)
        if not text:
            logger.warning("SimpleTextChunker received empty text payload for %s", context.object_id)
            return

        paragraphs = [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]

        buffer = []
        buffer_len = 0
        max_size = self.config.max_chunk_size
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph_len = len(paragraph)
            if buffer and buffer_len + paragraph_len + 1 > max_size:
                chunk_text = "\n".join(buffer)
                yield Chunk(text=chunk_text, chunk_index=chunk_index)
                chunk_index += 1
                buffer = [paragraph]
                buffer_len = paragraph_len
            else:
                buffer.append(paragraph)
                buffer_len += paragraph_len + 1  # account for newline

        if buffer:
            chunk_text = "\n".join(buffer)
            yield Chunk(text=chunk_text, chunk_index=chunk_index)

    def _load_text(self, context: RawContextProperties) -> str:
        if context.content_text:
            return context.content_text
        if context.content_path:
            try:
                return Path(context.content_path).read_text(encoding="utf-8")
            except FileNotFoundError:
                logger.error("Transcript text file not found: %s", context.content_path)
            except Exception as exc:
                logger.error("Failed to read transcript text file %s: %s", context.content_path, exc)
        return ""
