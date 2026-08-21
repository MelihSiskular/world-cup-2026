import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PlayerProfileResponse } from "@/lib/api/types";

import { PlayerProfileView } from "./player-profile-view";

const basePlayer: PlayerProfileResponse = {
  player_id: 978838,
  player_name: "Michael Olise",
  national_team_name: "France",
  country_name: "France",
  country_alpha3: "FRA",
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
  tournament: {
    matches: 8,
    starts: 8,
    substitute_appearances: 0,
    captain_appearances: 0,
    minutes: 650,
    formations_used: 1,
    primary_formation: "4-2-3-1",
    primary_lineup_position: "M",
  },
  intelligence: {
    position_group: "midfielder",
    sample: {
      target_minutes: 650,
      minimum_peer_minutes: 180,
      target_meets_peer_minimum: true,
    },
    groups: [],
    strengths: [],
    watch_outs: [],
  },
};

function createPlayer(
  overrides: Partial<PlayerProfileResponse> = {},
): PlayerProfileResponse {
  return {
    ...basePlayer,
    ...overrides,
  };
}

function expectDetailValue(label: string, value: string): void {
  const labelElement = screen.getByText(label, {
    selector: "dt",
  });

  const row = labelElement.closest("div");

  if (!row) {
    throw new Error(`Detail row not found for ${label}`);
  }

  expect(
    within(row).getByText(value, {
      selector: "dd",
    }),
  ).toBeInTheDocument();
}

