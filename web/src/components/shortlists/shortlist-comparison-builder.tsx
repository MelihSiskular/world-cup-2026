"use client";

import Link from "next/link";
import {
  useMemo,
  useState,
} from "react";

import type {
  Shortlist,
  ShortlistPlayerSnapshot,
} from "@/lib/shortlists/types";
import {
  createMultiComparisonHref,
  MAX_MULTI_COMPARISON_CANDIDATES,
} from "@/lib/transfer-intelligence/multi-comparison-selection";

type ShortlistComparisonBuilderProps =
  Readonly<{
    shortlist: Shortlist;
  }>;

function hasCompatiblePosition(
  target:
    ShortlistPlayerSnapshot,
  candidate:
    ShortlistPlayerSnapshot,
): boolean {
  return (
    target.position !== null
    && candidate.position !== null
    && target.position ===
      candidate.position
  );
}

export function ShortlistComparisonBuilder({
  shortlist,
}: ShortlistComparisonBuilderProps) {
  const [
    preferredTargetPlayerId,
    setPreferredTargetPlayerId,
  ] = useState<number | null>(
    shortlist.entries[0]
      ?.player.playerId ??
      null,
  );

  const [
    candidatePlayerIds,
    setCandidatePlayerIds,
  ] = useState<
    readonly number[]
  >([]);

  const targetPlayer =
    useMemo(
      () =>
        shortlist.entries.find(
          (entry) =>
            entry.player
              .playerId ===
            preferredTargetPlayerId,
        )?.player ??
        shortlist.entries[0]
          ?.player ??
        null,
      [
        preferredTargetPlayerId,
        shortlist.entries,
      ],
    );

  const eligibleCandidates =
    useMemo(
      () => {
        if (targetPlayer === null) {
          return [];
        }

        return shortlist.entries
          .map(
            (entry) =>
              entry.player,
          )
          .filter(
            (player) =>
              player.playerId !==
                targetPlayer.playerId
              && hasCompatiblePosition(
                targetPlayer,
                player,
              ),
          );
      },
      [
        shortlist.entries,
        targetPlayer,
      ],
    );

  const eligibleCandidateIds =
    useMemo(
      () =>
        new Set(
          eligibleCandidates.map(
            (player) =>
              player.playerId,
          ),
        ),
      [eligibleCandidates],
    );

  const selectedCandidateIds =
    useMemo(
      () =>
        candidatePlayerIds
          .filter(
            (playerId) =>
              eligibleCandidateIds.has(
                playerId,
              ),
          )
          .slice(
            0,
            MAX_MULTI_COMPARISON_CANDIDATES,
          ),
      [
        candidatePlayerIds,
        eligibleCandidateIds,
      ],
    );

  const comparisonHref =
    useMemo(
      () => {
        if (
          targetPlayer === null
          || selectedCandidateIds
            .length === 0
        ) {
          return null;
        }

        return createMultiComparisonHref({
          targetPlayerId:
            targetPlayer.playerId,
          candidatePlayerIds:
            selectedCandidateIds,
        });
      },
      [
        selectedCandidateIds,
        targetPlayer,
      ],
    );

  const handleCandidateChange = (
    playerId: number,
    checked: boolean,
  ) => {
    setCandidatePlayerIds(
      (current) => {
        const validCurrent =
          current.filter(
            (candidateId) =>
              eligibleCandidateIds.has(
                candidateId,
              ),
          );

        if (!checked) {
          return validCurrent.filter(
            (candidateId) =>
              candidateId !==
              playerId,
          );
        }

        if (
          validCurrent.includes(
            playerId,
          )
          || validCurrent.length >=
            MAX_MULTI_COMPARISON_CANDIDATES
        ) {
          return validCurrent;
        }

        return [
          ...validCurrent,
          playerId,
        ];
      },
    );
  };

  return (
    <section
      aria-label={`Compare players in ${shortlist.name}`}
      className="mt-5 rounded-2xl border border-border bg-page p-4 sm:p-5"
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
            Multi-player comparison
          </p>

          <h3 className="mt-1 text-lg font-bold tracking-[-0.025em]">
            Compare shortlist players
          </h3>

          <p className="mt-1 max-w-2xl text-xs leading-5 text-muted">
            Choose one target and up to{" "}
            {MAX_MULTI_COMPARISON_CANDIDATES}{" "}
            candidates from the same
            position.
          </p>
        </div>

        <p
          aria-live="polite"
          className="text-xs font-semibold text-muted"
        >
          {
            selectedCandidateIds
              .length
          }{" "}
          of{" "}
          {
            MAX_MULTI_COMPARISON_CANDIDATES
          }{" "}
          candidates selected
        </p>
      </div>

      {shortlist.entries.length < 2 ? (
        <p className="mt-4 rounded-xl border border-dashed border-border bg-surface px-4 py-3 text-xs leading-5 text-muted">
          Add at least one more player
          before starting a comparison.
        </p>
      ) : (
        <>
          <div className="mt-4">
            <label
              htmlFor={`comparison-target-${shortlist.id}`}
              className="text-xs font-semibold"
            >
              Target player
            </label>

            <select
              id={`comparison-target-${shortlist.id}`}
              value={
                targetPlayer
                  ?.playerId ??
                ""
              }
              onChange={(
                event,
              ) => {
                const nextTargetId =
                  Number(
                    event
                      .currentTarget
                      .value,
                  );

                setPreferredTargetPlayerId(
                  nextTargetId,
                );

                setCandidatePlayerIds(
                  [],
                );
              }}
              className="mt-2 min-h-11 w-full rounded-xl border border-border bg-surface px-3 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/15"
            >
              {shortlist.entries.map(
                (entry) => (
                  <option
                    key={
                      entry.player
                        .playerId
                    }
                    value={
                      entry.player
                        .playerId
                    }
                  >
                    {
                      entry.player
                        .playerName
                    }
                  </option>
                ),
              )}
            </select>
          </div>

          <fieldset className="mt-4">
            <legend className="text-xs font-semibold">
              Candidate players
            </legend>

            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {shortlist.entries
                .filter(
                  (entry) =>
                    entry.player
                      .playerId !==
                    targetPlayer
                      ?.playerId,
                )
                .map(
                  (entry) => {
                    const candidate =
                      entry.player;

                    const eligible =
                      targetPlayer !==
                        null
                      && hasCompatiblePosition(
                        targetPlayer,
                        candidate,
                      );

                    const checked =
                      selectedCandidateIds.includes(
                        candidate.playerId,
                      );

                    const atLimit =
                      selectedCandidateIds
                        .length >=
                        MAX_MULTI_COMPARISON_CANDIDATES;

                    const disabled =
                      !eligible
                      || (
                        atLimit
                        && !checked
                      );

                    return (
                      <label
                        key={
                          candidate
                            .playerId
                        }
                        className={[
                          "flex min-h-12 items-center gap-3 rounded-xl border px-3 py-2 text-sm",
                          checked
                            ? "border-brand bg-brand/5"
                            : "border-border bg-surface",
                          disabled
                            ? "cursor-not-allowed opacity-55"
                            : "cursor-pointer",
                        ].join(
                          " ",
                        )}
                      >
                        <input
                          type="checkbox"
                          aria-label={`Select ${candidate.playerName} as candidate`}
                          checked={
                            checked
                          }
                          disabled={
                            disabled
                          }
                          onChange={(
                            event,
                          ) => {
                            handleCandidateChange(
                              candidate.playerId,
                              event
                                .currentTarget
                                .checked,
                            );
                          }}
                          className="size-4 shrink-0 accent-brand"
                        />

                        <span className="min-w-0 flex-1">
                          <span className="block break-words font-semibold">
                            {
                              candidate
                                .playerName
                            }
                          </span>

                          <span className="mt-0.5 block text-xs text-muted">
                            {eligible
                              ? (
                                  candidate
                                    .position ??
                                  "Position unavailable"
                                )
                              : "Different or unavailable position"}
                          </span>
                        </span>
                      </label>
                    );
                  },
                )}
            </div>

            {eligibleCandidates.length ===
            0 ? (
              <p className="mt-3 text-xs leading-5 text-warning">
                This target has no
                same-position candidates
                in the shortlist.
              </p>
            ) : null}
          </fieldset>

          <div className="mt-4 border-t border-border pt-4">
            {comparisonHref ===
            null ? (
              <span
                aria-disabled="true"
                className="inline-flex min-h-11 w-full cursor-not-allowed items-center justify-center rounded-xl bg-brand px-4 text-sm font-semibold text-white opacity-45 sm:w-auto"
              >
                Compare selected players
              </span>
            ) : (
              <Link
                href={
                  comparisonHref
                }
                className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-brand px-4 text-sm font-semibold text-white transition-colors hover:bg-brand-dark sm:w-auto"
              >
                Compare selected players
              </Link>
            )}
          </div>
        </>
      )}
    </section>
  );
}
