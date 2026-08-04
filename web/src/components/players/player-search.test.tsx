import {
  fireEvent,
  screen,
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
  searchPlayers,
} from "@/lib/api/browser-players";
import type {
  PlayerSearchResponse,
} from "@/lib/api/types";
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
    searchPlayers:
      vi.fn(),
  }),
);

const searchPlayersMock =
  vi.mocked(
    searchPlayers,
  );

const successfulResponse = {
  query: "olise",
  count: 1,
  players: [
    {
      player_id: 978838,
      player_name:
        "Michael Olise",
      national_team_name:
        "France",
      position: "M",
      final_role:
        "Central Half-Space Creator",
      archetype:
        "Wide Creator",
      age: 24.6,
      market_value:
        144_000_000,
      market_value_currency:
        "EUR",
    },
  ],
} as unknown as PlayerSearchResponse;

describe(
  "PlayerSearch",
  () => {
    beforeEach(() => {
      searchPlayersMock
        .mockReset();
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
      "renders successful search results",
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
      "renders the empty state",
      async () => {
        searchPlayersMock
          .mockResolvedValue({
            query:
              "unknown",
            count: 0,
            players: [],
          } as unknown as PlayerSearchResponse);

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
  },
);
