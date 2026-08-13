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

import type {
  PlayerProfileResponse,
} from "@/lib/api/types";

import {
  PlayerProfileView,
} from "./player-profile-view";

const basePlayer: PlayerProfileResponse = {
  player_id: 978838,
  player_name: "Michael Olise",
  national_team_name: "France",
  country_name: "France",
  position: "M",
  age: 24,
  height_cm: 184,
  appearances: 7,
  starts: 6,
  minutes: 650,
  weighted_rating: 7.85,
  market_value: 100_000_000,
  market_value_currency: "EUR",
  archetype: "Creative attacker",
  spatial_role: "Right half-space creator",
  final_role: "Advanced Playmaker",
  lateral_profile: "Right",
  vertical_profile: "Advanced",
  mobility_profile: "Mobile",
  role_confidence_pct: 82,
  spatial_reliability: 0.75,
  data_reliability_score: 0.8,
  player_quality_score: 0.9,
  role_reason: "Strong right-side occupation",
};

function createPlayer(
  overrides: Partial<PlayerProfileResponse> = {},
): PlayerProfileResponse {
  return {
    ...basePlayer,
    ...overrides,
  };
}

function expectDetailValue(
  label: string,
  value: string,
): void {
  const labelElement = screen.getByText(
    label,
    {
      selector: "dt",
    },
  );

  const row = labelElement.closest("div");

  if (!row) {
    throw new Error(
      `Detail row not found for ${label}`,
    );
  }

  expect(
    within(row).getByText(
      value,
      {
        selector: "dd",
      },
    ),
  ).toBeInTheDocument();
}

describe("PlayerProfileView", () => {
  it("renders missing player evidence as unavailable instead of zero", () => {
    render(
      <PlayerProfileView
        player={createPlayer({
          national_team_name: null,
          country_name: null,
          position: null,
          age: null,
          height_cm: null,
          appearances: null,
          starts: null,
          minutes: null,
          weighted_rating: null,
          market_value: null,
          market_value_currency: null,
          archetype: null,
          spatial_role: null,
          final_role: null,
          lateral_profile: null,
          vertical_profile: null,
          mobility_profile: null,
          role_confidence_pct: null,
          spatial_reliability: null,
          data_reliability_score: null,
          player_quality_score: null,
          role_reason: null,
        })}
      />,
    );

    expect(
      screen.getByText(
        "Position unavailable",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "National team unavailable",
      ),
    ).toBeInTheDocument();

    expect(
    screen.getByText(
        /Archetype unavailable/,
    ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /Spatial role unavailable/,
      ),
    ).toBeInTheDocument();

    expectDetailValue(
      "Appearances",
      "Not reported",
    );

    expectDetailValue(
      "Starts",
      "Not reported",
    );

    expectDetailValue(
      "Minutes",
      "Not reported",
    );

    expectDetailValue(
      "Start rate",
      "Not reported",
    );

    expectDetailValue(
      "Lateral profile",
      "Not reported",
    );

    expectDetailValue(
      "Vertical profile",
      "Not reported",
    );

    expectDetailValue(
      "Mobility profile",
      "Not reported",
    );

    expectDetailValue(
      "Spatial reliability",
      "Not reported",
    );

    const marketValueLabel =
      screen.getByText(
        "Estimated market value",
      );

    const marketValueSection =
      marketValueLabel.closest("aside");

    if (!marketValueSection) {
      throw new Error(
        "Market value section not found",
      );
    }

    expect(
      within(
        marketValueSection,
      ).getAllByText(
        "Not reported",
      ).length,
    ).toBeGreaterThan(0);
  });

  it("keeps reported zero values distinct from missing data", () => {
    render(
      <PlayerProfileView
        player={createPlayer({
          appearances: 0,
          starts: 0,
          minutes: 0,
          weighted_rating: 0,
          market_value: 0,
          market_value_currency: "EUR",
          role_confidence_pct: 0,
          spatial_reliability: 0,
          data_reliability_score: 0,
          player_quality_score: 0,
        })}
      />,
    );

    expectDetailValue(
      "Appearances",
      "0",
    );

    expectDetailValue(
      "Starts",
      "0",
    );

    expectDetailValue(
      "Minutes",
      "0",
    );

    expectDetailValue(
      "Start rate",
      "Not reported",
    );

    expectDetailValue(
      "Spatial reliability",
      "0%",
    );

    const marketValueLabel =
      screen.getByText(
        "Estimated market value",
      );

    const marketValueSection =
      marketValueLabel.closest("aside");

    if (!marketValueSection) {
      throw new Error(
        "Market value section not found",
      );
    }

    expect(
      within(
        marketValueSection,
      ).queryByText(
        "Not reported",
        {
          exact: true,
        },
      ),
    ).not.toBeInTheDocument();

    expect(
      marketValueSection.textContent,
    ).toMatch(/0/);
  });
});
