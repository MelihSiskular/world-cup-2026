import {
  describe,
  expect,
  it,
} from "vitest";

import {
  addPlayerToShortlist,
  createShortlist,
  deleteShortlist,
  getShortlistsContainingPlayer,
  isPlayerInShortlist,
  removePlayerFromShortlist,
  renameShortlist,
  ShortlistDomainError,
} from "@/lib/shortlists/model";
import type {
  ShortlistDomainErrorCode,
} from "@/lib/shortlists/model";
import {
  createEmptyShortlistState,
  MAX_PLAYERS_PER_SHORTLIST,
  MAX_SHORTLISTS,
} from "@/lib/shortlists/types";
import type {
  Shortlist,
  ShortlistPlayerSnapshot,
  ShortlistState,
} from "@/lib/shortlists/types";

const createdAt =
  "2026-08-25T12:00:00.000Z";

const updatedAt =
  "2026-08-25T13:00:00.000Z";

function createPlayer(
  playerId = 978838,
  playerName = "Michael Olise",
): ShortlistPlayerSnapshot {
  return {
    playerId,
    playerName,
    nationalTeamName:
      "France",
    countryName: "France",
    countryAlpha3: "FRA",
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
    roleConfidencePct: 87.2,
    dataReliabilityScore: 81.4,
    playerQualityScore: 85.5,
  };
}

function getOnlyShortlist(
  state: ShortlistState,
): Shortlist {
  const shortlist =
    state.lists[0];

  if (shortlist === undefined) {
    throw new Error(
      "Expected one shortlist.",
    );
  }

  return shortlist;
}

function expectDomainError(
  operation: () => unknown,
  code:
    ShortlistDomainErrorCode,
): void {
  try {
    operation();
  } catch (error) {
    expect(error).toBeInstanceOf(
      ShortlistDomainError,
    );

    expect(error).toMatchObject({
      code,
    });

    return;
  }

  throw new Error(
    `Expected shortlist domain error: ${code}`,
  );
}

function createStateWithList():
  ShortlistState {
  return createShortlist(
    createEmptyShortlistState(),
    {
      id: "summer-2027-lcb",
      name: "Summer 2027 — LCB",
      now: createdAt,
    },
  );
}

