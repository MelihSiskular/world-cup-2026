import {
  describe,
  expect,
  it,
} from "vitest";

import {
  createMultiComparisonHref,
  parseMultiComparisonIdentifiers,
} from "@/lib/transfer-intelligence/multi-comparison-selection";

describe(
  "multi-player comparison identifiers",
  () => {
    it(
      "parses one target and up to three ordered candidates",
      () => {
        expect(
          parseMultiComparisonIdentifiers(
            "978838",
            "789071,805078,123456",
          ),
        ).toEqual({
          success: true,
          values: {
            targetPlayerId:
              978838,
            candidatePlayerIds: [
              789071,
              805078,
              123456,
            ],
          },
        });
      },
    );

    it(
      "rejects invalid target and candidate identifiers",
      () => {
        expect(
          parseMultiComparisonIdentifiers(
            "not-a-player",
            "789071",
          ),
        ).toMatchObject({
          success: false,
          code: "invalid_target",
        });

        expect(
          parseMultiComparisonIdentifiers(
            "978838",
            "789071,invalid",
          ),
        ).toMatchObject({
          success: false,
          code:
            "invalid_candidate",
        });
      },
    );

    it(
      "requires between one and three candidates",
      () => {
        expect(
          parseMultiComparisonIdentifiers(
            "978838",
            "",
          ),
        ).toMatchObject({
          success: false,
          code:
            "invalid_candidate",
        });

        expect(
          parseMultiComparisonIdentifiers(
            "978838",
            "1,2,3,4",
          ),
        ).toMatchObject({
          success: false,
          code:
            "invalid_candidate_count",
        });
      },
    );

    it(
      "rejects target reuse and duplicate candidates",
      () => {
        expect(
          parseMultiComparisonIdentifiers(
            "978838",
            "978838",
          ),
        ).toMatchObject({
          success: false,
          code:
            "duplicate_player",
        });

        expect(
          parseMultiComparisonIdentifiers(
            "978838",
            "789071,789071",
          ),
        ).toMatchObject({
          success: false,
          code:
            "duplicate_player",
        });
      },
    );

    it(
      "rejects repeated candidate query parameters",
      () => {
        expect(
          parseMultiComparisonIdentifiers(
            "978838",
            [
              "789071",
              "805078",
            ],
          ),
        ).toMatchObject({
          success: false,
          code:
            "invalid_candidate",
        });
      },
    );

    it(
      "creates a canonical shareable comparison URL",
      () => {
        expect(
          createMultiComparisonHref({
            targetPlayerId:
              978838,
            candidatePlayerIds: [
              789071,
              805078,
            ],
          }),
        ).toBe(
          "/compare/multi/978838"
          + "?candidates=789071%2C805078",
        );
      },
    );

    it(
      "refuses to serialize an invalid domain value",
      () => {
        expect(() =>
          createMultiComparisonHref({
            targetPlayerId:
              978838,
            candidatePlayerIds: [
              978838,
            ],
          }),
        ).toThrow(
          "Target and candidate player IDs must be unique.",
        );
      },
    );
  },
);
