# crypto-orderflow-backtest-lab

**Technical portfolio demo** for crypto trading systems & market-data engineering in Python.

This repository shows clean, testable plumbing for:

- validating chronological order-book / trade event streams  
- merging DEPTH + TRADE feeds with a TRADE-before-DEPTH tie-break  
- applying a **trade-feed latency proxy** without mutating DEPTH arrival times  
- comparing toy **MARKET vs LIMIT** fills with explicit fees  

> **Not a trading strategy.**  
> Data are **synthetic**. Numbers in the demo are **not** proof of edge or live performance.

---

## Why this exists

Clients on marketplaces like Upwork often need someone who can:

1. keep microstructure data **honest** (partial days stay partial),  
2. build **reproducible** research / backtest pipelines, and  
3. reason about **latency, fees, and fill realism** — not only signal code.

This lab is a compact, public-safe sample of that skill set.

---

## Quick start

```bash
cd crypto-orderflow-backtest-lab
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
python examples/run_demo.py
# or: orderflow-demo
```

Expected demo highlights:

- session status `COMPLETE` on the bundled synthetic fixture  
- latency variant `+128 ms` on trade `local_ts` with exch/px/qty preserved  
- MARKET fill-rate ≫ LIMIT fill-rate on the same toy signals  
- fee drag visible in the summary table  

---

## Project layout

```
src/orderflow_lab/     # library code
data/synthetic/        # tiny CSV fixtures (no exchange credentials)
examples/run_demo.py   # one-command human-readable demo
tests/                 # pytest
docs/METHODOLOGY.md    # honest scope / non-claims
```

---

## What the demo measures

| Component | Behavior |
|-----------|----------|
| Validation | Non-decreasing `exch_ts` / `local_ts`; event counts |
| Merge | Sort by exchange time; trades before depth on ties |
| Latency | `local_ts := exch_ts + N ms` for trades only |
| MARKET | Immediate fill at touch ± slip; taker-style fee |
| LIMIT | Rest at touch; fill only if a later opposing trade crosses |

Details and non-claims: [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

---

## Safety & publishing notes

- No API keys, passwords, SSH configs, or `.env` files are included.  
- No production captures from private bots or VPS loggers.  
- MIT licensed; dependencies are common open-source libraries (numpy, pandas, pytest).  

If you fork this for client work, replace synthetic CSVs with **your** licensed data feeds and keep secrets out of git.

---

## License

MIT — see [`LICENSE`](LICENSE).
