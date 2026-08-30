import {
  render,
  screen,
} from "@testing-library/react";
import {
  NextIntlClientProvider,
} from "next-intl";
import type {
  ComponentProps,
  ReactNode,
} from "react";

import englishMessages from "../../../messages/en.json";
import turkishMessages from "../../../messages/tr.json";
import userEvent from "@testing-library/user-event";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  ShortlistComparisonBuilder,
} from "@/components/shortlists/shortlist-comparison-builder";
import type {
  Shortlist,
  ShortlistPlayerSnapshot,
} from "@/lib/shortlists/types";

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

        return (
          <a
            href={
              locale === "tr"
                ? `/tr${href}`
                : href
            }
            {...properties}
          />
        );
      },
    };
  },
);

const BASE_PLAYER:
  ShortlistPlayerSnapshot = {
    playerId: 978838,
    playerName: "Michael Olise",
    nationalTeamName: "France",
    countryName: "France",
    countryAlpha3: "FRA",
    position: "M",
    age: 24,
    marketValue: 100_000_000,
    marketValueCurrency: "EUR",
    finalRole:
      "Right Half-Space Creator",
    archetype: "Wide Creator",
    spatialRole:
      "Right Half-Space",
    minutes: 540,
    roleConfidencePct: 82,
    dataReliabilityScore: 78,
    playerQualityScore: 88,
  };

function buildPlayer(
  playerId: number,
  playerName: string,
  position = "M",
): ShortlistPlayerSnapshot {
  return {
    ...BASE_PLAYER,
    playerId,
    playerName,
    position,
  };
}

const PLAYERS:
  readonly ShortlistPlayerSnapshot[] = [
    BASE_PLAYER,
    buildPlayer(
      789071,
      "Dani Olmo",
    ),
    buildPlayer(
      805078,
      "Florian Wirtz",
    ),
    buildPlayer(
      123456,
      "Jamal Musiala",
    ),
    buildPlayer(
      654321,
      "Jude Bellingham",
    ),
    buildPlayer(
      111111,
      "Defender Player",
      "D",
    ),
  ];

function buildShortlist(
  players:
    readonly ShortlistPlayerSnapshot[],
): Shortlist {
  return {
    id: "list-1",
    name: "Creative midfielders",
    createdAt:
      "2026-08-27T03:00:00.000Z",
    updatedAt:
      "2026-08-27T03:00:00.000Z",
    entries: players.map(
      (player) => ({
        player,
        addedAt:
          "2026-08-27T03:00:00.000Z",
      }),
    ),
  };
}

type TestLocale =
  "en" | "tr";

function renderComparison(
  children: ReactNode,
  locale: TestLocale = "en",
) {
  const messages =
    locale === "tr"
      ? turkishMessages
      : englishMessages;

  return render(
    <NextIntlClientProvider
      locale={locale}
      messages={messages}
    >
      {children}
    </NextIntlClientProvider>,
  );
}

describe(
  "ShortlistComparisonBuilder",
  () => {
    it(
      "requires at least two saved players",
      () => {
        renderComparison(
          <ShortlistComparisonBuilder
            shortlist={buildShortlist(
              [
                BASE_PLAYER,
              ],
            )}
          />,
        );

        expect(
          screen.getByText(
            "Add at least one more player before starting a comparison.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByRole(
            "combobox",
            {
              name:
                "Target player",
            },
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "creates a canonical ordered comparison link",
      async () => {
        const user =
          userEvent.setup();

        renderComparison(
          <ShortlistComparisonBuilder
            shortlist={buildShortlist(
              PLAYERS,
            )}
          />,
        );

        expect(
          screen.getByRole(
            "combobox",
            {
              name:
                "Target player",
            },
          ),
        ).toHaveValue(
          "978838",
        );

        await user.click(
          screen.getByRole(
            "checkbox",
            {
              name:
                "Select Dani Olmo as candidate",
            },
          ),
        );

        await user.click(
          screen.getByRole(
            "checkbox",
            {
              name:
                "Select Florian Wirtz as candidate",
            },
          ),
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Compare selected players",
            },
          ),
        ).toHaveAttribute(
          "href",
          (
            "/compare/multi/978838"
            + "?candidates=789071%2C805078"
          ),
        );

        expect(
          screen.getByText(
            "2 of 3 candidates selected",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "clears candidate selection when the target changes",
      async () => {
        const user =
          userEvent.setup();

        renderComparison(
          <ShortlistComparisonBuilder
            shortlist={buildShortlist(
              PLAYERS,
            )}
          />,
        );

        await user.click(
          screen.getByRole(
            "checkbox",
            {
              name:
                "Select Dani Olmo as candidate",
            },
          ),
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Compare selected players",
            },
          ),
        ).toBeInTheDocument();

        await user.selectOptions(
          screen.getByRole(
            "combobox",
            {
              name:
                "Target player",
            },
          ),
          "789071",
        );

        expect(
          screen.queryByRole(
            "link",
            {
              name:
                "Compare selected players",
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByRole(
            "checkbox",
            {
              name:
                "Select Michael Olise as candidate",
            },
          ),
        ).not.toBeChecked();
      },
    );

    it(
      "enforces position compatibility and the three-candidate limit",
      async () => {
        const user =
          userEvent.setup();

        renderComparison(
          <ShortlistComparisonBuilder
            shortlist={buildShortlist(
              PLAYERS,
            )}
          />,
        );

        const defender =
          screen.getByRole(
            "checkbox",
            {
              name:
                "Select Defender Player as candidate",
            },
          );

        expect(
          defender,
        ).toBeDisabled();

        for (const name of [
          "Dani Olmo",
          "Florian Wirtz",
          "Jamal Musiala",
        ]) {
          await user.click(
            screen.getByRole(
              "checkbox",
              {
                name:
                  `Select ${name} as candidate`,
              },
            ),
          );
        }

        expect(
          screen.getByRole(
            "checkbox",
            {
              name:
                "Select Jude Bellingham as candidate",
            },
          ),
        ).toBeDisabled();

        expect(
          screen.getByText(
            "3 of 3 candidates selected",
          ),
        ).toBeInTheDocument();
      },
    );
    it(
      "localizes comparison controls while preserving canonical IDs",
      async () => {
        const user =
          userEvent.setup();

        renderComparison(
          <ShortlistComparisonBuilder
            shortlist={buildShortlist(
              PLAYERS,
            )}
          />,
          "tr",
        );

        expect(
          screen.getByRole(
            "region",
            {
              name:
                "Creative midfielders listesindeki oyuncuları karşılaştır",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "combobox",
            {
              name:
                "Hedef oyuncu",
            },
          ),
        ).toHaveValue(
          "978838",
        );

        await user.click(
          screen.getByRole(
            "checkbox",
            {
              name:
                "Dani Olmo oyuncusunu aday olarak seç",
            },
          ),
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Seçilen oyuncuları karşılaştır",
            },
          ),
        ).toHaveAttribute(
          "href",
          (
            "/tr/compare/multi/978838"
            + "?candidates=789071"
          ),
        );
      },
    );

  },
);
