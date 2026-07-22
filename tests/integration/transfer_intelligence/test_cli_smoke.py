"""End-to-end smoke tests for transfer intelligence."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_FEATURES,
    DEFAULT_HEATMAP_PROFILES,
    DEFAULT_HEATMAP_SIMILARITY,
    DEFAULT_SIMILARITY,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_INPUTS = (
    DEFAULT_FEATURES,
    DEFAULT_SIMILARITY,
    DEFAULT_HEATMAP_SIMILARITY,
    DEFAULT_HEATMAP_PROFILES,
)


@pytest.mark.integration
def test_real_transfer_intelligence_cli(
    tmp_path: Path,
) -> None:
    """Run the complete CLI against local processed data."""

    if os.getenv("WC26_RUN_INTEGRATION") != "1":
        pytest.skip("Set WC26_RUN_INTEGRATION=1 to run real-data integration tests.")

    missing_inputs = [path for path in REQUIRED_INPUTS if not (PROJECT_ROOT / path).exists()]

    if missing_inputs:
        missing_text = ", ".join(str(path) for path in missing_inputs)
        pytest.skip(f"Required processed datasets are missing: {missing_text}")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.transfer_intelligence.find_replacements",
            "--player",
            "Michael Olise",
            "--top-n",
            "1",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )

    assert completed.returncode == 0, (
        f"Transfer CLI failed.\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
    )

    assert "FOOTBALL SCOUTING DECISION ENGINE V4" in completed.stdout
    assert "Target Player:" in completed.stdout
    assert "Michael Olise" in completed.stdout
    assert "IMMEDIATE REPLACEMENTS" in completed.stdout
    assert "DEVELOPMENT PROSPECTS" in completed.stdout
    assert "BEST VALUE OPTIONS" in completed.stdout
    assert "SHORT-TERM EXPERIENCED OPTIONS" in completed.stdout

    generated_csv_files = list(tmp_path.rglob("*.csv"))

    assert generated_csv_files, "The pipeline completed but produced no CSV output."
