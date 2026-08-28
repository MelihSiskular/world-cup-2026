"use client";

import Link from "next/link";
import {
  useMemo,
  useState,
} from "react";
import type {
  FormEvent,
} from "react";

import {
  CountryFlag,
} from "@/components/players/country-flag";
import {
  PlayerImage,
} from "@/components/players/player-image";
import {
  useShortlists,
} from "@/components/providers/shortlist-provider";
import {
  ShortlistComparisonBuilder,
} from "@/components/shortlists/shortlist-comparison-builder";
import type {
  Shortlist,
  ShortlistPlayerSnapshot,
} from "@/lib/shortlists/types";
import {
  formatMarketValue,
  formatPlayerPosition,
  formatProfileNumber,
} from "@/lib/players/profile-format";

function formatAge(
  age: number | null,
): string {
  if (age === null) {
    return "Age unavailable";
  }

  return `${formatProfileNumber(
    age,
    {
      maximumFractionDigits: 1,
    },
  )} years`;
}

function formatMinutes(
  minutes: number | null,
): string {
  if (minutes === null) {
    return "Minutes unavailable";
  }

  return `${formatProfileNumber(
    minutes,
  )} minutes`;
}

function formatEntryCount(
  count: number,
): string {
  return `${count} ${
    count === 1
      ? "player"
      : "players"
  }`;
}

function ShortlistPlayerCard({
  shortlist,
  player,
  onRemove,
}: Readonly<{
  shortlist: Shortlist;
  player: ShortlistPlayerSnapshot;
  onRemove(
    shortlistId: string,
    shortlistName: string,
    playerId: number,
    playerName: string,
  ): void;
}>) {
  return (
    <article className="rounded-2xl border border-border bg-page p-4">
      <div className="flex min-w-0 items-start gap-4">
        <PlayerImage
          playerId={player.playerId}
          playerName={player.playerName}
          size="card"
        />

        <div className="min-w-0 flex-1">
          <Link
            href={`/players/${player.playerId}`}
            className="break-words text-lg font-bold tracking-[-0.025em] transition-colors hover:text-brand"
          >
            {player.playerName}
          </Link>

          <div className="mt-1 flex min-w-0 items-center gap-2 text-sm text-muted">
            <CountryFlag
              countryAlpha3={
                player.countryAlpha3
              }
              className="w-4"
            />

            <span className="min-w-0 break-words">
              {player.nationalTeamName ??
                player.countryName ??
                "National team unavailable"}
            </span>
          </div>

          <p className="mt-2 break-words text-sm font-semibold text-brand">
            {player.finalRole ??
              player.archetype ??
              "Role unavailable"}
          </p>
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-border pt-4 text-xs sm:grid-cols-4">
        <div>
          <dt className="text-muted">
            Position
          </dt>

          <dd className="mt-1 font-semibold">
            {formatPlayerPosition(
              player.position,
            )}
          </dd>
        </div>

        <div>
          <dt className="text-muted">
            Age
          </dt>

          <dd className="mt-1 font-semibold">
            {formatAge(
              player.age,
            )}
          </dd>
        </div>

        <div>
          <dt className="text-muted">
            Market value
          </dt>

          <dd className="mt-1 font-semibold text-brand-dark">
            {formatMarketValue(
              player.marketValue,
              player.marketValueCurrency,
            )}
          </dd>
        </div>

        <div>
          <dt className="text-muted">
            Tournament sample
          </dt>

          <dd className="mt-1 font-semibold">
            {formatMinutes(
              player.minutes,
            )}
          </dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-col gap-2 border-t border-border pt-4 sm:flex-row">
        <Link
          href={`/players/${player.playerId}`}
          className="inline-flex min-h-10 flex-1 items-center justify-center rounded-xl border border-border bg-surface px-3 text-xs font-semibold transition-colors hover:bg-surface-secondary"
        >
          Open profile
        </Link>

        <button
          type="button"
          aria-label={`Remove ${player.playerName} from ${shortlist.name}`}
          onClick={() => {
            onRemove(
              shortlist.id,
              shortlist.name,
              player.playerId,
              player.playerName,
            );
          }}
          className="inline-flex min-h-10 flex-1 items-center justify-center rounded-xl border border-warning/25 bg-warning/10 px-3 text-xs font-semibold text-warning transition-colors hover:bg-warning/15"
        >
          Remove
        </button>
      </div>
    </article>
  );
}