describe("PlayerProfileView", () => {
  it("renders enriched tournament and sample context", () => {
    render(<PlayerProfileView player={basePlayer} />);

    expectDetailValue("Matches", "8");

    expectDetailValue("Starts", "8");

    expectDetailValue("Substitute appearances", "0");

    expectDetailValue("Captain appearances", "0");

    expectDetailValue("Minutes", "650");

    expectDetailValue("Primary formation", "4-2-3-1");

    expectDetailValue("Lineup position", "M");

    expectDetailValue("Formations used", "1");

    expect(
      screen.getByText("Target sample meets the 180-minute peer benchmark."),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /Comparison peers require at least 180 tournament minutes/,
      ),
    ).toBeInTheDocument();
  });

  it("renders the deterministic player photo in the profile identity", () => {
    render(<PlayerProfileView player={basePlayer} />);

    const playerImage = screen.getByRole("img", {
      name: "Michael Olise player photo",
    });

    expect(
      new URL(playerImage.getAttribute("src") ?? "", "http://localhost")
        .pathname,
    ).toBe("/player-images/978838.png");
  });

  it("includes the position-aware scouting insights section", () => {
    render(<PlayerProfileView player={basePlayer} />);

    expect(
      screen.getByRole("heading", {
        name: "Scouting insights",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(/No standout strengths were surfaced/),
    ).toBeInTheDocument();

    expect(
      screen.getByText(/No watch-out signals were surfaced/),
    ).toBeInTheDocument();
  });

  it("includes the position-aware performance profile", () => {
    render(<PlayerProfileView player={basePlayer} />);

    expect(
      screen.getByRole("heading", {
        name: "Performance profile",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(/No position-aware performance metrics were available/),
    ).toBeInTheDocument();
  });

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
          tournament: null,
          intelligence: null,
        })}
      />,
    );

    expect(screen.getByText("Position unavailable")).toBeInTheDocument();

    expect(screen.getByText("National team unavailable")).toBeInTheDocument();

    expect(screen.getByText(/Archetype unavailable/)).toBeInTheDocument();

    expect(screen.getByText(/Spatial role unavailable/)).toBeInTheDocument();

    expectDetailValue("Matches", "Not reported");

    expectDetailValue("Starts", "Not reported");

    expectDetailValue("Substitute appearances", "Not reported");

    expectDetailValue("Captain appearances", "Not reported");

    expectDetailValue("Minutes", "Not reported");

    expectDetailValue("Primary formation", "Not reported");

    expectDetailValue("Lineup position", "Not reported");

    expectDetailValue("Formations used", "Not reported");

    expectDetailValue("Lateral profile", "Not reported");

    expectDetailValue("Vertical profile", "Not reported");

    expectDetailValue("Mobility profile", "Not reported");

    expectDetailValue("Spatial reliability", "Not reported");

    expect(
      screen.getByText("Tournament-minute sample context is not available."),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Enriched sample evidence was not reported for this player.",
      ),
    ).toBeInTheDocument();

    const marketValueLabel = screen.getByText("Estimated market value");

    const marketValueSection = marketValueLabel.closest("aside");

    if (!marketValueSection) {
      throw new Error("Market value section not found");
    }

    expect(
      within(marketValueSection).getAllByText("Not reported").length,
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
          tournament: {
            matches: 0,
            starts: 0,
            substitute_appearances: 0,
            captain_appearances: 0,
            minutes: 0,
            formations_used: 0,
            primary_formation: null,
            primary_lineup_position: null,
          },
          intelligence: {
            position_group: "midfielder",
            sample: {
              target_minutes: 0,
              minimum_peer_minutes: 180,
              target_meets_peer_minimum: false,
            },
            groups: [],
            strengths: [],
            watch_outs: [],
          },
        })}
      />,
    );

    expectDetailValue("Matches", "0");

    expectDetailValue("Starts", "0");

    expectDetailValue("Substitute appearances", "0");

    expectDetailValue("Captain appearances", "0");

    expectDetailValue("Minutes", "0");

    expectDetailValue("Formations used", "0");

    expectDetailValue("Primary formation", "Not reported");

    expectDetailValue("Lineup position", "Not reported");

    expectDetailValue("Spatial reliability", "0%");

    expect(
      screen.getByText(
        "Target sample is below the 180-minute peer benchmark; percentile comparisons should be read with added caution.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /Comparison peers require at least 180 tournament minutes/,
      ),
    ).toBeInTheDocument();

    const marketValueLabel = screen.getByText("Estimated market value");

    const marketValueSection = marketValueLabel.closest("aside");

    if (!marketValueSection) {
      throw new Error("Market value section not found");
    }

    expect(
      within(marketValueSection).queryByText("Not reported", {
        exact: true,
      }),
    ).not.toBeInTheDocument();

    expect(marketValueSection.textContent).toMatch(/0/);
  });

  it("keeps long player identity content available without truncating the data", () => {
    const longPlayerName =
      "Jean-Baptiste Alexandre Maximilien Very Long Footballer Name";

    const longRole =
      "Advanced Central Half-Space Creative Progression Specialist";

    render(
      <PlayerProfileView
        player={createPlayer({
          player_name: longPlayerName,
          final_role: longRole,
        })}
      />,
    );

    expect(
      screen.getByRole("heading", {
        name: longPlayerName,
      }),
    ).toBeInTheDocument();

    const renderedLongRoles = screen.getAllByText(longRole);

    expect(renderedLongRoles.length).toBeGreaterThanOrEqual(1);

    for (const renderedRole of renderedLongRoles) {
      expect(renderedRole).toBeInTheDocument();
    }
  });

  it("shows caution for a low-minute target while preserving enriched tournament values", () => {
    render(
      <PlayerProfileView
        player={createPlayer({
          tournament: {
            matches: 2,
            starts: 1,
            substitute_appearances: 1,
            captain_appearances: 0,
            minutes: 95,
            formations_used: 2,
            primary_formation: "4-3-3",
            primary_lineup_position: "M",
          },
          intelligence: {
            position_group: "midfielder",
            sample: {
              target_minutes: 95,
              minimum_peer_minutes: 180,
              target_meets_peer_minimum: false,
            },
            groups: [],
            strengths: [],
            watch_outs: [],
          },
        })}
      />,
    );

    expectDetailValue("Matches", "2");

    expectDetailValue("Starts", "1");

    expectDetailValue("Substitute appearances", "1");

    expectDetailValue("Captain appearances", "0");

    expectDetailValue("Minutes", "95");

    expectDetailValue("Formations used", "2");

    expectDetailValue("Primary formation", "4-3-3");

    expectDetailValue("Lineup position", "M");

    expect(
      screen.getByText(
        "Target sample is below the 180-minute peer benchmark; percentile comparisons should be read with added caution.",
      ),
    ).toBeInTheDocument();
  });

  it("keeps role assignment evidence available behind a collapsed disclosure", () => {
    render(<PlayerProfileView player={basePlayer} />);

    const disclosureLabel = screen.getByText("View role assignment evidence");

    expect(disclosureLabel).toBeInTheDocument();

    const details = disclosureLabel.closest("details");

    if (!details) {
      throw new Error("Role evidence details element not found.");
    }

    expect(details).not.toHaveAttribute("open");

    expect(
      screen.getByText("Strong right-side occupation"),
    ).toBeInTheDocument();
  });
});
