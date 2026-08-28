import {
  screen,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  MultiPlayerComparison,
} from "@/components/transfer-intelligence/multi-player-comparison";
import {
  fetchMultiPlayerComparison,
} from "@/lib/api/browser-transfer-intelligence";
import type {
  MultiPlayerComparisonResponse,
} from "@/lib/api/types";
import {
  renderWithQueryClient,
} from "@/test/render-with-query-client";

vi.mock(
  "@/components/transfer-intelligence/multi-player-comparison-evidence",
  () => ({
    MultiPlayerComparisonEvidence:
      () => (
        <div>
          Focused pair evidence
        </div>
      ),
  }),
);

vi.mock(
  "@/lib/api/browser-transfer-intelligence",
  () => ({
    fetchMultiPlayerComparison:
      vi.fn(),
  }),
);

const fetchMultiPlayerComparisonMock =
  vi.mocked(
    fetchMultiPlayerComparison,
  );

const response: MultiPlayerComparisonResponse =
  {
    target: {
      player_id: 978838,
      player_name:
        "Michael Olise",
      national_team_name:
        "France",
      position: "M",
      age: 24,
      minutes: 540,
      market_value:
        100_000_000,
      market_value_currency:
        "EUR",
      final_role:
        "Advanced Playmaker",
      player_quality_score:
        91,
      data_reliability_score:
        0.92,
    },
    candidates: [
      {
        player: {
          player_id: 789071,
          player_name:
            "Dani Olmo",
          national_team_name:
            "Spain",
          position: "M",
          age: 28,
          minutes: 480,
          market_value:
            60_000_000,
          market_value_currency:
            "EUR",
          final_role:
            "Advanced Playmaker",
          player_quality_score:
            87,
          data_reliability_score:
            0.9,
        },
        evidence: {
          statistical_similarity_pct:
            91,
          spatial_similarity_pct:
            84,
          heatmap_similarity_score_pct:
            88,
          role_fit_pct: 86,
          market_value_advantage_pct:
            60,
        },
      },
      {
        player: {
          player_id: 805078,
          player_name:
            "Candidate Without Pair Evidence",
          national_team_name:
            "Germany",
          position: "M",
          age: 23,
          minutes: 310,
          market_value:
            35_000_000,
          market_value_currency:
            "EUR",
          final_role:
            "Wide Creator",
          player_quality_score:
            79,
          data_reliability_score:
            0.78,
        },
        evidence: {
          statistical_similarity_pct:
            null,
          spatial_similarity_pct:
            72,
          heatmap_similarity_score_pct:
            null,
          role_fit_pct: 78,
          market_value_advantage_pct:
            70,
        },
      },
    ],
    role_metrics: [
      {
        key: "chance-creation",
        label:
          "Chance creation",
        metrics: [
          {
            key: "goals",
            label: "Goals",
            values: [
              {
                player_id: 978838,
                total: 5,
                per90: 0.83,
              },
              {
                player_id: 789071,
                total: 3,
                per90: 0.56,
              },
              {
                player_id: 805078,
                total: null,
                per90: null,
              },
            ],
          },
        ],
      },
    ],
  };

const identifiers = {
  targetPlayerId: 978838,
  candidatePlayerIds: [
    789071,
    805078,
  ],
} as const;

beforeEach(() => {
  fetchMultiPlayerComparisonMock
    .mockReset();
});

