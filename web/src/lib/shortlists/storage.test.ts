import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  readShortlistState,
  shortlistStateSchema,
  writeShortlistState,
} from "@/lib/shortlists/storage";
import type {
  ShortlistStorageAdapter,
} from "@/lib/shortlists/storage";
import {
  createEmptyShortlistState,
  SHORTLIST_STORAGE_KEY,
  SHORTLIST_STORAGE_VERSION,
} from "@/lib/shortlists/types";
import type {
  ShortlistState,
} from "@/lib/shortlists/types";

const timestamp =
  "2026-08-25T12:00:00.000Z";

const populatedState = {
  version:
    SHORTLIST_STORAGE_VERSION,
  lists: [
    {
      id: "summer-2027-lcb",
      name: "Summer 2027 — LCB",
      createdAt: timestamp,
      updatedAt: timestamp,
      entries: [
        {
          addedAt: timestamp,
          player: {
            playerId: 978838,
            playerName:
              "Michael Olise",
            nationalTeamName:
              "France",
            countryName:
              "France",
            countryAlpha3:
              "FRA",
            position: "M",
            age: 24.6,
            marketValue:
              144_000_000,
            marketValueCurrency:
              "EUR",
            finalRole:
              "Central Half-Space Creator",
            archetype:
              "Wide Creator",
            spatialRole:
              "Right Half-Space",
            minutes: 650,
            roleConfidencePct:
              87.2,
            dataReliabilityScore:
              81.4,
            playerQualityScore:
              85.5,
          },
        },
      ],
    },
  ],
} satisfies ShortlistState;

function createMemoryStorage(
  initialValue: string | null = null,
): Readonly<{
  storage:
    ShortlistStorageAdapter;
  readStoredValue:
    () => string | null;
}> {
  let storedValue =
    initialValue;

  return {
    storage: {
      getItem: vi.fn(
        (key: string) => {
          expect(key).toBe(
            SHORTLIST_STORAGE_KEY,
          );

          return storedValue;
        },
      ),
      setItem: vi.fn(
        (
          key: string,
          value: string,
        ) => {
          expect(key).toBe(
            SHORTLIST_STORAGE_KEY,
          );

          storedValue = value;
        },
      ),
    },
    readStoredValue:
      () => storedValue,
  };
}

describe(
  "shortlist storage",
  () => {
    it(
      "returns an empty versioned state when no saved data exists",
      () => {
        const {
          storage,
        } =
          createMemoryStorage();

        expect(
          readShortlistState(
            storage,
          ),
        ).toEqual({
          state:
            createEmptyShortlistState(),
          issue: null,
        });
      },
    );

    it(
      "writes and reads a valid shortlist state",
      () => {
        const memory =
          createMemoryStorage();

        expect(
          writeShortlistState(
            memory.storage,
            populatedState,
          ),
        ).toEqual({
          ok: true,
        });

        expect(
          memory.readStoredValue(),
        ).not.toBeNull();

        expect(
          readShortlistState(
            memory.storage,
          ),
        ).toEqual({
          state:
            populatedState,
          issue: null,
        });
      },
    );

    it(
      "recovers safely from malformed JSON",
      () => {
        const {
          storage,
        } =
          createMemoryStorage(
            "{broken",
          );

        expect(
          readShortlistState(
            storage,
          ),
        ).toEqual({
          state:
            createEmptyShortlistState(),
          issue:
            "invalid_json",
        });
      },
    );

    it(
      "rejects unsupported storage versions",
      () => {
        const {
          storage,
        } =
          createMemoryStorage(
            JSON.stringify({
              version: 99,
              lists: [],
            }),
          );

        expect(
          readShortlistState(
            storage,
          ).issue,
        ).toBe(
          "unsupported_version",
        );
      },
    );

    it(
      "rejects duplicate players and duplicate shortlist names",
      () => {
        const firstShortlist =
          populatedState.lists[0];

        const firstEntry =
          firstShortlist?.entries[0];

        if (
          firstShortlist ===
            undefined ||
          firstEntry === undefined
        ) {
          throw new Error(
            "Expected populated shortlist fixture.",
          );
        }

        const duplicatePlayerState = {
          ...populatedState,
          lists: [
            {
              ...firstShortlist,
              entries: [
                firstEntry,
                firstEntry,
              ],
            },
          ],
        };

        expect(
          shortlistStateSchema.safeParse(
            duplicatePlayerState,
          ).success,
        ).toBe(false);

        const duplicateNameState = {
          ...populatedState,
          lists: [
            firstShortlist,
            {
              ...firstShortlist,
              id: "second-list",
              name:
                "summer 2027 — lcb",
            },
          ],
        };

        expect(
          shortlistStateSchema.safeParse(
            duplicateNameState,
          ).success,
        ).toBe(false);
      },
    );

    it(
      "reports unavailable and failing storage without throwing",
      () => {
        expect(
          readShortlistState(null),
        ).toEqual({
          state:
            createEmptyShortlistState(),
          issue:
            "storage_unavailable",
        });

        expect(
          writeShortlistState(
            null,
            populatedState,
          ),
        ).toEqual({
          ok: false,
          issue:
            "storage_unavailable",
        });

        const failingRead = {
          getItem: vi.fn(() => {
            throw new Error(
              "Read blocked",
            );
          }),
          setItem: vi.fn(),
        } satisfies ShortlistStorageAdapter;

        expect(
          readShortlistState(
            failingRead,
          ).issue,
        ).toBe("read_failed");

        const failingWrite = {
          getItem: vi.fn(
            () => null,
          ),
          setItem: vi.fn(() => {
            throw new Error(
              "Quota exceeded",
            );
          }),
        } satisfies ShortlistStorageAdapter;

        expect(
          writeShortlistState(
            failingWrite,
            populatedState,
          ),
        ).toEqual({
          ok: false,
          issue:
            "write_failed",
        });
      },
    );
  },
);
