import {
  z,
} from "zod";

import type {
  TransferAnalysisPayload,
} from "@/lib/api/types";

export const DEFAULT_TRANSFER_ANALYSIS_VALUES = {
  minimumMinutes: 150,
  minimumRoleConfidence: 50,
  maximumMarketValueMillions: undefined,
  neutralHeatmapScore: 70,
} as const;

export const transferAnalysisFormSchema =
  z.object({
    minimumMinutes:
      z
        .number()
        .finite(
          "Minimum minutes must be a number.",
        )
        .min(
          0,
          "Minimum minutes cannot be negative.",
        ),

    minimumRoleConfidence:
      z
        .number()
        .finite(
          "Role confidence must be a number.",
        )
        .min(
          0,
          "Role confidence cannot be below 0%.",
        )
        .max(
          100,
          "Role confidence cannot exceed 100%.",
        ),

    maximumMarketValueMillions:
      z
        .number()
        .finite(
          "Market value must be a number.",
        )
        .min(
          0,
          "Market value cannot be negative.",
        )
        .optional(),

    neutralHeatmapScore:
      z
        .number()
        .finite(
          "Heatmap score must be a number.",
        )
        .min(
          0,
          "Heatmap score cannot be below 0%.",
        )
        .max(
          100,
          "Heatmap score cannot exceed 100%.",
        ),
  });

export type TransferAnalysisFormValues =
  z.infer<
    typeof transferAnalysisFormSchema
  >;

export function createTransferAnalysisPayload(
  playerId: number,
  values: TransferAnalysisFormValues,
): TransferAnalysisPayload {
  return {
    player_id: playerId,
    minimum_minutes:
      values.minimumMinutes,
    minimum_role_confidence:
      values.minimumRoleConfidence,
    maximum_market_value:
      values.maximumMarketValueMillions ===
      undefined
        ? null
        : values
            .maximumMarketValueMillions *
          1_000_000,
    neutral_heatmap_score:
      values.neutralHeatmapScore,
  };
}

export function createAnalysisSearchParameters(
  values: TransferAnalysisFormValues,
): URLSearchParams {
  const parameters =
    new URLSearchParams({
      minimum_minutes: String(
        values.minimumMinutes,
      ),
      minimum_role_confidence:
        String(
          values.minimumRoleConfidence,
        ),
      neutral_heatmap_score:
        String(
          values.neutralHeatmapScore,
        ),
    });

  if (
    values.maximumMarketValueMillions !==
    undefined
  ) {
    parameters.set(
      "maximum_market_value",
      String(
        values
          .maximumMarketValueMillions *
          1_000_000,
      ),
    );
  }

  return parameters;
}
