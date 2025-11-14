from __future__ import annotations

import json

import pytest

from glass.ingestion import AlignmentManifest, AlignmentSegment, SegmentType


def test_alignment_segment_validates_range() -> None:
    with pytest.raises(ValueError):
        AlignmentSegment(
            start=1.5,
            end=1.0,
            type=SegmentType.AUDIO,
            payload="bad range",
        )


def test_alignment_manifest_sorts_segments() -> None:
    manifest = AlignmentManifest(
        timeline_id="timeline-123",
        source="sample.mp4",
        segments=[
            AlignmentSegment(
                start=10.0,
                end=12.0,
                type=SegmentType.AUDIO,
                payload="late",
            ),
            AlignmentSegment(
                start=0.0,
                end=2.0,
                type=SegmentType.FRAME,
                payload="frame_0001.png",
            ),
        ],
    )

    starts = [segment.start for segment in manifest.segments]
    assert starts == [0.0, 10.0]


def test_alignment_manifest_requires_segments() -> None:
    with pytest.raises(ValueError):
        AlignmentManifest(timeline_id="timeline", source="foo.mp4", segments=[])


def test_manifest_json_serialisation() -> None:
    manifest = AlignmentManifest(
        timeline_id="timeline-xyz",
        source="video.mov",
        segments=[
            AlignmentSegment(
                start=0.0,
                end=1.5,
                type=SegmentType.AUDIO,
                payload="hello world",
            )
        ],
    )

    data = json.loads(manifest.to_json())
    assert data["timeline_id"] == "timeline-xyz"
    assert data["segments"][0]["type"] == SegmentType.AUDIO


def test_manifest_iter_segments_filters_by_type() -> None:
    manifest = AlignmentManifest(
        timeline_id="timeline-iter",
        source="foo.mp4",
        segments=[
            AlignmentSegment(
                start=0.0,
                end=0.5,
                type=SegmentType.FRAME,
                payload="frame_1.png",
            ),
            AlignmentSegment(
                start=0.0,
                end=0.5,
                type=SegmentType.AUDIO,
                payload="hello",
            ),
        ],
    )

    frames = list(manifest.iter_segments(SegmentType.FRAME))
    assert len(frames) == 1
    assert frames[0].type is SegmentType.FRAME
