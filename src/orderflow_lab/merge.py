"""Merge DEPTH + TRADE streams with TRADE-before-DEPTH tie-break."""

from __future__ import annotations

from .events import (
    EventKind,
    MarketEvent,
    assert_trade_before_depth,
    validate_event_stream,
)


def merge_trade_before_depth(
    depths: list[MarketEvent],
    trades: list[MarketEvent],
    *,
    validate: bool = True,
) -> list[MarketEvent]:
    """Concatenate and sort: ``exch_ts``, then TRADE before DEPTH.

    Local timestamps are left as provided (latency proxies belong in
    ``latency.apply_trade_local_latency``).
    """
    if any(e.kind is not EventKind.DEPTH for e in depths):
        raise ValueError("depths list contains non-DEPTH events")
    if any(e.kind is not EventKind.TRADE for e in trades):
        raise ValueError("trades list contains non-TRADE events")

    combined = list(trades) + list(depths)

    def sort_key(e: MarketEvent) -> tuple[int, int, int]:
        # 0 = TRADE, 1 = DEPTH on equal exch_ts
        kind_rank = 0 if e.kind is EventKind.TRADE else 1
        return (e.exch_ts, kind_rank, e.seq)

    ordered = sorted(combined, key=sort_key)
    if validate:
        validate_event_stream(ordered)
        assert_trade_before_depth(ordered)
    return ordered
