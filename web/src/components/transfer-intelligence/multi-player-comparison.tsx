"use client";

import {
  useQuery,
} from "@tanstack/react-query";
import Link from "next/link";

import {
  ApiErrorReference,
} from "@/components/feedback/api-error-reference";
import {
  MultiPlayerComparisonEvidence,
} from "@/components/transfer-intelligence/multi-player-comparison-evidence";
import {
  fetchMultiPlayerComparison,
} from "@/lib/api/browser-transfer-intelligence";
import type {
  MultiPlayerComparisonCandidateResponse,
  MultiPlayerComparisonPlayerResponse,
} from "@/lib/api/types";
import {
  formatMarketValue,
  formatPlayerPosition,
  formatProfileNumber,
  formatProfilePercentage,
} from "@/lib/players/profile-format";
import type {
  MultiComparisonIdentifiers,
} from "@/lib/transfer-intelligence/multi-comparison-selection";

type MultiPlayerComparisonProps =
  Readonly<{
    identifiers:
      MultiComparisonIdentifiers;
  }>;

type ComparisonMatrixRow =
  Readonly<{
    key: string;
    label: string;
    description: string;
    targetValue: string;
    candidateValues:
      readonly string[];
  }>;

function formatOptionalAge(
  value:
    | number
    | null
    | undefined,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "Unavailable";
  }

  return (
    `${formatProfileNumber(
      value,
      {
        maximumFractionDigits: 0,
      },
    )} years`
  );
}

function formatOptionalNumber(
  value:
    | number
    | null
    | undefined,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "Unavailable";
  }

  return formatProfileNumber(
    value,
  );
}

function formatOptionalScore(
  value:
    | number
    | null
    | undefined,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "Unavailable";
  }

  return (
    `${formatProfileNumber(
      value,
      {
        maximumFractionDigits: 1,
      },
    )} / 100`
  );
}

function formatOptionalPercentage(
  value:
    | number
    | null
    | undefined,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "Unavailable";
  }

  return formatProfilePercentage(
    value,
  );
}

function formatOptionalMarketValue(
  player:
    MultiPlayerComparisonPlayerResponse,
): string {
  if (
    player.market_value ===
      null ||
    player.market_value ===
      undefined
  ) {
    return "Unavailable";
  }

  return formatMarketValue(
    player.market_value,
    player
      .market_value_currency ??
      null,
  );
}

function formatRole(
  player:
    MultiPlayerComparisonPlayerResponse,
): string {
  return (
    player.final_role ??
    player.archetype ??
    player.spatial_role ??
    "Unavailable"
  );
}

function formatPosition(
  player:
    MultiPlayerComparisonPlayerResponse,
): string {
  if (
    player.position === null ||
    player.position ===
      undefined
  ) {
    return "Unavailable";
  }

  return formatPlayerPosition(
    player.position,
  );
}

