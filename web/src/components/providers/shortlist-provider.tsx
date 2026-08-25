"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type {
  ReactNode,
} from "react";

import {
  addPlayerToShortlist,
  createShortlist as createShortlistState,
  deleteShortlist as deleteShortlistState,
  getShortlistsContainingPlayer,
  isPlayerInShortlist,
  removePlayerFromShortlist,
  renameShortlist as renameShortlistState,
  ShortlistDomainError,
} from "@/lib/shortlists/model";
import type {
  ShortlistDomainErrorCode,
} from "@/lib/shortlists/model";
import {
  readShortlistState,
  writeShortlistState,
} from "@/lib/shortlists/storage";
import type {
  ShortlistStorageAdapter,
  ShortlistStorageReadIssue,
  ShortlistStorageWriteIssue,
} from "@/lib/shortlists/storage";
import {
  createEmptyShortlistState,
  SHORTLIST_STORAGE_KEY,
} from "@/lib/shortlists/types";
import type {
  Shortlist,
  ShortlistPlayerSnapshot,
  ShortlistState,
} from "@/lib/shortlists/types";

type StorageIssueCode =
  | ShortlistStorageReadIssue
  | ShortlistStorageWriteIssue;

export type ShortlistProviderIssue =
  | Readonly<{
      source: "lifecycle";
      code: "not_hydrated";
      message: string;
    }>
  | Readonly<{
      source: "storage";
      code: StorageIssueCode;
      message: string;
    }>
  | Readonly<{
      source: "domain";
      code: ShortlistDomainErrorCode;
      message: string;
    }>;

export type ShortlistMutationResult =
  | Readonly<{
      ok: true;
    }>
  | Readonly<{
      ok: false;
      issue: ShortlistProviderIssue;
    }>;

export type CreateShortlistResult =
  | Readonly<{
      ok: true;
      shortlistId: string;
    }>
  | Readonly<{
      ok: false;
      issue: ShortlistProviderIssue;
    }>;

export type ShortlistContextValue =
  Readonly<{
    state: ShortlistState;
    lists: readonly Shortlist[];
    isHydrated: boolean;
    issue: ShortlistProviderIssue | null;
    clearIssue(): void;
    createList(
      name: string,
    ): CreateShortlistResult;
    createListWithPlayer(
      name: string,
      player: ShortlistPlayerSnapshot,
    ): CreateShortlistResult;
    renameList(
      shortlistId: string,
      name: string,
    ): ShortlistMutationResult;
    deleteList(
      shortlistId: string,
    ): ShortlistMutationResult;
    addPlayer(
      shortlistId: string,
      player: ShortlistPlayerSnapshot,
    ): ShortlistMutationResult;
    removePlayer(
      shortlistId: string,
      playerId: number,
    ): ShortlistMutationResult;
    getListsForPlayer(
      playerId: number,
    ): readonly Shortlist[];
    isPlayerSaved(
      shortlistId: string,
      playerId: number,
    ): boolean;
  }>;

export type ShortlistProviderProps =
  Readonly<{
    children: ReactNode;
    storage?:
      | ShortlistStorageAdapter
      | null;
    now?: () => string;
    createId?: () => string;
  }>;

const STORAGE_ISSUE_MESSAGES:
  Readonly<Record<
    StorageIssueCode,
    string
  >> = {
    storage_unavailable:
      "Shortlists cannot access browser storage.",
    read_failed:
      "Saved shortlists could not be read.",
    invalid_json:
      "Saved shortlist data is malformed.",
    unsupported_version:
      "Saved shortlist data uses an unsupported version.",
    invalid_data:
      "Saved shortlist data does not match the expected contract.",
    invalid_state:
      "The updated shortlist state is invalid.",
    write_failed:
      "Shortlist changes could not be saved.",
  };

const ShortlistContext =
  createContext<
    ShortlistContextValue | undefined
  >(undefined);

type StateOperation = (
  state: ShortlistState,
) => ShortlistState;

function defaultNow(): string {
  return new Date().toISOString();
}

