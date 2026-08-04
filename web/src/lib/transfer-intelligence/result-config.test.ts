import {
  describe,
  expect,
  it,
} from "vitest";

import type {
  TransferRecommendationResponse,
} from "@/lib/api/types";
import {
  getRecommendationRank,
  getRecommendationScore,
  parseTransferMode,
} from "@/lib/transfer-intelligence/result-config";

const recommendation = {
  player_id: 100,
  player_name:
    "Test Candidate",
  recommendation_type:
    "Balanced alternative",
  recommendation_strength:
    "Good",
  why_recommended:
    "Good profile fit.",
  immediate_score:
    66.5,
  immediate_rank:
    1,
  development_score:
    71.2,
  development_rank:
    2,
  value_score:
    81.1,
  value_rank:
    3,
  short_term_score:
    62.4,
  short_term_rank:
    4,
} as TransferRecommendationResponse;

describe(
  "parseTransferMode",
  () => {
    it.each([
      "immediate",
      "development",
      "value",
      "short_term",
    ] as const)(
      "accepts %s",
      (mode) => {
        expect(
          parseTransferMode(
            mode,
          ),
        ).toBe(mode);
      },
    );

    it(
      "uses the first repeated value",
      () => {
        expect(
          parseTransferMode([
            "value",
            "immediate",
          ]),
        ).toBe(
          "value",
        );
      },
    );

    it.each([
      undefined,
      "unknown",
      "",
    ])(
      "rejects %s",
      (value) => {
        expect(
          parseTransferMode(
            value,
          ),
        ).toBeNull();
      },
    );
  },
);

describe(
  "recommendation score and rank helpers",
  () => {
    it.each([
      [
        "immediate",
        66.5,
        1,
      ],
      [
        "development",
        71.2,
        2,
      ],
      [
        "value",
        81.1,
        3,
      ],
      [
        "short_term",
        62.4,
        4,
      ],
    ] as const)(
      "reads %s values",
      (
        mode,
        score,
        rank,
      ) => {
        expect(
          getRecommendationScore(
            mode,
            recommendation,
          ),
        ).toBe(score);

        expect(
          getRecommendationRank(
            mode,
            recommendation,
          ),
        ).toBe(rank);
      },
    );
  },
);
