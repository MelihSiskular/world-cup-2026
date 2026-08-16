import { screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PlayerComparison } from "@/components/transfer-intelligence/player-comparison";
import {
  fetchHeatmapComparison,
  fetchRadarComparison,
  runTransferAnalysis,
} from "@/lib/api/browser-transfer-intelligence";
import type {
  HeatmapComparisonResponse,
  RadarComparisonResponse,
  TransferAnalysisResponse,
  TransferRecommendationResponse,
} from "@/lib/api/types";
import { DEFAULT_TRANSFER_ANALYSIS_VALUES } from "@/lib/transfer-intelligence/analysis-form";
import { renderWithQueryClient } from "@/test/render-with-query-client";

vi.mock("@/lib/api/browser-transfer-intelligence", () => ({
  fetchHeatmapComparison: vi.fn(),
  fetchRadarComparison: vi.fn(),
  runTransferAnalysis: vi.fn(),
}));

const fetchHeatmapComparisonMock = vi.mocked(fetchHeatmapComparison);

const fetchRadarComparisonMock = vi.mocked(fetchRadarComparison);

const runTransferAnalysisMock = vi.mocked(runTransferAnalysis);

function createResponse(
  includeCandidate: boolean,
  recommendationOverrides: Partial<TransferRecommendationResponse> = {},
): TransferAnalysisResponse {
  const recommendation = includeCandidate
    ? [
        {
          player_id: 12345,
          player_name: "Test Candidate",
          national_team_name: "Test Nation",
          position: "M",
          age: 23,
          minutes: 500,
          weighted_rating: 7.1,
          market_value: 50_000_000,
          market_value_currency: "EUR",
          final_role: "Central Creator",
          archetype: "Wide Creator",
          statistical_similarity_pct: 72.5,
          spatial_similarity_pct: 61.2,
          weighted_mean_x: 61.8,
          weighted_mean_y: 43.2,
          weighted_x_std: 6.4,
          weighted_y_std: 7.1,
          lateral_profile_similarity_pct: 81.4,
          vertical_profile_similarity_pct: 76.2,
          heatmap_similarity_score_pct: 88.4,
          role_fit_pct: 79.5,
          market_value_advantage_pct: 82.6,
          immediate_score: 74.3,
          immediate_rank: 2,
          recommendation_type: "Strong tactical alternative",
          recommendation_strength: "Strong",
          why_recommended: "Strong tactical and spatial evidence.",
          ...recommendationOverrides,
        },
      ]
    : [];

  return {
    target: {
      player_id: 978838,
      player_name: "Michael Olise",
      national_team_name: "France",
      position: "M",
      age: 24.6,
      minutes: 650,
      weighted_rating: 7.35,
      market_value: 144_000_000,
      market_value_currency: "EUR",
      final_role: "Central Half-Space Creator",
      archetype: "Wide Creator",
      spatial_role: "Advanced Central Zone",
      lateral_profile: "Central Lane",
      vertical_profile: "Advanced Middle Third",
      mobility_profile: "Positionally Stable",
      role_confidence_pct: 87.2,
      weighted_mean_x: 58.7,
      weighted_mean_y: 49.1,
      weighted_x_std: 5.8,
      weighted_y_std: 6.2,
    },

    modes: {
      immediate: {
        mode: "immediate",
        recommendations: recommendation,
      },
      development: {
        mode: "development",
        recommendations: [],
      },
      value: {
        mode: "value",
        recommendations: [],
      },
      short_term: {
        mode: "short_term",
        recommendations: [],
      },
    },
  } as unknown as TransferAnalysisResponse;
}