export function ShortlistManager() {
  const {
    lists,
    isHydrated,
    issue,
    clearIssue,
    createList,
    renameList,
    deleteList,
    removePlayer,
  } = useShortlists();

  const [
    newListName,
    setNewListName,
  ] = useState("");

  const [
    editingListId,
    setEditingListId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    editingName,
    setEditingName,
  ] = useState("");

  const [
    deletingListId,
    setDeletingListId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    announcement,
    setAnnouncement,
  ] =
    useState<string | null>(
      null,
    );

  const uniquePlayerCount =
    useMemo(
      () =>
        new Set(
          lists.flatMap(
            (shortlist) =>
              shortlist.entries.map(
                (entry) =>
                  entry.player
                    .playerId,
              ),
          ),
        ).size,
      [lists],
    );

  const savedSelectionCount =
    useMemo(
      () =>
        lists.reduce(
          (
            total,
            shortlist,
          ) =>
            total +
            shortlist.entries
              .length,
          0,
        ),
      [lists],
    );

  if (!isHydrated) {
    return (
      <div
        role="status"
        aria-label="Loading shortlists"
        className="min-h-72 animate-pulse rounded-3xl border border-border bg-surface-secondary"
      />
    );
  }

  const handleCreate = (
    event:
      FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const result =
      createList(newListName);

    if (!result.ok) {
      setAnnouncement(null);
      return;
    }

    const normalizedName =
      newListName
        .trim()
        .replace(/\s+/gu, " ");

    setNewListName("");

    setAnnouncement(
      `${normalizedName} created.`,
    );
  };

  const beginRename = (
    shortlist: Shortlist,
  ) => {
    clearIssue();
    setDeletingListId(null);
    setEditingListId(
      shortlist.id,
    );
    setEditingName(
      shortlist.name,
    );
    setAnnouncement(null);
  };

  const handleRename = (
    event:
      FormEvent<HTMLFormElement>,
    shortlist: Shortlist,
  ) => {
    event.preventDefault();

    const result =
      renameList(
        shortlist.id,
        editingName,
      );

    if (!result.ok) {
      setAnnouncement(null);
      return;
    }

    const normalizedName =
      editingName
        .trim()
        .replace(/\s+/gu, " ");

    setEditingListId(null);
    setEditingName("");

    setAnnouncement(
      `${shortlist.name} renamed to ${normalizedName}.`,
    );
  };

  const handleDelete = (
    shortlist: Shortlist,
  ) => {
    const result =
      deleteList(
        shortlist.id,
      );

    if (!result.ok) {
      setAnnouncement(null);
      return;
    }

    setDeletingListId(null);

    setAnnouncement(
      `${shortlist.name} deleted.`,
    );
  };

  const handleRemovePlayer = (
    shortlistId: string,
    shortlistName: string,
    playerId: number,
    playerName: string,
  ) => {
    const result =
      removePlayer(
        shortlistId,
        playerId,
      );

    if (!result.ok) {
      setAnnouncement(null);
      return;
    }

    setAnnouncement(
      `${playerName} removed from ${shortlistName}.`,
    );
  };

  return (
    <section
      aria-labelledby="shortlist-workspace-title"
      className="space-y-6"
    >
      <div className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-8">
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          Recruitment workspace
        </p>

        <h1
          id="shortlist-workspace-title"
          className="mt-2 text-3xl font-bold tracking-[-0.04em] sm:text-4xl"
        >
          Shortlist workspace
        </h1>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">
          Organize tournament players into
          focused recruitment lists. Saved
          data remains in this browser.
        </p>

        <dl className="mt-6 grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-border bg-page p-4">
            <dt className="text-xs font-semibold text-muted">
              Shortlists
            </dt>

            <dd className="mt-2 text-2xl font-bold text-brand-dark">
              {lists.length}
            </dd>
          </div>

          <div className="rounded-2xl border border-border bg-page p-4">
            <dt className="text-xs font-semibold text-muted">
              Unique players
            </dt>

            <dd className="mt-2 text-2xl font-bold text-brand-dark">
              {uniquePlayerCount}
            </dd>
          </div>

          <div className="rounded-2xl border border-border bg-page p-4">
            <dt className="text-xs font-semibold text-muted">
              Saved selections
            </dt>

            <dd className="mt-2 text-2xl font-bold text-brand-dark">
              {savedSelectionCount}
            </dd>
          </div>
        </dl>

        <form
          onSubmit={handleCreate}
          className="mt-6 border-t border-border pt-6"
        >
          <label
            htmlFor="shortlist-manager-new-list"
            className="text-sm font-semibold"
          >
            Create a shortlist
          </label>

          <div className="mt-2 flex flex-col gap-3 sm:flex-row">
            <input
              id="shortlist-manager-new-list"
              type="text"
              value={newListName}
              onChange={(
                event,
              ) => {
                setNewListName(
                  event
                    .currentTarget
                    .value,
                );
              }}
              placeholder="Summer 2027 — LCB"
              autoComplete="off"
              className="min-h-12 min-w-0 flex-1 rounded-xl border border-border bg-page px-4 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/15"
            />

            <button
              type="submit"
              disabled={
                newListName
                  .trim()
                  .length === 0
              }
              className="inline-flex min-h-12 items-center justify-center rounded-xl bg-brand px-5 text-sm font-semibold text-white transition-colors hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50"
            >
              Create shortlist
            </button>
          </div>
        </form>

        {issue ? (
          <div
            role="alert"
            className="mt-4 flex flex-col gap-3 rounded-xl border border-warning/25 bg-warning/10 px-4 py-3 text-sm text-warning sm:flex-row sm:items-center sm:justify-between"
          >
            <span>
              {issue.message}
            </span>

            <button
              type="button"
              onClick={clearIssue}
              className="self-start text-xs font-semibold underline underline-offset-4 sm:self-auto"
            >
              Dismiss
            </button>
          </div>
        ) : announcement ? (
          <p
            role="status"
            className="mt-4 rounded-xl border border-success/20 bg-success/10 px-4 py-3 text-sm text-success"
          >
            {announcement}
          </p>
        ) : null}
      </div>

      {lists.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-border bg-surface p-8 text-center shadow-sm sm:p-12">
          <p className="text-lg font-bold">
            No shortlists yet
          </p>

          <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted">
            Create a named recruitment list
            here or save a player directly
            from discovery, profile and
            recommendation surfaces.
          </p>

          <Link
            href="/players"
            className="mt-5 inline-flex min-h-11 items-center justify-center rounded-xl border border-border px-4 text-sm font-semibold transition-colors hover:bg-surface-secondary"
          >
            Explore players
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {lists.map(
            (shortlist) => (
              <article
                key={shortlist.id}
                className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-6"
              >
                <div className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                      Shortlist
                    </p>

                    <h2 className="mt-2 break-words text-2xl font-bold tracking-[-0.03em]">
                      {shortlist.name}
                    </h2>

                    <p className="mt-1 text-sm text-muted">
                      {formatEntryCount(
                        shortlist
                          .entries
                          .length,
                      )}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        beginRename(
                          shortlist,
                        );
                      }}
                      className="inline-flex min-h-10 items-center justify-center rounded-xl border border-border px-4 text-xs font-semibold transition-colors hover:bg-surface-secondary"
                    >
                      Rename
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setEditingListId(
                          null,
                        );
                        setDeletingListId(
                          shortlist.id,
                        );
                        setAnnouncement(
                          null,
                        );
                        clearIssue();
                      }}
                      className="inline-flex min-h-10 items-center justify-center rounded-xl border border-warning/25 bg-warning/10 px-4 text-xs font-semibold text-warning transition-colors hover:bg-warning/15"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {editingListId ===
                shortlist.id ? (
                  <form
                    onSubmit={(
                      event,
                    ) => {
                      handleRename(
                        event,
                        shortlist,
                      );
                    }}
                    className="mt-4 rounded-2xl border border-border bg-page p-4"
                  >
                    <label
                      htmlFor={`rename-${shortlist.id}`}
                      className="text-xs font-semibold"
                    >
                      Rename{" "}
                      {shortlist.name}
                    </label>

                    <div className="mt-2 flex flex-col gap-2 sm:flex-row">
                      <input
                        id={`rename-${shortlist.id}`}
                        type="text"
                        value={
                          editingName
                        }
                        onChange={(
                          event,
                        ) => {
                          setEditingName(
                            event
                              .currentTarget
                              .value,
                          );
                        }}
                        className="min-h-11 min-w-0 flex-1 rounded-xl border border-border bg-surface px-3 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/15"
                      />

                      <button
                        type="submit"
                        disabled={
                          editingName
                            .trim()
                            .length ===
                          0
                        }
                        className="inline-flex min-h-11 items-center justify-center rounded-xl bg-brand px-4 text-xs font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
                      >
                        Save name
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setEditingListId(
                            null,
                          );
                        }}
                        className="inline-flex min-h-11 items-center justify-center rounded-xl border border-border px-4 text-xs font-semibold hover:bg-surface-secondary"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                ) : null}

                {deletingListId ===
                shortlist.id ? (
                  <div
                    role="alert"
                    className="mt-4 rounded-2xl border border-warning/25 bg-warning/10 p-4"
                  >
                    <p className="text-sm font-semibold text-warning">
                      Delete{" "}
                      {shortlist.name}?
                    </p>

                    <p className="mt-1 text-xs leading-5 text-muted">
                      This removes the list
                      and all of its saved
                      player references from
                      this browser.
                    </p>

                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        aria-label={`Confirm delete ${shortlist.name}`}
                        onClick={() => {
                          handleDelete(
                            shortlist,
                          );
                        }}
                        className="inline-flex min-h-10 items-center justify-center rounded-xl bg-warning px-4 text-xs font-semibold text-white"
                      >
                        Confirm delete
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setDeletingListId(
                            null,
                          );
                        }}
                        className="inline-flex min-h-10 items-center justify-center rounded-xl border border-border bg-surface px-4 text-xs font-semibold"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : null}

                {shortlist.entries
                  .length > 0 ? (
                  <ShortlistComparisonBuilder
                    shortlist={
                      shortlist
                    }
                  />
                ) : null}

                {shortlist.entries
                  .length === 0 ? (
                  <div className="mt-5 rounded-2xl border border-dashed border-border bg-page p-6 text-center">
                    <p className="text-sm font-semibold">
                      This shortlist is empty
                    </p>

                    <p className="mt-1 text-xs leading-5 text-muted">
                      Add players from the
                      discovery catalogue,
                      profile pages or
                      recommendations.
                    </p>
                  </div>
                ) : (
                  <div className="mt-5 grid gap-4 xl:grid-cols-2">
                    {shortlist.entries.map(
                      (entry) => (
                        <ShortlistPlayerCard
                          key={
                            entry.player
                              .playerId
                          }
                          shortlist={
                            shortlist
                          }
                          player={
                            entry.player
                          }
                          onRemove={
                            handleRemovePlayer
                          }
                        />
                      ),
                    )}
                  </div>
                )}
              </article>
            ),
          )}
        </div>
      )}
    </section>
  );
}
