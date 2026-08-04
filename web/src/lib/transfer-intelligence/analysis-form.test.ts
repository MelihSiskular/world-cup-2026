import {
  describe,
  expect,
  it,
} from "vitest";

import {
  createAnalysisSearchParameters,
  createTransferAnalysisPayload,
  DEFAULT_TRANSFER_ANALYSIS_VALUES,
  parseAnalysisSearchParameters,
} from "@/lib/transfer-intelligence/analysis-form";

describe(
  "analysis search parameters",
  () => {
    it(
      "uses defaults when query parameters are missing",
      () => {
        const result =
          parseAnalysisSearchParameters(
            {},
          );

        expect(result).toEqual({
          success: true,
          values: {
            ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
          },
        });
      },
    );

    it(
      "converts market value from euros to millions",
      () => {
        const result =
          parseAnalysisSearchParameters(
            {
              minimum_minutes:
                "300",
              minimum_role_confidence:
                "60",
              maximum_market_value:
                "50000000",
              neutral_heatmap_score:
                "65",
            },
          );

        expect(result).toEqual({
          success: true,
          values: {
            minimumMinutes:
              300,
            minimumRoleConfidence:
              60,
            maximumMarketValueMillions:
              50,
            neutralHeatmapScore:
              65,
          },
        });
      },
    );

    it(
      "uses the first value from repeated query parameters",
      () => {
        const result =
          parseAnalysisSearchParameters(
            {
              minimum_minutes: [
                "200",
                "400",
              ],
            },
          );

        expect(
          result.success,
        ).toBe(true);

        if (
          result.success
        ) {
          expect(
            result.values
              .minimumMinutes,
          ).toBe(200);
        }
      },
    );

    it(
      "rejects invalid percentage thresholds",
      () => {
        const result =
          parseAnalysisSearchParameters(
            {
              minimum_role_confidence:
                "101",
            },
          );

        expect(
          result.success,
        ).toBe(false);

        if (
          !result.success
        ) {
          expect(
            result.message,
          ).toBe(
            "Role confidence cannot exceed 100%.",
          );
        }
      },
    );
  },
);

describe(
  "analysis payload generation",
  () => {
    it(
      "creates a payload without a market limit",
      () => {
        expect(
          createTransferAnalysisPayload(
            978838,
            {
              minimumMinutes:
                150,
              minimumRoleConfidence:
                50,
              maximumMarketValueMillions:
                undefined,
              neutralHeatmapScore:
                70,
            },
          ),
        ).toEqual({
          player_id:
            978838,
          minimum_minutes:
            150,
          minimum_role_confidence:
            50,
          maximum_market_value:
            null,
          neutral_heatmap_score:
            70,
        });
      },
    );

    it(
      "converts a million-euro form value to euros",
      () => {
        const payload =
          createTransferAnalysisPayload(
            978838,
            {
              minimumMinutes:
                200,
              minimumRoleConfidence:
                55,
              maximumMarketValueMillions:
                49.5,
              neutralHeatmapScore:
                60,
            },
          );

        expect(
          payload
            .maximum_market_value,
        ).toBe(
          49_500_000,
        );
      },
    );

    it(
      "creates stable URL search parameters",
      () => {
        const parameters =
          createAnalysisSearchParameters(
            {
              minimumMinutes:
                250,
              minimumRoleConfidence:
                65,
              maximumMarketValueMillions:
                40,
              neutralHeatmapScore:
                75,
            },
          );

        expect(
          parameters.toString(),
        ).toBe(
          [
            "minimum_minutes=250",
            "minimum_role_confidence=65",
            "neutral_heatmap_score=75",
            "maximum_market_value=40000000",
          ].join("&"),
        );
      },
    );
  },
);