function createHeatmapResponse(
  similarityScore: number | null = 90.9,
): HeatmapComparisonResponse {
  return {
    target: {
      player_id: 978838,
      player_name: "Michael Olise",
      available: true,
      grid_width: 2,
      grid_height: 2,
      grid: [
        [0.1, 0.2],
        [0.3, 0.4],
      ],
      matches_with_heatmap: 6,
      heatmap_point_count: 509,
      weighted_mean_x: 61.3,
      weighted_mean_y: 41.2,
      peak_cell_x: 62.5,
      peak_cell_y: 42.5,
      heatmap_entropy: 0.944,
    },

    candidate: {
      player_id: 12345,
      player_name: "Test Candidate",
      available: true,
      grid_width: 2,
      grid_height: 2,
      grid: [
        [0.05, 0.1],
        [0.2, 0.35],
      ],
      matches_with_heatmap: 5,
      heatmap_point_count: 320,
      weighted_mean_x: 59.2,
      weighted_mean_y: 43.4,
      peak_cell_x: 57.5,
      peak_cell_y: 42.5,
      heatmap_entropy: 0.921,
    },

    similarity: {
      available: similarityScore !== null,
      heatmap_similarity_score_pct: similarityScore,
      heatmap_cosine_similarity_pct: similarityScore === null ? null : 92.8,
      occupation_overlap_pct: similarityScore === null ? null : 81.4,
      peak_zone_similarity_pct: similarityScore === null ? null : 93.9,
      peak_zone_distance: similarityScore === null ? null : 8.6,
      entropy_similarity_pct: similarityScore === null ? null : 98.8,
      target_matches_with_heatmap: similarityScore === null ? null : 6,
      candidate_matches_with_heatmap: similarityScore === null ? null : 5,
      target_heatmap_points: similarityScore === null ? null : 509,
      candidate_heatmap_points: similarityScore === null ? null : 320,
    },
  };
}

function createRadarResponse(
  overlayAvailable = true,
): RadarComparisonResponse {
  const targetDimensions = [
    {
      key: "creativity",
      label: "Creativity",
      raw_score: 4.516,
      percentile: 100,
      peer_count: 216,
    },
    {
      key: "progression",
      label: "Progression",
      raw_score: 2.87,
      percentile: 98.6,
      peer_count: 216,
    },
    {
      key: "dribbling",
      label: "Dribbling",
      raw_score: 1.626,
      percentile: 94,
      peer_count: 216,
    },
  ];

  const candidateDimensions = overlayAvailable
    ? [
        {
          key: "creativity",
          label: "Creativity",
          raw_score: 1.604,
          percentile: 91.7,
          peer_count: 216,
        },
        {
          key: "progression",
          label: "Progression",
          raw_score: 0.115,
          percentile: 60.6,
          peer_count: 216,
        },
        {
          key: "dribbling",
          label: "Dribbling",
          raw_score: 0.621,
          percentile: 79.2,
          peer_count: 216,
        },
      ]
    : [
        {
          key: "finishing",
          label: "Finishing",
          raw_score: 1.2,
          percentile: 88,
          peer_count: 75,
        },
        {
          key: "shooting_volume",
          label: "Shooting Volume",
          raw_score: 0.9,
          percentile: 82,
          peer_count: 75,
        },
        {
          key: "off_ball_threat",
          label: "Off Ball Threat",
          raw_score: 0.7,
          percentile: 76,
          peer_count: 75,
        },
      ];

  return {
    target: {
      player_id: 978838,
      player_name: "Michael Olise",
      position: "M",
      available: true,
      peer_count: 216,
      dimensions: targetDimensions,
    },
    candidate: {
      player_id: 12345,
      player_name: "Test Candidate",
      position: overlayAvailable
        ? "M"
        : "F",
      available: true,
      peer_count: overlayAvailable
        ? 216
        : 75,
      dimensions: candidateDimensions,
    },
    comparison: {
      same_position: overlayAvailable,
      overlay_available: overlayAvailable,
      reason: overlayAvailable
        ? null
        : "different_position_profiles",
    },
  };
}


