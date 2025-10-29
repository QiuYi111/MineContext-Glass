from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import List

from bleach.sanitizer import Cleaner
from markdown_it import MarkdownIt

from glass.reports.models import DailyReport, TimelineHighlight, VisualCard

from ..models import TimelineRecord

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


class MarkdownRenderer:
    """Render Markdown into sanitised HTML for the WebUI."""

    def __init__(self) -> None:
        self._markdown = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable(["table"])
        self._cleaner = Cleaner(tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRIBUTES, strip=True)

    def render(self, markdown: str | None) -> str | None:
        if not markdown:
            return None
        html = self._markdown.render(markdown)
        return self._cleaner.clean(html)


@dataclass(slots=True)
class DailyReportBuilder:
    """Produce synthetic reports for demo and lightweight processing flows."""

    renderer: MarkdownRenderer

    def build_auto_report(self, record: TimelineRecord) -> DailyReport:
        auto_markdown = self._build_auto_markdown(record)
        highlights = record.highlights or self._build_highlights(record)
        visual_cards = record.visual_cards or self._build_visual_cards(record)

        record.auto_markdown = auto_markdown
        record.highlights = highlights
        record.visual_cards = visual_cards
        record.completed_at = record.completed_at or dt.datetime.now(dt.timezone.utc)

        rendered_html = self.renderer.render(record.manual_markdown or auto_markdown)
        record.rendered_html = rendered_html

        return DailyReport(
            timeline_id=record.timeline_id,
            source=record.filename,
            auto_markdown=auto_markdown,
            manual_markdown=record.manual_markdown,
            rendered_html=rendered_html,
            highlights=highlights,
            visual_cards=visual_cards,
            manual_metadata=record.manual_metadata,
            updated_at=record.completed_at,
        )

    def rebuild_rendered_html(self, record: TimelineRecord) -> None:
        record.completed_at = dt.datetime.now(dt.timezone.utc)
        record.auto_markdown = record.auto_markdown or self._build_auto_markdown(record)
        record.highlights = record.highlights or self._build_highlights(record)
        record.visual_cards = record.visual_cards or self._build_visual_cards(record)
        record.manual_metadata = record.manual_metadata or {}
        record.rendered_html = self.renderer.render(record.manual_markdown or record.auto_markdown)

    def _build_auto_markdown(self, record: TimelineRecord) -> str:
        created = record.submitted_at.isoformat()
        completed = (record.completed_at or dt.datetime.now(dt.timezone.utc)).isoformat()
        lines = [
            "# Glass Timeline Daily Report",
            "",
            f"- Timeline: `{record.timeline_id}`",
            f"- Source: `{record.filename}`",
            f"- Uploaded at: {created}",
            f"- Processed at: {completed}",
            "",
            "## Summary",
            "本日报告由 Glass 轻量后端自动生成，用于演示独立 WebUI 的实时能力。",
            "",
            "## Highlights",
        ]
        for highlight in self._build_highlights(record):
            timestamp = _format_timestamp(highlight.timestamp or highlight.segment_start or 0.0)
            lines.append(f"- [{timestamp}] {highlight.title}")
        lines.append("")
        lines.append("## Notes")
        lines.append(
            "您可以在右侧编辑器中补充手动 Markdown，通过 `Ctrl+S`/`Cmd+S` 保存并即时预览。"
        )
        return "\n".join(lines)

    def _build_highlights(self, record: TimelineRecord) -> List[TimelineHighlight]:
        if record.highlights:
            return record.highlights
        highlights: List[TimelineHighlight] = []
        for index in range(3):
            timestamp = float(index * 45)
            highlights.append(
                TimelineHighlight(
                    title=f"关键事件 #{index + 1}",
                    summary="自动生成的演示摘要，用于展示 Highlights 栏位。",
                    modality="frame" if index % 2 == 0 else "audio",
                    timestamp=timestamp,
                    segment_start=timestamp,
                    segment_end=timestamp + 12,
                    context_id=f"{record.timeline_id}-ctx-{index}",
                )
            )
        return highlights

    def _build_visual_cards(self, record: TimelineRecord) -> List[VisualCard]:
        if record.visual_cards:
            return record.visual_cards
        cards: List[VisualCard] = []
        for index in range(3):
            bg = "0D6EFD" if index % 2 == 0 else "101010"
            fg = "FFFFFF" if index % 2 == 0 else "0D6EFD"
            cards.append(
                VisualCard(
                    image_url=f"https://dummyimage.com/800x450/{bg}/{fg}&text=Glass+Frame+{index + 1}",
                    caption=f"示例画面 #{index + 1}",
                    segment_start=float(index * 45),
                    segment_end=float(index * 45 + 10),
                )
            )
        return cards


def _format_timestamp(value: float) -> str:
    minutes, seconds = divmod(max(value, 0.0), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:05.2f}"
    return f"{int(minutes):02d}:{seconds:05.2f}"

