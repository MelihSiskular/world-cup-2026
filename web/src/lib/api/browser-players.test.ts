import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  fetchPlayerSearchFilters,
  searchPlayers,
} from "@/lib/api/browser-players";

const fetchMock =
  vi.fn<typeof fetch>();

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

describe(
  "player browser API",
  () => {
    it(
      "requests advanced player discovery with repeated filters",
      async () => {
        fetchMock.mockResolvedValue(
          new Response(
            JSON.stringify({
              query: null,
              count: 0,
              total: 0,
              offset: 0,
              limit: 10,
              has_more: false,
              sort_by:
                "player_quality",
              sort_direction:
                "desc",
              players: [],
            }),
            {
              status: 200,
              headers: {
                "content-type":
                  "application/json",
              },
            },
          ),
        );

        vi.stubGlobal(
          "fetch",
          fetchMock,
        );

        await searchPlayers({
          positions: [
            "M",
            "D",
          ],
          countries: [
            "France",
          ],
          maximumAge: 24,
          minimumMinutes: 300,
        });

        const [
          requestPath,
          options,
        ] =
          fetchMock.mock.calls[0] ??
          [];

        expect(
          typeof requestPath,
        ).toBe("string");

        const url = new URL(
          String(requestPath),
          "http://localhost",
        );

        expect(
          url.pathname,
        ).toBe(
          "/api/players/search",
        );

        expect(
          url.searchParams.getAll(
            "position",
          ),
        ).toEqual([
          "D",
          "M",
        ]);

        expect(
          url.searchParams.get(
            "country",
          ),
        ).toBe("France");

        expect(
          url.searchParams.get(
            "max_age",
          ),
        ).toBe("24");

        expect(
          url.searchParams.get(
            "min_minutes",
          ),
        ).toBe("300");

        expect(options).toMatchObject({
          cache: "no-store",
        });
      },
    );

    it(
      "requests dataset-backed filter metadata",
      async () => {
        fetchMock.mockResolvedValue(
          new Response(
            JSON.stringify({
              player_count: 532,
              positions: [],
              final_roles: [],
              archetypes: [],
              countries: [],
              age: {
                minimum: 17.8,
                maximum: 41.4,
              },
              market_value: {
                minimum: 48_000,
                maximum:
                  218_000_000,
              },
              minutes: {
                minimum: 180,
                maximum: 810,
              },
              role_confidence: {
                minimum: 37.58,
                maximum: 90.78,
              },
              data_reliability: {
                minimum: 31.38,
                maximum: 85.96,
              },
              market_value_currency:
                "EUR",
            }),
            {
              status: 200,
              headers: {
                "content-type":
                  "application/json",
              },
            },
          ),
        );

        vi.stubGlobal(
          "fetch",
          fetchMock,
        );

        const result =
          await fetchPlayerSearchFilters();

        expect(
          fetchMock,
        ).toHaveBeenCalledTimes(
          1,
        );

        expect(
          fetchMock,
        ).toHaveBeenCalledWith(
          "/api/players/search/filters",
          expect.objectContaining({
            cache: "no-store",
          }),
        );

        expect(
          result.player_count,
        ).toBe(532);
      },
    );
  },
);
