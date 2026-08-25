import {
  act,
  renderHook,
  waitFor,
} from "@testing-library/react";
import type {
  ReactNode,
} from "react";
import {
  describe,
  expect,
  it,
} from "vitest";

import {
  ShortlistProvider,
  useShortlists,
} from "@/components/providers/shortlist-provider";
import type {
  ShortlistMutationResult,
  ShortlistProviderProps,
} from "@/components/providers/shortlist-provider";
import {
  addPlayerToShortlist,
  createShortlist,
} from "@/lib/shortlists/model";
import type {
  ShortlistStorageAdapter,
} from "@/lib/shortlists/storage";
import {
  createEmptyShortlistState,
  SHORTLIST_STORAGE_KEY,
} from "@/lib/shortlists/types";
import type {
  ShortlistPlayerSnapshot,
  ShortlistState,
} from "@/lib/shortlists/types";

const NOW =
  "2026-08-25T01:00:00.000Z";

const player:
  ShortlistPlayerSnapshot = {
    playerId: 978838,
    playerName: "Michael Olise",
    nationalTeamName: "France",
    countryName: "France",
    countryAlpha3: "FRA",
    position: "M",
    age: 24,
    marketValue: 100_000_000,
    marketValueCurrency: "EUR",
    finalRole:
      "Right Half-Space Creator",
    archetype: "Wide Creator",
    spatialRole:
      "Right Half-Space",
    minutes: 540,
    roleConfidencePct: 82,
    dataReliabilityScore: 78,
    playerQualityScore: 88,
  };

type MemoryStorage =
  Readonly<{
    adapter:
      ShortlistStorageAdapter;
    readValue(): string | null;
    writeCount(): number;
  }>;

function createMemoryStorage(
  initialValue: string | null = null,
): MemoryStorage {
  let value = initialValue;
  let writes = 0;

  return {
    adapter: {
      getItem(key) {
        return key ===
          SHORTLIST_STORAGE_KEY
          ? value
          : null;
      },
      setItem(key, nextValue) {
        if (
          key ===
          SHORTLIST_STORAGE_KEY
        ) {
          value = nextValue;
          writes += 1;
        }
      },
    },
    readValue() {
      return value;
    },
    writeCount() {
      return writes;
    },
  };
}

type ProviderOverrides =
  Pick<
    ShortlistProviderProps,
    "storage" | "now" | "createId"
  >;

function createWrapper(
  overrides: ProviderOverrides,
) {
  return function Wrapper({
    children,
  }: Readonly<{
    children: ReactNode;
  }>) {
    return (
      <ShortlistProvider
        {...overrides}
      >
        {children}
      </ShortlistProvider>
    );
  };
}

async function renderShortlists(
  overrides: ProviderOverrides,
) {
  const rendered =
    renderHook(
      () => useShortlists(),
      {
        wrapper:
          createWrapper(overrides),
      },
    );

  await waitFor(() => {
    expect(
      rendered.result.current
        .isHydrated,
    ).toBe(true);
  });

  return rendered;
}

