from __future__ import annotations

from wc26.analytics.transfer_intelligence import reporting
from wc26.analytics.transfer_intelligence.utils import (
    format_market_value,
    format_optional_score,
)


def test_reporting_uses_formatting_utilities() -> None:
    assert reporting.format_market_value is format_market_value
    assert reporting.format_optional_score is format_optional_score
