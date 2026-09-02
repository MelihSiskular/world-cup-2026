import {
  render as renderTestingLibrary,
  screen,
  within,
} from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ComponentProps, ReactElement, ReactNode } from "react";

import englishMessages from "../../../messages/en.json";
import { describe, expect, it, vi } from "vitest";

import { TransferRecommendationCard } from "@/components/transfer-intelligence/transfer-recommendation-card";
import type { TransferRecommendationResponse } from "@/lib/api/types";
import { DEFAULT_TRANSFER_ANALYSIS_VALUES } from "@/lib/transfer-intelligence/analysis-form";

function IntlTestProvider({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <NextIntlClientProvider locale="en" messages={englishMessages}>
      {children}
    </NextIntlClientProvider>
  );
}

function render(element: ReactElement) {
  return renderTestingLibrary(element, {
    wrapper: IntlTestProvider,
  });
}

vi.mock("@/i18n/navigation", () => ({
  Link: (props: ComponentProps<"a">) => <a {...props} />,
}));

vi.mock("@/components/shortlists/shortlist-action", () => ({
  ShortlistAction: ({
    player,
    variant,
  }: Readonly<{
    player: {
      playerName: string;
    };
    variant?: string;
  }>) => (
    <button type="button">
      Save {player.playerName} ({variant ?? "default"})
    </button>
  ),
}));

function createRecommendation(): TransferRecommendationResponse {
  return {
    player_id: 12345,
    player_name: "Test Candidate",
    national_team_name: "Spain",
    country_name: "Spain",
    position: "M",
    age: 28.7,
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

    recommendation_type: "Strong tactical alternative",
    recommendation_strength: "Strong",
    why_recommended: "same final role; strong statistical similarity (72.5%)",
    explainability: {
      mode: "immediate",
      score: {
        weighted_signal_total: 68.3,
        bonus_total: 6,
        pre_clip_score: 74.3,
        final_score: 74.3,
        was_clipped: false,
      },
      signals: [
        {
          key: "statistical_similarity_pct",
          label: "Statistical similarity",
          description: "Similarity across the statistical feature model.",
          source_score: 72.5,
          input_score: 72.5,
          weight: 0.2,
          weighted_contribution: 14.5,
          evidence_status: "available",
          note: null,
        },
        {
          key: "effective_heatmap_score_pct",
          label: "Heatmap evidence",
          description:
            "Heatmap occupation evidence used by the recruitment scoring model.",
          source_score: null,
          input_score: 70,
          weight: 0.12,
          weighted_contribution: 8.4,
          evidence_status: "fallback",
          note: "Direct heatmap evidence is unavailable; the configured neutral fallback is used for scoring.",
        },
      ],
      bonuses: [
        {
          key: "same_final_role",
          label: "Same final role",
          configured_points: 6,
          applied: true,
          applied_points: 6,
        },
        {
          key: "same_archetype",
          label: "Same statistical archetype",
          configured_points: 2,
          applied: false,
          applied_points: 0,
        },
      ],
      reasons: [
        {
          key: "same_final_role",
          group: "role",
          text: "same final role",
        },
        {
          key: "statistical_similarity",
          group: "statistics",
          text: "strong statistical similarity (72.5%)",
        },
      ],
    },
  } as unknown as TransferRecommendationResponse;
}