function buildMatrixRows(
  target:
    MultiPlayerComparisonPlayerResponse,
  candidates:
    readonly MultiPlayerComparisonCandidateResponse[],
): readonly ComparisonMatrixRow[] {
  return [
    {
      key: "position",
      label: "Position",
      description:
        "Broad player position.",
      targetValue:
        formatPosition(target),
      candidateValues:
        candidates.map(
          ({ player }) =>
            formatPosition(
              player,
            ),
        ),
    },
    {
      key: "role",
      label: "Final role",
      description:
        "Primary analytical role label.",
      targetValue:
        formatRole(target),
      candidateValues:
        candidates.map(
          ({ player }) =>
            formatRole(player),
        ),
    },
    {
      key: "age",
      label: "Age",
      description:
        "Reported player age.",
      targetValue:
        formatOptionalAge(
          target.age,
        ),
      candidateValues:
        candidates.map(
          ({ player }) =>
            formatOptionalAge(
              player.age,
            ),
        ),
    },
    {
      key: "market-value",
      label: "Market value",
      description:
        "Reported market value and currency.",
      targetValue:
        formatOptionalMarketValue(
          target,
        ),
      candidateValues:
        candidates.map(
          ({ player }) =>
            formatOptionalMarketValue(
              player,
            ),
        ),
    },
    {
      key: "minutes",
      label: "Tournament minutes",
      description:
        "Minutes recorded in the tournament dataset.",
      targetValue:
        formatOptionalNumber(
          target.minutes,
        ),
      candidateValues:
        candidates.map(
          ({ player }) =>
            formatOptionalNumber(
              player.minutes,
            ),
        ),
    },
    {
      key: "quality",
      label: "Player quality",
      description:
        "Combined player-quality score.",
      targetValue:
        formatOptionalScore(
          target
            .player_quality_score,
        ),
      candidateValues:
        candidates.map(
          ({ player }) =>
            formatOptionalScore(
              player
                .player_quality_score,
            ),
        ),
    },
    {
      key: "reliability",
      label: "Data reliability",
      description:
        "Reliability of the available player evidence.",
      targetValue:
        formatOptionalPercentage(
          target
            .data_reliability_score,
        ),
      candidateValues:
        candidates.map(
          ({ player }) =>
            formatOptionalPercentage(
              player
                .data_reliability_score,
            ),
        ),
    },
    {
      key:
        "statistical-similarity",
      label:
        "Statistical similarity",
      description:
        "Measured statistical similarity relative to the target.",
      targetValue:
        "Reference",
      candidateValues:
        candidates.map(
          ({ evidence }) =>
            formatOptionalPercentage(
              evidence
                .statistical_similarity_pct,
            ),
        ),
    },
    {
      key:
        "spatial-similarity",
      label:
        "Spatial similarity",
      description:
        "Same-position spatial similarity relative to the target.",
      targetValue:
        "Reference",
      candidateValues:
        candidates.map(
          ({ evidence }) =>
            formatOptionalPercentage(
              evidence
                .spatial_similarity_pct,
            ),
        ),
    },
    {
      key:
        "heatmap-similarity",
      label:
        "Heatmap similarity",
      description:
        "Measured tournament heatmap similarity relative to the target.",
      targetValue:
        "Reference",
      candidateValues:
        candidates.map(
          ({ evidence }) =>
            formatOptionalPercentage(
              evidence
                .heatmap_similarity_score_pct,
            ),
        ),
    },
    {
      key: "role-fit",
      label: "Role fit",
      description:
        "Role compatibility relative to the target.",
      targetValue:
        "Reference",
      candidateValues:
        candidates.map(
          ({ evidence }) =>
            formatOptionalPercentage(
              evidence
                .role_fit_pct,
            ),
        ),
    },
    {
      key:
        "market-advantage",
      label:
        "Market advantage",
      description:
        "Candidate market-value advantage relative to the target.",
      targetValue:
        "Reference",
      candidateValues:
        candidates.map(
          ({ evidence }) =>
            formatOptionalPercentage(
              evidence
                .market_value_advantage_pct,
            ),
        ),
    },
  ];
}

function MultiPlayerComparisonSkeleton() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Preparing multi-player comparison"
      className="animate-pulse space-y-5 motion-reduce:animate-none"
    >
      <div className="h-24 rounded-3xl border border-border bg-surface-secondary" />

      <div className="overflow-hidden rounded-3xl border border-border bg-surface">
        <div className="h-16 border-b border-border bg-surface-secondary" />

        {Array.from({
          length: 8,
        }).map(
          (_, index) => (
            <div
              key={index}
              className="grid grid-cols-4 gap-4 border-b border-border px-5 py-4 last:border-b-0"
            >
              <div className="h-4 rounded bg-surface-secondary" />
              <div className="h-4 rounded bg-surface-secondary" />
              <div className="h-4 rounded bg-surface-secondary" />
              <div className="h-4 rounded bg-surface-secondary" />
            </div>
          ),
        )}
      </div>

      <span className="sr-only">
        Preparing multi-player
        comparison…
      </span>
    </div>
  );
}

