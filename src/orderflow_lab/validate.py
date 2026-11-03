"""Session-level data-quality checks for the demo pipeline."""

from __future__ import annotations

from .events import EventKind, MarketEvent, validate_event_stream
from .status import SessionReport, classify_session


def coverage_seconds(events: list[MarketEvent]) -> float:
    if not events:
        return 0.0
    return (events[-1].exch_ts - events[0].exch_ts) / 1e9


def audit_session(
    depths: list[MarketEvent],
    trades: list[MarketEvent],
    merged: list[MarketEvent],
    *,
    session_id: str,
    expected_seconds: float,
) -> dict:
    """Run validators and return a JSON-serializable audit blob."""
    depth_rep = validate_event_stream(depths)
    trade_rep = validate_event_stream(trades)
    merged_rep = validate_event_stream(merged)
    cov = coverage_seconds(merged)
    report: SessionReport = classify_session(
        session_id=session_id,
        n_depth=sum(1 for e in merged if e.kind is EventKind.DEPTH),
        n_trade=sum(1 for e in merged if e.kind is EventKind.TRADE),
        coverage_seconds=cov,
        expected_seconds=expected_seconds,
    )
    return {
        "session_id": session_id,
        "depth": depth_rep,
        "trades": trade_rep,
        "merged": merged_rep,
        "status": report.to_dict(),
    }
