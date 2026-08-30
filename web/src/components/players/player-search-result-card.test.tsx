import type {
  ComponentProps,
  ReactNode,
} from "react";
import {
  NextIntlClientProvider,
} from "next-intl";

import englishMessages from "../../../messages/en.json";
import turkishMessages from "../../../messages/tr.json";

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
  "@/i18n/navigation",
  async () => {
    const {
      useLocale,
    } = await vi.importActual<
      typeof import("next-intl")
    >("next-intl");

    return {
      Link: ({
        href,
        ...properties
      }: ComponentProps<"a"> &
        Readonly<{
          href: string;
        }>) => {
        const locale =
          useLocale();

        const localizedHref =
          locale === "tr"
            ? `/tr${href}`
            : href;

        return (
          <a
            href={localizedHref}
            {...properties}
          />
        );
      },
    };
  },
);

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

type TestLocale =
  "en" | "tr";

function renderResultCard(
  children: ReactNode,
  locale: TestLocale = "en",
) {
  const messages =
    locale === "tr"
      ? turkishMessages
      : englishMessages;

  return renderWithQueryClient(
    <NextIntlClientProvider
      locale={locale}
      messages={messages}
    >
      {children}
    </NextIntlClientProvider>,
  );
}

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
        renderResultCard(
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
        renderResultCard(
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
      "exposes shortlist controls outside the profile link",
      async () => {
        renderResultCard(
          <ul>
            <PlayerSearchResultCard
              player={player}
            />
          </ul>,
        );

        const shortlistButton =
          await screen.findByRole(
            "button",
            {
              name:
                "Add to shortlist",
            },
          );

        await waitFor(() => {
          expect(
            shortlistButton,
          ).toBeEnabled();
        });

        fireEvent.click(
          shortlistButton,
        );

        expect(
          screen.getByRole(
            "region",
            {
              name:
                "Shortlist options for Michael Olise",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Open Michael Olise scouting profile",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/players/978838",
        );
      },
    );

    it(
      "does not refetch an already fresh prefetched profile",
      async () => {
        renderResultCard(
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
    it(
      "localizes player-card presentation without translating player data",
      () => {
        renderResultCard(
          <ul>
            <PlayerSearchResultCard
              player={player}
            />
          </ul>,
          "tr",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Michael Olise scouting profilini aç",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/tr/players/978838",
        );

        expect(
          screen.getByText(
            "Nihai rol:",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Central Half-Space Creator",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Orta saha",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "25 yaş",
          ),
        ).toBeInTheDocument();
      },
    );

  },
);