describe("TransferRecommendationCard", () => {
  it("exposes shortlist controls in featured and compact variants", () => {
    const recommendation = createRecommendation();

    const rendered = render(
      <TransferRecommendationCard
        targetPlayerId={978838}
        mode="immediate"
        analysisValues={{
          ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
        }}
        recommendation={recommendation}
      />,
    );

    expect(
      screen.getByRole("button", {
        name: "Save Test Candidate (default)",
      }),
    ).toBeInTheDocument();

    rendered.rerender(
      <TransferRecommendationCard
        targetPlayerId={978838}
        mode="immediate"
        analysisValues={{
          ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
        }}
        recommendation={recommendation}
        variant="compact"
      />,
    );

    expect(
      screen.getByRole("button", {
        name: "Save Test Candidate (compact)",
      }),
    ).toBeInTheDocument();
  });

  it("keeps decision fallback separate from measured spatial evidence", () => {
    render(
      <TransferRecommendationCard
        targetPlayerId={978838}
        mode="immediate"
        analysisValues={{
          ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
        }}
        recommendation={createRecommendation()}
      />,
    );

    const spatialLabel = screen.getByText("Spatial similarity");

    const spatialMetric = spatialLabel.closest("div");

    if (!spatialMetric) {
      throw new Error("Spatial similarity metric not found");
    }

    expect(within(spatialMetric).getByText("61.2%")).toBeInTheDocument();

    expect(
      within(spatialMetric).queryByText("70%", {
        exact: true,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders the candidate player image", () => {
    render(
      <TransferRecommendationCard
        targetPlayerId={978838}
        mode="immediate"
        analysisValues={{
          ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
        }}
        recommendation={createRecommendation()}
      />,
    );

    expect(
      screen.getByAltText("Test Candidate player photo"),
    ).toBeInTheDocument();
  });

  it("renders missing market and role data explicitly", () => {
    render(
      <TransferRecommendationCard
        targetPlayerId={978838}
        mode="immediate"
        analysisValues={{
          ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
        }}
        recommendation={createRecommendation()}
      />,
    );

    expect(screen.getByText("Role unavailable")).toBeInTheDocument();

    const marketLabel = screen.getByText("Market value");

    const marketRow = marketLabel.closest("div");

    if (!marketRow) {
      throw new Error("Market value row not found");
    }

    expect(within(marketRow).getByText("Not reported")).toBeInTheDocument();
  });
  it("renders backend-selected recommendation reasons", () => {
    render(
      <TransferRecommendationCard
        targetPlayerId={978838}
        mode="immediate"
        analysisValues={{
          ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
        }}
        recommendation={createRecommendation()}
      />,
    );

    expect(screen.getByText("Why this candidate")).toBeInTheDocument();

    expect(screen.getByText("same final role")).toBeInTheDocument();

    expect(
      screen.getByText("good statistical similarity (72.5%)"),
    ).toBeInTheDocument();
  });

  it("preserves heatmap fallback semantics in score breakdown", () => {
    render(
      <TransferRecommendationCard
        targetPlayerId={978838}
        mode="immediate"
        analysisValues={{
          ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
        }}
        recommendation={createRecommendation()}
      />,
    );

    expect(screen.getByText("Fallback input")).toBeInTheDocument();

    expect(
      screen.getByText(/Direct heatmap evidence is unavailable/),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "It is not a probability that a transfer will succeed.",
        {
          exact: false,
        },
      ),
    ).toBeInTheDocument();
  });

  it("renders the country flag and truncates candidate age in both variants", () => {
    const recommendation = createRecommendation();

    const rendered = render(
      <TransferRecommendationCard
        targetPlayerId={978838}
        mode="immediate"
        analysisValues={{
          ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
        }}
        recommendation={recommendation}
      />,
    );

    expect(
      rendered.container.querySelector('[data-country-code="ESP"]'),
    ).not.toBeNull();

    expect(screen.getByText("28 years")).toBeInTheDocument();

    expect(screen.queryByText("28.7 years")).not.toBeInTheDocument();

    rendered.rerender(
      <TransferRecommendationCard
        targetPlayerId={978838}
        mode="immediate"
        analysisValues={{
          ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
        }}
        recommendation={recommendation}
        variant="compact"
      />,
    );

    expect(
      rendered.container.querySelector('[data-country-code="ESP"]'),
    ).not.toBeNull();

    expect(screen.getByText("28 years")).toBeInTheDocument();

    expect(screen.queryByText("28.7 years")).not.toBeInTheDocument();
  });
});
