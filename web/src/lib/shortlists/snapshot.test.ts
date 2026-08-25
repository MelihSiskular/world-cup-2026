import {
  describe,
  expect,
  it,
} from "vitest";

import {
  createShortlistPlayerSnapshot,
} from "@/lib/shortlists/snapshot";

describe(
  "shortlist player snapshot",
  () => {
    it(
      "maps complete player evidence into the canonical contract",
      () => {
        expect(
          createShortlistPlayerSnapshot({
            player_id: 978838,
            player_name:
              "Michael Olise",
            national_team_name:
              "France",
            country_name:
              "France",
            country_alpha3:
              "fra",
            position: "M",
            age: 24.6,
            market_value:
              144_000_000,
            market_value_currency:
              "eur",
            final_role:
              "Central Half-Space Creator",
            archetype:
              "Wide Creator",
            spatial_role:
              "Right Half-Space",
            minutes: 650,
            role_confidence_pct:
              87.2,
            data_reliability_score:
              82.9,
            player_quality_score:
              85.5,
          }),
        ).toEqual({
          playerId: 978838,
          playerName:
            "Michael Olise",
          nationalTeamName:
            "France",
          countryName: "France",
          countryAlpha3: "FRA",
          position: "M",
          age: 24.6,
          marketValue:
            144_000_000,
          marketValueCurrency:
            "EUR",
          finalRole:
            "Central Half-Space Creator",
          archetype:
            "Wide Creator",
          spatialRole:
            "Right Half-Space",
          minutes: 650,
          roleConfidencePct: 87.2,
          dataReliabilityScore:
            82.9,
          playerQualityScore:
            85.5,
        });
      },
    );

    it(
      "normalizes player text without inventing missing evidence",
      () => {
        expect(
          createShortlistPlayerSnapshot({
            player_id: 12345,
            player_name:
              "  Test   Candidate ",
            national_team_name:
              " Test   Nation ",
            country_alpha3: null,
            position: undefined,
            age: undefined,
            market_value: null,
            market_value_currency:
              undefined,
            final_role: null,
            archetype: undefined,
          }),
        ).toEqual({
          playerId: 12345,
          playerName:
            "Test Candidate",
          nationalTeamName:
            "Test Nation",
          countryName: null,
          countryAlpha3: null,
          position: null,
          age: null,
          marketValue: null,
          marketValueCurrency:
            null,
          finalRole: null,
          archetype: null,
          spatialRole: null,
          minutes: null,
          roleConfidencePct: null,
          dataReliabilityScore:
            null,
          playerQualityScore:
            null,
        });
      },
    );

    it(
      "preserves finite zero values",
      () => {
        const snapshot =
          createShortlistPlayerSnapshot({
            player_id: 1,
            player_name:
              "Zero Evidence",
            age: 0,
            market_value: 0,
            minutes: 0,
            role_confidence_pct: 0,
            data_reliability_score:
              0,
            player_quality_score: 0,
          });

        expect(snapshot).toMatchObject({
          age: 0,
          marketValue: 0,
          minutes: 0,
          roleConfidencePct: 0,
          dataReliabilityScore: 0,
          playerQualityScore: 0,
        });
      },
    );

    it(
      "rejects invalid player identities",
      () => {
        expect(
          () =>
            createShortlistPlayerSnapshot({
              player_id: 0,
              player_name:
                "Invalid Player",
            }),
        ).toThrow(
          "Shortlist player ID must be a positive integer.",
        );

        expect(
          () =>
            createShortlistPlayerSnapshot({
              player_id: 1,
              player_name: "   ",
            }),
        ).toThrow(
          "Shortlist player name cannot be empty.",
        );
      },
    );
  },
);