describe("PlayerComparison", () => {
  beforeEach(() => {
    fetchHeatmapComparisonMock.mockReset();

    fetchRadarComparisonMock.mockReset();

    runTransferAnalysisMock.mockReset();

    fetchHeatmapComparisonMock.mockResolvedValue(createHeatmapResponse());

    fetchRadarComparisonMock.mockResolvedValue(createRadarResponse());
  });

  it("shows a candidate-unavailable state", async () => {
    runTransferAnalysisMock.mockResolvedValue(createResponse(false));

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

    expect(
      await screen.findByText("This candidate is no longer eligible"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", {
        name: "Return to recommendations",
      }),
    ).toHaveAttribute(
      "href",
      "/analysis/978838/results?minimum_minutes=150&minimum_role_confidence=50&neutral_heatmap_score=70&mode=immediate",
    );
  });

  it("keeps spatial and heatmap similarity separate", async () => {
    runTransferAnalysisMock.mockResolvedValue(createResponse(true));

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

    expect(
      await screen.findByRole("heading", {
        name: "Test Candidate",
      }),
    ).toBeInTheDocument();

    const comparisonIndicators = screen.getByRole("region", {
      name: "Comparison indicators",
    });

    expect(
      within(comparisonIndicators).getByText("Spatial similarity"),
    ).toBeInTheDocument();

    expect(within(comparisonIndicators).getByText("61.2%")).toBeInTheDocument();

    expect(
      within(comparisonIndicators).getByText("Heatmap similarity"),
    ).toBeInTheDocument();

    expect(within(comparisonIndicators).getByText("88.4%")).toBeInTheDocument();
  });
  it("does not present the neutral heatmap fallback as measured similarity", async () => {
    runTransferAnalysisMock.mockResolvedValue(
      createResponse(true, {
        heatmap_similarity_score_pct: null,
        effective_heatmap_score_pct: 70,
        has_heatmap_similarity: false,
      }),
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

    const heatmapLabel = await screen.findByText("Heatmap similarity");

    const heatmapMetric = heatmapLabel.closest("article");

    if (!heatmapMetric) {
      throw new Error("Heatmap similarity metric not found");
    }

    expect(within(heatmapMetric).getByText("Not reported")).toBeInTheDocument();

    expect(within(heatmapMetric).queryByText("70%")).not.toBeInTheDocument();
  });

  it("keeps measured zero heatmap similarity distinct from missing evidence", async () => {
    runTransferAnalysisMock.mockResolvedValue(
      createResponse(true, {
        heatmap_similarity_score_pct: 0,
        effective_heatmap_score_pct: 0,
        has_heatmap_similarity: true,
      }),
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

    const heatmapLabel = await screen.findByText("Heatmap similarity");

    const heatmapMetric = heatmapLabel.closest("article");

    if (!heatmapMetric) {
      throw new Error("Heatmap similarity metric not found");
    }

    expect(within(heatmapMetric).getByText("0%")).toBeInTheDocument();
  });

  it("renders tactical and spatial visual comparison", async () => {
    runTransferAnalysisMock.mockResolvedValue(createResponse(true));

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

    expect(
      await screen.findByText("Tactical role alignment"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("img", {
        name: "Spatial position comparison for Michael Olise and Test Candidate",
      }),
    ).toBeInTheDocument();

    expect(screen.getByText("Lateral similarity")).toBeInTheDocument();

    expect(screen.getByText("81.4%")).toBeInTheDocument();

    expect(screen.getByText("Vertical similarity")).toBeInTheDocument();

    expect(screen.getByText("76.2%")).toBeInTheDocument();

    expect(screen.getByTestId("target-spatial-position")).toBeInTheDocument();

    expect(
      screen.getByTestId("candidate-spatial-position"),
    ).toBeInTheDocument();
  });

  it("renders missing candidate identity evidence explicitly", async () => {
    runTransferAnalysisMock.mockResolvedValue(
      createResponse(true, {
        market_value: null,
        market_value_currency: null,
        final_role: null,
        archetype: null,
        age: null,
      }),
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

    const candidateHeading = await screen.findByRole("heading", {
      name: "Test Candidate",
    });

    const candidateCard = candidateHeading.closest("article");

    if (!candidateCard) {
      throw new Error("Candidate identity card not found");
    }

    expect(
      within(candidateCard).getByText("Role unavailable"),
    ).toBeInTheDocument();

    expect(
      within(candidateCard).getAllByText("Not reported").length,
    ).toBeGreaterThanOrEqual(2);
  });
  it("renders measured tournament heatmaps", async () => {
    runTransferAnalysisMock.mockResolvedValue(createResponse(true));

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

    expect(
      await screen.findByRole("heading", {
        name: "Measured tournament occupation",
      }),
    ).toBeInTheDocument();

    expect(fetchHeatmapComparisonMock).toHaveBeenCalledTimes(1);

    expect(fetchHeatmapComparisonMock.mock.calls[0]?.[0]).toBe(978838);

    expect(fetchHeatmapComparisonMock.mock.calls[0]?.[1]).toBe(12345);

    const heatmapRegion = screen.getByRole("region", {
      name: "Heatmap profile comparison",
    });

    expect(
      await within(heatmapRegion).findByRole("img", {
        name: "Tournament heatmap for Michael Olise",
      }),
    ).toBeInTheDocument();

    expect(
      within(heatmapRegion).getByRole("img", {
        name: "Tournament heatmap for Test Candidate",
      }),
    ).toBeInTheDocument();

    expect(
      within(heatmapRegion).getByText("Measured pair evidence"),
    ).toBeInTheDocument();

    expect(within(heatmapRegion).getByText("90.9%")).toBeInTheDocument();

    expect(within(heatmapRegion).getByText("92.8%")).toBeInTheDocument();

    expect(within(heatmapRegion).getByText("81.4%")).toBeInTheDocument();
  });

  it("keeps heatmap failure isolated from the main comparison", async () => {
    runTransferAnalysisMock.mockResolvedValue(createResponse(true));

    fetchHeatmapComparisonMock.mockRejectedValue(
      new Error("Heatmap service unavailable"),
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

    expect(
      await screen.findByRole("heading", {
        name: "Test Candidate",
      }),
    ).toBeInTheDocument();

    expect(
      await screen.findByText("Heatmap comparison unavailable"),
    ).toBeInTheDocument();

    expect(screen.getByText("Performance context")).toBeInTheDocument();

    expect(
      screen.queryByText("The player comparison could not be prepared"),
    ).not.toBeInTheDocument();
  });
  it("renders a shared same-position radar overlay", async () => {
    runTransferAnalysisMock.mockResolvedValue(createResponse(true));

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

    const radarRegion = await screen.findByRole(
      "region",
      {
        name: "Playing style radar comparison",
      },
    );

    expect(
      fetchRadarComparisonMock,
    ).toHaveBeenCalledTimes(1);

    expect(
      fetchRadarComparisonMock.mock.calls[0]?.[0],
    ).toBe(978838);

    expect(
      fetchRadarComparisonMock.mock.calls[0]?.[1],
    ).toBe(12345);

    expect(
      await within(radarRegion).findByText(
        "Shared position overlay",
      ),
    ).toBeInTheDocument();

    expect(
      within(radarRegion).getByRole(
        "img",
        {
          name:
            "Playing style radar comparison for Michael Olise and Test Candidate",
        },
      ),
    ).toBeInTheDocument();

    expect(
      within(radarRegion).getByTestId(
        "radar-polygon-primary",
      ),
    ).toBeInTheDocument();

    expect(
      within(radarRegion).getByTestId(
        "radar-polygon-secondary",
      ),
    ).toBeInTheDocument();
  });

  it("renders cross-position radar profiles separately", async () => {
    runTransferAnalysisMock.mockResolvedValue(createResponse(true));

    fetchRadarComparisonMock.mockResolvedValue(
      createRadarResponse(false),
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

    const radarRegion = await screen.findByRole(
      "region",
      {
        name: "Playing style radar comparison",
      },
    );

    expect(
      await within(radarRegion).findByText(
        "Separate position profiles",
      ),
    ).toBeInTheDocument();

    expect(
      within(radarRegion).getByRole(
        "img",
        {
          name:
            "Playing style radar for Michael Olise",
        },
      ),
    ).toBeInTheDocument();

    expect(
      within(radarRegion).getByRole(
        "img",
        {
          name:
            "Playing style radar for Test Candidate",
        },
      ),
    ).toBeInTheDocument();

    expect(
      within(radarRegion).queryByRole(
        "img",
        {
          name:
            "Playing style radar comparison for Michael Olise and Test Candidate",
        },
      ),
    ).not.toBeInTheDocument();
  });

  it("keeps radar failure isolated from the main comparison", async () => {
    runTransferAnalysisMock.mockResolvedValue(createResponse(true));

    fetchRadarComparisonMock.mockRejectedValue(
      new Error("Radar service unavailable"),
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

    expect(
      await screen.findByRole("heading", {
        name: "Test Candidate",
      }),
    ).toBeInTheDocument();

    expect(
      await screen.findByText(
        "Radar comparison unavailable",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Performance context",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        "The player comparison could not be prepared",
      ),
    ).not.toBeInTheDocument();
  });

});
