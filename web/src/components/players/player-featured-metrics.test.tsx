import {
  render,
  screen,
} from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PlayerProfileResponse } from "@/lib/api/types";

import { PlayerFeaturedMetrics } from "./player-featured-metrics";

type Intelligence =
  NonNullable<PlayerProfileResponse["intelligence"]>;

const intelligence: Intelligence = {
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
          value: 0.45,
          performance_percentile: 98.8,
          peer_count: 216,
        },
        {
          key: "key_passes_per90",
          label: "Key passes per 90",
          short_label: "Key passes / 90",
          unit: "per90",
          value: 2.3,
          performance_percentile: 99.5,
          peer_count: 216,
        },
      ],
    },
    {
      key: "progression",
      metrics: [
        {
          key: "total_progression_per90",
          label: "Total progression per 90",
          short_label: "Progression / 90",
          unit: "per90",
          value: 81.2,
          performance_percentile: 94.1,
          peer_count: 216,
        },
      ],
    },
    {
      key: "possession",
      metrics: [
        {
          key: "pass_accuracy_pct",
          label: "Pass accuracy",
          short_label: "Pass accuracy",
          unit: "percent",
          value: 88.4,
          performance_percentile: 85.2,
          peer_count: 216,
        },
      ],
    },
  ],
};

describe("PlayerFeaturedMetrics", () => {
  it("surfaces position-aware backend metrics with percentile context", () => {
    render(
      <PlayerFeaturedMetrics
        intelligence={intelligence}
      />,
    );

    expect(
      screen.getByRole("heading", {
        name: "Position-relevant metrics",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "xA / 90",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Progression / 90",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Pass accuracy",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getAllByText(
        "216",
      ).length,
    ).toBeGreaterThan(0);
  });

  it("renders nothing when position-aware intelligence is unavailable", () => {
    const { container } = render(
      <PlayerFeaturedMetrics
        intelligence={null}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});
