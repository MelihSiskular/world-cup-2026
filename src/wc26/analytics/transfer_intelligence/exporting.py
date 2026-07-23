"""CSV output adapters for transfer intelligence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisResult,
)
from wc26.analytics.transfer_intelligence.utils import (
    slugify,
)


def export_transfer_csv(
    result: TransferAnalysisResult,
    output_dir: Path,
) -> tuple[Path, ...]:
    """Export non-empty recommendation modes as CSV files."""

    player_name = result.target.get("player_name")

    if not isinstance(player_name, str) or not player_name.strip():
        raise ValueError("Transfer analysis result must contain a valid player_name.")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    player_slug = slugify(player_name)
    exported_files: list[Path] = []

    for mode_result in result.modes:
        if not mode_result.recommendations:
            continue

        records = [recommendation.to_dict() for recommendation in mode_result.recommendations]

        output_path = output_dir / (f"{player_slug}_{mode_result.mode}_recommendations.csv")

        pd.DataFrame(records).to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
        )

        exported_files.append(output_path)

    return tuple(exported_files)


__all__ = [
    "export_transfer_csv",
]
