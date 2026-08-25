"use client";

import {
  useId,
  useState,
} from "react";
import type {
  FormEvent,
} from "react";

import {
  useShortlists,
} from "@/components/providers/shortlist-provider";
import type {
  ShortlistPlayerSnapshot,
} from "@/lib/shortlists/types";

type ShortlistActionVariant =
  | "default"
  | "compact";

type ShortlistActionProps =
  Readonly<{
    player: ShortlistPlayerSnapshot;
    variant?: ShortlistActionVariant;
  }>;

function formatPlayerCount(
  count: number,
): string {
  return `${count} ${
    count === 1
      ? "player"
      : "players"
  }`;
}

export function ShortlistAction({
  player,
  variant = "default",
}: ShortlistActionProps) {
  const {
    lists,
    isHydrated,
    issue,
    clearIssue,
    createListWithPlayer,
    addPlayer,
    removePlayer,
    getListsForPlayer,
  } = useShortlists();

  const generatedId = useId();

  const panelId =
    `shortlist-options-${generatedId.replaceAll(
      ":",
      "",
    )}`;

  const [
    isOpen,
    setIsOpen,
  ] = useState(false);

  const [
    newListName,
    setNewListName,
  ] = useState("");

  const [
    announcement,
    setAnnouncement,
  ] =
    useState<string | null>(
      null,
    );

  const containingLists =
    getListsForPlayer(
      player.playerId,
    );

  const savedCount =
    containingLists.length;

  const handleDisclosure =
    () => {
      const nextOpen = !isOpen;

      setIsOpen(nextOpen);
      setAnnouncement(null);

      if (nextOpen) {
        clearIssue();
      }
    };

  const handleMembershipChange =
    (
      shortlistId: string,
      shortlistName: string,
      checked: boolean,
    ) => {
      const result = checked
        ? addPlayer(
            shortlistId,
            player,
          )
        : removePlayer(
            shortlistId,
            player.playerId,
          );

      if (!result.ok) {
        setAnnouncement(null);
        return;
      }

      setAnnouncement(
        checked
          ? `${player.playerName} added to ${shortlistName}.`
          : `${player.playerName} removed from ${shortlistName}.`,
      );
    };

  const handleCreateList = (
    event:
      FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const creation =
      createListWithPlayer(
        newListName,
        player,
      );

    if (!creation.ok) {
      setAnnouncement(null);
      return;
    }

    const normalizedName =
      newListName
        .trim()
        .replace(/\s+/gu, " ");

    setNewListName("");

    setAnnouncement(
      `${normalizedName} created and ${player.playerName} added.`,
    );
  };

  const buttonClassName =
    variant === "compact"
      ? "inline-flex min-h-11 w-full items-center justify-center rounded-xl border border-border bg-surface px-4 py-2 text-xs font-semibold transition-colors hover:bg-surface-secondary disabled:cursor-wait disabled:opacity-60 sm:w-auto"
      : "inline-flex min-h-12 w-full items-center justify-center rounded-xl border border-brand/25 bg-brand/5 px-5 py-3 text-sm font-semibold text-brand-dark transition-colors hover:bg-brand/10 disabled:cursor-wait disabled:opacity-60 sm:w-auto";

  return (
    <div className="relative w-full sm:w-auto">
      <button
        type="button"
        aria-expanded={isOpen}
        aria-controls={panelId}
        disabled={!isHydrated}
        onClick={handleDisclosure}
        className={buttonClassName}
      >
        {!isHydrated
          ? "Loading shortlists"
          : savedCount > 0
            ? `Shortlisted (${savedCount})`
            : "Add to shortlist"}
      </button>

      {isOpen ? (
        <section
          id={panelId}
          aria-label={`Shortlist options for ${player.playerName}`}
          className="mt-2 w-full rounded-2xl border border-border bg-surface p-4 shadow-lg sm:min-w-80"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                Shortlists
              </p>

              <p className="mt-1 text-sm font-semibold">
                Save {player.playerName}
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
              }}
              className="inline-flex min-h-9 items-center justify-center rounded-lg border border-border px-3 text-xs font-semibold hover:bg-surface-secondary"
            >
              Done
            </button>
          </div>

          {lists.length > 0 ? (
            <fieldset className="mt-4 space-y-2">
              <legend className="sr-only">
                Select shortlists
              </legend>

              {lists.map(
                (shortlist) => {
                  const isChecked =
                    containingLists.some(
                      (candidate) =>
                        candidate.id ===
                        shortlist.id,
                    );

                  return (
                    <label
                      key={shortlist.id}
                      className="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border border-border px-3 py-2.5 transition-colors hover:bg-surface-secondary"
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={(
                          event,
                        ) => {
                          handleMembershipChange(
                            shortlist.id,
                            shortlist.name,
                            event
                              .currentTarget
                              .checked,
                          );
                        }}
                        className="size-4 shrink-0 accent-brand"
                      />

                      <span className="min-w-0 flex-1">
                        <span className="block break-words text-sm font-semibold">
                          {
                            shortlist.name
                          }
                        </span>

                        <span className="mt-0.5 block text-xs text-muted">
                          {formatPlayerCount(
                            shortlist
                              .entries
                              .length,
                          )}
                        </span>
                      </span>
                    </label>
                  );
                },
              )}
            </fieldset>
          ) : (
            <p className="mt-4 rounded-xl border border-border bg-surface-secondary px-3 py-3 text-xs leading-5 text-muted">
              No shortlists yet. Create
              the first list below.
            </p>
          )}

          <form
            onSubmit={
              handleCreateList
            }
            className="mt-4 border-t border-border pt-4"
          >
            <label
              htmlFor={`${panelId}-name`}
              className="text-xs font-semibold text-foreground"
            >
              New shortlist
            </label>

            <div className="mt-2 flex flex-col gap-2 sm:flex-row">
              <input
                id={`${panelId}-name`}
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
                className="min-h-11 min-w-0 flex-1 rounded-xl border border-border bg-page px-3 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/15"
              />

              <button
                type="submit"
                disabled={
                  newListName
                    .trim()
                    .length === 0
                }
                className="inline-flex min-h-11 items-center justify-center rounded-xl bg-brand px-4 text-xs font-semibold text-white transition-colors hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50"
              >
                Create and add
              </button>
            </div>
          </form>

          {issue ? (
            <p
              role="alert"
              className="mt-3 rounded-xl border border-warning/25 bg-warning/10 px-3 py-2 text-xs leading-5 text-warning"
            >
              {issue.message}
            </p>
          ) : announcement ? (
            <p
              role="status"
              className="mt-3 rounded-xl border border-success/20 bg-success/10 px-3 py-2 text-xs leading-5 text-success"
            >
              {announcement}
            </p>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
