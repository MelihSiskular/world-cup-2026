import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  fetchHeatmapComparison,
} from "@/lib/api/browser-transfer-intelligence";

const fetchMock =
  vi.fn<typeof fetch>();

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

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
