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

import type { PlayerProfileResponse } from "@/lib/api/types";

import { PlayerPerformanceProfile } from "./player-performance-profile";

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
  strengths: [],
  watch_outs: [],
  groups: [
    {
      key: "creation",
      metrics: [
        {
          key: "expected_assists_per90",
          label: "Expected assists per 90",
          short_label: "xA / 90",
          unit: "per90",
          value: 0.4533,
          performance_percentile: 98.8,
          peer_count: 216,
        },
        {
          key: "key_passes_per90",
          label: "Key passes per 90",
          short_label: "Key passes / 90",
          unit: "per90",
          value: 2.4923,
          performance_percentile: 94.2,
          peer_count: 216,
        },
      ],
    },
    {
      key: "possession",
      metrics: [
        {
          key: "pass_accuracy",
          label: "Pass accuracy",
          short_label: "Pass accuracy",
          unit: "percent",
          value: 86.62,
          performance_percentile: 55.8,
          peer_count: 216,
        },
      ],
    },
  ],
};

describe("PlayerPerformanceProfile", () => {
  it("renders backend metric groups and values", () => {
    render(<PlayerPerformanceProfile intelligence={intelligence} />);

    expect(
      screen.getByRole("heading", {
        name: "Performance profile",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Chance creation",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Possession",
      }),
    ).toBeInTheDocument();

    expect(screen.getByText("0.45")).toBeInTheDocument();

    expect(screen.getByText("86.62%")).toBeInTheDocument();
  });

  it("renders backend performance percentiles accessibly", () => {
    render(<PlayerPerformanceProfile intelligence={intelligence} />);

    expect(
      screen.getByRole("progressbar", {
        name: "xA / 90 performance percentile",
      }),
    ).toHaveAttribute("aria-valuenow", "98.8");

    expect(
      screen.getByRole("progressbar", {
        name: "Pass accuracy performance percentile",
      }),
    ).toHaveAttribute("aria-valuenow", "55.8");

    expect(screen.getAllByText(/216/).length).toBeGreaterThan(0);
  });

  it("uses compact metric copy without repeating unit and peer sentences", () => {
    render(<PlayerPerformanceProfile intelligence={intelligence} />);

    expect(
      screen.getAllByTestId(
        "performance-group-column",
      ),
    ).toHaveLength(2);

    expect(
      screen.queryByText("Metric group"),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByText("2 metrics"),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByText("1 metric"),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByText("Per 90"),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByText(/Compared with/),
    ).not.toBeInTheDocument();

    expect(
      screen.getAllByText("n=216 peers"),
    ).toHaveLength(3);

    expect(
      screen.getByText("X.XX"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("75.0"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("n=XXX peers"),
    ).toBeInTheDocument();
  });

  it("preserves a reported metric value when percentile evidence is unavailable", () => {
    const limitedEvidence: PlayerIntelligence = {
      ...intelligence,
      groups: [
        {
          key: "progression",
          metrics: [
            {
              key: "progressive_carries_per90",
              label: "Progressive carries per 90",
              short_label: "Prog. carries / 90",
              unit: "per90",
              value: 5.95,
              performance_percentile: null,
              peer_count: 4,
            },
          ],
        },
      ],
    };

    render(<PlayerPerformanceProfile intelligence={limitedEvidence} />);

    expect(screen.getByText("5.95")).toBeInTheDocument();

    expect(screen.getByText("Percentile unavailable")).toBeInTheDocument();

    expect(
      screen.queryByRole("progressbar", {
        name: "Prog. carries / 90 performance percentile",
      }),
    ).not.toBeInTheDocument();

    expect(screen.getByText(/4/)).toBeInTheDocument();
  });

  it("renders an explicit empty state when no metric groups are available", () => {
    render(
      <PlayerPerformanceProfile
        intelligence={{
          ...intelligence,
          groups: [],
        }}
      />,
    );

    expect(
      screen.getByText(/No position-aware performance metrics were available/),
    ).toBeInTheDocument();
  });

  it("renders an explicit unavailable state without intelligence", () => {
    render(<PlayerPerformanceProfile intelligence={null} />);

    expect(
      screen.getByText(/Position-aware performance metrics were not reported/),
    ).toBeInTheDocument();
  });

  it("renders goalkeeper-specific metric groups without assuming outfield metrics", () => {
    const goalkeeperIntelligence: PlayerIntelligence = {
      position_group: "goalkeeper",
      sample: {
        target_minutes: 540,
        minimum_peer_minutes: 180,
        target_meets_peer_minimum: true,
      },
      strengths: [],
      watch_outs: [],
      groups: [
        {
          key: "goalkeeping",
          metrics: [
            {
              key: "saves_per90",
              label: "Saves per 90",
              short_label: "Saves / 90",
              unit: "per90",
              value: 4.25,
              performance_percentile: 87.5,
              peer_count: 48,
            },
            {
              key: "goals_prevented_per90",
              label: "Goals prevented per 90",
              short_label: "Goals prevented / 90",
              unit: "per90",
              value: 0.31,
              performance_percentile: 91.7,
              peer_count: 48,
            },
          ],
        },
      ],
    };

    render(<PlayerPerformanceProfile intelligence={goalkeeperIntelligence} />);

    expect(
      screen.getByRole("heading", {
        name: "Goalkeeping",
      }),
    ).toBeInTheDocument();

    expect(screen.getByText("Saves / 90")).toBeInTheDocument();

    expect(screen.getByText("Goals prevented / 90")).toBeInTheDocument();

    expect(
      screen.getByRole("progressbar", {
        name: "Saves / 90 performance percentile",
      }),
    ).toHaveAttribute("aria-valuenow", "87.5");
  });

  it("keeps a zero percentile distinct from unavailable evidence", () => {
    const zeroPercentile: PlayerIntelligence = {
      ...intelligence,
      groups: [
        {
          key: "possession",
          metrics: [
            {
              key: "possession_lost_per90",
              label: "Possession lost per 90",
              short_label: "Poss. lost / 90",
              unit: "per90",
              value: 12.4,
              performance_percentile: 0,
              peer_count: 216,
            },
          ],
        },
      ],
    };

    render(<PlayerPerformanceProfile intelligence={zeroPercentile} />);

    expect(screen.getByText("12.4")).toBeInTheDocument();

    expect(
      screen.getByRole("progressbar", {
        name: "Poss. lost / 90 performance percentile",
      }),
    ).toHaveAttribute("aria-valuenow", "0");

    expect(
      screen.queryByText("Percentile unavailable"),
    ).not.toBeInTheDocument();

    expect(screen.getByText(/216/)).toBeInTheDocument();
  });

  it("localizes performance context and numbers in Turkish", () => {
    render(
      <PlayerPerformanceProfile
        intelligence={intelligence}
      />,
      "tr",
    );

    expect(
      screen.getByRole(
        "heading",
        {
          name:
            "Performans profili",
        },
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole(
        "heading",
        {
          name:
            "Fırsat yaratma",
        },
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole(
        "heading",
        {
          name:
            "Topa sahip olma",
        },
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "0,45",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "86,62%",
      ),
    ).toBeInTheDocument();

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
      screen.getAllByText(
        "n=216 eş",
      ),
    ).toHaveLength(3);

    expect(
      screen.getByText(
        "Profil nasıl okunur?",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "xA / 90",
      ),
    ).toBeInTheDocument();
  });

  it("localizes the empty performance state in Turkish", () => {
    render(
      <PlayerPerformanceProfile
        intelligence={{
          ...intelligence,
          groups: [],
        }}
      />,
      "tr",
    );

    expect(
      screen.getByText(
        "Bu oyuncu için pozisyona özgü performans metriği bulunamadı.",
      ),
    ).toBeInTheDocument();
  });


});
