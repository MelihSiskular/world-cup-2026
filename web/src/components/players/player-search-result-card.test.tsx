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
  PlayerSearchResultCard,
} from "@/components/players/player-search-result-card";
import {
  fetchPlayerProfile,
} from "@/lib/api/browser-players";
import type {
  PlayerSearchItemResponse,
  PlayerProfileResponse,
} from "@/lib/api/types";
import {
  renderWithQueryClient,
} from "@/test/render-with-query-client";

vi.mock(
  "@/lib/api/browser-players",
  () => ({
    fetchPlayerProfile:
      vi.fn(),
  }),
);

const fetchPlayerProfileMock =
  vi.mocked(
    fetchPlayerProfile,
  );

const player = {
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
  spatial_role:
    "Right Half-Space",
  age: 24.6,
  market_value:
    144_000_000,
  market_value_currency:
    "EUR",
} as PlayerSearchItemResponse;

const profileResponse = {
  player_id: 978838,
  player_name:
    "Michael Olise",
} as unknown as PlayerProfileResponse;

describe(
  "PlayerSearchResultCard",
  () => {
    beforeEach(() => {
      fetchPlayerProfileMock
        .mockReset();

      fetchPlayerProfileMock
        .mockResolvedValue(
          profileResponse,
        );
    });

    it(
      "prefetches the player profile on hover",
      async () => {
        renderWithQueryClient(
          <ul>
            <PlayerSearchResultCard
              player={player}
            />
          </ul>,
        );

        const link =
          screen.getByRole(
            "link",
            {
              name:
                /Michael Olise/i,
            },
          );

        fireEvent.mouseEnter(
          link,
        );

        await waitFor(() => {
          expect(
            fetchPlayerProfileMock,
          ).toHaveBeenCalledTimes(
            1,
          );
        });

        expect(
          fetchPlayerProfileMock,
        ).toHaveBeenCalledWith(
          978838,
          expect.any(AbortSignal),
        );
      },
    );

    it(
      "prefetches the player profile for keyboard navigation",
      async () => {
        renderWithQueryClient(
          <ul>
            <PlayerSearchResultCard
              player={player}
            />
          </ul>,
        );

        const link =
          screen.getByRole(
            "link",
            {
              name:
                /Michael Olise/i,
            },
          );

        fireEvent.focus(
          link,
        );

        await waitFor(() => {
          expect(
            fetchPlayerProfileMock,
          ).toHaveBeenCalledTimes(
            1,
          );
        });
      },
    );

    it(
      "does not refetch an already fresh prefetched profile",
      async () => {
        renderWithQueryClient(
          <ul>
            <PlayerSearchResultCard
              player={player}
            />
          </ul>,
        );

        const link =
          screen.getByRole(
            "link",
            {
              name:
                /Michael Olise/i,
            },
          );

        fireEvent.mouseEnter(
          link,
        );

        await waitFor(() => {
          expect(
            fetchPlayerProfileMock,
          ).toHaveBeenCalledTimes(
            1,
          );
        });

        fireEvent.focus(
          link,
        );

        await waitFor(() => {
          expect(
            fetchPlayerProfileMock,
          ).toHaveBeenCalledTimes(
            1,
          );
        });
      },
    );
  },
);
