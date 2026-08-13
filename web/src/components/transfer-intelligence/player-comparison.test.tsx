import {
  screen,
  within,
} from "@testing-library/react";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  PlayerComparison,
} from "@/components/transfer-intelligence/player-comparison";
import {
  runTransferAnalysis,
} from "@/lib/api/browser-transfer-intelligence";
import type {
  TransferAnalysisResponse,
  TransferRecommendationResponse,
} from "@/lib/api/types";
import {
  DEFAULT_TRANSFER_ANALYSIS_VALUES,
} from "@/lib/transfer-intelligence/analysis-form";
import {
  renderWithQueryClient,
} from "@/test/render-with-query-client";

vi.mock(
  "@/lib/api/browser-transfer-intelligence",
  () => ({
    runTransferAnalysis:
      vi.fn(),
  }),
);

const runTransferAnalysisMock =
  vi.mocked(
    runTransferAnalysis,
  );

function createResponse(
  includeCandidate: boolean,
  recommendationOverrides:
    Partial<TransferRecommendationResponse> = {},
): TransferAnalysisResponse {
  const recommendation =
    includeCandidate
      ? [
          {
            player_id:
              12345,
            player_name:
              "Test Candidate",
            national_team_name:
              "Test Nation",
            position: "M",
            age: 23,
            minutes: 500,
            weighted_rating:
              7.1,
            market_value:
              50_000_000,
            market_value_currency:
              "EUR",
            final_role:
              "Central Creator",
            archetype:
              "Wide Creator",
            statistical_similarity_pct:
              72.5,
            spatial_similarity_pct:
              61.2,
            heatmap_similarity_score_pct:
              88.4,
            role_fit_pct:
              79.5,
            market_value_advantage_pct:
              82.6,
            immediate_score:
              74.3,
            immediate_rank:
              2,
            recommendation_type:
              "Strong tactical alternative",
            recommendation_strength:
              "Strong",
            why_recommended:
              "Strong tactical and spatial evidence.",
            ...recommendationOverrides,
          },
        ]
      : [];

  return {
    target: {
      player_id: 978838,
      player_name:
        "Michael Olise",
      national_team_name:
        "France",
      position: "M",
      age: 24.6,
      minutes: 650,
      weighted_rating:
        7.35,
      market_value:
        144_000_000,
      market_value_currency:
        "EUR",
      final_role:
        "Central Half-Space Creator",
      archetype:
        "Wide Creator",
    },

    modes: {
      immediate: {
        mode:
          "immediate",
        recommendations:
          recommendation,
      },
      development: {
        mode:
          "development",
        recommendations: [],
      },
      value: {
        mode: "value",
        recommendations: [],
      },
      short_term: {
        mode:
          "short_term",
        recommendations: [],
      },
    },
  } as unknown as TransferAnalysisResponse;
}

describe(
  "PlayerComparison",
  () => {
    beforeEach(() => {
      runTransferAnalysisMock
        .mockReset();
    });

    it(
      "shows a candidate-unavailable state",
      async () => {
        runTransferAnalysisMock
          .mockResolvedValue(
            createResponse(
              false,
            ),
          );

        renderWithQueryClient(
          <PlayerComparison
            targetPlayerId={
              978838
            }
            candidatePlayerId={
              12345
            }
            mode="immediate"
            values={{
              ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
            }}
          />,
        );

        expect(
          await screen.findByText(
            "This candidate is no longer eligible",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Return to recommendations",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/analysis/978838/results?minimum_minutes=150&minimum_role_confidence=50&neutral_heatmap_score=70&mode=immediate",
        );
      },
    );

    it(
      "keeps spatial and heatmap similarity separate",
      async () => {
        runTransferAnalysisMock
          .mockResolvedValue(
            createResponse(
              true,
            ),
          );

        renderWithQueryClient(
          <PlayerComparison
            targetPlayerId={
              978838
            }
            candidatePlayerId={
              12345
            }
            mode="immediate"
            values={{
              ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
            }}
          />,
        );

        expect(
          await screen.findByRole(
            "heading",
            {
              name:
                "Test Candidate",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Spatial similarity",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "61.2%",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Heatmap similarity",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "88.4%",
          ),
        ).toBeInTheDocument();
      },
    );
        it(
      "does not present the neutral heatmap fallback as measured similarity",
      async () => {
        runTransferAnalysisMock
          .mockResolvedValue(
            createResponse(
              true,
              {
                heatmap_similarity_score_pct:
                  null,
                effective_heatmap_score_pct:
                  70,
                has_heatmap_similarity:
                  false,
              },
            ),
          );

        renderWithQueryClient(
          <PlayerComparison
            targetPlayerId={978838}
            candidatePlayerId={12345}
            mode="immediate"
            values={{
              ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
            }}
          />,
        );

        const heatmapLabel =
          await screen.findByText(
            "Heatmap similarity",
          );

        const heatmapMetric =
          heatmapLabel.closest(
            "article",
          );

        if (!heatmapMetric) {
          throw new Error(
            "Heatmap similarity metric not found",
          );
        }

        expect(
          within(
            heatmapMetric,
          ).getByText(
            "Not reported",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            heatmapMetric,
          ).queryByText(
            "70%",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "keeps measured zero heatmap similarity distinct from missing evidence",
      async () => {
        runTransferAnalysisMock
          .mockResolvedValue(
            createResponse(
              true,
              {
                heatmap_similarity_score_pct:
                  0,
                effective_heatmap_score_pct:
                  0,
                has_heatmap_similarity:
                  true,
              },
            ),
          );

        renderWithQueryClient(
          <PlayerComparison
            targetPlayerId={978838}
            candidatePlayerId={12345}
            mode="immediate"
            values={{
              ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
            }}
          />,
        );

        const heatmapLabel =
          await screen.findByText(
            "Heatmap similarity",
          );

        const heatmapMetric =
          heatmapLabel.closest(
            "article",
          );

        if (!heatmapMetric) {
          throw new Error(
            "Heatmap similarity metric not found",
          );
        }

        expect(
          within(
            heatmapMetric,
          ).getByText(
            "0%",
          ),
        ).toBeInTheDocument();
      },
    );

        it(
      "renders missing candidate identity evidence explicitly",
      async () => {
        runTransferAnalysisMock
          .mockResolvedValue(
            createResponse(
              true,
              {
                market_value: null,
                market_value_currency:
                  null,
                final_role: null,
                archetype: null,
                age: null,
              },
            ),
          );

        renderWithQueryClient(
          <PlayerComparison
            targetPlayerId={978838}
            candidatePlayerId={12345}
            mode="immediate"
            values={{
              ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
            }}
          />,
        );

        const candidateHeading =
          await screen.findByRole(
            "heading",
            {
              name:
                "Test Candidate",
            },
          );

        const candidateCard =
          candidateHeading.closest(
            "article",
          );

        if (!candidateCard) {
          throw new Error(
            "Candidate identity card not found",
          );
        }

        expect(
          within(
            candidateCard,
          ).getByText(
            "Role unavailable",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            candidateCard,
          ).getAllByText(
            "Not reported",
          ).length,
        ).toBeGreaterThanOrEqual(
          2,
        );
      },
    );
  },
);
