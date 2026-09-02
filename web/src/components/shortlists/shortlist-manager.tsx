"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import type { FormEvent } from "react";

import { CountryFlag } from "@/components/players/country-flag";
import { PlayerImage } from "@/components/players/player-image";
import { useShortlists } from "@/components/providers/shortlist-provider";
import { ShortlistComparisonBuilder } from "@/components/shortlists/shortlist-comparison-builder";
import { Link } from "@/i18n/navigation";
import type {
  Shortlist,
  ShortlistPlayerSnapshot,
} from "@/lib/shortlists/types";
function formatMarketValue(
  value: number | null,
  currency: string | null,
  locale: string,
  unavailable: string,
): string {
  if (value === null || !currency) {
    return unavailable;
  }

  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(value);
  } catch {
    return `${value.toLocaleString(locale)} ${currency}`;
  }
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
  const locale = useLocale();
  const translations = useTranslations("ShortlistManager");

  const positionLabels: Readonly<Record<string, string>> = {
    G: translations("positionLabels.goalkeeper"),
    D: translations("positionLabels.defender"),
    M: translations("positionLabels.midfielder"),
    F: translations("positionLabels.forward"),
  };

  const formattedPosition = player.position
    ? (positionLabels[player.position] ?? player.position)
    : translations("positionUnavailable");

  const formattedAge =
    player.age === null
      ? translations("ageUnavailable")
      : translations("ageValue", {
          value: new Intl.NumberFormat(locale, {
            maximumFractionDigits: 1,
          }).format(player.age),
        });

  const formattedMinutes =
    player.minutes === null
      ? translations("minutesUnavailable")
      : translations("minutesValue", {
          value: new Intl.NumberFormat(locale).format(player.minutes),
        });

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
            <CountryFlag countryAlpha3={player.countryAlpha3} className="w-4" />

            <span className="min-w-0 break-words">
              {player.nationalTeamName ??
                player.countryName ??
                translations("nationalTeamUnavailable")}
            </span>
          </div>

          <p className="mt-2 break-words text-sm font-semibold text-brand">
            {player.finalRole ??
              player.archetype ??
              translations("roleUnavailable")}
          </p>
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-border pt-4 text-xs sm:grid-cols-4">
        <div>
          <dt className="text-muted">{translations("positionLabel")}</dt>

          <dd className="mt-1 font-semibold">{formattedPosition}</dd>
        </div>

        <div>
          <dt className="text-muted">{translations("ageLabel")}</dt>

          <dd className="mt-1 font-semibold">{formattedAge}</dd>
        </div>

        <div>
          <dt className="text-muted">{translations("marketValueLabel")}</dt>

          <dd className="mt-1 font-semibold text-brand-dark">
            {formatMarketValue(
              player.marketValue,
              player.marketValueCurrency,
              locale,
              translations("marketValueUnavailable"),
            )}
          </dd>
        </div>

        <div>
          <dt className="text-muted">
            {translations("tournamentSampleLabel")}
          </dt>

          <dd className="mt-1 font-semibold">{formattedMinutes}</dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-col gap-2 border-t border-border pt-4 sm:flex-row">
        <Link
          href={`/players/${player.playerId}`}
          className="inline-flex min-h-10 flex-1 items-center justify-center rounded-xl border border-border bg-surface px-3 text-xs font-semibold transition-colors hover:bg-surface-secondary"
        >
          {translations("openProfile")}
        </Link>

        <button
          type="button"
          aria-label={translations("removePlayerLabel", {
            player: player.playerName,
            shortlist: shortlist.name,
          })}
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
          {translations("remove")}
        </button>
      </div>
    </article>
  );
}

