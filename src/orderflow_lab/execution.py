"""Toy MARKET vs LIMIT execution with fees.

This is an *accounting* and fill-logic demo — not a claim of edge.
Signals are arbitrary (every Nth trade) so reviewers see plumbing, not alpha.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .events import EventKind, MarketEvent, Side


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass(slots=True)
class Fill:
    order_type: OrderType
    side: Side
    signal_exch_ts: int
    fill_exch_ts: int
    price: float
    qty: float
    fee: float
    filled: bool
    reason: str


@dataclass(slots=True)
class ExecSummary:
    order_type: OrderType
    n_signals: int
    n_fills: int
    fill_rate: float
    gross_pnl: float
    fees: float
    net_pnl: float
    fills: list[Fill]


def _mid_from_depth(depth: MarketEvent) -> float:
    # Synthetic depth rows store bid; approximate mid as bid + 0.05.
    return depth.price + 0.05


def _next_depths_after(
    events: list[MarketEvent], ts: int
) -> list[MarketEvent]:
    return [e for e in events if e.kind is EventKind.DEPTH and e.exch_ts >= ts]


def _trades_after(events: list[MarketEvent], ts: int) -> list[MarketEvent]:
    return [e for e in events if e.kind is EventKind.TRADE and e.exch_ts > ts]


def generate_toy_signals(
    events: list[MarketEvent], *, every_n_trades: int = 8
) -> list[tuple[int, Side]]:
    """Emit alternating long/short signals on every Nth trade timestamp."""
    trades = [e for e in events if e.kind is EventKind.TRADE]
    signals: list[tuple[int, Side]] = []
    for i, t in enumerate(trades):
        if i % every_n_trades != 0:
            continue
        side = Side.BUY if (i // every_n_trades) % 2 == 0 else Side.SELL
        signals.append((t.exch_ts, side))
    return signals


def simulate_market(
    events: list[MarketEvent],
    signals: list[tuple[int, Side]],
    *,
    qty: float = 0.01,
    fee_bps: float = 4.0,
    slip_ticks: float = 0.1,
) -> ExecSummary:
    """MARKET: fill immediately at next touch +/- slip; always fills if book exists."""
    fills: list[Fill] = []
    for ts, side in signals:
        depths = _next_depths_after(events, ts)
        if not depths:
            fills.append(
                Fill(
                    OrderType.MARKET,
                    side,
                    ts,
                    ts,
                    0.0,
                    0.0,
                    0.0,
                    False,
                    "no_depth",
                )
            )
            continue
        mid = _mid_from_depth(depths[0])
        px = mid + slip_ticks if side is Side.BUY else mid - slip_ticks
        notional = px * qty
        fee = notional * (fee_bps / 10_000.0)
        fills.append(
            Fill(
                OrderType.MARKET,
                side,
                ts,
                depths[0].exch_ts,
                px,
                qty,
                fee,
                True,
                "filled",
            )
        )
    return _summarize(OrderType.MARKET, signals, fills)


def simulate_limit(
    events: list[MarketEvent],
    signals: list[tuple[int, Side]],
    *,
    qty: float = 0.01,
    fee_bps: float = 2.0,
    improve_ticks: float = 0.0,
    max_wait_ns: int = 200_000_000,
) -> ExecSummary:
    """LIMIT: rest at touch; fill only if a later opposing trade crosses.

    Fill rate is intentionally much lower than MARKET — useful for demos of
    queue / adverse-selection style comparisons without real LOB queue models.
    """
    fills: list[Fill] = []
    for ts, side in signals:
        depths = _next_depths_after(events, ts)
        if not depths:
            fills.append(
                Fill(
                    OrderType.LIMIT,
                    side,
                    ts,
                    ts,
                    0.0,
                    0.0,
                    0.0,
                    False,
                    "no_depth",
                )
            )
            continue
        mid = _mid_from_depth(depths[0])
        limit_px = mid - improve_ticks if side is Side.BUY else mid + improve_ticks
        deadline = ts + max_wait_ns
        hit = None
        for tr in _trades_after(events, ts):
            if tr.exch_ts > deadline:
                break
            if side is Side.BUY and tr.side is Side.SELL and tr.price <= limit_px:
                hit = tr
                break
            if side is Side.SELL and tr.side is Side.BUY and tr.price >= limit_px:
                hit = tr
                break
        if hit is None:
            fills.append(
                Fill(
                    OrderType.LIMIT,
                    side,
                    ts,
                    ts,
                    limit_px,
                    0.0,
                    0.0,
                    False,
                    "unfilled",
                )
            )
            continue
        notional = limit_px * qty
        fee = notional * (fee_bps / 10_000.0)
        fills.append(
            Fill(
                OrderType.LIMIT,
                side,
                ts,
                hit.exch_ts,
                limit_px,
                qty,
                fee,
                True,
                "filled",
            )
        )
    return _summarize(OrderType.LIMIT, signals, fills)


def _summarize(
    order_type: OrderType,
    signals: list[tuple[int, Side]],
    fills: list[Fill],
) -> ExecSummary:
    done = [f for f in fills if f.filled]
    # Toy PnL: mark each fill against the next fill of opposite side (pairs),
    # leftover open ignored — enough to show fee drag in the demo table.
    gross = 0.0
    open_pos: Fill | None = None
    for f in done:
        if open_pos is None:
            open_pos = f
            continue
        if open_pos.side is f.side:
            open_pos = f
            continue
        # Close
        if open_pos.side is Side.BUY:
            gross += (f.price - open_pos.price) * min(open_pos.qty, f.qty)
        else:
            gross += (open_pos.price - f.price) * min(open_pos.qty, f.qty)
        open_pos = None
    fees = sum(f.fee for f in done)
    n_sig = len(signals)
    n_fill = len(done)
    return ExecSummary(
        order_type=order_type,
        n_signals=n_sig,
        n_fills=n_fill,
        fill_rate=(n_fill / n_sig) if n_sig else 0.0,
        gross_pnl=gross,
        fees=fees,
        net_pnl=gross - fees,
        fills=fills,
    )
