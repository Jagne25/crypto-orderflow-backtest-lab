"""Market event model and chronological validators.

This module intentionally uses plain dataclasses (not exchange-specific
binary formats) so the demo stays dependency-light and easy to audit.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence


class EventKind(str, Enum):
    DEPTH = "DEPTH"
    TRADE = "TRADE"


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NA = "NA"


@dataclass(frozen=True, slots=True)
class MarketEvent:
    """One book update or public trade.

    Timestamps are nanoseconds since Unix epoch.
    ``exch_ts`` is exchange event time; ``local_ts`` is feed-arrival time
    (or a modeled proxy thereof).
    """

    kind: EventKind
    exch_ts: int
    local_ts: int
    price: float
    qty: float
    side: Side = Side.NA
    seq: int = 0

    def __post_init__(self) -> None:
        if self.exch_ts < 0 or self.local_ts < 0:
            raise ValueError("timestamps must be non-negative")
        if self.price <= 0 or self.qty < 0:
            raise ValueError("price must be > 0 and qty >= 0")
        if self.kind is EventKind.TRADE and self.side is Side.NA:
            raise ValueError("trades require BUY/SELL side")


def validate_nondecreasing(ts: Sequence[int], *, label: str) -> None:
    """Raise if ``ts`` ever decreases (strict chronology check)."""
    if len(ts) < 2:
        return
    for i in range(1, len(ts)):
        if ts[i] < ts[i - 1]:
            raise ValueError(
                f"{label} decreases at index {i}: {ts[i - 1]} -> {ts[i]}"
            )


def _sorted_by_exch(events: Sequence[MarketEvent]) -> list[MarketEvent]:
    return sorted(
        events,
        key=lambda e: (e.exch_ts, 0 if e.kind is EventKind.TRADE else 1, e.seq),
    )


def _sorted_by_local(events: Sequence[MarketEvent]) -> list[MarketEvent]:
    return sorted(
        events,
        key=lambda e: (e.local_ts, 0 if e.kind is EventKind.TRADE else 1, e.seq),
    )


def validate_event_stream(events: Sequence[MarketEvent]) -> dict:
    """Validate a mixed DEPTH/TRADE stream.

    ``exch_ts`` and ``local_ts`` are checked on *their own* sorted views.
    After a trade-latency proxy, local order diverges from exchange order;
    requiring both clocks to be monotone on one shared sequence would be
    incorrect.
    """
    if not events:
        raise ValueError("empty event stream")

    by_exch = _sorted_by_exch(events)
    by_local = _sorted_by_local(events)
    exch = [e.exch_ts for e in by_exch]
    local = [e.local_ts for e in by_local]
    validate_nondecreasing(exch, label="exch_ts")
    validate_nondecreasing(local, label="local_ts")

    n_depth = sum(1 for e in events if e.kind is EventKind.DEPTH)
    n_trade = sum(1 for e in events if e.kind is EventKind.TRADE)
    return {
        "ok": True,
        "n_events": len(events),
        "n_depth": n_depth,
        "n_trade": n_trade,
        "exch_span_ns": exch[-1] - exch[0],
        "local_span_ns": local[-1] - local[0],
    }


def trade_before_depth_violations(events: Sequence[MarketEvent]) -> int:
    """Count same-timestamp groups where a DEPTH appears before a TRADE.

    Microstructure convention used in this lab: when ``exch_ts`` ties,
    public trades are ordered before depth updates.
    """
    violations = 0
    i = 0
    n = len(events)
    while i < n:
        j = i + 1
        while j < n and events[j].exch_ts == events[i].exch_ts:
            j += 1
        group = events[i:j]
        kinds = [e.kind for e in group]
        if EventKind.TRADE in kinds and EventKind.DEPTH in kinds:
            last_trade = max(k for k, kind in enumerate(kinds) if kind is EventKind.TRADE)
            first_depth = min(k for k, kind in enumerate(kinds) if kind is EventKind.DEPTH)
            if last_trade > first_depth:
                violations += 1
        i = j
    return violations


def assert_trade_before_depth(events: Sequence[MarketEvent]) -> None:
    n = trade_before_depth_violations(events)
    if n:
        raise ValueError(f"trade-before-depth violations={n}")


def iter_by_kind(events: Iterable[MarketEvent], kind: EventKind) -> list[MarketEvent]:
    return [e for e in events if e.kind is kind]