export function ShortlistManager() {
  const translations = useTranslations("ShortlistManager");
  const issueTranslations = useTranslations("ShortlistAction");

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

  const issueMessage =
    issue === null
      ? null
      : {
          not_hydrated: issueTranslations("issues.notHydrated"),
          storage_unavailable: issueTranslations("issues.storageUnavailable"),
          read_failed: issueTranslations("issues.readFailed"),
          invalid_json: issueTranslations("issues.invalidJson"),
          unsupported_version: issueTranslations("issues.unsupportedVersion"),
          invalid_data: issueTranslations("issues.invalidData"),
          invalid_state: issueTranslations("issues.invalidState"),
          write_failed: issueTranslations("issues.writeFailed"),
          invalid_shortlist_id: issueTranslations("issues.invalidShortlistId"),
          invalid_shortlist_name: issueTranslations(
            "issues.invalidShortlistName",
            {
              maximum: 80,
            },
          ),
          invalid_timestamp: issueTranslations("issues.invalidTimestamp"),
          duplicate_shortlist_id: issueTranslations(
            "issues.duplicateShortlistId",
          ),
          duplicate_shortlist_name: issueTranslations(
            "issues.duplicateShortlistName",
          ),
          shortlist_limit_reached: issueTranslations(
            "issues.shortlistLimitReached",
            {
              maximum: 20,
            },
          ),
          shortlist_not_found: issueTranslations("issues.shortlistNotFound"),
          invalid_player: issueTranslations("issues.invalidPlayer"),
          player_limit_reached: issueTranslations("issues.playerLimitReached", {
            maximum: 50,
          }),
        }[issue.code];

  const [newListName, setNewListName] = useState("");

  const [editingListId, setEditingListId] = useState<string | null>(null);

  const [editingName, setEditingName] = useState("");

  const [deletingListId, setDeletingListId] = useState<string | null>(null);

  const [announcement, setAnnouncement] = useState<string | null>(null);

  if (!isHydrated) {
    return (
      <div
        role="status"
        aria-label={translations("loading")}
        className="min-h-72 animate-pulse rounded-3xl border border-border bg-surface-secondary"
      />
    );
  }

  const handleCreate = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const result = createList(newListName);

    if (!result.ok) {
      setAnnouncement(null);
      return;
    }

    const normalizedName = newListName.trim().replace(/\s+/gu, " ");

    setNewListName("");

    setAnnouncement(
      translations("createdAnnouncement", {
        shortlist: normalizedName,
      }),
    );
  };

  const beginRename = (shortlist: Shortlist) => {
    clearIssue();
    setDeletingListId(null);
    setEditingListId(shortlist.id);
    setEditingName(shortlist.name);
    setAnnouncement(null);
  };

  const handleRename = (
    event: FormEvent<HTMLFormElement>,
    shortlist: Shortlist,
  ) => {
    event.preventDefault();

    const result = renameList(shortlist.id, editingName);

    if (!result.ok) {
      setAnnouncement(null);
      return;
    }

    const normalizedName = editingName.trim().replace(/\s+/gu, " ");

    setEditingListId(null);
    setEditingName("");

    setAnnouncement(
      translations("renamedAnnouncement", {
        shortlist: shortlist.name,
        newName: normalizedName,
      }),
    );
  };

  const handleDelete = (shortlist: Shortlist) => {
    const result = deleteList(shortlist.id);

    if (!result.ok) {
      setAnnouncement(null);
      return;
    }

    setDeletingListId(null);

    setAnnouncement(
      translations("deletedAnnouncement", {
        shortlist: shortlist.name,
      }),
    );
  };

  const handleRemovePlayer = (
    shortlistId: string,
    shortlistName: string,
    playerId: number,
    playerName: string,
  ) => {
    const result = removePlayer(shortlistId, playerId);

    if (!result.ok) {
      setAnnouncement(null);
      return;
    }

    setAnnouncement(
      translations("playerRemovedAnnouncement", {
        player: playerName,
        shortlist: shortlistName,
      }),
    );
  };

  return (
    <section aria-labelledby="shortlist-workspace-title" className="space-y-6">
      <div className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-8">
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          {translations("eyebrow")}
        </p>

        <h1
          id="shortlist-workspace-title"
          className="mt-2 text-3xl font-bold tracking-[-0.04em] sm:text-4xl"
        >
          {translations("title")}
        </h1>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">
          {translations("description")}
        </p>

        <form onSubmit={handleCreate} className="mt-6">
          <label
            htmlFor="shortlist-manager-new-list"
            className="text-sm font-semibold"
          >
            {translations("createLabel")}
          </label>

          <div className="mt-2 flex flex-col gap-3 sm:flex-row">
            <input
              id="shortlist-manager-new-list"
              type="text"
              value={newListName}
              onChange={(event) => {
                setNewListName(event.currentTarget.value);
              }}
              placeholder={translations("namePlaceholder")}
              autoComplete="off"
              className="min-h-12 min-w-0 flex-1 rounded-xl border border-border bg-page px-4 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/15"
            />

            <button
              type="submit"
              disabled={newListName.trim().length === 0}
              className="inline-flex min-h-12 items-center justify-center rounded-xl bg-brand px-5 text-sm font-semibold text-white transition-colors hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50"
            >
              {translations("createButton")}
            </button>
          </div>
        </form>

        {issue ? (
          <div
            role="alert"
            className="mt-4 flex flex-col gap-3 rounded-xl border border-warning/25 bg-warning/10 px-4 py-3 text-sm text-warning sm:flex-row sm:items-center sm:justify-between"
          >
            <span>{issueMessage}</span>

            <button
              type="button"
              onClick={clearIssue}
              className="self-start text-xs font-semibold underline underline-offset-4 sm:self-auto"
            >
              {translations("dismiss")}
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
            {translations("emptyWorkspaceTitle")}
          </p>

          <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted">
            {translations("emptyWorkspaceDescription")}
          </p>

          <Link
            href="/players"
            className="mt-5 inline-flex min-h-11 items-center justify-center rounded-xl border border-border px-4 text-sm font-semibold transition-colors hover:bg-surface-secondary"
          >
            {translations("explorePlayers")}
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {lists.map((shortlist) => (
            <article
              key={shortlist.id}
              className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-6"
            >
              <div className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                    {translations("shortlistEyebrow")}
                  </p>

                  <h2 className="mt-2 break-words text-2xl font-bold tracking-[-0.03em]">
                    {shortlist.name}
                  </h2>

                  <p className="mt-1 text-sm text-muted">
                    {translations("entryCount", {
                      count: shortlist.entries.length,
                    })}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      beginRename(shortlist);
                    }}
                    className="inline-flex min-h-10 items-center justify-center rounded-xl border border-border px-4 text-xs font-semibold transition-colors hover:bg-surface-secondary"
                  >
                    {translations("rename")}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setEditingListId(null);
                      setDeletingListId(shortlist.id);
                      setAnnouncement(null);
                      clearIssue();
                    }}
                    className="inline-flex min-h-10 items-center justify-center rounded-xl border border-warning/25 bg-warning/10 px-4 text-xs font-semibold text-warning transition-colors hover:bg-warning/15"
                  >
                    {translations("delete")}
                  </button>
                </div>
              </div>

              {editingListId === shortlist.id ? (
                <form
                  onSubmit={(event) => {
                    handleRename(event, shortlist);
                  }}
                  className="mt-4 rounded-2xl border border-border bg-page p-4"
                >
                  <label
                    htmlFor={`rename-${shortlist.id}`}
                    className="text-xs font-semibold"
                  >
                    {translations("renameLabel", {
                      shortlist: shortlist.name,
                    })}
                  </label>

                  <div className="mt-2 flex flex-col gap-2 sm:flex-row">
                    <input
                      id={`rename-${shortlist.id}`}
                      type="text"
                      value={editingName}
                      onChange={(event) => {
                        setEditingName(event.currentTarget.value);
                      }}
                      className="min-h-11 min-w-0 flex-1 rounded-xl border border-border bg-surface px-3 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/15"
                    />

                    <button
                      type="submit"
                      disabled={editingName.trim().length === 0}
                      className="inline-flex min-h-11 items-center justify-center rounded-xl bg-brand px-4 text-xs font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
                    >
                      {translations("saveName")}
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setEditingListId(null);
                      }}
                      className="inline-flex min-h-11 items-center justify-center rounded-xl border border-border px-4 text-xs font-semibold hover:bg-surface-secondary"
                    >
                      {translations("cancel")}
                    </button>
                  </div>
                </form>
              ) : null}

              {deletingListId === shortlist.id ? (
                <div
                  role="alert"
                  className="mt-4 rounded-2xl border border-warning/25 bg-warning/10 p-4"
                >
                  <p className="text-sm font-semibold text-warning">
                    {translations("deleteQuestion", {
                      shortlist: shortlist.name,
                    })}
                  </p>

                  <p className="mt-1 text-xs leading-5 text-muted">
                    {translations("deleteDescription")}
                  </p>

                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      aria-label={translations("confirmDeleteLabel", {
                        shortlist: shortlist.name,
                      })}
                      onClick={() => {
                        handleDelete(shortlist);
                      }}
                      className="inline-flex min-h-10 items-center justify-center rounded-xl bg-warning px-4 text-xs font-semibold text-white"
                    >
                      {translations("confirmDelete")}
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setDeletingListId(null);
                      }}
                      className="inline-flex min-h-10 items-center justify-center rounded-xl border border-border bg-surface px-4 text-xs font-semibold"
                    >
                      {translations("cancel")}
                    </button>
                  </div>
                </div>
              ) : null}

              {shortlist.entries.length > 0 ? (
                <ShortlistComparisonBuilder shortlist={shortlist} />
              ) : null}

              {shortlist.entries.length === 0 ? (
                <div className="mt-5 rounded-2xl border border-dashed border-border bg-page p-6 text-center">
                  <p className="text-sm font-semibold">
                    {translations("emptyListTitle")}
                  </p>

                  <p className="mt-1 text-xs leading-5 text-muted">
                    {translations("emptyListDescription")}
                  </p>
                </div>
              ) : (
                <div className="mt-5 grid gap-4 xl:grid-cols-2">
                  {shortlist.entries.map((entry) => (
                    <ShortlistPlayerCard
                      key={entry.player.playerId}
                      shortlist={shortlist}
                      player={entry.player}
                      onRemove={handleRemovePlayer}
                    />
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
