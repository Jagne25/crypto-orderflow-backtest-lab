# crypto-orderflow-backtest-lab

Technical portfolio demo for **crypto market-data engineering** and **execution plumbing** in Python.

This repository demonstrates:

- chronological validation of DEPTH / TRADE event streams
- merging feeds with a TRADE-before-DEPTH tie-break on equal timestamps
- a trade-feed **latency proxy** that shifts trade `local_ts` without mutating DEPTH arrival times
- a toy **MARKET vs LIMIT** fill simulator with explicit fee accounting

> **Scope.** This is not a trading strategy and not investment advice.  
> Bundled data are **synthetic**. Demo numbers do **not** imply live edge or exchange connectivity.

---

## Quick Start

```bash
git clone https://github.com/Jagne25/crypto-orderflow-backtest-lab.git
cd crypto-orderflow-backtest-lab

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
pytest
python examples/run_demo.py
```

Optional entry point after install:

```bash
orderflow-demo
```

---

## Example Demo Output (Synthetic)

Reproducible summary from `python examples/run_demo.py` on the bundled `SYNTH_001` fixture (+128 ms trade-local latency proxy):

| Order type | Signals | Fills | Fill rate | Fees (toy) | Net (toy) |
|------------|--------:|------:|----------:|-----------:|----------:|
| MARKET     |       8 |     8 |    100.0% |   2.159983 | −2.174983 |
| LIMIT      |       8 |     1 |     12.5% |   0.134999 | −0.134999 |

**How to read this table**

- **Fill rate** — share of toy signals that receive a fill under the demo rules. MARKET crosses the book immediately (high fill rate). LIMIT rests at the touch and fills only if a later opposing public trade crosses the rest price (much lower fill rate here).
- **Fees** — notional × fee rate (taker-style for MARKET, lower maker-style for LIMIT in this demo). Higher MARKET fill count implies higher cumulative fees even when per-fill size is identical.
- **Net** — toy pair-accounting PnL minus fees on synthetic prints. Negative net here is expected and **not** a performance claim; it illustrates fee drag and incomplete LIMIT participation on the same signal clock.

Session checks in the same run: status `COMPLETE`, trade `exch_ts` / price / qty preserved under the latency proxy, DEPTH rows unchanged.

---

## What the Demo Implements

| Component | Behavior |
|-----------|----------|
| Validation | Non-decreasing `exch_ts` / `local_ts` on their respective sorted views; event counts |
| Merge | Sort by exchange time; trades before depth on timestamp ties |
| Latency | `trade.local_ts := exch_ts + N ms`; DEPTH `local_ts` untouched |
| MARKET | Immediate fill at touch ± slip; taker-style fee |
| LIMIT | Rest at touch; fill only if a later opposing trade crosses |

Methodology and non-claims: [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

---

## Related Research Experience

The following topics reflect **ongoing private research and engineering practice**. They are **not** features of this public repository and are **not** shipped as code, configs, or datasets here:

- order-book **imbalance (IMB)** and related microstructure features
- futures **volume / onset-style** signal construction and forward evaluation hygiene
- **OFI** (order-flow imbalance) and **CVD**-style cumulative volume delta analysis
- **HftBacktest**-oriented replay pipelines (depth + trades, event ordering, sanity replay)
- **latency** modeling for trade-feed arrival vs book updates
- **execution** research comparing aggressive vs passive fills, fees, and fill realism

This public lab only exposes a **sanitized, synthetic subset** of the data-integrity and execution-accounting patterns used in that broader work. Proprietary signal rules, frozen research specs, production captures, and private results are intentionally excluded.

---

## Project Layout

```text
src/orderflow_lab/     # library code
data/synthetic/        # tiny generated CSV fixtures (no exchange credentials)
examples/run_demo.py   # one-command human-readable demo
tests/                 # pytest
docs/METHODOLOGY.md    # scope, synthetic limits, non-claims
```

---

## Dependencies

- Python ≥ 3.10
- Runtime: `numpy`, `pandas`
- Dev: `pytest` (`pip install -e ".[dev]"`)

---

## Safety Notes

- No API keys, passwords, SSH configs, or `.env` files
- No production order-book / trade captures
- No proprietary strategy parameters or frozen research artifacts
- MIT license; replace synthetic fixtures with your own licensed data for client deployments and keep secrets out of version control

---

## License

MIT — see [`LICENSE`](LICENSE).
