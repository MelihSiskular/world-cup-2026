import {
  z,
} from "zod";

import type {
  TransferAnalysisPayload,
} from "@/lib/api/types";

const transferAnalysisPayloadSchema =
  z
    .object({
      player:
        z
          .string()
          .trim()
          .min(1)
          .nullable()
          .optional(),

      player_id:
        z
          .number()
          .int()
          .positive()
          .nullable()
          .optional(),

      minimum_minutes:
        z
          .number()
          .finite()
          .min(0)
          .default(150),

      minimum_role_confidence:
        z
          .number()
          .finite()
          .min(0)
          .max(100)
          .default(50),

      maximum_market_value:
        z
          .number()
          .finite()
          .min(0)
          .nullable()
          .optional(),

      neutral_heatmap_score:
        z
          .number()
          .finite()
          .min(0)
          .max(100)
          .default(70),
    })
    .strict()
    .superRefine(
      (
        value,
        context,
      ) => {
        const hasPlayerName =
          typeof value.player ===
            "string" &&
          value.player.length > 0;

        const hasPlayerId =
          typeof value.player_id ===
          "number";

        if (
          hasPlayerName ===
          hasPlayerId
        ) {
          context.addIssue({
            code:
              "custom",
            message:
              "Provide exactly one of player or player_id.",
          });
        }
      },
    );

type ValidatedTransferPayload =
  | Readonly<{
      success: true;
      data: TransferAnalysisPayload;
    }>
  | Readonly<{
      success: false;
      message: string;
    }>;

export function validateTransferAnalysisPayload(
  value: unknown,
): ValidatedTransferPayload {
  const result =
    transferAnalysisPayloadSchema
      .safeParse(value);

  if (!result.success) {
    return {
      success: false,
      message:
        result.error.issues[0]
          ?.message ??
        "The transfer analysis request is invalid.",
    };
  }

  return {
    success: true,
    data:
      result.data as TransferAnalysisPayload,
  };
}
