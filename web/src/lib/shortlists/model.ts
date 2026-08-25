import {
  MAX_PLAYERS_PER_SHORTLIST,
  MAX_SHORTLIST_NAME_LENGTH,
  MAX_SHORTLISTS,
} from "@/lib/shortlists/types";
import type {
  Shortlist,
  ShortlistPlayerSnapshot,
  ShortlistState,
} from "@/lib/shortlists/types";

export type ShortlistDomainErrorCode =
  | "invalid_shortlist_id"
  | "invalid_shortlist_name"
  | "invalid_timestamp"
  | "duplicate_shortlist_id"
  | "duplicate_shortlist_name"
  | "shortlist_limit_reached"
  | "shortlist_not_found"
  | "invalid_player"
  | "player_limit_reached";

export class ShortlistDomainError
  extends Error {
  readonly code:
    ShortlistDomainErrorCode;

  constructor(
    code: ShortlistDomainErrorCode,
    message: string,
  ) {
    super(message);

    this.name =
      "ShortlistDomainError";

    this.code = code;
  }
}

type CreateShortlistInput =
  Readonly<{
    id: string;
    name: string;
    now: string;
  }>;

type RenameShortlistInput =
  Readonly<{
    shortlistId: string;
    name: string;
    now: string;
  }>;

type DeleteShortlistInput =
  Readonly<{
    shortlistId: string;
  }>;

type AddPlayerInput =
  Readonly<{
    shortlistId: string;
    player:
      ShortlistPlayerSnapshot;
    now: string;
  }>;

type RemovePlayerInput =
  Readonly<{
    shortlistId: string;
    playerId: number;
    now: string;
  }>;

function normalizeWhitespace(
  value: string,
): string {
  return value
    .trim()
    .replace(/\s+/gu, " ");
}

function normalizeNameKey(
  value: string,
): string {
  return normalizeWhitespace(
    value,
  ).toLocaleLowerCase(
    "en-US",
  );
}

function validateShortlistId(
  value: string,
): string {
  const normalized =
    value.trim();

  if (!normalized) {
    throw new ShortlistDomainError(
      "invalid_shortlist_id",
      "Shortlist ID cannot be empty.",
    );
  }

  return normalized;
}

function validateShortlistName(
  value: string,
): string {
  const normalized =
    normalizeWhitespace(value);

  if (
    !normalized ||
    normalized.length >
      MAX_SHORTLIST_NAME_LENGTH
  ) {
    throw new ShortlistDomainError(
      "invalid_shortlist_name",
      `Shortlist name must contain between 1 and ${MAX_SHORTLIST_NAME_LENGTH} characters.`,
    );
  }

  return normalized;
}

function validateTimestamp(
  value: string,
): string {
  if (
    Number.isNaN(
      Date.parse(value),
    )
  ) {
    throw new ShortlistDomainError(
      "invalid_timestamp",
      "Shortlist operations require a valid timestamp.",
    );
  }

  return value;
}

function validatePlayer(
  player:
    ShortlistPlayerSnapshot,
): ShortlistPlayerSnapshot {
  if (
    !Number.isSafeInteger(
      player.playerId,
    ) ||
    player.playerId <= 0
  ) {
    throw new ShortlistDomainError(
      "invalid_player",
      "Player ID must be a positive integer.",
    );
  }

  const playerName =
    normalizeWhitespace(
      player.playerName,
    );

  if (!playerName) {
    throw new ShortlistDomainError(
      "invalid_player",
      "Player name cannot be empty.",
    );
  }

  return {
    ...player,
    playerName,
  };
}

function findShortlist(
  state: ShortlistState,
  shortlistId: string,
): Shortlist | undefined {
  return state.lists.find(
    (shortlist) =>
      shortlist.id ===
      shortlistId,
  );
}

function requireShortlist(
  state: ShortlistState,
  shortlistId: string,
): Shortlist {
  const shortlist =
    findShortlist(
      state,
      shortlistId,
    );

  if (shortlist === undefined) {
    throw new ShortlistDomainError(
      "shortlist_not_found",
      "The requested shortlist could not be found.",
    );
  }

  return shortlist;
}

function replaceShortlist(
  state: ShortlistState,
  replacement: Shortlist,
): ShortlistState {
  return {
    ...state,
    lists:
      state.lists.map(
        (shortlist) =>
          shortlist.id ===
          replacement.id
            ? replacement
            : shortlist,
      ),
  };
}

function assertUniqueName(
  state: ShortlistState,
  name: string,
  excludedId?: string,
): void {
  const nameKey =
    normalizeNameKey(name);

  const duplicate =
    state.lists.some(
      (shortlist) =>
        shortlist.id !==
          excludedId &&
        normalizeNameKey(
          shortlist.name,
        ) === nameKey,
    );

  if (duplicate) {
    throw new ShortlistDomainError(
      "duplicate_shortlist_name",
      "Shortlist names must be unique.",
    );
  }
}