function defaultCreateId(): string {
  if (
    typeof globalThis.crypto !==
      "undefined" &&
    typeof globalThis.crypto
      .randomUUID === "function"
  ) {
    return globalThis.crypto.randomUUID();
  }

  return [
    "shortlist",
    Date.now().toString(36),
    Math.random()
      .toString(36)
      .slice(2),
  ].join("-");
}

function getBrowserStorage():
  ShortlistStorageAdapter | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function createStorageIssue(
  code: StorageIssueCode,
): ShortlistProviderIssue {
  return {
    source: "storage",
    code,
    message:
      STORAGE_ISSUE_MESSAGES[code],
  };
}

function createLifecycleIssue():
  ShortlistProviderIssue {
  return {
    source: "lifecycle",
    code: "not_hydrated",
    message:
      "Shortlists are still loading.",
  };
}

export function ShortlistProvider({
  children,
  storage,
  now,
  createId,
}: ShortlistProviderProps) {
  const [
    state,
    setState,
  ] = useState<ShortlistState>(
    createEmptyShortlistState,
  );

  const [
    isHydrated,
    setIsHydrated,
  ] = useState(false);

  const [
    issue,
    setIssue,
  ] =
    useState<
      ShortlistProviderIssue | null
    >(null);

  const stateRef =
    useRef(state);

  const storageRef =
    useRef<
      ShortlistStorageAdapter | null
    >(null);

  const hydratedRef =
    useRef(false);

  useEffect(() => {
    const resolvedStorage =
      storage === undefined
        ? getBrowserStorage()
        : storage;

    storageRef.current =
      resolvedStorage;

    let isActive = true;

    queueMicrotask(() => {
      if (!isActive) {
        return;
      }

      const result =
        readShortlistState(
          resolvedStorage,
        );

      stateRef.current =
        result.state;

      setState(result.state);

      setIssue(
        result.issue === null
          ? null
          : createStorageIssue(
              result.issue,
            ),
      );

      hydratedRef.current = true;
      setIsHydrated(true);
    });

    if (
      storage !== undefined ||
      typeof window === "undefined"
    ) {
      return () => {
        isActive = false;
        hydratedRef.current = false;
      };
    }

    const handleStorage = (
      event: StorageEvent,
    ) => {
      if (
        event.key !== null &&
        event.key !==
          SHORTLIST_STORAGE_KEY
      ) {
        return;
      }

      const refreshed =
        readShortlistState(
          storageRef.current,
        );

      stateRef.current =
        refreshed.state;

      setState(refreshed.state);

      setIssue(
        refreshed.issue === null
          ? null
          : createStorageIssue(
              refreshed.issue,
            ),
      );
    };

    window.addEventListener(
      "storage",
      handleStorage,
    );

    return () => {
      isActive = false;
      hydratedRef.current = false;

      window.removeEventListener(
        "storage",
        handleStorage,
      );
    };
  }, [storage]);

  const commit = useCallback(
    (
      operation: StateOperation,
    ): ShortlistMutationResult => {
      if (!hydratedRef.current) {
        const nextIssue =
          createLifecycleIssue();

        setIssue(nextIssue);

        return {
          ok: false,
          issue: nextIssue,
        };
      }

      let nextState:
        ShortlistState;

      try {
        nextState = operation(
          stateRef.current,
        );
      } catch (error) {
        if (
          error instanceof
          ShortlistDomainError
        ) {
          const nextIssue:
            ShortlistProviderIssue = {
              source: "domain",
              code: error.code,
              message: error.message,
            };

          setIssue(nextIssue);

          return {
            ok: false,
            issue: nextIssue,
          };
        }

        throw error;
      }

      if (
        nextState ===
        stateRef.current
      ) {
        setIssue(null);

        return {
          ok: true,
        };
      }

      const writeResult =
        writeShortlistState(
          storageRef.current,
          nextState,
        );

      if (!writeResult.ok) {
        const nextIssue =
          createStorageIssue(
            writeResult.issue,
          );

        setIssue(nextIssue);

        return {
          ok: false,
          issue: nextIssue,
        };
      }

      stateRef.current =
        nextState;

      setState(nextState);
      setIssue(null);

      return {
        ok: true,
      };
    },
    [],
  );

  const clearIssue =
    useCallback(() => {
      setIssue(null);
    }, []);

  const createList =
    useCallback(
      (
        name: string,
      ): CreateShortlistResult => {
        const shortlistId =
          (
            createId ??
            defaultCreateId
          )();

        const result = commit(
          (currentState) =>
            createShortlistState(
              currentState,
              {
                id: shortlistId,
                name,
                now:
                  (now ?? defaultNow)(),
              },
            ),
        );

        if (!result.ok) {
          return result;
        }

        return {
          ok: true,
          shortlistId,
        };
      },
      [
        commit,
        createId,
        now,
      ],
    );

  const createListWithPlayer =
    useCallback(
      (
        name: string,
        player:
          ShortlistPlayerSnapshot,
      ): CreateShortlistResult => {
        const shortlistId =
          (
            createId ??
            defaultCreateId
          )();

        const timestamp =
          (now ?? defaultNow)();

        const result = commit(
          (currentState) => {
            const createdState =
              createShortlistState(
                currentState,
                {
                  id: shortlistId,
                  name,
                  now: timestamp,
                },
              );

            return addPlayerToShortlist(
              createdState,
              {
                shortlistId,
                player,
                now: timestamp,
              },
            );
          },
        );

        if (!result.ok) {
          return result;
        }

        return {
          ok: true,
          shortlistId,
        };
      },
      [
        commit,
        createId,
        now,
      ],
    );

  const renameList =
    useCallback(
      (
        shortlistId: string,
        name: string,
      ) =>
        commit(
          (currentState) =>
            renameShortlistState(
              currentState,
              {
                shortlistId,
                name,
                now:
                  (now ?? defaultNow)(),
              },
            ),
        ),
      [
        commit,
        now,
      ],
    );

  const deleteList =
    useCallback(
      (shortlistId: string) =>
        commit(
          (currentState) =>
            deleteShortlistState(
              currentState,
              {
                shortlistId,
              },
            ),
        ),
      [commit],
    );

  const addPlayer =
    useCallback(
      (
        shortlistId: string,
        player:
          ShortlistPlayerSnapshot,
      ) =>
        commit(
          (currentState) =>
            addPlayerToShortlist(
              currentState,
              {
                shortlistId,
                player,
                now:
                  (now ?? defaultNow)(),
              },
            ),
        ),
      [
        commit,
        now,
      ],
    );

  const removePlayer =
    useCallback(
      (
        shortlistId: string,
        playerId: number,
      ) =>
        commit(
          (currentState) =>
            removePlayerFromShortlist(
              currentState,
              {
                shortlistId,
                playerId,
                now:
                  (now ?? defaultNow)(),
              },
            ),
        ),
      [
        commit,
        now,
      ],
    );

  const getListsForPlayer =
    useCallback(
      (playerId: number) =>
        getShortlistsContainingPlayer(
          state,
          playerId,
        ),
      [state],
    );

  const isPlayerSaved =
    useCallback(
      (
        shortlistId: string,
        playerId: number,
      ) =>
        isPlayerInShortlist(
          state,
          shortlistId,
          playerId,
        ),
      [state],
    );

  const value =
    useMemo<ShortlistContextValue>(
      () => ({
        state,
        lists: state.lists,
        isHydrated,
        issue,
        clearIssue,
        createList,
        createListWithPlayer,
        renameList,
        deleteList,
        addPlayer,
        removePlayer,
        getListsForPlayer,
        isPlayerSaved,
      }),
      [
        state,
        isHydrated,
        issue,
        clearIssue,
        createList,
        createListWithPlayer,
        renameList,
        deleteList,
        addPlayer,
        removePlayer,
        getListsForPlayer,
        isPlayerSaved,
      ],
    );

  return (
    <ShortlistContext.Provider
      value={value}
    >
      {children}
    </ShortlistContext.Provider>
  );
}

export function useShortlists():
  ShortlistContextValue {
  const context =
    useContext(ShortlistContext);

  if (context === undefined) {
    throw new Error(
      "useShortlists must be used within ShortlistProvider.",
    );
  }

  return context;
}
