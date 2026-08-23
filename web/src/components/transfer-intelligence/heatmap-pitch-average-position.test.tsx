import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
} from "vitest";

import {
  HeatmapPitch,
} from "@/components/transfer-intelligence/heatmap-pitch";
import type {
  HeatmapPlayerResponse,
} from "@/lib/api/types";

function buildPlayer(
  overrides: Partial<HeatmapPlayerResponse> = {},
): HeatmapPlayerResponse {
  return {
    player_id: 978838,
    player_name: "Michael Olise",
    available: true,
    grid_width: 2,
    grid_height: 2,
    grid: [
      [0.2, 0.4],
      [0.7, 1],
    ],
    matches_with_heatmap: 6,
    heatmap_point_count: 509,
    weighted_mean_x: 61.3,
    weighted_mean_y: 41.2,
    peak_cell_x: 62.5,
    peak_cell_y: 42.5,
    heatmap_entropy: 0.81,
    ...overrides,
  };
}

describe(
  "HeatmapPitch average position",
  () => {
    it(
      "renders measured average position on the heatmap pitch",
      () => {
        render(
          <HeatmapPitch
            player={buildPlayer()}
            showAveragePosition
          />,
        );

        const marker =
          screen.getByTestId(
            "heatmap-average-position",
          );

        const circles =
          marker.querySelectorAll(
            "circle",
          );

        expect(circles).toHaveLength(2);

        const outerMarker =
          circles[0];

        expect(
          Number(
            outerMarker?.getAttribute(
              "cx",
            ),
          ),
        ).toBeCloseTo(
          64.365,
          3,
        );

        expect(
          Number(
            outerMarker?.getAttribute(
              "cy",
            ),
          ),
        ).toBeCloseTo(
          39.984,
          3,
        );

        expect(
          screen.getByText(
            "Average tournament position",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "does not invent a marker when coordinates are unavailable",
      () => {
        render(
          <HeatmapPitch
            player={buildPlayer({
              weighted_mean_x: null,
              weighted_mean_y: null,
            })}
            showAveragePosition
          />,
        );

        expect(
          screen.queryByTestId(
            "heatmap-average-position",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            "Average tournament position",
          ),
        ).not.toBeInTheDocument();
      },
    );
  },
);
