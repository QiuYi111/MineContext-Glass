from __future__ import annotations

import argparse
import datetime

from opencontext import cli


def _make_namespace(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_resolve_report_window_with_explicit_times() -> None:
    start = datetime.datetime(2025, 1, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
    args = _make_namespace(start=start.isoformat(), end=end.isoformat(), lookback_minutes=15)

    start_ts, end_ts = cli._resolve_report_window(args)

    assert start_ts == int(start.timestamp())
    assert end_ts == int(end.timestamp())


def test_resolve_report_window_fallback_lookback(monkeypatch) -> None:
    reference = datetime.datetime(2025, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)

    class _FixedDatetime:
        @staticmethod
        def now(tz=None):  # noqa: D401 - mimic datetime.now
            return reference if tz else reference.replace(tzinfo=None)

        @staticmethod
        def fromisoformat(value: str):
            return datetime.datetime.fromisoformat(value)

    monkeypatch.setattr(cli, "datetime", _FixedDatetime)

    args = _make_namespace(start=None, end=None, lookback_minutes=30)
    start_ts, end_ts = cli._resolve_report_window(args)

    assert end_ts == int(reference.timestamp())
    assert end_ts - start_ts == 30 * 60
