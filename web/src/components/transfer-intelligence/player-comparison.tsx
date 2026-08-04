"use client";

import {
  useQuery,
} from "@tanstack/react-query";
import Link from "next/link";

import {
  ApiErrorReference,
} from "@/components/feedback/api-error-reference";
import {
  PlayerComparisonSkeleton,
} from "@/components/transfer-intelligence/player-comparison-skeleton";
import {
  isBrowserApiError,
} from "@/lib/api/browser-client";
import {
  runTransferAnalysis,
} from "@/lib/api/browser-transfer-intelligence";
import type {
  TransferModeName,
  TransferRecommendationResponse,
  TransferTargetResponse,
} from "@/lib/api/types";
import {
  formatMarketValue,
  formatPlayerPosition,
  formatProfileNumber,
  formatProfilePercentage,
} from "@/lib/players/profile-format";
import {
  createAnalysisSearchParameters,
  createTransferAnalysisPayload,
} from "@/lib/transfer-intelligence/analysis-form";
import type {
  TransferAnalysisFormValues,
} from "@/lib/transfer-intelligence/analysis-form";
import {
  getRecommendationRank,
  getRecommendationScore,
  TRANSFER_MODE_DETAILS,
} from "@/lib/transfer-intelligence/result-config";

type PlayerComparisonProps =
  Readonly<{
    targetPlayerId: number;
    candidatePlayerId: number;
    mode: TransferModeName;
    values: TransferAnalysisFormValues;
  }>;

type ComparisonPlayer =
  | TransferTargetResponse
  | TransferRecommendationResponse;

type ComparisonValue =
  string | number | null | undefined;

function formatTextValue(
  value: ComparisonValue,
): string {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "Not reported";
  }

  return String(value);
}

function ComparisonMetric({
  label,
  value,
  description,
}: Readonly<{
  label: string;
  value: string;
  description: string;
}>) {
  return (
    <article className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
      <p className="text-sm font-semibold text-muted">
        {label}
      </p>

      <p className="mt-3 text-3xl font-bold tracking-[-0.04em] text-brand-dark">
        {value}
      </p>

      <p className="mt-2 text-xs leading-5 text-muted">
        {description}
      </p>
    </article>
  );
}

function PlayerIdentityCard({
  label,
  player,
  score,
  scoreLabel,
}: Readonly<{
  label: string;
  player: ComparisonPlayer;
  score?: number | null;
  scoreLabel?: string;
}>) {
  return (
    <article className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          {label}
        </p>

        <span className="rounded-full bg-surface-secondary px-3 py-1.5 text-xs font-semibold text-brand-dark">
          {formatPlayerPosition(
            player.position,
          )}
        </span>
      </div>

      <h2 className="mt-5 text-3xl font-bold tracking-[-0.04em]">
        {player.player_name}
      </h2>

      <p className="mt-2 text-sm font-medium text-muted">
        {player.national_team_name ??
          player.country_name ??
          "National team unavailable"}
      </p>

      <p className="mt-4 font-semibold text-brand">
        {player.final_role ??
          player.archetype ??
          "Role unavailable"}
      </p>

      <dl className="mt-7 grid grid-cols-2 gap-4 rounded-2xl bg-surface-secondary p-5 text-sm">
        <div>
          <dt className="text-muted">
            Market value
          </dt>
          <dd className="mt-1 font-bold">
            {formatMarketValue(
              player.market_value,
              player.market_value_currency,
            )}
          </dd>
        </div>

        <div>
          <dt className="text-muted">
            Age
          </dt>
          <dd className="mt-1 font-bold">
            {player.age === null
              ? "Not reported"
              : `${formatProfileNumber(
                  player.age,
                  {
                    maximumFractionDigits: 1,
                  },
                )} years`}
          </dd>
        </div>

        <div>
          <dt className="text-muted">
            Tournament minutes
          </dt>
          <dd className="mt-1 font-bold">
            {formatProfileNumber(
              player.minutes,
            )}
          </dd>
        </div>

        <div>
          <dt className="text-muted">
            {scoreLabel ??
              "Weighted rating"}
          </dt>
          <dd className="mt-1 font-bold">
            {score !== undefined
              ? score === null
                ? "Not reported"
                : formatProfileNumber(
                    score,
                    {
                      maximumFractionDigits: 1,
                    },
                  )
              : formatProfileNumber(
                  player.weighted_rating,
                  {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  },
                )}
          </dd>
        </div>
      </dl>
    </article>
  );
}

