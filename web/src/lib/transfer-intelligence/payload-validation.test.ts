import {
  describe,
  expect,
  it,
} from "vitest";

import {
  validateTransferAnalysisPayload,
} from "@/lib/transfer-intelligence/payload-validation";

describe(
  "validateTransferAnalysisPayload",
  () => {
    it(
      "accepts a player ID and applies defaults",
      () => {
        const result =
          validateTransferAnalysisPayload(
            {
              player_id:
                978838,
            },
          );

        expect(
          result.success,
        ).toBe(true);

        if (
          result.success
        ) {
          expect(
            result.data,
          ).toMatchObject({
            player_id:
              978838,
            minimum_minutes:
              150,
            minimum_role_confidence:
              50,
            neutral_heatmap_score:
              70,
          });
        }
      },
    );

    it(
      "accepts a player name",
      () => {
        const result =
          validateTransferAnalysisPayload(
            {
              player:
                "Michael Olise",
            },
          );

        expect(
          result.success,
        ).toBe(true);

        if (
          result.success
        ) {
          expect(
            result.data.player,
          ).toBe(
            "Michael Olise",
          );
        }
      },
    );

    it.each([
      {
        label:
          "neither player selector",
        value: {},
      },
      {
        label:
          "both player selectors",
        value: {
          player:
            "Michael Olise",
          player_id:
            978838,
        },
      },
    ])(
      "rejects $label",
      ({
        value,
      }) => {
        const result =
          validateTransferAnalysisPayload(
            value,
          );

        expect(
          result,
        ).toEqual({
          success: false,
          message:
            "Provide exactly one of player or player_id.",
        });
      },
    );

    it(
      "rejects unknown request fields",
      () => {
        const result =
          validateTransferAnalysisPayload(
            {
              player_id:
                978838,
              unexpected:
                true,
            },
          );

        expect(
          result.success,
        ).toBe(false);
      },
    );

    it(
      "rejects out-of-range thresholds",
      () => {
        const result =
          validateTransferAnalysisPayload(
            {
              player_id:
                978838,
              neutral_heatmap_score:
                101,
            },
          );

        expect(
          result.success,
        ).toBe(false);
      },
    );
  },
);