describe(
  "ShortlistProvider",
  () => {
    it(
      "hydrates a valid persisted shortlist state",
      async () => {
        let persisted =
          createShortlist(
            createEmptyShortlistState(),
            {
              id: "summer-lcb",
              name: "Summer 2027 — LCB",
              now: NOW,
            },
          );

        persisted =
          addPlayerToShortlist(
            persisted,
            {
              shortlistId:
                "summer-lcb",
              player,
              now: NOW,
            },
          );

        const storage =
          createMemoryStorage(
            JSON.stringify(
              persisted,
            ),
          );

        const rendered =
          await renderShortlists({
            storage:
              storage.adapter,
          });

        expect(
          rendered.result.current
            .lists,
        ).toHaveLength(1);

        expect(
          rendered.result.current
            .lists[0]?.entries[0]
            ?.player.playerName,
        ).toBe("Michael Olise");

        expect(
          rendered.result.current
            .issue,
        ).toBeNull();
      },
    );

    it(
      "recovers safely from corrupted persisted data",
      async () => {
        const storage =
          createMemoryStorage(
            "{invalid-json",
          );

        const rendered =
          await renderShortlists({
            storage:
              storage.adapter,
          });

        expect(
          rendered.result.current
            .lists,
        ).toEqual([]);

        expect(
          rendered.result.current
            .issue,
        ).toMatchObject({
          source: "storage",
          code: "invalid_json",
        });

        act(() => {
          rendered.result.current
            .clearIssue();
        });

        expect(
          rendered.result.current
            .issue,
        ).toBeNull();
      },
    );

    it(
      "persists create, rename, add, remove and delete mutations",
      async () => {
        const storage =
          createMemoryStorage();

        const rendered =
          await renderShortlists({
            storage:
              storage.adapter,
            now: () => NOW,
            createId:
              () => "summer-lcb",
          });

        let createResult:
          ReturnType<
            typeof rendered.result
              .current.createList
          >;

        act(() => {
          createResult =
            rendered.result.current
              .createList(
                "Summer 2027 — LCB",
              );
        });

        expect(
          createResult!.ok,
        ).toBe(true);

        act(() => {
          rendered.result.current
            .renameList(
              "summer-lcb",
              "Summer 2027 — Defenders",
            );

          rendered.result.current
            .addPlayer(
              "summer-lcb",
              player,
            );
        });

        expect(
          rendered.result.current
            .lists[0]?.name,
        ).toBe(
          "Summer 2027 — Defenders",
        );

        expect(
          rendered.result.current
            .getListsForPlayer(
              player.playerId,
            ),
        ).toHaveLength(1);

        expect(
          rendered.result.current
            .isPlayerSaved(
              "summer-lcb",
              player.playerId,
            ),
        ).toBe(true);

        const savedAfterAdd =
          JSON.parse(
            storage.readValue() ??
              "",
          ) as ShortlistState;

        expect(
          savedAfterAdd.lists[0]
            ?.entries,
        ).toHaveLength(1);

        act(() => {
          rendered.result.current
            .removePlayer(
              "summer-lcb",
              player.playerId,
            );

          rendered.result.current
            .deleteList(
              "summer-lcb",
            );
        });

        expect(
          rendered.result.current
            .lists,
        ).toEqual([]);

        const savedAfterDelete =
          JSON.parse(
            storage.readValue() ??
              "",
          ) as ShortlistState;

        expect(
          savedAfterDelete.lists,
        ).toEqual([]);
      },
    );

    it(
      "creates a shortlist with its first player in one persisted transition",
      async () => {
        const storage =
          createMemoryStorage();

        const rendered =
          await renderShortlists({
            storage:
              storage.adapter,
            now: () => NOW,
            createId:
              () => "list-1",
          });

        let creationSucceeded =
          false;

        act(() => {
          creationSucceeded =
            rendered.result.current
              .createListWithPlayer(
                "Summer 2027 — LCB",
                player,
              ).ok;
        });

        expect(
          creationSucceeded,
        ).toBe(true);

        expect(
          rendered.result.current
            .lists,
        ).toHaveLength(1);

        expect(
          rendered.result.current
            .lists[0]?.entries,
        ).toHaveLength(1);

        expect(
          rendered.result.current
            .lists[0]?.entries[0]
            ?.player.playerId,
        ).toBe(player.playerId);

        expect(
          storage.writeCount(),
        ).toBe(1);

        const persisted =
          JSON.parse(
            storage.readValue() ??
              "",
          ) as ShortlistState;

        expect(
          persisted.lists[0]
            ?.entries[0]
            ?.player.playerId,
        ).toBe(player.playerId);
      },
    );

    it(
      "surfaces domain failures without changing state",
      async () => {
        const storage =
          createMemoryStorage();

        let idIndex = 0;

        const rendered =
          await renderShortlists({
            storage:
              storage.adapter,
            now: () => NOW,
            createId: () => {
              idIndex += 1;

              return `list-${idIndex}`;
            },
          });

        act(() => {
          rendered.result.current
            .createList(
              "Recruitment",
            );
        });

        let duplicateResult:
          ReturnType<
            typeof rendered.result
              .current.createList
          >;

        act(() => {
          duplicateResult =
            rendered.result.current
              .createList(
                "  recruitment  ",
              );
        });

        expect(
          duplicateResult!.ok,
        ).toBe(false);

        expect(
          rendered.result.current
            .issue,
        ).toMatchObject({
          source: "domain",
          code:
            "duplicate_shortlist_name",
        });

        expect(
          rendered.result.current
            .lists,
        ).toHaveLength(1);
      },
    );

    it(
      "does not advance UI state when persistence fails",
      async () => {
        const failingStorage:
          ShortlistStorageAdapter = {
            getItem() {
              return null;
            },
            setItem() {
              throw new Error(
                "Storage quota exceeded.",
              );
            },
          };

        const rendered =
          await renderShortlists({
            storage:
              failingStorage,
            now: () => NOW,
            createId:
              () => "list-1",
          });

        let mutation:
          ShortlistMutationResult |
          undefined;

        act(() => {
          mutation =
            rendered.result.current
              .createList(
                "Recruitment",
              );
        });

        expect(
          mutation?.ok,
        ).toBe(false);

        expect(
          rendered.result.current
            .issue,
        ).toMatchObject({
          source: "storage",
          code: "write_failed",
        });

        expect(
          rendered.result.current
            .lists,
        ).toEqual([]);
      },
    );

    it(
      "reports unavailable storage and keeps mutations recoverable",
      async () => {
        const rendered =
          await renderShortlists({
            storage: null,
            now: () => NOW,
            createId:
              () => "list-1",
          });

        expect(
          rendered.result.current
            .issue,
        ).toMatchObject({
          source: "storage",
          code:
            "storage_unavailable",
        });

        act(() => {
          rendered.result.current
            .createList(
              "Recruitment",
            );
        });

        expect(
          rendered.result.current
            .lists,
        ).toEqual([]);

        expect(
          rendered.result.current
            .issue,
        ).toMatchObject({
          source: "storage",
          code:
            "storage_unavailable",
        });
      },
    );
  },
);
