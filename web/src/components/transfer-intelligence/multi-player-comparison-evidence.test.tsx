import {
  screen,
  waitFor,
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
  MultiPlayerComparisonEvidence,
} from "@/components/transfer-intelligence/multi-player-comparison-evidence";
import {
  fetchHeatmapComparison,
  fetchRadarComparison,
} from "@/lib/api/browser-transfer-intelligence";
import type {
  HeatmapComparisonResponse,
  MultiPlayerComparisonCandidateResponse,
  MultiPlayerComparisonPlayerResponse,
  RadarComparisonResponse,
} from "@/lib/api/types";
import {
  renderWithQueryClient,
} from "@/test/render-with-query-client";

vi.mock(
  "@/lib/api/browser-transfer-intelligence",
  () => ({
    fetchHeatmapComparison:
      vi.fn(),
    fetchRadarComparison:
      vi.fn(),
  }),
);

const fetchHeatmapComparisonMock =
  vi.mocked(
    fetchHeatmapComparison,
  );

const fetchRadarComparisonMock =
  vi.mocked(
    fetchRadarComparison,
  );

const target:
  MultiPlayerComparisonPlayerResponse =
  {
    player_id: 978838,
    player_name:
      "Michael Olise",
    position: "M",
  };

const candidates:
  readonly MultiPlayerComparisonCandidateResponse[] =
  [
    {
      player: {
        player_id: 789071,
        player_name:
          "Dani Olmo",
        position: "M",
      },
      evidence: {
        statistical_similarity_pct:
          91,
      },
    },
    {
      player: {
        player_id: 805078,
        player_name:
          "Candidate Without Pair Evidence",
        position: "M",
      },
      evidence: {
        statistical_similarity_pct:
          null,
      },
    },
  ];

function createRadarResponse(
  candidatePlayerId = 789071,
  candidatePlayerName =
    "Dani Olmo",
): RadarComparisonResponse {
  const dimensions = [
    {
      key: "creativity",
      label: "Creativity",
      raw_score: 4.5,
      percentile: 95,
      peer_count: 216,
    },
    {
      key: "progression",
      label: "Progression",
      raw_score: 3.8,
      percentile: 88,
      peer_count: 216,
    },
    {
      key: "ball_security",
      label:
        "Ball Security",
      raw_score: 3.2,
      percentile: 81,
      peer_count: 216,
    },
  ];

  return {
    target: {
      player_id: 978838,
      player_name:
        "Michael Olise",
      position: "M",
      available: true,
      peer_count: 216,
      dimensions,
    },
    candidate: {
      player_id:
        candidatePlayerId,
      player_name:
        candidatePlayerName,
      position: "M",
      available: true,
      peer_count: 216,
      dimensions:
        dimensions.map(
          (dimension) => ({
            ...dimension,
            percentile:
              dimension.percentile -
              10,
          }),
        ),
    },
    comparison: {
      same_position: true,
      overlay_available:
        true,
      reason: null,
    },
  };
}

function createHeatmapResponse(
  candidatePlayerId = 789071,
  candidatePlayerName =
    "Dani Olmo",
): HeatmapComparisonResponse {
  return {
    target: {
      player_id: 978838,
      player_name:
        "Michael Olise",
      available: true,
      grid_width: 2,
      grid_height: 2,
      grid: [
        [0.1, 0.4],
        [0.7, 1],
      ],
      matches_with_heatmap:
        6,
      heatmap_point_count:
        509,
    },
    candidate: {
      player_id:
        candidatePlayerId,
      player_name:
        candidatePlayerName,
      available: true,
      grid_width: 2,
      grid_height: 2,
      grid: [
        [0.2, 0.5],
        [0.6, 0.8],
      ],
      matches_with_heatmap:
        5,
      heatmap_point_count:
        420,
    },
    similarity: {
      available: true,
      heatmap_similarity_score_pct:
        88,
      heatmap_cosine_similarity_pct:
        90,
      occupation_overlap_pct:
        82,
      peak_zone_similarity_pct:
        79,
      peak_zone_distance:
        8.5,
      entropy_similarity_pct:
        84,
    },
  };
}

