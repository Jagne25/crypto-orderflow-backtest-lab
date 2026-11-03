"""Trade-feed latency proxies.

DEPTH ``local_ts`` (feed arrival) is never mutated here. Only trade
``local_ts`` is shifted — a common way to stress-test whether a strategy
still behaves when public prints arrive late relative to the book.
"""

from __future__ import annotations

from dataclasses import replace

from .events import EventKind, MarketEvent, validate_event_stream
from .merge import merge_trade_before_depth


def apply_trade_local_latency(
    events: list[MarketEvent],
    *,
    delay_ms: int,
) -> list[MarketEvent]:
    """Return a new stream where TRADE ``local_ts += delay_ms``.

    Identity invariants (checked by tests):
    - TRADE ``exch_ts``, ``price``, ``qty``, ``side`` unchanged
    - DEPTH rows byte-for-byte identical (same object fields)
    """
    if delay_ms < 0:
        raise ValueError("delay_ms must be >= 0")
    delta_ns = delay_ms * 1_000_000

    depths = [e for e in events if e.kind is EventKind.DEPTH]
    trades = [e for e in events if e.kind is EventKind.TRADE]
    delayed_trades = [
        replace(t, local_ts=t.exch_ts + delta_ns) for t in trades
    ]
    # Primary stream: exchange-time order (TRADE-before-DEPTH on ties).
    # validate_event_stream checks each clock on its own sorted view.
    out = merge_trade_before_depth(depths, delayed_trades, validate=True)
    validate_event_stream(out)
    return out


def summarize_latency(base: list[MarketEvent], delayed: list[MarketEvent]) -> dict:
    key = lambda e: (e.exch_ts, e.seq)
    base_trades = sorted(
        (e for e in base if e.kind is EventKind.TRADE), key=key
    )
    delayed_trades = sorted(
        (e for e in delayed if e.kind is EventKind.TRADE), key=key
    )
    if len(base_trades) != len(delayed_trades):
        raise ValueError("trade count changed after latency transform")
    deltas_ms = [
        (d.local_ts - b.exch_ts) / 1_000_000
        for b, d in zip(base_trades, delayed_trades)
    ]
    base_depth = sorted(
        (e for e in base if e.kind is EventKind.DEPTH), key=key
    )
    delayed_depth = sorted(
        (e for e in delayed if e.kind is EventKind.DEPTH), key=key
    )
    return {
        "n_trades": len(base_trades),
        "delay_ms_applied": deltas_ms[0] if deltas_ms else 0.0,
        "exch_ts_preserved": all(
            b.exch_ts == d.exch_ts for b, d in zip(base_trades, delayed_trades)
        ),
        "px_qty_preserved": all(
            b.price == d.price and b.qty == d.qty
            for b, d in zip(base_trades, delayed_trades)
        ),
        "depth_unchanged": base_depth == delayed_depth,
    }
