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
import {
  describe,
  expect,
  it,
} from "vitest";

import englishMessages from "../../../messages/en.json";
import turkishMessages from "../../../messages/tr.json";

import type {
  PlayerProfileResponse,
} from "@/lib/api/types";

import {
  PlayerScoutingInsights,
} from "./player-scouting-insights";

type TestLocale =
  "en" | "tr";

function render(
  element: ReactElement,
  locale: TestLocale = "en",
) {
  return renderTestingLibrary(
    <NextIntlClientProvider
      locale={locale}
      messages={
        locale === "tr"
          ? turkishMessages
          : englishMessages
      }
    >
      {element}
    </NextIntlClientProvider>,
  );
}

type PlayerIntelligence =
  NonNullable<
    PlayerProfileResponse["intelligence"]
  >;

const intelligence: PlayerIntelligence = {
  position_group: "midfielder",
  sample: {
    target_minutes: 650,
    minimum_peer_minutes: 180,
    target_meets_peer_minimum: true,
  },
  groups: [],
  strengths: [
    {
      kind: "strength",
      group: "creation",
      group_label:
        "Chance creation",
      metric_key:
        "expected_assists_per90",
      metric_label:
        "Expected assists per 90",
      metric_short_label:
        "xA / 90",
      value: 0.4533,
      percentile: 98.8,
      peer_count: 216,
      evidence:
        "xA / 90 ranks at the 98.8 performance percentile among 216 same-position peers.",
    },
  ],
  watch_outs: [
    {
      kind: "watch_out",
      group: "possession",
      group_label:
        "Possession",
      metric_key:
        "possession_lost_per90",
      metric_label:
        "Possession lost per 90",
      metric_short_label:
        "Poss. lost / 90",
      value: 15,
      percentile: 4.9,
      peer_count: 216,
      evidence:
        "Poss. lost / 90 ranks at the 4.9 performance percentile among 216 same-position peers.",
    },
  ],
};

describe(
  "PlayerScoutingInsights",
  () => {
    it(
      "renders backend-selected strengths and watch-outs",
      () => {
        render(
          <PlayerScoutingInsights
            intelligence={
              intelligence
            }
          />,
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Scouting insights",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "xA / 90",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Poss. lost / 90",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /98.8 performance percentile among 216 same-position peers/,
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /4.9 performance percentile among 216 same-position peers/,
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "exposes percentiles accessibly",
      () => {
        render(
          <PlayerScoutingInsights
            intelligence={
              intelligence
            }
          />,
        );

        expect(
          screen.getByRole(
            "progressbar",
            {
              name:
                "xA / 90 performance percentile",
            },
          ),
        ).toHaveAttribute(
          "aria-valuenow",
          "98.8",
        );

        expect(
          screen.getByRole(
            "progressbar",
            {
              name:
                "Poss. lost / 90 performance percentile",
            },
          ),
        ).toHaveAttribute(
          "aria-valuenow",
          "4.9",
        );
      },
    );

    it(
      "renders an explicit unavailable state without intelligence",
      () => {
        render(
          <PlayerScoutingInsights
            intelligence={null}
          />,
        );

        expect(
          screen.getByText(
            /Position-aware scouting insights were not reported/,
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "localizes scouting context while preserving backend evidence",
      () => {
        render(
          <PlayerScoutingInsights
            intelligence={
              intelligence
            }
          />,
          "tr",
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Scouting içgörüleri",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Güçlü yönler",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Öne çıkan sinyaller",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Dikkat noktaları",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "İncelenecek alanlar",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "1 sinyal",
          ),
        ).toHaveLength(2);

        expect(
          screen.getByRole(
            "progressbar",
            {
              name:
                "xA / 90 performans yüzdelik dilimi",
            },
          ),
        ).toHaveAttribute(
          "aria-valuenow",
          "98.8",
        );

        expect(
          screen.getByText(
            /98.8 performance percentile among 216 same-position peers/,
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Chance creation",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "localizes the unavailable scouting state in Turkish",
      () => {
        render(
          <PlayerScoutingInsights
            intelligence={null}
          />,
          "tr",
        );

        expect(
          screen.getByText(
            "Bu oyuncu için pozisyona özgü scouting içgörüleri bildirilmedi.",
          ),
        ).toBeInTheDocument();
      },
    );


  },
);
