import {
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  PlayerSearch,
} from "@/components/players/player-search";
import {
  fetchPlayerSearchFilters,
  searchPlayers,
} from "@/lib/api/browser-players";
import type {
  PlayerSearchFiltersResponse,
  PlayerSearchResponse,
} from "@/lib/api/types";
import {
  readPlayerSearchUrlParameters,
} from "@/lib/players/search-parameters";
import {
  renderWithQueryClient,
} from "@/test/render-with-query-client";

vi.mock(
  "@/hooks/use-debounced-value",
  () => ({
    useDebouncedValue: (
      value: unknown,
    ) => value,
  }),
);

vi.mock(
  "@/lib/api/browser-players",
  () => ({
    fetchPlayerSearchFilters:
      vi.fn(),
    searchPlayers:
      vi.fn(),
  }),
);

const searchPlayersMock =
  vi.mocked(
    searchPlayers,
  );

const fetchPlayerSearchFiltersMock =
  vi.mocked(
    fetchPlayerSearchFilters,
  );

const filterMetadata = {
  player_count: 532,
  positions: [
    {
      value: "D",
      label: "D",
      count: 193,
      country_alpha3: null,
    },
    {
      value: "M",
      label: "M",
      count: 216,
      country_alpha3: null,
    },
  ],
  final_roles: [],
  archetypes: [],
  countries: [],
  age: {
    minimum: 17.8,
    maximum: 41.4,
  },
  market_value: {
    minimum: 48_000,
    maximum: 218_000_000,
  },
  market_value_currency: "EUR",
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
} satisfies PlayerSearchFiltersResponse;

const successfulResponse = {
  query: "olise",
  count: 1,
  total: 1,
  offset: 0,
  limit: 12,
  has_more: false,
  sort_by: "relevance",
  sort_direction: "asc",
  players: [
    {
      player_id: 978838,
      player_name:
        "Michael Olise",
      national_team_name:
        "France",
      country_name:
        "France",
      country_alpha3:
        "FRA",
      position: "M",
      final_role:
        "Central Half-Space Creator",
      archetype:
        "Wide Creator",
      spatial_role:
        "Advanced Central Zone",
      age: 24.6,
      market_value:
        144_000_000,
      market_value_currency:
        "EUR",
      minutes: 650,
      role_confidence_pct:
        87.2,
      data_reliability_score:
        82.9,
      player_quality_score:
        85.5,
    },
  ],
} satisfies PlayerSearchResponse;

