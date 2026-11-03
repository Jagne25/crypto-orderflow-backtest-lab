"""Day / session readiness labels used by the demo pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class DayStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    FAIL = "FAIL"


@dataclass(slots=True)
class SessionReport:
    session_id: str
    status: DayStatus
    n_depth: int
    n_trade: int
    coverage_seconds: float
    expected_seconds: float
    usable_for_batch_exec: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


def classify_session(
    *,
    session_id: str,
    n_depth: int,
    n_trade: int,
    coverage_seconds: float,
    expected_seconds: float,
    min_coverage_ratio: float = 0.95,
    min_depth: int = 50,
    min_trades: int = 10,
) -> SessionReport:
    """Honest COMPLETE vs PARTIAL labeling.

    A short synthetic window is COMPLETE when coverage matches the
    *declared* expected length. Real production days use wall-clock
    expectations (e.g. 86400 s); this demo keeps the same idea at toy scale.
    """
    if n_depth <= 0 or n_trade <= 0:
        return SessionReport(
            session_id=session_id,
            status=DayStatus.MISSING,
            n_depth=n_depth,
            n_trade=n_trade,
            coverage_seconds=coverage_seconds,
            expected_seconds=expected_seconds,
            usable_for_batch_exec=False,
            notes="missing depth or trades",
        )

    ratio = coverage_seconds / expected_seconds if expected_seconds > 0 else 0.0
    if n_depth < min_depth or n_trade < min_trades or ratio < min_coverage_ratio:
        return SessionReport(
            session_id=session_id,
            status=DayStatus.PARTIAL,
            n_depth=n_depth,
            n_trade=n_trade,
            coverage_seconds=coverage_seconds,
            expected_seconds=expected_seconds,
            usable_for_batch_exec=False,
            notes=f"coverage_ratio={ratio:.3f}; below COMPLETE thresholds",
        )

    return SessionReport(
        session_id=session_id,
        status=DayStatus.COMPLETE,
        n_depth=n_depth,
        n_trade=n_trade,
        coverage_seconds=coverage_seconds,
        expected_seconds=expected_seconds,
        usable_for_batch_exec=True,
        notes="meets synthetic COMPLETE thresholds",
    )
