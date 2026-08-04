import type {
  TransferModeName,
  TransferRecommendationResponse,
} from "@/lib/api/types";

export const TRANSFER_MODE_ORDER = [
  "immediate",
  "development",
  "value",
  "short_term",
] as const satisfies readonly TransferModeName[];

type TransferModeDetails =
  Readonly<{
    label: string;
    shortLabel: string;
    description: string;
    scoreLabel: string;
  }>;

export const TRANSFER_MODE_DETAILS = {
  immediate: {
    label: "Immediate impact",
    shortLabel: "Immediate",
    description:
      "Candidates ranked for first-team contribution now.",
    scoreLabel: "Immediate score",
  },
  development: {
    label: "Development investment",
    shortLabel: "Development",
    description:
      "Younger or developing candidates ranked for future value.",
    scoreLabel: "Development score",
  },
  value: {
    label: "Market value opportunity",
    shortLabel: "Value",
    description:
      "Candidates balancing suitability with financial efficiency.",
    scoreLabel: "Value score",
  },
  short_term: {
    label: "Short-term solution",
    shortLabel: "Short term",
    description:
      "Experienced candidates suited to a shorter recruitment horizon.",
    scoreLabel: "Short-term score",
  },
} satisfies Record<
  TransferModeName,
  TransferModeDetails
>;

export function parseTransferMode(
  value:
    | string
    | readonly string[]
    | undefined,
): TransferModeName | null {
  const candidate =
    typeof value === "string"
      ? value
      : value?.[0];

  return (
    TRANSFER_MODE_ORDER.find(
      (mode) => mode === candidate,
    ) ?? null
  );
}

export function getRecommendationScore(
  mode: TransferModeName,
  recommendation:
    TransferRecommendationResponse,
): number | null {
  switch (mode) {
    case "immediate":
      return (
        "immediate_score" in
          recommendation &&
        typeof recommendation
          .immediate_score === "number"
      )
        ? recommendation.immediate_score
        : null;

    case "development":
      return (
        "development_score" in
          recommendation &&
        typeof recommendation
          .development_score === "number"
      )
        ? recommendation.development_score
        : null;

    case "value":
      return (
        "value_score" in
          recommendation &&
        typeof recommendation
          .value_score === "number"
      )
        ? recommendation.value_score
        : null;

    case "short_term":
      return (
        "short_term_score" in
          recommendation &&
        typeof recommendation
          .short_term_score === "number"
      )
        ? recommendation.short_term_score
        : null;
  }
}

export function getRecommendationRank(
  mode: TransferModeName,
  recommendation:
    TransferRecommendationResponse,
): number | null {
  switch (mode) {
    case "immediate":
      return (
        "immediate_rank" in
          recommendation &&
        typeof recommendation
          .immediate_rank === "number"
      )
        ? recommendation.immediate_rank
        : null;

    case "development":
      return (
        "development_rank" in
          recommendation &&
        typeof recommendation
          .development_rank === "number"
      )
        ? recommendation.development_rank
        : null;

    case "value":
      return (
        "value_rank" in
          recommendation &&
        typeof recommendation
          .value_rank === "number"
      )
        ? recommendation.value_rank
        : null;

    case "short_term":
      return (
        "short_term_rank" in
          recommendation &&
        typeof recommendation
          .short_term_rank === "number"
      )
        ? recommendation.short_term_rank
        : null;
  }
}
