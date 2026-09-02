import { screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MultiPlayerRoleMetrics } from "@/components/transfer-intelligence/multi-player-role-metrics";
import type { MultiPlayerComparisonResponse } from "@/lib/api/types";
import { renderWithQueryClient } from "@/test/render-with-query-client";

vi.mock("@/i18n/navigation", () => ({
  Link: "a",
}));

const response: MultiPlayerComparisonResponse = {
  target: {
    player_id: 1,
    player_name: "Target Player",
    national_team_name: "France",
    position: "F",
    age: 25,
    minutes: 900,
    market_value: 50_000_000,
    market_value_currency: "EUR",
    final_role: "Advanced Forward",
    player_quality_score: 90,
    data_reliability_score: 0.9,
  },
  candidates: [
    {
      player: {
        player_id: 2,
        player_name: "Candidate Player",
        national_team_name: "Spain",
        position: "F",
        age: 27,
        minutes: 720,
        market_value: 40_000_000,
        market_value_currency: "EUR",
        final_role: "Wide Forward",
        player_quality_score: 84,
        data_reliability_score: 0.86,
      },
      evidence: {
        statistical_similarity_pct: 88,
        spatial_similarity_pct: 82,
        heatmap_similarity_score_pct: 80,
        role_fit_pct: 85,
        market_value_advantage_pct: 20,
      },
    },
  ],
  role_metrics: [
    {
      key: "scoring",
      label: "Scoring",
      metrics: [
        {
          key: "goals",
          label: "Goals",
          values: [
            {
              player_id: 1,
              total: 5,
              per90: 0.42,
            },
            {
              player_id: 2,
              total: null,
              per90: null,
            },
          ],
        },
        {
          key: "shots",
          label: "Shots",
          values: [
            {
              player_id: 1,
              total: 0,
              per90: 0,
            },
            {
              player_id: 2,
              total: 12,
              per90: 1.5,
            },
          ],
        },
      ],
    },
  ],
};

describe("MultiPlayerRoleMetrics", () => {
  it("shows tournament totals and per-90 values in canonical player order", () => {
    renderWithQueryClient(
      <MultiPlayerRoleMetrics
        target={response.target}
        candidates={response.candidates}
        groups={response.role_metrics ?? []}
      />,
    );

    const table = screen.getByRole("table", {
      name: "Target final-role metric comparison",
    });

    expect(
      screen.getByRole("region", {
        name: "Scrollable target final-role metrics",
      }),
    ).toHaveAttribute("tabindex", "0");

    const headers = within(table).getAllByRole("columnheader");

    expect(headers[1]).toHaveTextContent("TargetTarget Player");

    expect(headers[2]).toHaveTextContent("Candidate 1Candidate Player");

    const goalsRow = within(table).getByRole("row", {
      name: /Goals/i,
    });

    expect(
      within(goalsRow).getByRole("cell", {
        name: "5 total, 0.42 per 90",
      }),
    ).toHaveTextContent("5 (0.42/90)");

    expect(within(goalsRow).getByText("Unavailable")).toBeInTheDocument();
  });

  it("preserves measured zero values", () => {
    renderWithQueryClient(
      <MultiPlayerRoleMetrics
        target={response.target}
        candidates={response.candidates}
        groups={response.role_metrics ?? []}
      />,
    );

    const shotsRow = screen.getByRole("row", {
      name: /Shots/i,
    });

    expect(
      within(shotsRow).getByRole("cell", {
        name: "0 total, 0 per 90",
      }),
    ).toHaveTextContent("0 (0/90)");
  });
  it("localizes role metrics and number formatting in Turkish", () => {
    renderWithQueryClient(
      <MultiPlayerRoleMetrics
        target={response.target}
        candidates={response.candidates}
        groups={response.role_metrics ?? []}
      />,
      "tr",
    );

    const table = screen.getByRole("table", {
      name: "Hedef nihai rol metrik karşılaştırması",
    });

    expect(
      screen.getByRole("region", {
        name: "Kaydırılabilir hedef nihai rol metrikleri",
      }),
    ).toBeInTheDocument();

    expect(within(table).getByText("Metrik")).toBeInTheDocument();

    expect(within(table).getByText("Hedef")).toBeInTheDocument();

    expect(within(table).getByText("Aday 1")).toBeInTheDocument();

    expect(within(table).getByText("Skor üretimi")).toBeInTheDocument();

    const goalsRow = within(table).getByRole("row", {
      name: /Goller/i,
    });

    expect(
      within(goalsRow).getByRole("cell", {
        name: "5 toplam, 0,42 90 dakika başına",
      }),
    ).toHaveTextContent("5 (0,42/90)");

    expect(within(goalsRow).getByText("Kullanılamıyor")).toBeInTheDocument();
  });
  it("uses combined target and candidate role copy for all-player comparisons", () => {
    renderWithQueryClient(
      <MultiPlayerRoleMetrics
        target={response.target}
        candidates={response.candidates}
        groups={response.role_metrics ?? []}
        variant="all_players"
      />,
      "tr",
    );

    expect(
      screen.getByRole("heading", {
        name: "Rol odaklı metrik karşılaştırması",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Metrikler hedef oyuncu ve tüm adayların rol görevlerinin birleşiminden seçilir. Her değer turnuva toplamını ve ardından 90 dakika başına oranı gösterir.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("region", {
        name: "Kaydırılabilir tüm oyuncular rol metriği karşılaştırması",
      }),
    ).toHaveAttribute("tabindex", "0");

    expect(
      screen.getByRole("table", {
        name: "Tüm oyuncuların rol metriği karşılaştırması",
      }),
    ).toBeInTheDocument();
  });
});
