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
  getHeatmapGridMaximum,
  HeatmapPitch,
} from "@/components/transfer-intelligence/heatmap-pitch";
import type {
  HeatmapPlayerResponse,
} from "@/lib/api/types";

function createPlayer(
  overrides:
    Partial<HeatmapPlayerResponse> = {},
): HeatmapPlayerResponse {
  return {
    player_id: 978838,
    player_name:
      "Michael Olise",
    available: true,
    grid_width: 2,
    grid_height: 2,
    grid: [
      [0.1, 0.2],
      [0.3, 0.4],
    ],
    matches_with_heatmap: 6,
    heatmap_point_count: 509,
    weighted_mean_x: 61.3,
    weighted_mean_y: 41.2,
    peak_cell_x: 62.5,
    peak_cell_y: 42.5,
    heatmap_entropy: 0.944,
    ...overrides,
  };
}

describe(
  "HeatmapPitch",
  () => {
    it(
      "renders every grid cell",
      () => {
        const {
          container,
        } = render(
          <HeatmapPitch
            player={
              createPlayer()
            }
          />,
        );

        expect(
          screen.getByRole(
            "img",
            {
              name:
                "Tournament heatmap for Michael Olise",
            },
          ),
        ).toBeInTheDocument();

        expect(
          container.querySelectorAll(
            '[data-heatmap-cell="true"]',
          ),
        ).toHaveLength(4);

        expect(
          screen.getByText(
            "Relative tournament occupation density",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Attacking direction →",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "renders row zero at the lower edge of the SVG pitch",
      () => {
        render(
          <HeatmapPitch
            player={
              createPlayer({
                grid: [
                  [1, 0],
                  [0, 0],
                ],
              })
            }
          />,
        );

        expect(
          screen.getByTestId(
            "heatmap-cell-0-0",
          ),
        ).toHaveAttribute(
          "y",
          "34",
        );

        expect(
          screen.getByTestId(
            "heatmap-cell-1-0",
          ),
        ).toHaveAttribute(
          "y",
          "0",
        );
      },
    );

    it(
      "respects a shared comparison scale",
      () => {
        render(
          <HeatmapPitch
            player={
              createPlayer({
                grid: [
                  [0.5, 0],
                  [0, 0],
                ],
              })
            }
            scaleMax={1}
          />,
        );

        const cell =
          screen.getByTestId(
            "heatmap-cell-0-0",
          );

        const opacity =
          Number(
            cell.getAttribute(
              "opacity",
            ),
          );

        expect(opacity).toBeGreaterThan(
          0,
        );

        expect(opacity).toBeLessThan(
          0.82,
        );
      },
    );

    it(
      "keeps the local peak as a safety floor for the scale",
      () => {
        render(
          <HeatmapPitch
            player={
              createPlayer({
                grid: [
                  [0.8, 0],
                  [0, 0],
                ],
              })
            }
            scaleMax={0.2}
          />,
        );

        const opacity =
          Number(
            screen
              .getByTestId(
                "heatmap-cell-0-0",
              )
              .getAttribute(
                "opacity",
              ),
          );

        expect(opacity).toBeCloseTo(
          0.82,
        );
      },
    );

    it(
      "renders an explicit unavailable state",
      () => {
        render(
          <HeatmapPitch
            player={
              createPlayer({
                available: false,
                grid: null,
                grid_width: null,
                grid_height: null,
              })
            }
          />,
        );

        expect(
          screen.getByTestId(
            "heatmap-unavailable",
          ),
        ).toHaveTextContent(
          "Tournament heatmap data are not available for Michael Olise.",
        );

        expect(
          screen.queryByRole(
            "img",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
  "can hide density guidance for shared comparison layouts",
  () => {
    render(
      <HeatmapPitch
        player={
          createPlayer()
        }
        showDensityLegend={false}
      />,
    );

    expect(
      screen.queryByText(
        "Relative tournament occupation density",
      ),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByLabelText(
        "Relative occupation density legend",
      ),
    ).not.toBeInTheDocument();

    expect(
      screen.getByRole(
        "img",
        {
          name:
            "Tournament heatmap for Michael Olise",
        },
      ),
    ).toBeInTheDocument();
  },
);

    it(
      "does not render a malformed available grid",
      () => {
        render(
          <HeatmapPitch
            player={
              createPlayer({
                grid_width: 3,
              })
            }
          />,
        );

        expect(
          screen.getByTestId(
            "heatmap-unavailable",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);

describe(
  "getHeatmapGridMaximum",
  () => {
    it(
      "returns the genuine maximum density",
      () => {
        expect(
          getHeatmapGridMaximum(
            [
              [0.01, 0.03],
              [0.07, 0.02],
            ],
          ),
        ).toBe(
          0.07,
        );
      },
    );

    it(
      "returns zero when no grid is available",
      () => {
        expect(
          getHeatmapGridMaximum(
            null,
          ),
        ).toBe(0);
      },
    );
  },
);
