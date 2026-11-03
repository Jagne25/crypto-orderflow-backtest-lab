from __future__ import annotations

import pytest

from orderflow_lab.events import (
    EventKind,
    MarketEvent,
    Side,
    assert_trade_before_depth,
    trade_before_depth_violations,
    validate_event_stream,
    validate_nondecreasing,
)


def test_validate_nondecreasing_ok():
    validate_nondecreasing([1, 1, 2, 5], label="t")


def test_validate_nondecreasing_raises():
    with pytest.raises(ValueError, match="decreases"):
        validate_nondecreasing([1, 3, 2], label="t")


def test_trade_requires_side():
    with pytest.raises(ValueError):
        MarketEvent(EventKind.TRADE, 1, 1, 100.0, 0.1, Side.NA)


def test_trade_before_depth_detects_violation():
    bad = [
        MarketEvent(EventKind.DEPTH, 10, 10, 100.0, 1.0, Side.BUY, 1),
        MarketEvent(EventKind.TRADE, 10, 10, 100.0, 0.1, Side.BUY, 2),
    ]
    assert trade_before_depth_violations(bad) == 1
    with pytest.raises(ValueError):
        assert_trade_before_depth(bad)


def test_validate_event_stream_counts():
    ev = [
        MarketEvent(EventKind.TRADE, 1, 1, 10.0, 0.1, Side.BUY, 1),
        MarketEvent(EventKind.DEPTH, 2, 2, 10.0, 1.0, Side.BUY, 2),
    ]
    rep = validate_event_stream(ev)
    assert rep["ok"] is True
    assert rep["n_trade"] == 1 and rep["n_depth"] == 1
