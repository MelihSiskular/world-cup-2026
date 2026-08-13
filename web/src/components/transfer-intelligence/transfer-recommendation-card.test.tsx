import {
  render,
  screen,
  within,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
} from "vitest";

import {
  TransferRecommendationCard,
} from "@/components/transfer-intelligence/transfer-recommendation-card";
import type {
  TransferRecommendationResponse,
} from "@/lib/api/types";
import {
  DEFAULT_TRANSFER_ANALYSIS_VALUES,
} from "@/lib/transfer-intelligence/analysis-form";

function createRecommendation():
  TransferRecommendationResponse {
  return {
    player_id: 12345,
    player_name: "Test Candidate",
    national_team_name: "Test Nation",
    country_name: "Test Country",
    position: "M",
    age: 23,
    minutes: 500,
    weighted_rating: 7.1,

    market_value: null,
    market_value_currency: null,

    final_role: null,
    archetype: null,

    statistical_similarity_pct: 72.5,
    spatial_similarity_pct: 61.2,

    heatmap_similarity_score_pct: null,
    effective_heatmap_score_pct: 70,
    has_heatmap_similarity: false,

    role_fit_pct: 79.5,
    market_value_advantage_pct: 82.6,

    immediate_score: 74.3,
    immediate_rank: 2,

    recommendation_type:
      "Strong tactical alternative",
    recommendation_strength: "Strong",
    why_recommended:
      "Strong tactical and spatial evidence.",
  } as unknown as TransferRecommendationResponse;
}

describe(
  "TransferRecommendationCard",
  () => {
    it(
      "keeps decision fallback separate from measured spatial evidence",
      () => {
        render(
          <TransferRecommendationCard
            targetPlayerId={978838}
            mode="immediate"
            analysisValues={{
              ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
            }}
            recommendation={
              createRecommendation()
            }
          />,
        );

        const spatialLabel =
          screen.getByText(
            "Spatial similarity",
          );

        const spatialMetric =
          spatialLabel.closest("div");

        if (!spatialMetric) {
          throw new Error(
            "Spatial similarity metric not found",
          );
        }

        expect(
          within(
            spatialMetric,
          ).getByText("61.2%"),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "70%",
            {
              exact: true,
            },
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "renders missing market and role data explicitly",
      () => {
        render(
          <TransferRecommendationCard
            targetPlayerId={978838}
            mode="immediate"
            analysisValues={{
              ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
            }}
            recommendation={
              createRecommendation()
            }
          />,
        );

        expect(
          screen.getByText(
            "Role unavailable",
          ),
        ).toBeInTheDocument();

        const marketLabel =
          screen.getByText(
            "Market value",
          );

        const marketRow =
          marketLabel.closest("div");

        if (!marketRow) {
          throw new Error(
            "Market value row not found",
          );
        }

        expect(
          within(
            marketRow,
          ).getByText(
            "Not reported",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
