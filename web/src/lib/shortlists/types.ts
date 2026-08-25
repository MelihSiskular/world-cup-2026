export const SHORTLIST_STORAGE_VERSION =
  1 as const;

export const SHORTLIST_STORAGE_KEY =
  "wc26.shortlists";

export const MAX_SHORTLISTS = 20;

export const MAX_PLAYERS_PER_SHORTLIST =
  50;

export const MAX_SHORTLIST_NAME_LENGTH =
  80;

export type ShortlistPlayerSnapshot =
  Readonly<{
    playerId: number;
    playerName: string;
    nationalTeamName: string | null;
    countryName: string | null;
    countryAlpha3: string | null;
    position: string | null;
    age: number | null;
    marketValue: number | null;
    marketValueCurrency: string | null;
    finalRole: string | null;
    archetype: string | null;
    spatialRole: string | null;
    minutes: number | null;
    roleConfidencePct: number | null;
    dataReliabilityScore: number | null;
    playerQualityScore: number | null;
  }>;

export type ShortlistEntry =
  Readonly<{
    player: ShortlistPlayerSnapshot;
    addedAt: string;
  }>;

export type Shortlist =
  Readonly<{
    id: string;
    name: string;
    createdAt: string;
    updatedAt: string;
    entries:
      readonly ShortlistEntry[];
  }>;

export type ShortlistState =
  Readonly<{
    version:
      typeof SHORTLIST_STORAGE_VERSION;
    lists: readonly Shortlist[];
  }>;

export function createEmptyShortlistState():
  ShortlistState {
  return {
    version:
      SHORTLIST_STORAGE_VERSION,
    lists: [],
  };
}
