import {
  screen,
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
  },
);
