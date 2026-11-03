#!/usr/bin/env python3
"""One-command demo entrypoint for reviewers.

Usage (from repo root, after ``pip install -e .``)::

    python examples/run_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orderflow_lab.demo import main  # noqa: E402

if __name__ == "__main__":
    main()
