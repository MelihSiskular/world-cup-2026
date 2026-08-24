"use client";

import {
  useQuery,
} from "@tanstack/react-query";
import {
  useEffect,
  useId,
  useState,
} from "react";

import {
  ApiErrorReference,
} from "@/components/feedback/api-error-reference";
import {
  PlayerSearchActiveFilters,
} from "@/components/players/player-search-active-filters";
import {
  PlayerSearchFilterPanel,
} from "@/components/players/player-search-filter-panel";
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
  fetchPlayerSearchFilters,
  searchPlayers,
} from "@/lib/api/browser-players";
import {
  createPlayerSearchPageUrlParameters,
  createPlayerSearchQueryKey,
  normalizePlayerSearchParameters,
  readPlayerSearchUrlParameters,
} from "@/lib/players/search-parameters";
import type {
  PlayerSearchParameters,
} from "@/lib/players/search-parameters";
import {
  DEFAULT_PLAYER_SEARCH_LIMIT,
  MINIMUM_PLAYER_SEARCH_LENGTH,
  PLAYER_SEARCH_DEBOUNCE_MS,
} from "@/lib/players/search-config";

function countActiveFilters(
  parameters: PlayerSearchParameters,
): number {
  const normalized =
    normalizePlayerSearchParameters(
      parameters,
    );

  return (
    normalized.positions.length +
    normalized.finalRoles.length +
    normalized.archetypes.length +
    normalized.countries.length +
    [
      normalized.minimumAge,
      normalized.maximumAge,
      normalized.minimumMarketValue,
      normalized.maximumMarketValue,
      normalized.minimumMinutes,
      normalized.minimumRoleConfidence,
      normalized.minimumDataReliability,
    ].filter(
      (value) =>
        value !== undefined,
    ).length
  );
}

type PlayerSearchProps =
  Readonly<{
    initialParameters?:
      PlayerSearchParameters;
  }>;

