"""CLI demo: validate → merge → latency → MARKET/LIMIT summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .execution import generate_toy_signals, simulate_limit, simulate_market
from .latency import apply_trade_local_latency, summarize_latency
from .merge import merge_trade_before_depth
from .synthetic import DEFAULT_DATA_DIR, load_session_csvs
from .validate import audit_session, coverage_seconds


def run_demo(
    *,
    session_id: str = "SYNTH_001",
    data_dir: Path | None = None,
    delay_ms: int = 128,
    json_out: Path | None = None,
) -> dict:
    depths, trades = load_session_csvs(session_id, data_dir=data_dir)
    merged = merge_trade_before_depth(depths, trades)
    expected = max(coverage_seconds(merged), 1e-9)
    audit = audit_session(
        depths,
        trades,
        merged,
        session_id=session_id,
        expected_seconds=expected,
    )

    delayed = apply_trade_local_latency(merged, delay_ms=delay_ms)
    lat = summarize_latency(merged, delayed)

    signals = generate_toy_signals(delayed, every_n_trades=5)
    mkt = simulate_market(delayed, signals)
    lim = simulate_limit(delayed, signals)

    result = {
        "disclaimer": (
            "Technical demo only. Synthetic data. Not a trading strategy. "
            "No claim of profitability or live-exchange connectivity."
        ),
        "session_id": session_id,
        "audit": audit,
        "latency": {
            "variant": f"B_med_proxy_{delay_ms}ms",
            **lat,
        },
        "execution": {
            "MARKET": {
                "n_signals": mkt.n_signals,
                "n_fills": mkt.n_fills,
                "fill_rate": round(mkt.fill_rate, 4),
                "gross_pnl": round(mkt.gross_pnl, 6),
                "fees": round(mkt.fees, 6),
                "net_pnl": round(mkt.net_pnl, 6),
            },
            "LIMIT": {
                "n_signals": lim.n_signals,
                "n_fills": lim.n_fills,
                "fill_rate": round(lim.fill_rate, 4),
                "gross_pnl": round(lim.gross_pnl, 6),
                "fees": round(lim.fees, 6),
                "net_pnl": round(lim.net_pnl, 6),
            },
        },
    }

    _print_human(result)
    if json_out is not None:
        json_out = Path(json_out)
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote {json_out}")
    return result


def _print_human(result: dict) -> None:
    print("=" * 60)
    print("crypto-orderflow-backtest-lab — demo")
    print("=" * 60)
    print(result["disclaimer"])
    print()
    st = result["audit"]["status"]
    print(f"Session: {result['session_id']}")
    print(
        f"Status:  {st['status']}  "
        f"(depth={st['n_depth']}, trades={st['n_trade']}, "
        f"coverage={st['coverage_seconds']:.3f}s)"
    )
    print(
        f"Latency: +{result['latency']['delay_ms_applied']:.0f} ms on trade "
        f"local_ts | exch/px/qty preserved={result['latency']['exch_ts_preserved']}"
        f"/{result['latency']['px_qty_preserved']} | "
        f"depth unchanged={result['latency']['depth_unchanged']}"
    )
    print()
    print(f"{'Type':<8} {'Signals':>8} {'Fills':>8} {'Fill%':>8} {'Fees':>10} {'Net':>10}")
    print("-" * 60)
    for name in ("MARKET", "LIMIT"):
        e = result["execution"][name]
        print(
            f"{name:<8} {e['n_signals']:>8} {e['n_fills']:>8} "
            f"{100 * e['fill_rate']:>7.1f}% {e['fees']:>10.6f} {e['net_pnl']:>10.6f}"
        )
    print("-" * 60)
    print("Net values are toy accounting on synthetic prints — not performance.")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(
        description="Run the synthetic order-flow backtest lab demo."
    )
    p.add_argument("--session-id", default="SYNTH_001")
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    p.add_argument("--delay-ms", type=int, default=128)
    p.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write the machine-readable summary JSON.",
    )
    args = p.parse_args(argv)
    run_demo(
        session_id=args.session_id,
        data_dir=args.data_dir,
        delay_ms=args.delay_ms,
        json_out=args.json_out,
    )


if __name__ == "__main__":
    main()
