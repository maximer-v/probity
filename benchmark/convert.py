"""The framework's typed statement as a flat reading, the shape the scorer compares."""

from __future__ import annotations

from typing import Any

from probity.records import Statement


def statement_to_reading(st: Statement) -> dict[str, Any]:
    simple = st.to_simple()
    return {
        "account_id": simple["account_id"] or "",
        "period_start": simple["period_start"] or "",
        "period_end": simple["period_end"] or "",
        "opening_balance": simple["opening_balance"],
        "closing_balance": simple["closing_balance"],
        "tx_count": simple["tx_count"],
        "rows": simple["rows"],
    }
