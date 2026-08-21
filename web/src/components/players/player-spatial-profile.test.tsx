import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  PlayerSpatialProfile,
} from "@/components/players/player-spatial-profile";
import type {
  HeatmapPlayerResponse,
} from "@/lib/api/types";

const heatmap: HeatmapPlayerResponse = {
  player_id: 978838,
  player_name: "Michael Olise",
  available: true,
  grid_width: 2,
  grid_height: 2,
  grid: [
    [0.1, 0.4],
    [0.7, 1],
  ],
  matches_with_heatmap: 6,
  heatmap_point_count: 509,
  weighted_mean_x: 61.3,
  weighted_mean_y: 41.2,
  peak_cell_x: 62.5,
  peak_cell_y: 42.5,
  heatmap_entropy: 0.81,
};

describe("PlayerSpatialProfile", () => {
  it("renders measured heatmap and average position evidence", () => {
    render(
      <PlayerSpatialProfile
        playerName="Michael Olise"
        heatmap={heatmap}
        isPending={false}
        isError={false}
        onRetry={() => undefined}
      />,
    );

    expect(
      screen.getByRole("img", {
        name: "Tournament heatmap for Michael Olise",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByTestId(
        "heatmap-average-position",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText("509"),
    ).toBeInTheDocument();
  });

  it("renders a compact unavailable state without inventing spatial evidence", () => {
    render(
      <PlayerSpatialProfile
        playerName="Michael Olise"
        heatmap={{
          ...heatmap,
          available: false,
          grid_width: null,
          grid_height: null,
          grid: null,
        }}
        isPending={false}
        isError={false}
        onRetry={() => undefined}
      />,
    );

    expect(
      screen.getByText(
        "Spatial data unavailable",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByTestId(
        "heatmap-average-position",
      ),
    ).not.toBeInTheDocument();
  });

  it("allows spatial data to be retried independently", () => {
    const onRetry = vi.fn();

    render(
      <PlayerSpatialProfile
        playerName="Michael Olise"
        heatmap={null}
        isPending={false}
        isError
        onRetry={onRetry}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Retry spatial data",
      }),
    );

    expect(onRetry).toHaveBeenCalledOnce();
  });
});