describe(
  "MultiPlayerComparison",
  () => {
    it(
      "renders target and candidates in canonical request order",
      async () => {
        fetchMultiPlayerComparisonMock
          .mockResolvedValue(
            response,
          );

        renderWithQueryClient(
          <MultiPlayerComparison
            identifiers={
              identifiers
            }
          />,
        );

        const table =
          await screen.findByRole(
            "table",
            {
              name:
                "Target-relative comparison overview",
            },
          );

        const roleMetricTable =
          await screen.findByRole(
            "table",
            {
              name:
                "Target final-role metric comparison",
            },
          );

        expect(
          within(
            roleMetricTable,
          ).getByRole(
            "cell",
            {
              name:
                "5 total, 0.83 per 90",
            },
          ),
        ).toHaveTextContent(
          "5 (0.83/90)",
        );

        expect(
          within(
            roleMetricTable,
          ).getByText(
            "Unavailable",
          ),
        ).toBeInTheDocument();

        const headers =
          within(table)
            .getAllByRole(
              "columnheader",
            );

        expect(
          headers,
        ).toHaveLength(4);

        expect(
          headers[0],
        ).toHaveTextContent(
          "Metric",
        );

        expect(
          within(
            headers[1]!,
          ).getByText(
            "Target",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            headers[1]!,
          ).getByRole(
            "link",
            {
              name:
                "Michael Olise",
            },
          ),
        ).toBeInTheDocument();

        expect(
          within(
            headers[2]!,
          ).getByText(
            "Candidate 1",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            headers[2]!,
          ).getByRole(
            "link",
            {
              name:
                "Dani Olmo",
            },
          ),
        ).toBeInTheDocument();

        expect(
          within(
            headers[3]!,
          ).getByText(
            "Candidate 2",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            headers[3]!,
          ).getByRole(
            "link",
            {
              name:
                "Candidate Without Pair Evidence",
            },
          ),
        ).toBeInTheDocument();

        expect(
          fetchMultiPlayerComparisonMock,
        ).toHaveBeenCalledTimes(
          1,
        );

        const call =
          fetchMultiPlayerComparisonMock
            .mock.calls[0];

        expect(call?.[0]).toBe(
          978838,
        );

        expect(call?.[1]).toEqual([
          789071,
          805078,
        ]);
      },
    );

    it(
      "keeps missing pair evidence explicitly unavailable",
      async () => {
        fetchMultiPlayerComparisonMock
          .mockResolvedValue(
            response,
          );

        renderWithQueryClient(
          <MultiPlayerComparison
            identifiers={
              identifiers
            }
          />,
        );

        const table =
          await screen.findByRole(
            "table",
            {
              name:
                "Target-relative comparison overview",
            },
          );

        const statisticalRow =
          within(table).getByRole(
            "row",
            {
              name:
                /Statistical similarity/i,
            },
          );

        const heatmapRow =
          within(table).getByRole(
            "row",
            {
              name:
                /Heatmap similarity/i,
            },
          );

        expect(
          within(
            statisticalRow,
          ).getByText(
            "Unavailable",
          ),
        ).toBeInTheDocument();

        expect(
          within(
            heatmapRow,
          ).getByText(
            "Unavailable",
          ),
        ).toBeInTheDocument();

        expect(
          statisticalRow,
        ).not.toHaveTextContent(
          "0%",
        );

        expect(
          heatmapRow,
        ).not.toHaveTextContent(
          "0%",
        );
      },
    );

    it(
      "announces the loading state",
      () => {
        fetchMultiPlayerComparisonMock
          .mockImplementation(
            () =>
              new Promise(
                () => {
                  // Keep the request pending.
                },
              ),
          );

        renderWithQueryClient(
          <MultiPlayerComparison
            identifiers={
              identifiers
            }
          />,
        );

        expect(
          screen.getByRole(
            "status",
            {
              name:
                "Preparing multi-player comparison",
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "surfaces an error and retries the overview request",
      async () => {
        const user =
          userEvent.setup();

        fetchMultiPlayerComparisonMock
          .mockRejectedValueOnce(
            new Error(
              "Comparison service unavailable.",
            ),
          )
          .mockResolvedValue(
            response,
          );

        renderWithQueryClient(
          <MultiPlayerComparison
            identifiers={
              identifiers
            }
          />,
        );

        expect(
          await screen.findByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Comparison service unavailable.",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Retry comparison",
            },
          ),
        );

        expect(
          await screen.findByRole(
            "table",
            {
              name:
                "Target-relative comparison overview",
            },
          ),
        ).toBeInTheDocument();

        expect(
          fetchMultiPlayerComparisonMock,
        ).toHaveBeenCalledTimes(
          2,
        );
      },
    );
  },
);
