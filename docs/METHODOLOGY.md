# Methodology (honest scope)

This repository is a **technical portfolio demo**. It shows how a Python
developer can structure crypto microstructure tooling: event validation,
feed merging, latency stress tests, and simple MARKET vs LIMIT fill
accounting.

## What is real (as engineering practice)

- Chronological checks on exchange vs local timestamps
- TRADE-before-DEPTH ordering on equal timestamps
- Explicit COMPLETE / PARTIAL labeling instead of silent “full day” claims
- Separating **feed latency proxies** (shift trade `local_ts`) from
  **book timestamps** (DEPTH `local_ts` left alone)
- Fee-aware fill summaries and fill-rate comparison between order types

## What is synthetic / illustrative

- All market data under `data/synthetic/` is **generated offline**
- Signal timestamps are toy (`every_n_trades`) — **not** a research signal
- LIMIT fills use a simplified “opposing trade crosses rest price” rule —
  not a full exchange matching engine or queue position model
- PnL numbers are accounting demos and **must not** be read as strategy
  performance

## What this project deliberately excludes

- Exchange API keys, `.env` files, SSH / VPS access
- Production order-book captures or private research datasets
- Proprietary strategy rules, frozen research specs, or live trading bots
- Claims of profitability, risk-adjusted edge, or capacity

## Suggested reading order for reviewers

1. `README.md`
2. `examples/run_demo.py` output
3. `src/orderflow_lab/events.py` → `merge.py` → `latency.py` → `execution.py`
4. `tests/` (pytest)
