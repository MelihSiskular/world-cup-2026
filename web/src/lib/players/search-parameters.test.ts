import {
  describe,
  expect,
  it,
} from "vitest";

import {
  createPlayerSearchQueryKey,
  createPlayerSearchUrlParameters,
  hasPlayerSearchCriteria,
  readPlayerSearchUrlParameters,
} from "@/lib/players/search-parameters";

describe(
  "player search parameters",
  () => {
    it(
      "serializes the complete filter contract deterministically",
      () => {
        const parameters =
          createPlayerSearchUrlParameters({
            query: "  olise  ",
            positions: [
              "M",
              "D",
              "M",
            ],
            countries: [
              "France",
            ],
            maximumAge: 24,
            maximumMarketValue:
              30_000_000,
            minimumMinutes: 300,
            minimumRoleConfidence: 70,
            minimumDataReliability: 60,
            sortBy: "market_value",
            sortDirection: "asc",
            offset: 10,
            limit: 10,
          });

        expect(
          parameters.get("q"),
        ).toBe("olise");

        expect(
          parameters.getAll(
            "position",
          ),
        ).toEqual([
          "D",
          "M",
        ]);

        expect(
          parameters.get(
            "country",
          ),
        ).toBe("France");

        expect(
          parameters.get(
            "max_age",
          ),
        ).toBe("24");

        expect(
          parameters.get(
            "max_market_value",
          ),
        ).toBe("30000000");

        expect(
          parameters.get(
            "min_minutes",
          ),
        ).toBe("300");

        expect(
          parameters.get(
            "min_role_confidence",
          ),
        ).toBe("70");

        expect(
          parameters.get(
            "min_data_reliability",
          ),
        ).toBe("60");

        expect(
          parameters.get(
            "sort_by",
          ),
        ).toBe("market_value");

        expect(
          parameters.get(
            "sort_direction",
          ),
        ).toBe("asc");

        expect(
          parameters.get("offset"),
        ).toBe("10");

        expect(
          parameters.get("limit"),
        ).toBe("10");
      },
    );

    it(
      "creates the same cache identity for equivalent selections",
      () => {
        const first =
          createPlayerSearchQueryKey({
            positions: [
              "M",
              "D",
            ],
            countries: [
              "France",
              "Spain",
            ],
          });

        const second =
          createPlayerSearchQueryKey({
            positions: [
              "D",
              "M",
              "D",
            ],
            countries: [
              "Spain",
              "France",
            ],
          });

        expect(first).toEqual(
          second,
        );
      },
    );

    it(
      "round-trips URL-backed filter state",
      () => {
        const source =
          new URLSearchParams(
            "position=D&archetype=Ball-Carrying+Defender&max_age=24&limit=25",
          );

        const result =
          readPlayerSearchUrlParameters(
            source,
          );

        expect(
          result.positions,
        ).toEqual(["D"]);

        expect(
          result.archetypes,
        ).toEqual([
          "Ball-Carrying Defender",
        ]);

        expect(
          result.maximumAge,
        ).toBe(24);

        expect(result.limit).toBe(
          25,
        );
      },
    );

    it(
      "recognizes filter-only discovery criteria",
      () => {
        expect(
          hasPlayerSearchCriteria({
            positions: ["D"],
          }),
        ).toBe(true);

        expect(
          hasPlayerSearchCriteria({
            query: "   ",
          }),
        ).toBe(false);
      },
    );
  },
);