describe(
  "shortlist model",
  () => {
    it(
      "creates a normalized shortlist",
      () => {
        const state =
          createShortlist(
            createEmptyShortlistState(),
            {
              id:
                "  summer-2027-lcb  ",
              name:
                "  Summer   2027 — LCB  ",
              now: createdAt,
            },
          );

        expect(
          getOnlyShortlist(state),
        ).toEqual({
          id: "summer-2027-lcb",
          name:
            "Summer 2027 — LCB",
          createdAt,
          updatedAt: createdAt,
          entries: [],
        });
      },
    );

    it(
      "rejects invalid and duplicate shortlist identities",
      () => {
        const state =
          createStateWithList();

        expectDomainError(
          () =>
            createShortlist(
              state,
              {
                id: "another-list",
                name:
                  " summer 2027 — lcb ",
                now: createdAt,
              },
            ),
          "duplicate_shortlist_name",
        );

        expectDomainError(
          () =>
            createShortlist(
              state,
              {
                id:
                  "summer-2027-lcb",
                name:
                  "Another shortlist",
                now: createdAt,
              },
            ),
          "duplicate_shortlist_id",
        );

        expectDomainError(
          () =>
            createShortlist(
              state,
              {
                id: "empty-name",
                name: "   ",
                now: createdAt,
              },
            ),
          "invalid_shortlist_name",
        );
      },
    );

    it(
      "renames and deletes a shortlist",
      () => {
        let state =
          createStateWithList();

        state =
          renameShortlist(
            state,
            {
              shortlistId:
                "summer-2027-lcb",
              name:
                "January 2028 — LCB",
              now: updatedAt,
            },
          );

        expect(
          getOnlyShortlist(state),
        ).toMatchObject({
          name:
            "January 2028 — LCB",
          createdAt,
          updatedAt,
        });

        state =
          deleteShortlist(
            state,
            {
              shortlistId:
                "summer-2027-lcb",
            },
          );

        expect(
          state.lists,
        ).toEqual([]);
      },
    );

    it(
      "adds and refreshes a player without creating duplicates",
      () => {
        let state =
          createStateWithList();

        state =
          addPlayerToShortlist(
            state,
            {
              shortlistId:
                "summer-2027-lcb",
              player:
                createPlayer(),
              now: createdAt,
            },
          );

        state =
          addPlayerToShortlist(
            state,
            {
              shortlistId:
                "summer-2027-lcb",
              player:
                createPlayer(
                  978838,
                  " Michael   Olise ",
                ),
              now: updatedAt,
            },
          );

        const shortlist =
          getOnlyShortlist(
            state,
          );

        expect(
          shortlist.entries,
        ).toHaveLength(1);

        expect(
          shortlist.entries[0],
        ).toMatchObject({
          addedAt: createdAt,
          player: {
            playerId: 978838,
            playerName:
              "Michael Olise",
          },
        });

        expect(
          shortlist.updatedAt,
        ).toBe(updatedAt);
      },
    );

    it(
      "removes players idempotently and reports membership",
      () => {
        let state =
          createStateWithList();

        state =
          addPlayerToShortlist(
            state,
            {
              shortlistId:
                "summer-2027-lcb",
              player:
                createPlayer(),
              now: createdAt,
            },
          );

        expect(
          isPlayerInShortlist(
            state,
            "summer-2027-lcb",
            978838,
          ),
        ).toBe(true);

        expect(
          getShortlistsContainingPlayer(
            state,
            978838,
          ).map(
            (shortlist) =>
              shortlist.id,
          ),
        ).toEqual([
          "summer-2027-lcb",
        ]);

        state =
          removePlayerFromShortlist(
            state,
            {
              shortlistId:
                "summer-2027-lcb",
              playerId: 978838,
              now: updatedAt,
            },
          );

        expect(
          isPlayerInShortlist(
            state,
            "summer-2027-lcb",
            978838,
          ),
        ).toBe(false);

        const unchanged =
          removePlayerFromShortlist(
            state,
            {
              shortlistId:
                "summer-2027-lcb",
              playerId: 978838,
              now: updatedAt,
            },
          );

        expect(unchanged).toBe(state);
      },
    );

    it(
      "enforces shortlist and player capacity limits",
      () => {
        let state =
          createEmptyShortlistState();

        for (
          let index = 0;
          index < MAX_SHORTLISTS;
          index += 1
        ) {
          state =
            createShortlist(
              state,
              {
                id: `list-${index}`,
                name:
                  `Shortlist ${index}`,
                now: createdAt,
              },
            );
        }

        expectDomainError(
          () =>
            createShortlist(
              state,
              {
                id: "overflow",
                name: "Overflow",
                now: createdAt,
              },
            ),
          "shortlist_limit_reached",
        );

        let playerState =
          createStateWithList();

        for (
          let index = 0;
          index <
          MAX_PLAYERS_PER_SHORTLIST;
          index += 1
        ) {
          playerState =
            addPlayerToShortlist(
              playerState,
              {
                shortlistId:
                  "summer-2027-lcb",
                player:
                  createPlayer(
                    index + 1,
                    `Player ${index + 1}`,
                  ),
                now: createdAt,
              },
            );
        }

        expectDomainError(
          () =>
            addPlayerToShortlist(
              playerState,
              {
                shortlistId:
                  "summer-2027-lcb",
                player:
                  createPlayer(
                    MAX_PLAYERS_PER_SHORTLIST +
                      1,
                    "Overflow Player",
                  ),
                now: updatedAt,
              },
            ),
          "player_limit_reached",
        );
      },
    );
  },
);
