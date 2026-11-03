from __future__ import annotations

from orderflow_lab.execution import (
    generate_toy_signals,
    simulate_limit,
    simulate_market,
)
from orderflow_lab.merge import merge_trade_before_depth
from orderflow_lab.status import DayStatus, classify_session
from orderflow_lab.synthetic import generate_session, load_session_csvs
from orderflow_lab.validate import audit_session, coverage_seconds


def test_classify_complete_vs_partial():
    ok = classify_session(
        session_id="A",
        n_depth=100,
        n_trade=20,
        coverage_seconds=5.0,
        expected_seconds=5.0,
    )
    assert ok.status is DayStatus.COMPLETE
    assert ok.usable_for_batch_exec is True

    partial = classify_session(
        session_id="B",
        n_depth=10,
        n_trade=2,
        coverage_seconds=1.0,
        expected_seconds=5.0,
    )
    assert partial.status is DayStatus.PARTIAL
    assert partial.usable_for_batch_exec is False


def test_fixture_loads_and_audits():
    depths, trades = load_session_csvs("SYNTH_001")
    merged = merge_trade_before_depth(depths, trades)
    cov = coverage_seconds(merged)
    audit = audit_session(
        depths, trades, merged, session_id="SYNTH_001", expected_seconds=cov
    )
    assert audit["status"]["status"] == "COMPLETE"
    assert audit["merged"]["ok"] is True


def test_market_fills_more_than_limit():
    depths, trades = generate_session(n_depth=80, n_trades=40, seed=3)
    merged = merge_trade_before_depth(depths, trades)
    signals = generate_toy_signals(merged, every_n_trades=4)
    assert signals
    mkt = simulate_market(merged, signals)
    lim = simulate_limit(merged, signals)
    assert mkt.fill_rate >= lim.fill_rate
    assert mkt.fees >= 0 and lim.fees >= 0
    # MARKET should usually fill when depth exists
    assert mkt.n_fills >= 1
