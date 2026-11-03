from __future__ import annotations

from orderflow_lab.events import EventKind, assert_trade_before_depth
from orderflow_lab.latency import apply_trade_local_latency, summarize_latency
from orderflow_lab.merge import merge_trade_before_depth
from orderflow_lab.synthetic import generate_session


def test_merge_enforces_trade_before_depth():
    depths, trades = generate_session(n_depth=30, n_trades=20, seed=1)
    merged = merge_trade_before_depth(depths, trades)
    assert_trade_before_depth(merged)
    assert len(merged) == len(depths) + len(trades)


def test_latency_preserves_trade_identity_and_depth():
    depths, trades = generate_session(n_depth=40, n_trades=15, seed=2)
    base = merge_trade_before_depth(depths, trades)
    delayed = apply_trade_local_latency(base, delay_ms=128)
    summary = summarize_latency(base, delayed)
    assert summary["exch_ts_preserved"] is True
    assert summary["px_qty_preserved"] is True
    assert summary["depth_unchanged"] is True
    assert summary["delay_ms_applied"] == 128.0

    # DEPTH local_ts untouched
    base_depth = [e for e in base if e.kind is EventKind.DEPTH]
    delayed_depth = [e for e in delayed if e.kind is EventKind.DEPTH]
    assert [e.local_ts for e in base_depth] == [e.local_ts for e in delayed_depth]
