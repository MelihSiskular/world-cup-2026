import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  fetchHeatmapComparison,
  fetchPlayerHeatmap,
  fetchRadarComparison,
} from "@/lib/api/browser-transfer-intelligence";

const fetchMock =
  vi.fn<typeof fetch>();

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

describe(
  "fetchPlayerHeatmap",
  () => {
    it(
      "requests the single-player heatmap BFF route",
      async () => {
        fetchMock.mockResolvedValue(
          new Response(
            JSON.stringify({
              player_id: 978838,
              player_name: "Michael Olise",
              available: true,
              grid_width: 21,
              grid_height: 14,
              grid: [],
              matches_with_heatmap: 6,
              heatmap_point_count: 509,
              weighted_mean_x: 61.3,
              weighted_mean_y: 41.2,
            }),
            {
              status: 200,
              headers: {
                "content-type":
                  "application/json",
              },
            },
          ),
        );

        vi.stubGlobal(
          "fetch",
          fetchMock,
        );

        const result =
          await fetchPlayerHeatmap(
            978838,
          );

        expect(
          fetchMock,
        ).toHaveBeenCalledTimes(1);

        const [
          requestPath,
          options,
        ] =
          fetchMock.mock.calls[0] ??
          [];

        expect(requestPath).toBe(
          "/api/transfer-intelligence/heatmap/978838",
        );

        expect(options).toMatchObject({
          cache: "no-store",
        });

        expect(result.player_id).toBe(
          978838,
        );

        expect(
          result.weighted_mean_x,
        ).toBe(61.3);

        expect(
          result.weighted_mean_y,
        ).toBe(41.2);
      },
    );
  },
);


describe(
  "fetchHeatmapComparison",
  () => {
    it(
      "requests the target-to-candidate heatmap BFF route",
      async () => {
        fetchMock.mockResolvedValue(
          new Response(
            JSON.stringify({
              target: {
                player_id: 978838,
                player_name:
                  "Michael Olise",
                available: true,
                grid_width: 21,
                grid_height: 14,
                grid: [],
              },
              candidate: {
                player_id: 789071,
                player_name:
                  "Dani Olmo",
                available: true,
                grid_width: 21,
                grid_height: 14,
                grid: [],
              },
              similarity: {
                available: true,
                heatmap_similarity_score_pct:
                  90.9154,
              },
            }),
            {
              status: 200,
              headers: {
                "content-type":
                  "application/json",
              },
            },
          ),
        );

        vi.stubGlobal(
          "fetch",
          fetchMock,
        );

        const result =
          await fetchHeatmapComparison(
            978838,
            789071,
          );

        expect(
          fetchMock,
        ).toHaveBeenCalledTimes(
          1,
        );

        const [
          path,
          options,
        ] =
          fetchMock.mock.calls[0] ??
          [];

        expect(path).toBe(
          "/api/transfer-intelligence/heatmap-comparison/978838/789071",
        );

        expect(options).toMatchObject({
          cache: "no-store",
        });

        expect(
          result.target.player_name,
        ).toBe(
          "Michael Olise",
        );

        expect(
          result.candidate.player_name,
        ).toBe(
          "Dani Olmo",
        );

        expect(
          result.similarity
            .heatmap_similarity_score_pct,
        ).toBe(
          90.9154,
        );

        expect(
          "effective_heatmap_score_pct"
          in result.similarity,
        ).toBe(false);
      },
    );
  },
);



describe(
  "fetchRadarComparison",
  () => {
    it(
      "requests the target-to-candidate radar BFF route",
      async () => {
        fetchMock.mockResolvedValue(
          new Response(
            JSON.stringify({
              target: {
                player_id: 978838,
                player_name:
                  "Michael Olise",
                position: "M",
                available: true,
                peer_count: 216,
                dimensions: [
                  {
                    key: "creativity",
                    label: "Creativity",
                    raw_score: 4.516,
                    percentile: 100,
                    peer_count: 216,
                  },
                ],
              },
              candidate: {
                player_id: 789071,
                player_name:
                  "Dani Olmo",
                position: "M",
                available: true,
                peer_count: 216,
                dimensions: [
                  {
                    key: "creativity",
                    label: "Creativity",
                    raw_score: 1.604,
                    percentile: 91.7,
                    peer_count: 216,
                  },
                ],
              },
              comparison: {
                same_position: true,
                overlay_available: true,
                reason: null,
              },
            }),
            {
              status: 200,
              headers: {
                "content-type":
                  "application/json",
              },
            },
          ),
        );

        vi.stubGlobal(
          "fetch",
          fetchMock,
        );

        const result =
          await fetchRadarComparison(
            978838,
            789071,
          );

        expect(
          fetchMock,
        ).toHaveBeenCalledTimes(
          1,
        );

        const [
          path,
          options,
        ] =
          fetchMock.mock.calls[0] ??
          [];

        expect(path).toBe(
          "/api/transfer-intelligence/radar-comparison/978838/789071",
        );

        expect(options).toMatchObject({
          cache: "no-store",
        });

        expect(
          result.target.player_name,
        ).toBe(
          "Michael Olise",
        );

        expect(
          result.target
            .dimensions[0]
            ?.percentile,
        ).toBe(
          100,
        );

        expect(
          result.candidate.player_name,
        ).toBe(
          "Dani Olmo",
        );

        expect(
          result.comparison
            .overlay_available,
        ).toBe(true);

        expect(
          result.comparison.reason,
        ).toBeNull();
      },
    );
  },
);
