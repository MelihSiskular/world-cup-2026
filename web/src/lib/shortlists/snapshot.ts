import type {
  PlayerProfileResponse,
  PlayerSearchItemResponse,
  TransferRecommendationResponse,
} from "@/lib/api/types";
import type {
  ShortlistPlayerSnapshot,
} from "@/lib/shortlists/types";

export type ShortlistPlayerSource =
  Readonly<{
    player_id: number;
    player_name: string;
    national_team_name?:
      string | null;
    country_name?:
      string | null;
    country_alpha3?:
      string | null;
    position?:
      string | null;
    age?:
      number | null;
    market_value?:
      number | null;
    market_value_currency?:
      string | null;
    final_role?:
      string | null;
    archetype?:
      string | null;
    spatial_role?:
      string | null;
    minutes?:
      number | null;
    role_confidence_pct?:
      number | null;
    data_reliability_score?:
      number | null;
    player_quality_score?:
      number | null;
  }>;

function normalizeNullableText(
  value:
    string |
    null |
    undefined,
): string | null {
  if (typeof value !== "string") {
    return null;
  }

  const normalized =
    value
      .trim()
      .replace(/\s+/gu, " ");

  return normalized || null;
}

function normalizeNullableNumber(
  value:
    number |
    null |
    undefined,
): number | null {
  return (
    typeof value === "number" &&
    Number.isFinite(value)
  )
    ? value
    : null;
}

export function createShortlistPlayerSnapshot(
  source: ShortlistPlayerSource,
): ShortlistPlayerSnapshot {
  if (
    !Number.isSafeInteger(
      source.player_id,
    ) ||
    source.player_id <= 0
  ) {
    throw new TypeError(
      "Shortlist player ID must be a positive integer.",
    );
  }

  const playerName =
    normalizeNullableText(
      source.player_name,
    );

  if (playerName === null) {
    throw new TypeError(
      "Shortlist player name cannot be empty.",
    );
  }

  const countryAlpha3 =
    normalizeNullableText(
      source.country_alpha3,
    );

  return {
    playerId:
      source.player_id,
    playerName,
    nationalTeamName:
      normalizeNullableText(
        source.national_team_name,
      ),
    countryName:
      normalizeNullableText(
        source.country_name,
      ),
    countryAlpha3:
      countryAlpha3?.toUpperCase() ??
      null,
    position:
      normalizeNullableText(
        source.position,
      ),
    age:
      normalizeNullableNumber(
        source.age,
      ),
    marketValue:
      normalizeNullableNumber(
        source.market_value,
      ),
    marketValueCurrency:
      normalizeNullableText(
        source.market_value_currency,
      )?.toUpperCase() ?? null,
    finalRole:
      normalizeNullableText(
        source.final_role,
      ),
    archetype:
      normalizeNullableText(
        source.archetype,
      ),
    spatialRole:
      normalizeNullableText(
        source.spatial_role,
      ),
    minutes:
      normalizeNullableNumber(
        source.minutes,
      ),
    roleConfidencePct:
      normalizeNullableNumber(
        source.role_confidence_pct,
      ),
    dataReliabilityScore:
      normalizeNullableNumber(
        source.data_reliability_score,
      ),
    playerQualityScore:
      normalizeNullableNumber(
        source.player_quality_score,
      ),
  };
}

export function createShortlistSnapshotFromSearchPlayer(
  player: PlayerSearchItemResponse,
): ShortlistPlayerSnapshot {
  return createShortlistPlayerSnapshot(
    player,
  );
}

export function createShortlistSnapshotFromProfile(
  player: PlayerProfileResponse,
): ShortlistPlayerSnapshot {
  return createShortlistPlayerSnapshot(
    player,
  );
}

export function createShortlistSnapshotFromRecommendation(
  player:
    TransferRecommendationResponse,
): ShortlistPlayerSnapshot {
  return createShortlistPlayerSnapshot(
    player,
  );
}
