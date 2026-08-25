import {
  z,
} from "zod";

import {
  createEmptyShortlistState,
  MAX_PLAYERS_PER_SHORTLIST,
  MAX_SHORTLIST_NAME_LENGTH,
  MAX_SHORTLISTS,
  SHORTLIST_STORAGE_KEY,
  SHORTLIST_STORAGE_VERSION,
} from "@/lib/shortlists/types";
import type {
  ShortlistState,
} from "@/lib/shortlists/types";

const nullableTextSchema =
  z.string().nullable();

const nullableFiniteNumberSchema =
  z.number().finite().nullable();

const timestampSchema =
  z.string().refine(
    (value) =>
      !Number.isNaN(
        Date.parse(value),
      ),
    {
      message:
        "Expected a valid timestamp.",
    },
  );

const playerSnapshotSchema =
  z.object({
    playerId:
      z.number().int().positive(),
    playerName:
      z.string().trim().min(1),
    nationalTeamName:
      nullableTextSchema,
    countryName:
      nullableTextSchema,
    countryAlpha3:
      nullableTextSchema,
    position:
      nullableTextSchema,
    age:
      nullableFiniteNumberSchema,
    marketValue:
      nullableFiniteNumberSchema,
    marketValueCurrency:
      nullableTextSchema,
    finalRole:
      nullableTextSchema,
    archetype:
      nullableTextSchema,
    spatialRole:
      nullableTextSchema,
    minutes:
      nullableFiniteNumberSchema,
    roleConfidencePct:
      nullableFiniteNumberSchema,
    dataReliabilityScore:
      nullableFiniteNumberSchema,
    playerQualityScore:
      nullableFiniteNumberSchema,
  })
    .strict();

const shortlistEntrySchema =
  z.object({
    player:
      playerSnapshotSchema,
    addedAt:
      timestampSchema,
  })
    .strict();

const shortlistSchema =
  z.object({
    id:
      z.string().trim().min(1),
    name:
      z.string()
        .trim()
        .min(1)
        .max(
          MAX_SHORTLIST_NAME_LENGTH,
        ),
    createdAt:
      timestampSchema,
    updatedAt:
      timestampSchema,
    entries:
      z.array(
        shortlistEntrySchema,
      )
        .max(
          MAX_PLAYERS_PER_SHORTLIST,
        ),
  })
    .strict()
    .superRefine(
      (
        shortlist,
        context,
      ) => {
        const playerIds =
          new Set<number>();

        shortlist.entries.forEach(
          (
            entry,
            index,
          ) => {
            const playerId =
              entry.player.playerId;

            if (
              playerIds.has(playerId)
            ) {
              context.addIssue({
                code: "custom",
                message:
                  "A player can appear only once in a shortlist.",
                path: [
                  "entries",
                  index,
                  "player",
                  "playerId",
                ],
              });
            }

            playerIds.add(playerId);
          },
        );
      },
    );

export const shortlistStateSchema =
  z.object({
    version:
      z.literal(
        SHORTLIST_STORAGE_VERSION,
      ),
    lists:
      z.array(shortlistSchema)
        .max(MAX_SHORTLISTS),
  })
    .strict()
    .superRefine(
      (
        state,
        context,
      ) => {
        const ids =
          new Set<string>();

        const names =
          new Set<string>();

        state.lists.forEach(
          (
            shortlist,
            index,
          ) => {
            const normalizedName =
              shortlist.name
                .trim()
                .toLocaleLowerCase(
                  "en-US",
                );

            if (
              ids.has(shortlist.id)
            ) {
              context.addIssue({
                code: "custom",
                message:
                  "Shortlist IDs must be unique.",
                path: [
                  "lists",
                  index,
                  "id",
                ],
              });
            }

            if (
              names.has(
                normalizedName,
              )
            ) {
              context.addIssue({
                code: "custom",
                message:
                  "Shortlist names must be unique.",
                path: [
                  "lists",
                  index,
                  "name",
                ],
              });
            }

            ids.add(shortlist.id);
            names.add(normalizedName);
          },
        );
      },
    );

export type ShortlistStorageAdapter =
  Readonly<{
    getItem(
      key: string,
    ): string | null;
    setItem(
      key: string,
      value: string,
    ): void;
  }>;

export type ShortlistStorageReadIssue =
  | "storage_unavailable"
  | "read_failed"
  | "invalid_json"
  | "unsupported_version"
  | "invalid_data";

export type ShortlistStorageWriteIssue =
  | "storage_unavailable"
  | "invalid_state"
  | "write_failed";

export type ShortlistStorageReadResult =
  Readonly<{
    state: ShortlistState;
    issue:
      ShortlistStorageReadIssue |
      null;
  }>;

export type ShortlistStorageWriteResult =
  | Readonly<{
      ok: true;
    }>
  | Readonly<{
      ok: false;
      issue:
        ShortlistStorageWriteIssue;
    }>;

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

export function readShortlistState(
  storage:
    ShortlistStorageAdapter |
    null,
): ShortlistStorageReadResult {
  if (storage === null) {
    return {
      state:
        createEmptyShortlistState(),
      issue:
        "storage_unavailable",
    };
  }

  let serialized: string | null;

  try {
    serialized =
      storage.getItem(
        SHORTLIST_STORAGE_KEY,
      );
  } catch {
    return {
      state:
        createEmptyShortlistState(),
      issue: "read_failed",
    };
  }

  if (serialized === null) {
    return {
      state:
        createEmptyShortlistState(),
      issue: null,
    };
  }

  let parsed: unknown;

  try {
    parsed =
      JSON.parse(serialized);
  } catch {
    return {
      state:
        createEmptyShortlistState(),
      issue: "invalid_json",
    };
  }

  if (
    isRecord(parsed) &&
    "version" in parsed &&
    parsed.version !==
      SHORTLIST_STORAGE_VERSION
  ) {
    return {
      state:
        createEmptyShortlistState(),
      issue:
        "unsupported_version",
    };
  }

  const validation =
    shortlistStateSchema.safeParse(
      parsed,
    );

  if (!validation.success) {
    return {
      state:
        createEmptyShortlistState(),
      issue: "invalid_data",
    };
  }

  return {
    state:
      validation.data,
    issue: null,
  };
}

export function writeShortlistState(
  storage:
    ShortlistStorageAdapter |
    null,
  state: ShortlistState,
): ShortlistStorageWriteResult {
  if (storage === null) {
    return {
      ok: false,
      issue:
        "storage_unavailable",
    };
  }

  const validation =
    shortlistStateSchema.safeParse(
      state,
    );

  if (!validation.success) {
    return {
      ok: false,
      issue: "invalid_state",
    };
  }

  try {
    storage.setItem(
      SHORTLIST_STORAGE_KEY,
      JSON.stringify(
        validation.data,
      ),
    );
  } catch {
    return {
      ok: false,
      issue: "write_failed",
    };
  }

  return {
    ok: true,
  };
}
