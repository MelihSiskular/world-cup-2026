"""
Football Scouting Decision Engine v4

Scenario-specific player replacement recommendations combining:

- statistical similarity
- role fit
- average-position spatial similarity
- tournament heatmap occupation similarity
- player quality
- data reliability
- market-value advantage
- age suitability
- automatic recommendation labels
- automatic, data-driven explanation text

Run
---
python -m src.transfer_intelligence.find_replacements \
  --player "Michael Olise"
"""

from __future__ import annotations

# Compatibility re-exports for existing imports and tests.
# Remove these only as part of an explicitly breaking release.
from wc26.analytics.transfer_intelligence.candidates import (
    prepare_candidate_base as prepare_candidate_base,
)
from wc26.analytics.transfer_intelligence.cli import (
    parse_args as parse_args,
)
from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_FEATURES as DEFAULT_FEATURES,
)
from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_HEATMAP_PROFILES as DEFAULT_HEATMAP_PROFILES,
)
from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_HEATMAP_SIMILARITY as DEFAULT_HEATMAP_SIMILARITY,
)
from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_OUTPUT_DIR as DEFAULT_OUTPUT_DIR,
)
from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_SIMILARITY as DEFAULT_SIMILARITY,
)
from wc26.analytics.transfer_intelligence.config import (
    HEATMAP_METRIC_COLUMNS as HEATMAP_METRIC_COLUMNS,
)
from wc26.analytics.transfer_intelligence.config import (
    MODE_CONFIG as MODE_CONFIG,
)
from wc26.analytics.transfer_intelligence.datasets import (
    load_heatmap_profiles as load_heatmap_profiles,
)
from wc26.analytics.transfer_intelligence.datasets import (
    load_heatmap_similarity as load_heatmap_similarity,
)
from wc26.analytics.transfer_intelligence.datasets import (
    load_similarity as load_similarity,
)
from wc26.analytics.transfer_intelligence.entrypoint import (
    main as run_console,
)
from wc26.analytics.transfer_intelligence.explanations import (
    build_reason as build_reason,
)
from wc26.analytics.transfer_intelligence.explanations import (
    classify_candidate as classify_candidate,
)
from wc26.analytics.transfer_intelligence.explanations import (
    dominant_heatmap_zone as dominant_heatmap_zone,
)
from wc26.analytics.transfer_intelligence.explanations import (
    heatmap_difference_reason as heatmap_difference_reason,
)
from wc26.analytics.transfer_intelligence.explanations import (
    recommendation_strength as recommendation_strength,
)
from wc26.analytics.transfer_intelligence.matching import (
    attach_heatmap_profiles as attach_heatmap_profiles,
)
from wc26.analytics.transfer_intelligence.matching import (
    attach_heatmap_similarity as attach_heatmap_similarity,
)
from wc26.analytics.transfer_intelligence.matching import (
    attach_similarity as attach_similarity,
)
from wc26.analytics.transfer_intelligence.matching import (
    resolve_player as resolve_player,
)
from wc26.analytics.transfer_intelligence.recommendations import (
    filter_for_mode as filter_for_mode,
)
from wc26.analytics.transfer_intelligence.recommendations import (
    generate_mode_results as generate_mode_results,
)
from wc26.analytics.transfer_intelligence.reporting import (
    print_report as print_report,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_age_suitability as calculate_age_suitability,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_market_value_advantage as calculate_market_value_advantage,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_mode_score as calculate_mode_score,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_role_fit as calculate_role_fit,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_spatial_similarity as calculate_spatial_similarity,
)
from wc26.analytics.transfer_intelligence.scoring import (
    same_value_score as same_value_score,
)
from wc26.analytics.transfer_intelligence.utils import (
    format_market_value as format_market_value,
)
from wc26.analytics.transfer_intelligence.utils import (
    format_optional_score as format_optional_score,
)
from wc26.analytics.transfer_intelligence.utils import (
    normalize_text as normalize_text,
)
from wc26.analytics.transfer_intelligence.utils import (
    safe_float as safe_float,
)
from wc26.analytics.transfer_intelligence.utils import (
    slugify as slugify,
)


def main() -> None:
    """Preserve the legacy module entrypoint."""

    run_console()


if __name__ == "__main__":
    main()
