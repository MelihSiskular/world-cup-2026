"use client";

import {
  useQuery,
} from "@tanstack/react-query";
import {
  useId,
  useState,
} from "react";

import {
  ApiErrorReference,
} from "@/components/feedback/api-error-reference";
import {
  PlayerSearchResultCard,
} from "@/components/players/player-search-result-card";
import {
  PlayerSearchSkeleton,
} from "@/components/players/player-search-skeleton";
import {
  useDebouncedValue,
} from "@/hooks/use-debounced-value";
import {
  searchPlayers,
} from "@/lib/api/browser-players";
import {
  DEFAULT_PLAYER_SEARCH_LIMIT,
  MINIMUM_PLAYER_SEARCH_LENGTH,
  PLAYER_SEARCH_DEBOUNCE_MS,
} from "@/lib/players/search-config";

export function PlayerSearch() {
  const inputId = useId();
  const descriptionId = useId();

  const [
    query,
    setQuery,
  ] = useState("");

  const normalizedQuery =
    query.trim();

  const debouncedQuery =
    useDebouncedValue(
      normalizedQuery,
      PLAYER_SEARCH_DEBOUNCE_MS,
    );

  const hasMinimumInput =
    normalizedQuery.length >=
    MINIMUM_PLAYER_SEARCH_LENGTH;

  const waitingForDebounce =
    hasMinimumInput &&
    debouncedQuery !==
      normalizedQuery;

  const playerSearch =
    useQuery({
      queryKey: [
        "players",
        "search",
        debouncedQuery,
        DEFAULT_PLAYER_SEARCH_LIMIT,
      ],
      queryFn: ({
        signal,
      }) =>
        searchPlayers(
          debouncedQuery,
          {
            limit:
              DEFAULT_PLAYER_SEARCH_LIMIT,
            signal,
          },
        ),
      enabled:
        debouncedQuery.length >=
        MINIMUM_PLAYER_SEARCH_LENGTH,
      staleTime: 60_000,
      retry: false,
    });

  const showLoading =
    waitingForDebounce ||
    (
      hasMinimumInput &&
      playerSearch.isPending
    );

  return (
    <section
      aria-labelledby="player-search-heading"
      className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_19rem]"
    >
      <div className="min-w-0">
        <form
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
          }}
          className="rounded-2xl border border-border bg-surface p-5 shadow-sm sm:p-6"
        >
          <label
            id="player-search-heading"
            htmlFor={inputId}
            className="text-lg font-bold tracking-[-0.025em]"
          >
            Search player catalogue
          </label>

          <p
            id={descriptionId}
            className="mt-2 text-sm leading-6 text-muted"
          >
            Enter at least{" "}
            {MINIMUM_PLAYER_SEARCH_LENGTH}{" "}
            characters of a player&apos;s name.
          </p>

          <div className="relative mt-5">
            <svg
              aria-hidden="true"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="pointer-events-none absolute top-1/2 left-4 size-5 -translate-y-1/2 text-muted"
            >
              <circle
                cx="11"
                cy="11"
                r="7"
              />
              <path d="m20 20-3.5-3.5" />
            </svg>

            <input
              id={inputId}
              type="search"
              value={query}
              onChange={(event) => {
                setQuery(
                  event.target.value,
                );
              }}
              placeholder="Search Michael Olise, Alex Baena…"
              autoComplete="off"
              spellCheck={false}
              enterKeyHint="search"
              aria-describedby={descriptionId}
              aria-busy={showLoading}
              className="min-h-13 w-full rounded-xl border border-border bg-page py-3 pr-24 pl-12 text-base outline-none transition placeholder:text-muted/70 hover:border-brand/35 focus:border-brand focus:bg-surface"
            />

            {query ? (
              <button
                type="button"
                onClick={() => {
                  setQuery("");
                }}
                className="absolute top-1/2 right-3 -translate-y-1/2 rounded-lg px-3 py-2 text-xs font-semibold text-muted transition-colors hover:bg-surface-secondary hover:text-foreground"
              >
                Clear
              </button>
            ) : null}
          </div>
        </form>

        <div className="mt-6">
          {!normalizedQuery ? (
            <div className="rounded-2xl border border-dashed border-border bg-surface/60 p-8 text-center">
              <p className="font-semibold">
                Start with a player name
              </p>

              <p className="mt-2 text-sm leading-6 text-muted">
                Try searches such as
                Michael Olise, Alex,
                Alexander or Alexis.
              </p>
            </div>
          ) : normalizedQuery.length <
            MINIMUM_PLAYER_SEARCH_LENGTH ? (
            <div
              className="rounded-2xl border border-warning/25 bg-warning/10 p-6"
              role="status"
            >
              <p className="font-semibold text-warning">
                Keep typing
              </p>

              <p className="mt-2 text-sm text-muted">
                Player searches require at
                least{" "}
                {MINIMUM_PLAYER_SEARCH_LENGTH}{" "}
                characters.
              </p>
            </div>
          ) : showLoading ? (
            <PlayerSearchSkeleton />
          ) : playerSearch.isError ? (
            <div
              className="rounded-2xl border border-error/25 bg-error/10 p-6"
              role="alert"
            >
              <p className="font-semibold text-error">
                Player search unavailable
              </p>

              <p className="mt-2 text-sm leading-6 text-muted">
                {playerSearch.error
                  instanceof Error
                  ? playerSearch.error.message
                  : "The player catalogue could not be searched."}
              </p>

              <ApiErrorReference
                error={playerSearch.error}
              />

              <button
                type="button"
                onClick={() => {
                  void playerSearch.refetch();
                }}
                className="mt-5 rounded-lg border border-error/30 bg-surface px-4 py-2 text-sm font-semibold text-error"
              >
                Retry search
              </button>
            </div>
          ) : playerSearch.data &&
            playerSearch.data.count === 0 ? (
            <div className="rounded-2xl border border-border bg-surface p-8 text-center shadow-sm">
              <p className="font-semibold">
                No players found
              </p>

              <p className="mt-2 text-sm leading-6 text-muted">
                No catalogue entries matched
                “{playerSearch.data.query}”.
                Check the spelling or try a
                shorter name fragment.
              </p>
            </div>
          ) : playerSearch.data ? (
            <div>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <p
                  className="text-sm text-muted"
                  role="status"
                  aria-live="polite"
                >
                  <strong className="text-foreground">
                    {playerSearch.data.count}
                  </strong>{" "}
                  {playerSearch.data.count === 1
                    ? "player"
                    : "players"}{" "}
                  found for “
                  {playerSearch.data.query}”
                </p>

                {playerSearch.isFetching ? (
                  <span className="text-xs font-medium text-brand">
                    Updating…
                  </span>
                ) : null}
              </div>

              <ul className="space-y-4">
                {playerSearch.data.players.map(
                  (player) => (
                    <PlayerSearchResultCard
                      key={player.player_id}
                      player={player}
                    />
                  ),
                )}
              </ul>
            </div>
          ) : null}
        </div>
      </div>

      <aside className="h-fit rounded-2xl border border-border bg-surface-secondary p-6 lg:sticky lg:top-24">
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          Search result data
        </p>

        <h2 className="mt-4 text-xl font-bold tracking-[-0.025em]">
          More than a player name
        </h2>

        <p className="mt-3 text-sm leading-6 text-muted">
          Every result includes a stable
          player identity and enough role
          context to choose the correct
          tournament profile.
        </p>

        <dl className="mt-6 space-y-4 text-sm">
          <div>
            <dt className="font-semibold">
              Role context
            </dt>
            <dd className="mt-1 text-muted">
              Final role and statistical
              archetype
            </dd>
          </div>

          <div>
            <dt className="font-semibold">
              Market context
            </dt>
            <dd className="mt-1 text-muted">
              Age and estimated market value
            </dd>
          </div>

          <div>
            <dt className="font-semibold">
              Stable navigation
            </dt>
            <dd className="mt-1 text-muted">
              Profiles open through a
              persistent player ID
            </dd>
          </div>
        </dl>
      </aside>
    </section>
  );
}