export function PlayerSearch({
  initialParameters = {
    limit:
      DEFAULT_PLAYER_SEARCH_LIMIT,
  },
}: PlayerSearchProps) {
  const inputId = useId();
  const descriptionId = useId();
  const mobileFiltersId = useId();

  const [
    parameters,
    setParameters,
  ] =
    useState<PlayerSearchParameters>(
      () =>
        normalizePlayerSearchParameters(
          initialParameters,
        ),
    );

  const [
    filtersOpen,
    setFiltersOpen,
  ] = useState(false);

  useEffect(() => {
    const searchParameters =
      createPlayerSearchPageUrlParameters(
        parameters,
      );

    const queryString =
      searchParameters.toString();

    const nextUrl = [
      window.location.pathname,
      queryString
        ? `?${queryString}`
        : "",
      window.location.hash,
    ].join("");

    const currentUrl = [
      window.location.pathname,
      window.location.search,
      window.location.hash,
    ].join("");

    if (nextUrl === currentUrl) {
      return;
    }

    window.history.replaceState(
      window.history.state,
      "",
      nextUrl,
    );
  }, [parameters]);

  useEffect(() => {
    function applyHistoryState(): void {
      setParameters(
        readPlayerSearchUrlParameters(
          new URLSearchParams(
            window.location.search,
          ),
        ),
      );
    }

    window.addEventListener(
      "popstate",
      applyHistoryState,
    );

    return () => {
      window.removeEventListener(
        "popstate",
        applyHistoryState,
      );
    };
  }, []);

  const query =
    parameters.query ?? "";

  const normalizedQuery =
    query.trim();

  const debouncedQuery =
    useDebouncedValue(
      normalizedQuery,
      PLAYER_SEARCH_DEBOUNCE_MS,
    );

  const filterCount =
    countActiveFilters(
      parameters,
    );

  const hasFilters =
    filterCount > 0;

  const hasPartialQuery =
    normalizedQuery.length > 0 &&
    normalizedQuery.length <
      MINIMUM_PLAYER_SEARCH_LENGTH;

  const hasSearchableQuery =
    normalizedQuery.length >=
    MINIMUM_PLAYER_SEARCH_LENGTH;

  const effectiveQuery =
    debouncedQuery.length >=
    MINIMUM_PLAYER_SEARCH_LENGTH
      ? debouncedQuery
      : "";

  const searchParameters = {
    ...parameters,
    query: effectiveQuery,
    limit:
      parameters.limit ??
      DEFAULT_PLAYER_SEARCH_LIMIT,
  } satisfies PlayerSearchParameters;

  const criteriaReady =
    !hasPartialQuery &&
    (
      effectiveQuery.length >=
        MINIMUM_PLAYER_SEARCH_LENGTH ||
      hasFilters
    );

  const waitingForDebounce =
    hasSearchableQuery &&
    debouncedQuery !==
      normalizedQuery;

  const filterMetadata =
    useQuery({
      queryKey: [
        "players",
        "search",
        "filters",
      ],
      queryFn: ({
        signal,
      }) =>
        fetchPlayerSearchFilters(
          signal,
        ),
      staleTime:
        10 * 60 * 1000,
      retry: false,
    });

  const playerSearch =
    useQuery({
      queryKey:
        createPlayerSearchQueryKey(
          searchParameters,
        ),
      queryFn: ({
        signal,
      }) =>
        searchPlayers(
          searchParameters,
          {
            signal,
          },
        ),
      enabled: criteriaReady,
      placeholderData: (
        previousData,
      ) => previousData,
      staleTime: 60_000,
      retry: false,
    });

  const showLoading =
    criteriaReady &&
    !playerSearch.data &&
    (
      waitingForDebounce ||
      playerSearch.isPending
    );

  function updateParameters(
    nextParameters:
      PlayerSearchParameters,
  ): void {
    setParameters({
      ...nextParameters,
      offset: 0,
      limit:
        nextParameters.limit ??
        DEFAULT_PLAYER_SEARCH_LIMIT,
    });
  }

  function clearFilters(): void {
    setParameters({
      query,
      limit:
        DEFAULT_PLAYER_SEARCH_LIMIT,
    });
  }

  function changePage(
    offset: number,
  ): void {
    setParameters(
      (current) => ({
        ...current,
        offset:
          Math.max(0, offset),
      }),
    );
  }

  return (
    <section
      aria-labelledby="player-search-heading"
      className="grid gap-6 lg:grid-cols-[20rem_minmax(0,1fr)] lg:items-start lg:gap-8"
    >
      <form
        role="search"
        onSubmit={(event) => {
          event.preventDefault();
        }}
        className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-7 lg:col-start-2"
      >
        <label
          id="player-search-heading"
          htmlFor={inputId}
          className="text-lg font-bold tracking-[-0.025em]"
        >
          Search players
        </label>

        <p
          id={descriptionId}
          className="mt-2 text-sm leading-6 text-muted"
        >
          Search by player name or combine advanced
          recruitment filters.
        </p>

        <div className="relative mt-6">
          <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="pointer-events-none absolute top-1/2 left-5 size-5 -translate-y-1/2 text-muted"
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
              setParameters(
                (current) => ({
                  ...current,
                  query:
                    event.target.value,
                  offset: 0,
                }),
              );
            }}
            placeholder="Search Michael Olise, Alex Baena…"
            autoComplete="off"
            spellCheck={false}
            enterKeyHint="search"
            aria-describedby={descriptionId}
            aria-busy={
              showLoading ||
              playerSearch.isFetching
            }
            className="min-h-14 w-full rounded-2xl border border-border bg-page py-3 pr-24 pl-13 text-base font-medium outline-none transition placeholder:font-normal placeholder:text-muted/70 hover:border-brand/40 focus:border-brand focus:bg-surface"
          />

          {query ? (
            <button
              type="button"
              onClick={() => {
                setParameters(
                  (current) => ({
                    ...current,
                    query: "",
                    offset: 0,
                  }),
                );
              }}
              className="absolute top-1/2 right-3 min-h-10 -translate-y-1/2 rounded-xl px-3.5 text-xs font-semibold text-muted transition-colors hover:bg-surface-secondary hover:text-foreground"
            >
              Clear
            </button>
          ) : null}
        </div>
      </form>

      <div className="lg:col-start-1 lg:row-start-1 lg:row-span-2">
        <button
          type="button"
          aria-expanded={filtersOpen}
          aria-controls={mobileFiltersId}
          onClick={() => {
            setFiltersOpen(
              (current) =>
                !current,
            );
          }}
          className="flex min-h-12 w-full items-center justify-between rounded-2xl border border-border bg-surface px-4 py-3 text-sm font-semibold shadow-sm lg:hidden"
        >
          <span>
            Advanced filters
          </span>

          <span className="flex items-center gap-2">
            {filterCount > 0 ? (
              <span className="rounded-full bg-brand/10 px-2 py-0.5 text-xs text-brand">
                {filterCount}
              </span>
            ) : null}

            <span
              aria-hidden="true"
              className={[
                "text-lg leading-none text-muted transition-transform",
                filtersOpen
                  ? "rotate-45"
                  : "",
              ].join(" ")}
            >
              +
            </span>
          </span>
        </button>

        <div
          id={mobileFiltersId}
          className={[
            filtersOpen
              ? "mt-3 block"
              : "hidden",
            "lg:sticky lg:top-24 lg:mt-0 lg:block",
          ].join(" ")}
        >
          {filterMetadata.isPending ? (
            <div
              className="min-h-80 animate-pulse rounded-3xl border border-border bg-surface-secondary"
              role="status"
              aria-label="Loading advanced filters"
            />
          ) : filterMetadata.isError ? (
            <div
              className="rounded-3xl border border-error/25 bg-error/10 p-5"
              role="alert"
            >
              <p className="font-semibold text-error">
                Filters unavailable
              </p>

              <p className="mt-2 text-sm leading-6 text-muted">
                The player catalogue can still be searched
                by name.
              </p>

              <button
                type="button"
                onClick={() => {
                  void filterMetadata.refetch();
                }}
                className="mt-4 min-h-11 rounded-xl border border-error/30 bg-surface px-4 py-2 text-sm font-semibold text-error"
              >
                Retry filters
              </button>
            </div>
          ) : filterMetadata.data ? (
            <PlayerSearchFilterPanel
              metadata={
                filterMetadata.data
              }
              parameters={
                parameters
              }
              onChange={
                updateParameters
              }
              onClear={
                clearFilters
              }
            />
          ) : null}
        </div>
      </div>

      <div className="min-w-0 lg:col-start-2">
        {filterCount > 0 &&
        filterMetadata.data ? (
          <PlayerSearchActiveFilters
            metadata={
              filterMetadata.data
            }
            parameters={
              parameters
            }
            onChange={
              updateParameters
            }
            onClear={
              clearFilters
            }
          />
        ) : null}

        {!normalizedQuery &&
        !hasFilters ? (
          <div className="rounded-2xl border border-dashed border-border bg-surface/60 p-8 text-center">
            <p className="font-semibold">
              Start with a player name
            </p>

            <p className="mt-2 text-sm leading-6 text-muted">
              Search directly or use advanced filters to
              explore the full analytical catalogue.
            </p>
          </div>
        ) : hasPartialQuery ? (
          <div
            className="rounded-2xl border border-warning/25 bg-warning/10 p-6"
            role="status"
          >
            <p className="font-semibold text-warning">
              Keep typing
            </p>

            <p className="mt-2 text-sm text-muted">
              Player-name searches require at least{" "}
              {MINIMUM_PLAYER_SEARCH_LENGTH} characters.
              Clear the partial name to search only with
              filters.
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
              error={
                playerSearch.error
              }
            />

            <button
              type="button"
              onClick={() => {
                void playerSearch.refetch();
              }}
              className="mt-5 min-h-11 rounded-lg border border-error/30 bg-surface px-4 py-2 text-sm font-semibold text-error"
            >
              Retry search
            </button>
          </div>
        ) : playerSearch.data &&
          playerSearch.data.total === 0 ? (
          <div className="rounded-2xl border border-border bg-surface p-8 text-center shadow-sm">
            <p className="font-semibold">
              No players found
            </p>

            <p className="mt-2 text-sm leading-6 text-muted">
              No catalogue entries matched the current
              discovery criteria. Broaden the filters or
              try another player name.
            </p>
          </div>
        ) : playerSearch.data ? (
          <div>
            <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
              <div>
                <p
                  className="text-sm text-muted"
                  role="status"
                  aria-live="polite"
                >
                  <strong className="text-foreground">
                    {playerSearch.data.total}
                  </strong>{" "}
                  {playerSearch.data.total === 1
                    ? "player"
                    : "players"}{" "}
                  found
                  {playerSearch.data.query
                    ? ` for “${playerSearch.data.query}”`
                    : ""}
                </p>

                <p className="mt-1 text-xs text-muted">
                  Showing{" "}
                  {playerSearch.data.offset + 1}–
                  {playerSearch.data.offset +
                    playerSearch.data.count}{" "}
                  of{" "}
                  {playerSearch.data.total}
                </p>
              </div>

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
                    key={
                      player.player_id
                    }
                    player={player}
                  />
                ),
              )}
            </ul>

            {playerSearch.data.offset > 0 ||
            playerSearch.data.has_more ? (
              <nav
                aria-label="Player search pagination"
                className="mt-6 flex items-center justify-between gap-4 rounded-2xl border border-border bg-surface px-4 py-3 shadow-sm"
              >
                <button
                  type="button"
                  disabled={
                    playerSearch.data.offset === 0
                  }
                  onClick={() => {
                    changePage(
                      playerSearch.data.offset -
                        playerSearch.data.limit,
                    );
                  }}
                  className="min-h-11 rounded-xl border border-border px-4 py-2 text-sm font-semibold transition enabled:hover:bg-surface-secondary disabled:cursor-not-allowed disabled:opacity-45"
                >
                  Previous
                </button>

                <span className="text-xs font-medium text-muted">
                  Page{" "}
                  {Math.floor(
                    playerSearch.data.offset /
                      playerSearch.data.limit,
                  ) + 1}
                </span>

                <button
                  type="button"
                  disabled={
                    !playerSearch.data.has_more
                  }
                  onClick={() => {
                    changePage(
                      playerSearch.data.offset +
                        playerSearch.data.limit,
                    );
                  }}
                  className="min-h-11 rounded-xl border border-border px-4 py-2 text-sm font-semibold transition enabled:hover:bg-surface-secondary disabled:cursor-not-allowed disabled:opacity-45"
                >
                  Next
                </button>
              </nav>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}