export function PlayerComparison({
  targetPlayerId,
  candidatePlayerId,
  mode,
  values,
}: PlayerComparisonProps) {
  const payload =
    createTransferAnalysisPayload(
      targetPlayerId,
      values,
    );

  const comparison =
    useQuery({
      queryKey: [
        "transfer-intelligence",
        "comparison",
        targetPlayerId,
        candidatePlayerId,
        mode,
        values.minimumMinutes,
        values.minimumRoleConfidence,
        values.maximumMarketValueMillions ??
          null,
        values.neutralHeatmapScore,
      ],
      queryFn: ({
        signal,
      }) =>
        runTransferAnalysis(
          payload,
          signal,
        ),
      staleTime:
        5 * 60 * 1000,
      retry: (
        failureCount,
        error,
      ) => {
        if (
          isBrowserApiError(error) &&
          (
            error.status === 400 ||
            error.status === 404
          )
        ) {
          return false;
        }

        return failureCount < 1;
      },
    });

  if (comparison.isPending) {
    return <PlayerComparisonSkeleton />;
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
          The player comparison could not be prepared
        </h2>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">
          {comparison.error
            instanceof Error
            ? comparison.error.message
            : "The transfer analysis request failed."}
        </p>

        <ApiErrorReference
          error={comparison.error}
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

  const target =
    comparison.data.target;

  const recommendations =
    comparison.data.modes[mode]
      .recommendations as readonly TransferRecommendationResponse[];

  const candidate =
    recommendations.find(
      (recommendation) =>
        recommendation.player_id ===
        candidatePlayerId,
    );

  const resultParameters =
    createAnalysisSearchParameters(
      values,
    );

  resultParameters.set(
    "mode",
    mode,
  );

  const resultsHref =
    `/analysis/${targetPlayerId}/results` +
    `?${resultParameters.toString()}`;

  if (!candidate) {
    return (
      <section className="rounded-2xl border border-warning/25 bg-warning/10 p-7">
        <p className="text-sm font-semibold tracking-[0.14em] text-warning uppercase">
          Candidate unavailable
        </p>

        <h2 className="mt-3 text-3xl font-bold tracking-[-0.035em]">
          This candidate is no longer eligible
        </h2>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">
          The player does not appear in the
          selected recruitment scenario with
          the current analysis thresholds.
        </p>

        <Link
          href={resultsHref}
          className="mt-7 inline-flex rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
        >
          Return to recommendations
        </Link>
      </section>
    );
  }

  const candidateScore =
    getRecommendationScore(
      mode,
      candidate,
    );

  const candidateRank =
    getRecommendationRank(
      mode,
      candidate,
    );

  const modeDetails =
    TRANSFER_MODE_DETAILS[mode];

  const comparisonMetrics = [
    {
      label: "Statistical similarity",
      value: formatProfilePercentage(
        candidate
          .statistical_similarity_pct,
      ),
      description:
        "Similarity across the position-specific statistical feature set.",
    },
    {
      label: "Spatial similarity",
      value: formatProfilePercentage(
        candidate
          .spatial_similarity_pct,
      ),
      description:
        "Similarity in average position, spatial spread, thirds and lane occupation.",
    },
    {
      label: "Heatmap similarity",
      value: formatProfilePercentage(
        candidate
          .heatmap_similarity_score_pct,
      ),
      description:
        "Direct measured similarity in occupied pitch zones and heatmap structure.",
    },
    {
      label: "Role fit",
      value: formatProfilePercentage(
        candidate.role_fit_pct,
      ),
      description:
        "Alignment with the target player's tactical role.",
    },
    {
      label: "Market advantage",
      value: formatProfilePercentage(
        candidate
          .market_value_advantage_pct,
      ),
      description:
        "Estimated financial advantage relative to the target.",
    },
  ] as const;

  const comparisonRows = [
    {
      label: "Final role",
      target:
        target.final_role,
      candidate:
        candidate.final_role,
    },
    {
      label: "Archetype",
      target:
        target.archetype,
      candidate:
        candidate.archetype,
    },
    {
      label: "Spatial role",
      target:
        target.spatial_role,
      candidate:
        candidate.spatial_role,
    },
    {
      label: "Lateral profile",
      target:
        target.lateral_profile,
      candidate:
        candidate.lateral_profile,
    },
    {
      label: "Vertical profile",
      target:
        target.vertical_profile,
      candidate:
        candidate.vertical_profile,
    },
    {
      label: "Mobility profile",
      target:
        target.mobility_profile,
      candidate:
        candidate.mobility_profile,
    },
    {
      label: "Weighted rating",
      target:
        formatProfileNumber(
          target.weighted_rating,
          {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          },
        ),
      candidate:
        formatProfileNumber(
          candidate.weighted_rating,
          {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          },
        ),
    },
    {
      label: "Player quality",
      target:
        formatProfilePercentage(
          target.player_quality_score,
        ),
      candidate:
        formatProfilePercentage(
          candidate.player_quality_score,
        ),
    },
    {
      label: "Role confidence",
      target:
        formatProfilePercentage(
          target.role_confidence_pct,
        ),
      candidate:
        formatProfilePercentage(
          candidate.role_confidence_pct,
        ),
    },
    {
      label: "Data reliability",
      target:
        formatProfilePercentage(
          target.data_reliability_score,
        ),
      candidate:
        formatProfilePercentage(
          candidate.data_reliability_score,
        ),
    },
    {
      label: "Tournament minutes",
      target:
        formatProfileNumber(
          target.minutes,
        ),
      candidate:
        formatProfileNumber(
          candidate.minutes,
        ),
    },
    {
      label: "Market value",
      target:
        formatMarketValue(
          target.market_value,
          target.market_value_currency,
        ),
      candidate:
        formatMarketValue(
          candidate.market_value,
          candidate.market_value_currency,
        ),
    },
  ] as const;

  const evidenceItems = [
    {
      label: "Same final role",
      value:
        candidate.same_final_role,
    },
    {
      label: "Same archetype",
      value:
        candidate.same_archetype,
    },
    {
      label: "Direct heatmap evidence",
      value:
        candidate.has_heatmap_similarity,
    },
  ].filter(
    (
      item,
    ): item is Readonly<{
      label: string;
      value: boolean;
    }> =>
      typeof item.value === "boolean",
  );

  return (
    <div className="space-y-6">
      <section className="grid gap-4 lg:grid-cols-2">
        <PlayerIdentityCard
          label="Target player"
          player={target}
        />

        <PlayerIdentityCard
          label={`Candidate · Rank ${candidateRank ?? "—"}`}
          player={candidate}
          score={candidateScore}
          scoreLabel={
            modeDetails.scoreLabel
          }
        />
      </section>

      <section
        aria-label="Comparison indicators"
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5"
      >
        {comparisonMetrics.map(
          (metric) => (
            <ComparisonMetric
              key={metric.label}
              label={metric.label}
              value={metric.value}
              description={
                metric.description
              }
            />
          ),
        )}
      </section>

      <section className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
        <div className="border-b border-border p-6 sm:p-7">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            Side-by-side profile
          </p>

          <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
            Tactical and performance context
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[46rem] border-collapse text-left">
            <thead>
              <tr className="border-b border-border bg-surface-secondary">
                <th className="px-6 py-4 text-xs font-semibold tracking-[0.1em] text-muted uppercase">
                  Metric
                </th>

                <th className="px-6 py-4 text-xs font-semibold tracking-[0.1em] text-muted uppercase">
                  {target.player_name}
                </th>

                <th className="px-6 py-4 text-xs font-semibold tracking-[0.1em] text-muted uppercase">
                  {candidate.player_name}
                </th>
              </tr>
            </thead>

            <tbody>
              {comparisonRows.map(
                (row) => (
                  <tr
                    key={row.label}
                    className="border-b border-border last:border-b-0"
                  >
                    <th className="px-6 py-4 text-sm font-medium text-muted">
                      {row.label}
                    </th>

                    <td className="px-6 py-4 text-sm font-semibold">
                      {formatTextValue(
                        row.target,
                      )}
                    </td>

                    <td className="px-6 py-4 text-sm font-semibold">
                      {formatTextValue(
                        row.candidate,
                      )}
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <article className="rounded-2xl border border-border bg-surface p-6 shadow-sm sm:p-7">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            Recommendation evidence
          </p>

          <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
            Why this candidate appears in {modeDetails.label.toLowerCase()}
          </h2>

          <p className="mt-5 rounded-xl border border-brand/15 bg-surface-secondary p-5 text-sm leading-7 text-muted">
            {candidate.why_recommended}
          </p>

          {evidenceItems.length > 0 ? (
            <dl className="mt-6 grid gap-3 sm:grid-cols-3">
              {evidenceItems.map(
                (item) => (
                  <div
                    key={item.label}
                    className="rounded-xl border border-border bg-page p-4"
                  >
                    <dt className="text-xs leading-5 text-muted">
                      {item.label}
                    </dt>

                    <dd className="mt-2 font-bold">
                      {item.value
                        ? "Yes"
                        : "No"}
                    </dd>
                  </div>
                ),
              )}
            </dl>
          ) : null}
        </article>

        <aside className="h-fit rounded-2xl border border-border bg-surface-secondary p-6 lg:sticky lg:top-24">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            Decision context
          </p>

          <p className="mt-4 text-sm leading-6 text-muted">
            This comparison explains the
            recommendation produced with the
            selected thresholds. It should
            support, not replace, broader
            scouting and recruitment review.
          </p>

          <div className="mt-6 space-y-3">
            <Link
              href={resultsHref}
              className="flex min-h-11 items-center justify-center rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-dark"
            >
              Back to recommendations
            </Link>

            <Link
              href={`/players/${candidate.player_id}`}
              className="flex min-h-11 items-center justify-center rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold hover:bg-page"
            >
              Open candidate profile
            </Link>

            <Link
              href={`/players/${target.player_id}`}
              className="flex min-h-11 items-center justify-center rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold hover:bg-page"
            >
              Open target profile
            </Link>
          </div>
        </aside>
      </section>
    </div>
  );
}