export function createShortlist(
  state: ShortlistState,
  input: CreateShortlistInput,
): ShortlistState {
  const id =
    validateShortlistId(
      input.id,
    );

  const name =
    validateShortlistName(
      input.name,
    );

  const now =
    validateTimestamp(
      input.now,
    );

  if (
    state.lists.length >=
    MAX_SHORTLISTS
  ) {
    throw new ShortlistDomainError(
      "shortlist_limit_reached",
      `A maximum of ${MAX_SHORTLISTS} shortlists is supported.`,
    );
  }

  if (
    findShortlist(
      state,
      id,
    ) !== undefined
  ) {
    throw new ShortlistDomainError(
      "duplicate_shortlist_id",
      "Shortlist IDs must be unique.",
    );
  }

  assertUniqueName(
    state,
    name,
  );

  const shortlist: Shortlist = {
    id,
    name,
    createdAt: now,
    updatedAt: now,
    entries: [],
  };

  return {
    ...state,
    lists: [
      ...state.lists,
      shortlist,
    ],
  };
}

export function renameShortlist(
  state: ShortlistState,
  input: RenameShortlistInput,
): ShortlistState {
  const shortlistId =
    validateShortlistId(
      input.shortlistId,
    );

  const shortlist =
    requireShortlist(
      state,
      shortlistId,
    );

  const name =
    validateShortlistName(
      input.name,
    );

  const now =
    validateTimestamp(
      input.now,
    );

  assertUniqueName(
    state,
    name,
    shortlistId,
  );

  if (
    shortlist.name === name
  ) {
    return state;
  }

  return replaceShortlist(
    state,
    {
      ...shortlist,
      name,
      updatedAt: now,
    },
  );
}

export function deleteShortlist(
  state: ShortlistState,
  input: DeleteShortlistInput,
): ShortlistState {
  const shortlistId =
    validateShortlistId(
      input.shortlistId,
    );

  requireShortlist(
    state,
    shortlistId,
  );

  return {
    ...state,
    lists:
      state.lists.filter(
        (shortlist) =>
          shortlist.id !==
          shortlistId,
      ),
  };
}

export function addPlayerToShortlist(
  state: ShortlistState,
  input: AddPlayerInput,
): ShortlistState {
  const shortlistId =
    validateShortlistId(
      input.shortlistId,
    );

  const shortlist =
    requireShortlist(
      state,
      shortlistId,
    );

  const player =
    validatePlayer(
      input.player,
    );

  const now =
    validateTimestamp(
      input.now,
    );

  const existingIndex =
    shortlist.entries.findIndex(
      (entry) =>
        entry.player.playerId ===
        player.playerId,
    );

  if (
    existingIndex === -1 &&
    shortlist.entries.length >=
      MAX_PLAYERS_PER_SHORTLIST
  ) {
    throw new ShortlistDomainError(
      "player_limit_reached",
      `A maximum of ${MAX_PLAYERS_PER_SHORTLIST} players is supported per shortlist.`,
    );
  }

  const entries =
    existingIndex === -1
      ? [
          ...shortlist.entries,
          {
            player,
            addedAt: now,
          },
        ]
      : shortlist.entries.map(
          (
            entry,
            index,
          ) =>
            index === existingIndex
              ? {
                  ...entry,
                  player,
                }
              : entry,
        );

  return replaceShortlist(
    state,
    {
      ...shortlist,
      updatedAt: now,
      entries,
    },
  );
}

export function removePlayerFromShortlist(
  state: ShortlistState,
  input: RemovePlayerInput,
): ShortlistState {
  const shortlistId =
    validateShortlistId(
      input.shortlistId,
    );

  const shortlist =
    requireShortlist(
      state,
      shortlistId,
    );

  if (
    !Number.isSafeInteger(
      input.playerId,
    ) ||
    input.playerId <= 0
  ) {
    throw new ShortlistDomainError(
      "invalid_player",
      "Player ID must be a positive integer.",
    );
  }

  const hasPlayer =
    shortlist.entries.some(
      (entry) =>
        entry.player.playerId ===
        input.playerId,
    );

  if (!hasPlayer) {
    return state;
  }

  const now =
    validateTimestamp(
      input.now,
    );

  return replaceShortlist(
    state,
    {
      ...shortlist,
      updatedAt: now,
      entries:
        shortlist.entries.filter(
          (entry) =>
            entry.player.playerId !==
            input.playerId,
        ),
    },
  );
}

export function getShortlistsContainingPlayer(
  state: ShortlistState,
  playerId: number,
): readonly Shortlist[] {
  if (
    !Number.isSafeInteger(playerId) ||
    playerId <= 0
  ) {
    return [];
  }

  return state.lists.filter(
    (shortlist) =>
      shortlist.entries.some(
        (entry) =>
          entry.player.playerId ===
          playerId,
      ),
  );
}

export function isPlayerInShortlist(
  state: ShortlistState,
  shortlistId: string,
  playerId: number,
): boolean {
  const shortlist =
    findShortlist(
      state,
      shortlistId,
    );

  return (
    shortlist?.entries.some(
      (entry) =>
        entry.player.playerId ===
        playerId,
    ) ?? false
  );
}
