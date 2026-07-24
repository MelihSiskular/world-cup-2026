from __future__ import annotations

from wc26.analytics import transfer_intelligence
from wc26.analytics.transfer_intelligence import (
    TransferAnalysisRequest,
    TransferAnalysisResult,
    TransferModeResult,
    TransferRecommendation,
    run_transfer_analysis,
)
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisRequest as ModelRequest,
)
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisResult as ModelResult,
)
from wc26.analytics.transfer_intelligence.models import (
    TransferModeResult as ModelModeResult,
)
from wc26.analytics.transfer_intelligence.models import (
    TransferRecommendation as ModelRecommendation,
)
from wc26.analytics.transfer_intelligence.service import (
    TransferAnalysisRequest as ServiceRequest,
)
from wc26.analytics.transfer_intelligence.service import (
    run_transfer_analysis as service_runner,
)


def test_package_exports_application_contract() -> None:
    assert TransferAnalysisRequest is ServiceRequest
    assert run_transfer_analysis is service_runner
    assert TransferAnalysisRequest is ModelRequest
    assert TransferAnalysisResult is ModelResult
    assert TransferModeResult is ModelModeResult
    assert TransferRecommendation is ModelRecommendation


def test_package_declares_small_public_api() -> None:
    assert transfer_intelligence.__all__ == [
        "PlayerSearchItem",
        "PlayerSearchRequest",
        "PlayerSearchResult",
        "search_players",
        "TransferAnalysisRequest",
        "TransferAnalysisResult",
        "TransferModeResult",
        "TransferRecommendation",
        "run_transfer_analysis",
    ]