export function MultiPlayerComparison({
  identifiers,
}: MultiPlayerComparisonProps) {
  const comparison =
    useQuery({
      queryKey: [
        "transfer-intelligence",
        "multi-player-comparison",
        identifiers
          .targetPlayerId,
        ...identifiers
          .candidatePlayerIds,
      ],
      queryFn: ({
        signal,
      }) =>
        fetchMultiPlayerComparison(
          identifiers
            .targetPlayerId,
          identifiers
            .candidatePlayerIds,
          signal,
        ),
      staleTime:
        5 * 60 * 1000,
      retry: false,
    });

  if (comparison.isPending) {
    return (
      <MultiPlayerComparisonSkeleton />
    );
  }

  if (comparison.isError) {
    return (
      <section
        role="alert"
        className="rounded-2xl border border-error/25 bg-error/10 p-7"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-error uppercase">
          Comparison unavailable
        </p>

        <h2 className="mt-3 text-3xl font-bold tracking-[-0.035em]">
          The multi-player
          comparison could not be
          prepared
        </h2>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">
          {
            comparison.error
              instanceof Error
              ? comparison
                  .error.message
              : "The comparison request failed."
          }
        </p>

        <ApiErrorReference
          error={
            comparison.error
          }
        />

        <button
          type="button"
          onClick={() => {
            void comparison.refetch();
          }}
          className="mt-7 rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
        >
          Retry comparison
        </button>
      </section>
    );
  }

  const {
    target,
    candidates,
  } = comparison.data;

  if (candidates.length === 0) {
    return (
      <section className="rounded-2xl border border-warning/25 bg-warning/10 p-7">
        <p className="text-sm font-semibold tracking-[0.14em] text-warning uppercase">
          Candidates unavailable
        </p>

        <h2 className="mt-3 text-3xl font-bold tracking-[-0.035em]">
          No comparison candidates
          were returned
        </h2>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">
          Return to the shortlist
          workspace and choose at
          least one same-position
          candidate.
        </p>

        <Link
          href="/shortlists"
          className="mt-7 inline-flex rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
        >
          Return to shortlists
        </Link>
      </section>
    );
  }

  const rows =
    buildMatrixRows(
      target,
      candidates,
    );

  return (
    <div className="space-y-8">
      <section
      aria-labelledby="multi-comparison-overview-title"
      className="overflow-hidden rounded-3xl border border-border bg-surface shadow-sm"
    >
      <div className="border-b border-border px-5 py-6 sm:px-7">
        <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
          Overview matrix
        </p>

        <h2
          id="multi-comparison-overview-title"
          className="mt-2 text-2xl font-bold tracking-[-0.035em]"
        >
          Target-relative comparison
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          {
            candidates.length
          }{" "}
          {
            candidates.length ===
            1
              ? "candidate"
              : "candidates"
          }{" "}
          compared with{" "}
          {target.player_name}.
          Unavailable pair evidence
          remains explicitly
          unavailable.
        </p>
      </div>

      <div
        role="region"
        aria-label="Scrollable multi-player comparison matrix"
        tabIndex={0}
        className="overflow-x-auto focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/25"
      >
        <table className="w-full min-w-[54rem] border-collapse text-left text-sm">
          <caption className="sr-only">
            Target-relative comparison
            overview
          </caption>

          <thead className="bg-surface-secondary">
            <tr>
              <th
                scope="col"
                className="sticky left-0 z-10 w-48 border-b border-r border-border bg-surface-secondary px-5 py-4 font-semibold"
              >
                Metric
              </th>

              <th
                scope="col"
                className="min-w-48 border-b border-border px-5 py-4"
              >
                <span className="block text-[11px] font-semibold tracking-[0.12em] text-brand uppercase">
                  Target
                </span>

                <Link
                  href={`/players/${target.player_id}`}
                  className="mt-1 block break-words font-bold hover:text-brand"
                >
                  {target.player_name}
                </Link>
              </th>

              {candidates.map(
                (
                  candidate,
                  index,
                ) => (
                  <th
                    key={
                      candidate
                        .player
                        .player_id
                    }
                    scope="col"
                    className="min-w-48 border-b border-border px-5 py-4"
                  >
                    <span className="block text-[11px] font-semibold tracking-[0.12em] text-muted uppercase">
                      Candidate{" "}
                      {index + 1}
                    </span>

                    <Link
                      href={`/players/${candidate.player.player_id}`}
                      className="mt-1 block break-words font-bold hover:text-brand"
                    >
                      {
                        candidate
                          .player
                          .player_name
                      }
                    </Link>
                  </th>
                ),
              )}
            </tr>
          </thead>

          <tbody>
            {rows.map(
              (row) => (
                <tr
                  key={row.key}
                  className="border-b border-border last:border-b-0"
                >
                  <th
                    scope="row"
                    title={
                      row.description
                    }
                    className="sticky left-0 z-10 border-r border-border bg-surface px-5 py-4 font-semibold"
                  >
                    {row.label}

                    <span className="sr-only">
                      .{" "}
                      {
                        row.description
                      }
                    </span>
                  </th>

                  <td className="px-5 py-4 font-medium">
                    {
                      row.targetValue
                    }
                  </td>

                  {row.candidateValues.map(
                    (
                      value,
                      index,
                    ) => (
                      <td
                        key={`${row.key}-${candidates[index]?.player.player_id ?? index}`}
                        className={[
                          "px-5 py-4 font-medium",
                          value ===
                          "Unavailable"
                            ? "text-muted"
                            : "",
                        ].join(
                          " ",
                        )}
                      >
                        {value}
                      </td>
                    ),
                  )}
                </tr>
              ),
            )}
          </tbody>
        </table>
      </div>

      <div className="border-t border-border bg-page px-5 py-4 sm:px-7">
        <p className="text-xs leading-5 text-muted">
          Reference cells identify
          the target baseline.
          Unavailable values mean the
          requested pair has no
          measured evidence in the
          current dataset.
        </p>
      </div>
      </section>

      <MultiPlayerComparisonEvidence
        target={target}
        candidates={candidates}
      />
    </div>
  );
}