beforeEach(() => {
  fetchHeatmapComparisonMock
    .mockReset();

  fetchRadarComparisonMock
    .mockReset();
});

describe(
  "MultiPlayerComparisonEvidence",
  () => {
    it(
      "loads one focused candidate pair by default",
      async () => {
        fetchRadarComparisonMock
          .mockResolvedValue(
            createRadarResponse(),
          );

        fetchHeatmapComparisonMock
          .mockResolvedValue(
            createHeatmapResponse(),
          );

        renderWithQueryClient(
          <MultiPlayerComparisonEvidence
            target={target}
            candidates={
              candidates
            }
          />,
        );

        expect(
          await screen.findByRole(
            "img",
            {
              name:
                "Playing style radar comparison for Michael Olise and Dani Olmo",
            },
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByRole(
            "img",
            {
              name:
                "Tournament heatmap for Dani Olmo",
            },
          ),
        ).toBeInTheDocument();

        const radarSelector =
          screen.getByRole(
            "group",
            {
              name:
                "Radar comparison candidate",
            },
          );

        const heatmapSelector =
          screen.getByRole(
            "group",
            {
              name:
                "Heatmap comparison candidate",
            },
          );

        expect(
          within(
            radarSelector,
          ).getByRole(
            "button",
            {
              name:
                "Dani Olmo",
            },
          ),
        ).toHaveAttribute(
          "aria-pressed",
          "true",
        );

        expect(
          within(
            heatmapSelector,
          ).getByRole(
            "button",
            {
              name:
                "Dani Olmo",
            },
          ),
        ).toHaveAttribute(
          "aria-pressed",
          "true",
        );

        expect(
          screen.queryByText(
            "Inspect one candidate pair",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            "Shared position overlay",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            "Measured pair evidence",
          ),
        ).not.toBeInTheDocument();

        expect(
          fetchRadarComparisonMock
            .mock.calls[0]
            ?.slice(0, 2),
        ).toEqual([
          978838,
          789071,
        ]);

        expect(
          fetchHeatmapComparisonMock
            .mock.calls[0]
            ?.slice(0, 2),
        ).toEqual([
          978838,
          789071,
        ]);
      },
    );

    it(
      "switches the focused pair without changing candidate order",
      async () => {
        const user =
          userEvent.setup();

        fetchRadarComparisonMock
          .mockImplementation(
            async (
              _targetPlayerId,
              candidatePlayerId,
            ) =>
              createRadarResponse(
                candidatePlayerId,
                candidatePlayerId ===
                  805078
                  ? "Candidate Without Pair Evidence"
                  : "Dani Olmo",
              ),
          );

        fetchHeatmapComparisonMock
          .mockImplementation(
            async (
              _targetPlayerId,
              candidatePlayerId,
            ) =>
              createHeatmapResponse(
                candidatePlayerId,
                candidatePlayerId ===
                  805078
                  ? "Candidate Without Pair Evidence"
                  : "Dani Olmo",
              ),
          );

        renderWithQueryClient(
          <MultiPlayerComparisonEvidence
            target={target}
            candidates={
              candidates
            }
          />,
        );

        await screen.findByRole(
          "img",
          {
            name:
              "Playing style radar comparison for Michael Olise and Dani Olmo",
          },
        );

        const radarSelector =
          screen.getByRole(
            "group",
            {
              name:
                "Radar comparison candidate",
            },
          );

        const heatmapSelector =
          screen.getByRole(
            "group",
            {
              name:
                "Heatmap comparison candidate",
            },
          );

        await user.click(
          within(
            radarSelector,
          ).getByRole(
            "button",
            {
              name:
                "Candidate Without Pair Evidence",
            },
          ),
        );

        expect(
          within(
            radarSelector,
          ).getByRole(
            "button",
            {
              name:
                "Candidate Without Pair Evidence",
            },
          ),
        ).toHaveAttribute(
          "aria-pressed",
          "true",
        );

        expect(
          within(
            heatmapSelector,
          ).getByRole(
            "button",
            {
              name:
                "Candidate Without Pair Evidence",
            },
          ),
        ).toHaveAttribute(
          "aria-pressed",
          "true",
        );

        expect(
          await screen.findByRole(
            "img",
            {
              name:
                "Playing style radar comparison for Michael Olise and Candidate Without Pair Evidence",
            },
          ),
        ).toBeInTheDocument();

        await waitFor(() => {
          const radarCall =
            fetchRadarComparisonMock
              .mock.calls[
                fetchRadarComparisonMock
                  .mock.calls
                  .length - 1
              ];

          const heatmapCall =
            fetchHeatmapComparisonMock
              .mock.calls[
                fetchHeatmapComparisonMock
                  .mock.calls
                  .length - 1
              ];

          expect(
            radarCall?.slice(
              0,
              2,
            ),
          ).toEqual([
            978838,
            805078,
          ]);

          expect(
            heatmapCall?.slice(
              0,
              2,
            ),
          ).toEqual([
            978838,
            805078,
          ]);
        });
      },
    );

    it(
      "keeps missing measured heatmap evidence explicit",
      async () => {
        fetchRadarComparisonMock
          .mockResolvedValue(
            createRadarResponse(),
          );

        fetchHeatmapComparisonMock
          .mockResolvedValue({
            ...createHeatmapResponse(),
            similarity: {
              available: false,
              heatmap_similarity_score_pct:
                null,
              heatmap_cosine_similarity_pct:
                null,
              occupation_overlap_pct:
                null,
              peak_zone_similarity_pct:
                null,
              peak_zone_distance:
                null,
              entropy_similarity_pct:
                null,
            },
          });

        renderWithQueryClient(
          <MultiPlayerComparisonEvidence
            target={target}
            candidates={
              candidates
            }
          />,
        );

        await screen.findByRole(
          "img",
          {
            name:
              "Tournament heatmap for Dani Olmo",
          },
        );

        expect(
          screen.queryByText(
            "Pair evidence unavailable",
          ),
        ).not.toBeInTheDocument();

        const metrics =
          screen.getByLabelText(
            "Focused heatmap evidence metrics",
          );

        expect(
          withinText(
            metrics,
          ),
        ).not.toContain(
          "0%",
        );

        expect(
          screen.getAllByText(
            "Unavailable",
          ),
        ).toHaveLength(6);
      },
    );

    it(
      "isolates a radar failure and retries it independently",
      async () => {
        const user =
          userEvent.setup();

        fetchRadarComparisonMock
          .mockRejectedValueOnce(
            new Error(
              "Radar service unavailable.",
            ),
          )
          .mockResolvedValue(
            createRadarResponse(),
          );

        fetchHeatmapComparisonMock
          .mockResolvedValue(
            createHeatmapResponse(),
          );

        renderWithQueryClient(
          <MultiPlayerComparisonEvidence
            target={target}
            candidates={
              candidates
            }
          />,
        );

        expect(
          await screen.findByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Radar comparison unavailable",
        );

        expect(
          await screen.findByRole(
            "img",
            {
              name:
                "Tournament heatmap for Dani Olmo",
            },
          ),
        ).toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Retry radar",
            },
          ),
        );

        expect(
          await screen.findByRole(
            "img",
            {
              name:
                "Playing style radar comparison for Michael Olise and Dani Olmo",
            },
          ),
        ).toBeInTheDocument();

        expect(
          fetchRadarComparisonMock,
        ).toHaveBeenCalledTimes(
          2,
        );
      },
    );
  },
);

function withinText(
  element: HTMLElement,
): string {
  return (
    element.textContent ??
    ""
  );
}
