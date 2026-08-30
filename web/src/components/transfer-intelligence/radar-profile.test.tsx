import {
  render as renderTestingLibrary,
  screen,
} from "@testing-library/react";
import {
  NextIntlClientProvider,
} from "next-intl";
import type {
  ReactElement,
} from "react";

import englishMessages from "../../../messages/en.json";
import turkishMessages from "../../../messages/tr.json";
import {
  describe,
  expect,
  it,
} from "vitest";

import {
  RadarProfile,
  type RadarProfileSeries,
} from "@/components/transfer-intelligence/radar-profile";

type TestLocale = "en" | "tr";

const messagesByLocale = {
  en: englishMessages,
  tr: turkishMessages,
} as const;

function renderLocalized(
  element: ReactElement,
  locale: TestLocale = "en",
) {
  return renderTestingLibrary(
    <NextIntlClientProvider
      locale={locale}
      messages={
        messagesByLocale[locale]
      }
    >
      {element}
    </NextIntlClientProvider>,
  );
}

function createSeries(
  overrides:
    Partial<RadarProfileSeries> = {},
): RadarProfileSeries {
  return {
    player_id: 978838,
    player_name:
      "Michael Olise",
    available: true,
    dimensions: [
      {
        key: "creativity",
        label: "Creativity",
        percentile: 100,
      },
      {
        key: "progression",
        label: "Progression",
        percentile: 75,
      },
      {
        key: "ball_security",
        label: "Ball Security",
        percentile: 50,
      },
      {
        key: "dribbling",
        label: "Dribbling",
        percentile: 25,
      },
    ],
    ...overrides,
  };
}

