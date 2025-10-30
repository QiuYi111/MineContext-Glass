from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Iterable, List, Optional

from bleach.sanitizer import Cleaner
from markdown_it import MarkdownIt

from glass.processing.envelope import ContextEnvelope
from glass.storage import DailyReportRecord, GlassContextRepository, Modality, MultimodalContextItem

from .models import DailyReport, TimelineHighlight, VisualCard

_ALLOWED_TAGS = [
    "a",
    "blockquote",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "ul",
]

_ALLOWED_ATTRIBUTES = {"a": ["href", "title", "target", "rel"]}

_markdown = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable(["table"])
_cleaner = Cleaner(tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRIBUTES, strip=True)


class DailyReportService:
    """Build and persist timeline-centric daily reports for the Glass WebUI."""

    def __init__(self, repository: GlassContextRepository | None = None) -> None:
        self._repository = repository or GlassContextRepository()

    def get_report(
        self,
        timeline_id: str,
        *,
        envelope: ContextEnvelope | None = None,
    ) -> DailyReport:
        envelope = envelope or self._repository.load_envelope(timeline_id)
        if envelope is None:
            raise ValueError(f"Timeline {timeline_id} has no processed contexts yet")

        highlights = self._build_highlights(envelope)
        visual_cards = self._build_visual_cards(envelope)
        auto_markdown = self._build_auto_markdown(envelope, highlights=highlights)

        manual_record = self._repository.load_daily_report_record(timeline_id)
        manual_markdown = manual_record.manual_markdown if manual_record else None
        manual_metadata = manual_record.manual_metadata if manual_record else {}
        updated_at = manual_record.updated_at if manual_record else None

        chosen_markdown = manual_markdown or auto_markdown
        if manual_record and manual_record.rendered_html:
            rendered_html = manual_record.rendered_html
        elif chosen_markdown:
            rendered_html = self._render_markdown(chosen_markdown)
        else:
            rendered_html = None

        return DailyReport(
            timeline_id=envelope.timeline_id,
            source=envelope.source,
            auto_markdown=auto_markdown,
            manual_markdown=manual_markdown,
            rendered_html=rendered_html,
            highlights=highlights,
            visual_cards=visual_cards,
            manual_metadata=manual_metadata or {},
            updated_at=updated_at,
        )

    def save_manual_report(
        self,
        *,
        timeline_id: str,
        manual_markdown: str,
        manual_metadata: Optional[dict] = None,
        envelope: ContextEnvelope | None = None,
    ) -> DailyReport:
        rendered_html = self._render_markdown(manual_markdown)
        record = self._repository.upsert_daily_report(
            timeline_id=timeline_id,
            manual_markdown=manual_markdown,
            manual_metadata=manual_metadata or {},
            rendered_html=rendered_html,
        )
        envelope = envelope or self._repository.load_envelope(timeline_id)
        if envelope is None:
            raise ValueError(f"Timeline {timeline_id} has no processed contexts yet")

        highlights = self._build_highlights(envelope)
        visual_cards = self._build_visual_cards(envelope)
        auto_markdown = self._build_auto_markdown(envelope, highlights=highlights)
        rendered_html = record.rendered_html or self._render_markdown(record.manual_markdown or auto_markdown or "")

        return DailyReport(
            timeline_id=envelope.timeline_id,
            source=envelope.source,
            auto_markdown=auto_markdown,
            manual_markdown=record.manual_markdown,
            rendered_html=rendered_html,
            highlights=highlights,
            visual_cards=visual_cards,
            manual_metadata=record.manual_metadata or {},
            updated_at=record.updated_at,
        )

    @staticmethod
    def _render_markdown(payload: str) -> str:
        html = _markdown.render(payload or "")
        return _cleaner.clean(html)

    def _build_highlights(self, envelope: ContextEnvelope, limit: int = 8) -> List[TimelineHighlight]:
        candidates: List[TimelineHighlight] = []
        for item in envelope.items:
            metadata = item.context.metadata or {}
            summary = (item.context.extracted_data.summary or "").strip()
            if not summary and item.modality is not Modality.FRAME:
                continue

            title = self._derive_title(item, summary=summary)
            thumbnail_url: str | None = None
            if item.modality is Modality.FRAME:
                thumbnail_url = item.content_ref
            else:
                thumbnail_url = (item.context.metadata or {}).get("thumbnail_url")

            highlight = TimelineHighlight(
                title=title,
                summary=summary or None,
                modality=item.modality.value,
                timestamp=_safe_float(metadata.get("segment_end")),
                segment_start=_safe_float(metadata.get("segment_start")),
                segment_end=_safe_float(metadata.get("segment_end")),
                context_id=item.context.id,
                thumbnail_url=thumbnail_url,
            )
            candidates.append(highlight)

        candidates.sort(key=lambda h: (h.segment_end or 0.0, h.segment_start or 0.0), reverse=True)
        return candidates[:limit]

    def _build_visual_cards(self, envelope: ContextEnvelope, limit: int = 6) -> List[VisualCard]:
        cards: List[VisualCard] = []
        for item in envelope.items:
            if item.modality is not Modality.FRAME:
                continue

            metadata = item.context.metadata or {}
            caption = (item.context.extracted_data.summary or "").strip() or "Captured frame"
            cards.append(
                VisualCard(
                    image_url=item.content_ref,
                    caption=caption,
                    segment_start=_safe_float(metadata.get("segment_start")),
                    segment_end=_safe_float(metadata.get("segment_end")),
                )
            )

        cards.sort(key=lambda c: (c.segment_end or 0.0, c.segment_start or 0.0), reverse=True)
        return cards[:limit]

    @staticmethod
    def build_summary(report: DailyReport, *, max_items: int = 3) -> str:
        """Derive a concise summary string from highlight content or auto markdown."""
        snippets: List[str] = []
        for highlight in report.highlights:
            text = (highlight.summary or highlight.title or "").strip()
            if text:
                snippets.append(text)
            if len(snippets) >= max_items:
                break

        if not snippets and report.auto_markdown:
            for line in report.auto_markdown.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#") or stripped.startswith("- Timeline"):
                    continue
                snippets.append(stripped)
                if len(snippets) >= max_items:
                    break

        return " / ".join(snippets)

    def _build_auto_markdown(
        self,
        envelope: ContextEnvelope,
        *,
        highlights: Iterable[TimelineHighlight],
        max_segments: int = 12,
    ) -> str:
        text_items = [
            item
            for item in envelope.items
            if item.modality in {Modality.AUDIO, Modality.TEXT, Modality.METADATA}
        ]
        text_items.sort(
            key=lambda item: (
                _safe_float((item.context.metadata or {}).get("segment_end")) or 0.0,
                _safe_float((item.context.metadata or {}).get("segment_start")) or 0.0,
            ),
            reverse=True,
        )
        selected_items = text_items[:max_segments]

        lines: List[str] = []
        lines.append("# Glass Timeline Daily Report")
        lines.append("")
        lines.append(f"- Timeline: `{envelope.timeline_id}`")
        if envelope.source:
            lines.append(f"- Source: `{envelope.source}`")
        lines.append(f"- Generated at: {_dt.datetime.now(tz=_dt.timezone.utc).isoformat()}")
        lines.append("")

        highlight_list = list(highlights)
        if highlight_list:
            lines.append("## Recent Highlights")
            for highlight in highlight_list[:5]:
                timestamp = format_timestamp(highlight.timestamp or highlight.segment_start)
                summary = highlight.summary or highlight.title
                lines.append(f"- [{timestamp}] {summary}")
            lines.append("")

        if selected_items:
            lines.append("## Detailed Segments")
            for item in selected_items:
                metadata = item.context.metadata or {}
                summary = (item.context.extracted_data.summary or "").strip()
                timestamp = format_timestamp(metadata.get("segment_start"))
                lines.append(f"### {timestamp} · {item.modality.value.capitalize()}")
                if summary:
                    lines.append("")
                    lines.append(summary)
                    lines.append("")
        else:
            lines.append("_No textual segments were generated for this timeline yet._")

        return "\n".join(lines).strip()

    @staticmethod
    def _derive_title(item: MultimodalContextItem, *, summary: str) -> str:
        if summary:
            return summary.splitlines()[0][:80]
        metadata = item.context.metadata or {}
        timestamp = format_timestamp(metadata.get("segment_start"))
        return f"{item.modality.value.title()} segment at {timestamp}"


def format_timestamp(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return "N/A"
    minutes, secs = divmod(max(seconds, 0.0), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{int(hours):02d}:{int(minutes):02d}:{secs:05.2f}"
    return f"{int(minutes):02d}:{secs:05.2f}"


def _safe_float(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
