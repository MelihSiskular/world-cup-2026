from __future__ import annotations

from wc26.analytics import transfer_intelligence
from wc26.analytics.transfer_intelligence import (
    TransferAnalysisRequest,
    run_transfer_analysis,
)
from wc26.analytics.transfer_intelligence.service import (
    TransferAnalysisRequest as ServiceRequest,
)
from wc26.analytics.transfer_intelligence.service import (
    run_transfer_analysis as service_runner,
)


def test_package_exports_application_service() -> None:
    assert TransferAnalysisRequest is ServiceRequest
    assert run_transfer_analysis is service_runner


def test_package_declares_small_public_api() -> None:
    assert transfer_intelligence.__all__ == [
        "TransferAnalysisRequest",
        "run_transfer_analysis",
    ]