describe(
  "PlayerSearch",
  () => {
    beforeEach(() => {
      window.history.replaceState(
        {},
        "",
        "/players",
      );

      searchPlayersMock
        .mockReset();

      fetchPlayerSearchFiltersMock
        .mockReset()
        .mockResolvedValue(
          filterMetadata,
        );
    });

    it(
      "shows the initial guidance",
      () => {
        renderWithQueryClient(
          <PlayerSearch />,
        );

        expect(
          screen.getByText(
            "Start with a player name",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "restores filter state from the page URL",
      async () => {
        window.history.replaceState(
          {},
          "",
          "/players?position=D&max_age=24",
        );

        searchPlayersMock
          .mockResolvedValue({
            ...successfulResponse,
            query: null,
          });

        const initialParameters =
          readPlayerSearchUrlParameters(
            new URLSearchParams(
              window.location.search,
            ),
          );

        renderWithQueryClient(
          <PlayerSearch
            initialParameters={
              initialParameters
            }
          />,
        );

        const defender =
          await screen.findByRole(
            "checkbox",
            {
              name:
                "Defender, 193 players",
            },
          );

        expect(
          defender,
        ).toBeChecked();

        expect(
          await screen.findByRole(
            "button",
            {
              name:
                "Remove Position: Defender filter",
            },
          ),
        ).toBeInTheDocument();

        await waitFor(() => {
          expect(
            searchPlayersMock,
          ).toHaveBeenCalledWith(
            expect.objectContaining({
              positions: ["D"],
              maximumAge: 24,
            }),
            expect.anything(),
          );
        });
      },
    );

    it(
      "writes filters to the URL and removes them from the active summary",
      async () => {
        searchPlayersMock
          .mockResolvedValue({
            ...successfulResponse,
            query: null,
          });

        renderWithQueryClient(
          <PlayerSearch />,
        );

        const defender =
          await screen.findByRole(
            "checkbox",
            {
              name:
                "Defender, 193 players",
            },
          );

        fireEvent.click(
          defender,
        );

        const removeFilter =
          await screen.findByRole(
            "button",
            {
              name:
                "Remove Position: Defender filter",
            },
          );

        await waitFor(() => {
          expect(
            new URLSearchParams(
              window.location.search,
            ).getAll(
              "position",
            ),
          ).toEqual(["D"]);
        });

        fireEvent.click(
          removeFilter,
        );

        await waitFor(() => {
          expect(
            new URLSearchParams(
              window.location.search,
            ).has(
              "position",
            ),
          ).toBe(false);

          expect(
            defender,
          ).not.toBeChecked();
        });
      },
    );

    it(
      "responds to browser history state changes",
      async () => {
        searchPlayersMock
          .mockResolvedValue({
            ...successfulResponse,
            query: null,
          });

        renderWithQueryClient(
          <PlayerSearch />,
        );

        const defender =
          await screen.findByRole(
            "checkbox",
            {
              name:
                "Defender, 193 players",
            },
          );

        window.history.pushState(
          {},
          "",
          "/players?position=D",
        );

        window.dispatchEvent(
          new PopStateEvent(
            "popstate",
          ),
        );

        await waitFor(() => {
          expect(
            defender,
          ).toBeChecked();
        });

        expect(
          await screen.findByRole(
            "button",
            {
              name:
                "Remove Position: Defender filter",
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "renders successful name-search results",
      async () => {
        searchPlayersMock
          .mockResolvedValue(
            successfulResponse,
          );

        renderWithQueryClient(
          <PlayerSearch />,
        );

        fireEvent.change(
          screen.getByRole(
            "searchbox",
          ),
          {
            target: {
              value: "olise",
            },
          },
        );

        expect(
          await screen.findByText(
            "Michael Olise",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "status",
          ),
        ).toHaveTextContent(
          /1\s+player\s+found\s+for/i,
        );
      },
    );

    it(
      "supports filter-only discovery",
      async () => {
        searchPlayersMock
          .mockResolvedValue({
            ...successfulResponse,
            query: null,
          });

        renderWithQueryClient(
          <PlayerSearch />,
        );

        const defender =
          await screen.findByRole(
            "checkbox",
            {
              name:
                "Defender, 193 players",
            },
          );

        fireEvent.click(
          defender,
        );

        expect(
          await screen.findByText(
            "Michael Olise",
          ),
        ).toBeInTheDocument();

        expect(
          searchPlayersMock,
        ).toHaveBeenLastCalledWith(
          expect.objectContaining({
            query: "",
            positions: [
              "D",
            ],
          }),
          expect.objectContaining({
            signal:
              expect.any(
                AbortSignal,
              ),
          }),
        );
      },
    );

    it(
      "keeps previous results visible while criteria update",
      async () => {
        let resolveNextSearch!: (
          value:
            PlayerSearchResponse,
        ) => void;

        const nextSearch =
          new Promise<PlayerSearchResponse>(
            (resolve) => {
              resolveNextSearch =
                resolve;
            },
          );

        const refreshedResponse = {
          ...successfulResponse,
          query: "alex",
          players: [
            {
              ...successfulResponse.players[0]!,
              player_id: 999999,
              player_name:
                "Alex Baena",
            },
          ],
        } satisfies PlayerSearchResponse;

        searchPlayersMock
          .mockResolvedValueOnce(
            successfulResponse,
          )
          .mockReturnValueOnce(
            nextSearch,
          );

        renderWithQueryClient(
          <PlayerSearch />,
        );

        fireEvent.change(
          screen.getByRole(
            "searchbox",
          ),
          {
            target: {
              value: "olise",
            },
          },
        );

        expect(
          await screen.findByText(
            "Michael Olise",
          ),
        ).toBeInTheDocument();

        fireEvent.change(
          screen.getByRole(
            "searchbox",
          ),
          {
            target: {
              value: "alex",
            },
          },
        );

        expect(
          screen.getByText(
            "Michael Olise",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "Updating…",
          ),
        ).toBeInTheDocument();

        resolveNextSearch(
          refreshedResponse,
        );

        expect(
          await screen.findByText(
            "Alex Baena",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "renders the empty state",
      async () => {
        searchPlayersMock
          .mockResolvedValue({
            ...successfulResponse,
            query:
              "unknown",
            count: 0,
            total: 0,
            players: [],
          });

        renderWithQueryClient(
          <PlayerSearch />,
        );

        fireEvent.change(
          screen.getByRole(
            "searchbox",
          ),
          {
            target: {
              value: "unknown",
            },
          },
        );

        expect(
          await screen.findByText(
            "No players found",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "recovers after retrying a failed search",
      async () => {
        searchPlayersMock
          .mockRejectedValueOnce(
            new Error(
              "Search failed.",
            ),
          )
          .mockResolvedValueOnce(
            successfulResponse,
          );

        renderWithQueryClient(
          <PlayerSearch />,
        );

        fireEvent.change(
          screen.getByRole(
            "searchbox",
          ),
          {
            target: {
              value: "olise",
            },
          },
        );

        expect(
          await screen.findByText(
            "Player search unavailable",
          ),
        ).toBeInTheDocument();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Retry search",
            },
          ),
        );

        expect(
          await screen.findByText(
            "Michael Olise",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "moves through paginated results",
      async () => {
        searchPlayersMock
          .mockResolvedValueOnce({
            ...successfulResponse,
            total: 13,
            has_more: true,
          })
          .mockResolvedValueOnce({
            ...successfulResponse,
            total: 13,
            offset: 12,
            has_more: false,
            players: [
              {
                ...successfulResponse.players[0]!,
                player_id: 999999,
                player_name:
                  "Alex Baena",
              },
            ],
          });

        renderWithQueryClient(
          <PlayerSearch />,
        );

        fireEvent.change(
          screen.getByRole(
            "searchbox",
          ),
          {
            target: {
              value: "oli",
            },
          },
        );

        expect(
          await screen.findByText(
            "Michael Olise",
          ),
        ).toBeInTheDocument();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "Next",
            },
          ),
        );

        expect(
          await screen.findByText(
            "Alex Baena",
          ),
        ).toBeInTheDocument();

        expect(
          searchPlayersMock,
        ).toHaveBeenLastCalledWith(
          expect.objectContaining({
            offset: 12,
          }),
          expect.anything(),
        );
      },
    );
  },
);