describe(
  "RadarProfile",
  () => {
    it(
      "renders the radar grid, axes and one complete profile",
      () => {
        renderLocalized(
          <RadarProfile
            primary={
              createSeries()
            }
          />,
        );

        expect(
          screen.getByRole(
            "img",
            {
              name:
                "Playing style radar for Michael Olise",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByTestId(
            /radar-ring-/,
          ),
        ).toHaveLength(4);

        expect(
          screen.getAllByTestId(
            /radar-axis-/,
          ),
        ).toHaveLength(4);

        expect(
          screen.getByTestId(
            "radar-polygon-primary",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Position-relative playing style",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Percentile · 0–100",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "renders two compatible profiles on the same radar",
      () => {
        renderLocalized(
          <RadarProfile
            primary={
              createSeries()
            }
            secondary={
              createSeries({
                player_id:
                  789071,
                player_name:
                  "Dani Olmo",
                dimensions: [
                  {
                    key:
                      "creativity",
                    label:
                      "Creativity",
                    percentile:
                      91.7,
                  },
                  {
                    key:
                      "progression",
                    label:
                      "Progression",
                    percentile:
                      60.6,
                  },
                  {
                    key:
                      "ball_security",
                    label:
                      "Ball Security",
                    percentile:
                      36.1,
                  },
                  {
                    key:
                      "dribbling",
                    label:
                      "Dribbling",
                    percentile:
                      79.2,
                  },
                ],
              })
            }
          />,
        );

        expect(
          screen.getByRole(
            "img",
            {
              name:
                "Playing style radar comparison for Michael Olise and Dani Olmo",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByTestId(
            "radar-polygon-primary",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByTestId(
            "radar-polygon-secondary",
          ),
        ).toBeInTheDocument();

        const legend =
          screen.getByLabelText(
            "Radar series legend",
          );

        expect(
          legend,
        ).toHaveTextContent(
          "Michael Olise",
        );

        expect(
          legend,
        ).toHaveTextContent(
          "Dani Olmo",
        );
      },
    );

    it(
      "keeps a measured zero percentile distinct from missing evidence",
      () => {
        renderLocalized(
          <RadarProfile
            primary={
              createSeries({
                dimensions: [
                  {
                    key:
                      "creativity",
                    label:
                      "Creativity",
                    percentile:
                      100,
                  },
                  {
                    key:
                      "progression",
                    label:
                      "Progression",
                    percentile:
                      75,
                  },
                  {
                    key:
                      "ball_security",
                    label:
                      "Ball Security",
                    percentile:
                      0,
                  },
                  {
                    key:
                      "dribbling",
                    label:
                      "Dribbling",
                    percentile:
                      25,
                  },
                ],
              })
            }
          />,
        );

        const zeroPoint =
          screen.getByTestId(
            "radar-point-primary-ball_security",
          );

        expect(
          zeroPoint,
        ).toHaveAttribute(
          "data-percentile",
          "0",
        );

        expect(
          zeroPoint,
        ).toHaveAttribute(
          "cx",
          "280",
        );

        expect(
          zeroPoint,
        ).toHaveAttribute(
          "cy",
          "195",
        );
      },
    );

    it(
      "does not invent a neutral value for missing percentile evidence",
      () => {
        renderLocalized(
          <RadarProfile
            primary={
              createSeries({
                dimensions: [
                  {
                    key:
                      "creativity",
                    label:
                      "Creativity",
                    percentile:
                      100,
                  },
                  {
                    key:
                      "progression",
                    label:
                      "Progression",
                    percentile:
                      75,
                  },
                  {
                    key:
                      "ball_security",
                    label:
                      "Ball Security",
                    percentile:
                      null,
                  },
                  {
                    key:
                      "dribbling",
                    label:
                      "Dribbling",
                    percentile:
                      25,
                  },
                ],
              })
            }
          />,
        );

        expect(
          screen.queryByTestId(
            "radar-polygon-primary",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByTestId(
            "radar-point-primary-ball_security",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByTestId(
            "radar-partial-evidence",
          ),
        ).toHaveTextContent(
          "Missing values are left unplotted",
        );
      },
    );

    it(
      "rejects an incompatible overlay dimension contract",
      () => {
        renderLocalized(
          <RadarProfile
            primary={
              createSeries()
            }
            secondary={
              createSeries({
                player_id:
                  789071,
                player_name:
                  "Dani Olmo",
                dimensions: [
                  {
                    key:
                      "creativity",
                    label:
                      "Creativity",
                    percentile:
                      90,
                  },
                  {
                    key:
                      "passing_volume",
                    label:
                      "Passing Volume",
                    percentile:
                      80,
                  },
                  {
                    key:
                      "ball_security",
                    label:
                      "Ball Security",
                    percentile:
                      70,
                  },
                  {
                    key:
                      "dribbling",
                    label:
                      "Dribbling",
                    percentile:
                      60,
                  },
                ],
              })
            }
          />,
        );

        expect(
          screen.getByTestId(
            "radar-incompatible",
          ),
        ).toHaveTextContent(
          "different radar dimensions",
        );

        expect(
          screen.queryByRole(
            "img",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "can hide internal guidance in compact comparison layouts",
      () => {
        renderLocalized(
          <RadarProfile
            primary={createSeries()}
            showHeader={false}
          />,
        );

        expect(
          screen.queryByText(
            "Position-relative playing style",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            "Percentile · 0–100",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByRole(
            "img",
            {
              name:
                "Playing style radar for Michael Olise",
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "renders an explicit unavailable state",
      () => {
        renderLocalized(
          <RadarProfile
            primary={
              createSeries({
                available:
                  false,
                dimensions:
                  [],
              })
            }
          />,
        );

        expect(
          screen.getByTestId(
            "radar-unavailable",
          ),
        ).toHaveTextContent(
          "Playing-style radar data are not available for Michael Olise.",
        );

        expect(
          screen.queryByRole(
            "img",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "localizes radar guidance while preserving backend axis labels",
      () => {
        renderLocalized(
          <RadarProfile
            primary={createSeries()}
          />,
          "tr",
        );

        expect(
          screen.getByRole(
            "img",
            {
              name:
                "Michael Olise için oyun stili radarı",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Pozisyona göre oyun stili",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByLabelText(
            "Radar seri göstergesi",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Creativity",
          ),
        ).toBeInTheDocument();
      },
    );

  },
);
