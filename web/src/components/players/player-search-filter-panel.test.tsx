import {
  NextIntlClientProvider,
} from "next-intl";
import {
  useState,
} from "react";

import englishMessages from "../../../messages/en.json";
import turkishMessages from "../../../messages/tr.json";
import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
} from "vitest";

import {
  PlayerSearchFilterPanel,
} from "@/components/players/player-search-filter-panel";
import type {
  PlayerSearchFiltersResponse,
} from "@/lib/api/types";
import type {
  PlayerSearchParameters,
} from "@/lib/players/search-parameters";

const metadata = {
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
  final_roles: [
    {
      value:
        "Left Wide Centre-Back",
      label:
        "Left Wide Centre-Back",
      count: 17,
      country_alpha3: null,
    },
  ],
  archetypes: [
    {
      value:
        "Ball-Carrying Defender",
      label:
        "Ball-Carrying Defender",
      count: 42,
      country_alpha3: null,
    },
  ],
  countries: [
    {
      value: "France",
      label: "France",
      count: 15,
      country_alpha3: "FRA",
    },
  ],
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

function FilterPanelHarness() {
  const [
    parameters,
    setParameters,
  ] =
    useState<PlayerSearchParameters>({
      query: "oli",
    });

  return (
    <PlayerSearchFilterPanel
      metadata={metadata}
      parameters={parameters}
      onChange={setParameters}
      onClear={() => {
        setParameters({
          query:
            parameters.query,
        });
      }}
    />
  );
}

type TestLocale =
  "en" | "tr";

function renderFilterPanel(
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
      <FilterPanelHarness />
    </NextIntlClientProvider>,
  );
}

describe(
  "PlayerSearchFilterPanel",
  () => {
    it(
      "renders dataset-backed option counts and ranges",
      () => {
        renderFilterPanel();

        expect(
          screen.getByText(
            /532-player analytical catalogue/i,
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "checkbox",
            {
              name:
                /Defender, 193 players/i,
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /Age range:\s*17.8–41.4/i,
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByLabelText(
            "Market value range",
          ),
        ).toHaveTextContent(
          /Value range:\s*0\.05M–218M\s+EUR/i,
        );
      },
    );

    it(
      "updates categorical and numeric filters",
      () => {
        renderFilterPanel();

        const defender =
          screen.getByRole(
            "checkbox",
            {
              name:
                /Defender, 193 players/i,
            },
          );

        fireEvent.click(
          defender,
        );

        expect(
          defender,
        ).toBeChecked();

        expect(
          screen.getByText(
            "1 active",
          ),
        ).toBeInTheDocument();

        fireEvent.click(
          screen.getByText(
            "Recruitment criteria",
          ),
        );

        const maximumAge =
          screen.getByRole(
            "spinbutton",
            {
              name:
                "Maximum age",
            },
          );

        fireEvent.change(
          maximumAge,
          {
            target: {
              value: "24",
            },
          },
        );

        expect(
          maximumAge,
        ).toHaveValue(24);

        expect(
          screen.getByText(
            "2 active",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "clears filters while preserving the search query",
      () => {
        renderFilterPanel();

        const defender =
          screen.getByRole(
            "checkbox",
            {
              name:
                /Defender, 193 players/i,
            },
          );

        fireEvent.click(
          defender,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Clear all filters",
            },
          ),
        );

        expect(
          defender,
        ).not.toBeChecked();

        expect(
          screen.queryByText(
            "1 active",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Clear all filters",
            },
          ),
        ).toBeDisabled();
      },
    );

    it(
      "supports explicit result sorting",
      () => {
        renderFilterPanel();

        const sortControl =
          screen.getByRole(
            "combobox",
            {
              name:
                "Sort results",
            },
          );

        fireEvent.change(
          sortControl,
          {
            target: {
              value:
                "market_value:asc",
            },
          },
        );

        expect(
          sortControl,
        ).toHaveValue(
          "market_value:asc",
        );
      },
    );
    it(
      "localizes filter controls in Turkish",
      () => {
        renderFilterPanel("tr");

        expect(
          screen.getByRole(
            "checkbox",
            {
              name:
                "Defans, 193 oyuncu",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "combobox",
            {
              name:
                "Sonuçları sırala",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /Yaş aralığı:/i,
          ),
        ).toHaveTextContent(
          "17,8–41,4",
        );
      },
    );

  },
);
