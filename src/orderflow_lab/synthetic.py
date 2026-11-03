"""Synthetic L2 + trade generator and CSV loaders.

No exchange credentials. No production captures. Fixtures are tiny and
deterministic so CI / Upwork reviewers can reproduce results offline.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .events import EventKind, MarketEvent, Side

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PACKAGE_ROOT / "data" / "synthetic"


def generate_session(
    *,
    session_id: str = "SYNTH_001",
    start_ts_ns: int = 1_700_000_000_000_000_000,
    n_depth: int = 120,
    n_trades: int = 40,
    mid0: float = 67_500.0,
    tick: float = 0.1,
    depth_dt_ns: int = 50_000_000,
    seed: int = 7,
) -> tuple[list[MarketEvent], list[MarketEvent]]:
    """Build a short, reproducible synthetic session.

    Depth updates walk a noisy mid; trades print at the touch with a
    modest buyer/seller mix. Local timestamps lag exchange time by a
    few milliseconds to mimic feed delay (still synthetic).
    """
    rng = np.random.default_rng(seed)
    depths: list[MarketEvent] = []
    mid = mid0
    for i in range(n_depth):
        mid = mid + float(rng.normal(0.0, tick))
        bid = round(mid - tick, 1)
        # Represent top-of-book as a single DEPTH row (bid side qty).
        exch = start_ts_ns + i * depth_dt_ns
        local = exch + int(rng.integers(1_000_000, 3_000_000))  # 1–3 ms
        depths.append(
            MarketEvent(
                kind=EventKind.DEPTH,
                exch_ts=exch,
                local_ts=local,
                price=bid,
                qty=round(float(rng.uniform(0.2, 2.5)), 4),
                side=Side.BUY,
                seq=i + 1,
            )
        )

    trades: list[MarketEvent] = []
    trade_times = sorted(
        rng.choice(
            np.arange(start_ts_ns, start_ts_ns + n_depth * depth_dt_ns, depth_dt_ns),
            size=n_trades,
            replace=True,
        ).tolist()
    )
    for j, exch in enumerate(trade_times):
        # Align some trades onto depth timestamps to exercise tie-breaks.
        if j % 5 == 0 and depths:
            exch = depths[min(j, len(depths) - 1)].exch_ts
        is_buy = bool(rng.random() > 0.48)
        px = round(mid0 + float(rng.normal(0.0, tick)), 1)
        trades.append(
            MarketEvent(
                kind=EventKind.TRADE,
                exch_ts=int(exch),
                local_ts=int(exch),  # Vision-style: local_ts == exch_ts until latency proxy
                price=px,
                qty=round(float(rng.uniform(0.001, 0.25)), 4),
                side=Side.BUY if is_buy else Side.SELL,
                seq=j + 1,
            )
        )
    trades.sort(key=lambda e: (e.exch_ts, 0 if e.side is Side.BUY else 1))
    return depths, trades


def events_to_frame(events: list[MarketEvent]) -> pd.DataFrame:
    rows = [
        {
            "kind": e.kind.value,
            "exch_ts": e.exch_ts,
            "local_ts": e.local_ts,
            "price": e.price,
            "qty": e.qty,
            "side": e.side.value,
            "seq": e.seq,
        }
        for e in events
    ]
    return pd.DataFrame(rows)


def frame_to_events(df: pd.DataFrame) -> list[MarketEvent]:
    out: list[MarketEvent] = []
    for row in df.itertuples(index=False):
        out.append(
            MarketEvent(
                kind=EventKind(str(row.kind)),
                exch_ts=int(row.exch_ts),
                local_ts=int(row.local_ts),
                price=float(row.price),
                qty=float(row.qty),
                side=Side(str(row.side)),
                seq=int(row.seq),
            )
        )
    return out


def write_session_csvs(
    depths: list[MarketEvent],
    trades: list[MarketEvent],
    out_dir: Path | None = None,
    session_id: str = "SYNTH_001",
) -> dict[str, Path]:
    out_dir = Path(out_dir or DEFAULT_DATA_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    depth_path = out_dir / f"{session_id}_depth.csv"
    trade_path = out_dir / f"{session_id}_trades.csv"
    events_to_frame(depths).to_csv(depth_path, index=False)
    events_to_frame(trades).to_csv(trade_path, index=False)
    meta = out_dir / f"{session_id}_meta.txt"
    meta.write_text(
        "synthetic=true\nsource=generated_offline\nno_exchange_credentials=true\n",
        encoding="utf-8",
    )
    return {"depth": depth_path, "trades": trade_path, "meta": meta}


def load_session_csvs(
    session_id: str = "SYNTH_001",
    data_dir: Path | None = None,
) -> tuple[list[MarketEvent], list[MarketEvent]]:
    data_dir = Path(data_dir or DEFAULT_DATA_DIR)
    depth_df = pd.read_csv(data_dir / f"{session_id}_depth.csv")
    trade_df = pd.read_csv(data_dir / f"{session_id}_trades.csv")
    return frame_to_events(depth_df), frame_to_events(trade_df)
