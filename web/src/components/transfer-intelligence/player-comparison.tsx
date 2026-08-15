"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { ApiErrorReference } from "@/components/feedback/api-error-reference";
import { PlayerImage } from "@/components/players/player-image";
import {
  getHeatmapGridMaximum,
  HeatmapDensityLegend,
  HeatmapPitch,
} from "@/components/transfer-intelligence/heatmap-pitch";
import { PlayerComparisonSkeleton } from "@/components/transfer-intelligence/player-comparison-skeleton";
import { RoleCompatibilityPanel } from "@/components/transfer-intelligence/role-compatibility-panel";
import { SpatialPositionPitch } from "@/components/transfer-intelligence/spatial-position-pitch";
import { isBrowserApiError } from "@/lib/api/browser-client";
import {
  fetchHeatmapComparison,
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
import type { TransferAnalysisFormValues } from "@/lib/transfer-intelligence/analysis-form";
import {
  getRecommendationRank,
  getRecommendationScore,
  TRANSFER_MODE_DETAILS,
} from "@/lib/transfer-intelligence/result-config";

type PlayerComparisonProps = Readonly<{
  targetPlayerId: number;
  candidatePlayerId: number;
  mode: TransferModeName;
  values: TransferAnalysisFormValues;
}>;

type ComparisonPlayer = TransferTargetResponse | TransferRecommendationResponse;

type ComparisonValue = string | number | null | undefined;

function formatTextValue(value: ComparisonValue): string {
  if (value === null || value === undefined || value === "") {
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
      <p className="text-sm font-semibold text-muted">{label}</p>

      <p className="mt-3 text-3xl font-bold tracking-[-0.04em] text-brand-dark">
        {value}
      </p>

      <p className="mt-2 text-xs leading-5 text-muted">{description}</p>
    </article>
  );
}

function HeatmapEvidenceMetric({
  label,
  value,
  description,
}: Readonly<{
  label: string;
  value: string;
  description: string;
}>) {
  return (
    <div className="rounded-xl border border-border bg-page p-4">
      <dt className="text-xs font-medium text-muted">{label}</dt>

      <dd className="mt-2 text-xl font-bold tracking-[-0.025em] text-brand-dark">
        {value}
      </dd>

      <p className="mt-2 text-[11px] leading-5 text-muted">{description}</p>
    </div>
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
    <article className="min-w-0 rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          {label}
        </p>

        <span className="rounded-full bg-surface-secondary px-3 py-1.5 text-xs font-semibold text-brand-dark">
          {formatPlayerPosition(player.position)}
        </span>
      </div>

      <div className="mt-5 flex min-w-0 items-start gap-4">
        <PlayerImage
          playerId={player.player_id}
          playerName={player.player_name}
          size="card"
          className="shrink-0 bg-page"
        />

        <div className="min-w-0 flex-1">
          <h2 className="break-words text-3xl font-bold tracking-[-0.04em]">
            {player.player_name}
          </h2>

          <p className="mt-2 break-words text-sm font-medium text-muted">
            {player.national_team_name ??
              player.country_name ??
              "National team unavailable"}
          </p>

          <p className="mt-3 break-words font-semibold text-brand">
            {player.final_role ?? player.archetype ?? "Role unavailable"}
          </p>
        </div>
      </div>

      <dl className="mt-7 grid grid-cols-2 gap-4 rounded-2xl bg-surface-secondary p-5 text-sm">
        <div>
          <dt className="text-muted">Market value</dt>
          <dd className="mt-1 font-bold">
            {formatMarketValue(
              player.market_value,
              player.market_value_currency,
            )}
          </dd>
        </div>

        <div>
          <dt className="text-muted">Age</dt>
          <dd className="mt-1 font-bold">
            {player.age === null
              ? "Not reported"
              : `${formatProfileNumber(player.age, {
                  maximumFractionDigits: 1,
                })} years`}
          </dd>
        </div>

        <div>
          <dt className="text-muted">Tournament minutes</dt>
          <dd className="mt-1 font-bold">
            {formatProfileNumber(player.minutes)}
          </dd>
        </div>

        <div>
          <dt className="text-muted">{scoreLabel ?? "Weighted rating"}</dt>
          <dd className="mt-1 font-bold">
            {score !== undefined
              ? score === null
                ? "Not reported"
                : formatProfileNumber(score, {
                    maximumFractionDigits: 1,
                  })
              : formatProfileNumber(player.weighted_rating, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
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
  const payload = createTransferAnalysisPayload(targetPlayerId, values);

  const comparison = useQuery({
    queryKey: [
      "transfer-intelligence",
      "comparison",
      targetPlayerId,
      candidatePlayerId,
      mode,
      values.minimumMinutes,
      values.minimumRoleConfidence,
      values.maximumMarketValueMillions ?? null,
      values.neutralHeatmapScore,
    ],
    queryFn: ({ signal }) => runTransferAnalysis(payload, signal),
    staleTime: 5 * 60 * 1000,
    retry: (failureCount, error) => {
      if (
        isBrowserApiError(error) &&
        (error.status === 400 || error.status === 404)
      ) {
        return false;
      }

      return failureCount < 1;
    },
  });

  const heatmapCandidateIsEligible =
    comparison.data?.modes[mode].recommendations.some(
      (recommendation) => recommendation.player_id === candidatePlayerId,
    ) ?? false;

  const heatmapComparison = useQuery({
    queryKey: [
      "transfer-intelligence",
      "heatmap-comparison",
      targetPlayerId,
      candidatePlayerId,
    ],
    queryFn: ({ signal }) =>
      fetchHeatmapComparison(targetPlayerId, candidatePlayerId, signal),
    enabled: heatmapCandidateIsEligible,
    staleTime: 5 * 60 * 1000,

    /*
     * Heatmaps are supplemental evidence.
     * Keep failure isolated to this panel
     * and let the explicit retry control
     * handle another request.
     */
    retry: false,
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
          {comparison.error instanceof Error
            ? comparison.error.message
            : "The transfer analysis request failed."}
        </p>

        <ApiErrorReference error={comparison.error} />

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

  const target = comparison.data.target;

  const recommendations = comparison.data.modes[mode]
    .recommendations as readonly TransferRecommendationResponse[];

  const candidate = recommendations.find(
    (recommendation) => recommendation.player_id === candidatePlayerId,
  );

  const resultParameters = createAnalysisSearchParameters(values);

  resultParameters.set("mode", mode);

  const resultsHref =
    `/analysis/${targetPlayerId}/results` + `?${resultParameters.toString()}`;

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
          The player does not appear in the selected recruitment scenario with
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

  const candidateScore = getRecommendationScore(mode, candidate);

  const candidateRank = getRecommendationRank(mode, candidate);

  const modeDetails = TRANSFER_MODE_DETAILS[mode];

  const sharedHeatmapMaximum = heatmapComparison.data
    ? Math.max(
        getHeatmapGridMaximum(heatmapComparison.data.target.grid),
        getHeatmapGridMaximum(heatmapComparison.data.candidate.grid),
      )
    : 0;

  const comparisonMetrics = [
    {
      label: "Statistical similarity",
      value: formatProfilePercentage(candidate.statistical_similarity_pct),
      description:
        "Similarity across the position-specific statistical feature set.",
    },
    {
      label: "Spatial similarity",
      value: formatProfilePercentage(candidate.spatial_similarity_pct),
      description:
        "Similarity in average position, spatial spread, thirds and lane occupation.",
    },
    {
      label: "Heatmap similarity",
      value: formatProfilePercentage(candidate.heatmap_similarity_score_pct),
      description:
        "Direct measured similarity in occupied pitch zones and heatmap structure.",
    },
    {
      label: "Role fit",
      value: formatProfilePercentage(candidate.role_fit_pct),
      description: "Alignment with the target player's tactical role.",
    },
    {
      label: "Market advantage",
      value: formatProfilePercentage(candidate.market_value_advantage_pct),
      description: "Estimated financial advantage relative to the target.",
    },
  ] as const;

  const comparisonRows = [
    {
      label: "Weighted rating",
      target: formatProfileNumber(target.weighted_rating, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
      candidate: formatProfileNumber(candidate.weighted_rating, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
    },
    {
      label: "Player quality",
      target: formatProfilePercentage(target.player_quality_score),
      candidate: formatProfilePercentage(candidate.player_quality_score),
    },
    {
      label: "Data reliability",
      target: formatProfilePercentage(target.data_reliability_score),
      candidate: formatProfilePercentage(candidate.data_reliability_score),
    },
    {
      label: "Tournament minutes",
      target: formatProfileNumber(target.minutes),
      candidate: formatProfileNumber(candidate.minutes),
    },
    {
      label: "Market value",
      target: formatMarketValue(
        target.market_value,
        target.market_value_currency,
      ),
      candidate: formatMarketValue(
        candidate.market_value,
        candidate.market_value_currency,
      ),
    },
  ] as const;

  const evidenceItems = [
    {
      label: "Same final role",
      value: candidate.same_final_role,
    },
    {
      label: "Same archetype",
      value: candidate.same_archetype,
    },
    {
      label: "Direct heatmap evidence",
      value: candidate.has_heatmap_similarity,
    },
  ].filter(
    (
      item,
    ): item is Readonly<{
      label: string;
      value: boolean;
    }> => typeof item.value === "boolean",
  );

  return (
    <div className="space-y-6">
      <section className="grid gap-4 lg:grid-cols-2">
        <PlayerIdentityCard label="Target player" player={target} />

        <PlayerIdentityCard
          label={`Candidate · Rank ${candidateRank ?? "—"}`}
          player={candidate}
          score={candidateScore}
          scoreLabel={modeDetails.scoreLabel}
        />
      </section>

      <section
        aria-label="Comparison indicators"
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5"
      >
        {comparisonMetrics.map((metric) => (
          <ComparisonMetric
            key={metric.label}
            label={metric.label}
            value={metric.value}
            description={metric.description}
          />
        ))}
      </section>

      <section className="grid min-w-0 gap-6 md:grid-cols-2">
        <RoleCompatibilityPanel target={target} candidate={candidate} />

        <article className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
          <div className="border-b border-border p-5 sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
                  Spatial profile
                </p>

                <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
                  Position and occupation context
                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
                  Compare weighted tournament positions and positional
                  dispersion on the same pitch.
                </p>
              </div>

              <div className="min-w-32 rounded-2xl border border-brand/15 bg-surface-secondary px-4 py-3 text-right">
                <p className="text-xs font-medium text-muted">
                  Spatial similarity
                </p>

                <p className="mt-1 text-3xl font-bold tracking-[-0.04em] text-brand-dark">
                  {formatProfilePercentage(candidate.spatial_similarity_pct)}
                </p>
              </div>
            </div>
          </div>

          <div className="p-5 sm:p-6">
            <SpatialPositionPitch
              target={{
                playerId: target.player_id,
                playerName: target.player_name,
                meanX: target.weighted_mean_x,
                meanY: target.weighted_mean_y,
                xStd: target.weighted_x_std,
                yStd: target.weighted_y_std,
              }}
              candidate={{
                playerId: candidate.player_id,
                playerName: candidate.player_name,
                meanX: candidate.weighted_mean_x,
                meanY: candidate.weighted_mean_y,
                xStd: candidate.weighted_x_std,
                yStd: candidate.weighted_y_std,
              }}
            />

            <dl className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-border bg-page p-4">
                <dt className="text-xs text-muted">Lateral similarity</dt>

                <dd className="mt-2 text-lg font-bold">
                  {formatProfilePercentage(
                    candidate.lateral_profile_similarity_pct,
                  )}
                </dd>
              </div>

              <div className="rounded-xl border border-border bg-page p-4">
                <dt className="text-xs text-muted">Vertical similarity</dt>

                <dd className="mt-2 text-lg font-bold">
                  {formatProfilePercentage(
                    candidate.vertical_profile_similarity_pct,
                  )}
                </dd>
              </div>
            </dl>

            <p className="mt-4 text-xs leading-5 text-muted">
              Pitch markers represent weighted mean tournament position.
              Ellipses represent positional dispersion on each axis. Overall
              spatial similarity also considers pitch thirds and lane
              occupation, so it is not simply the distance between the two
              markers.
            </p>
          </div>
        </article>
      </section>

      <section
        aria-label="Heatmap profile comparison"
        className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm"
      >
        <div className="border-b border-border p-6 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
                Heatmap profile
              </p>

              <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
                Measured tournament occupation
              </h2>

              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
                Compare where both players actually occupied the pitch during
                the tournament using measured heatmap evidence.
              </p>
            </div>

            {heatmapComparison.data ? (
              <span
                className={
                  heatmapComparison.data.similarity.available
                    ? "rounded-full border border-success/20 bg-success/10 px-3 py-1.5 text-xs font-semibold text-success"
                    : "rounded-full border border-border bg-page px-3 py-1.5 text-xs font-semibold text-muted"
                }
              >
                {heatmapComparison.data.similarity.available
                  ? "Measured pair evidence"
                  : "Pair evidence unavailable"}
              </span>
            ) : null}
          </div>
        </div>

        <div className="p-5 sm:p-6">
          {heatmapComparison.isPending ? (
            <div
              aria-label="Loading heatmap comparison"
              className="grid gap-5 lg:grid-cols-2"
            >
              <div className="min-h-72 animate-pulse rounded-2xl bg-surface-secondary" />
              <div className="min-h-72 animate-pulse rounded-2xl bg-surface-secondary" />
            </div>
          ) : heatmapComparison.isError ? (
            <div
              role="alert"
              className="rounded-2xl border border-warning/25 bg-warning/10 p-6"
            >
              <p className="text-sm font-semibold tracking-[0.12em] text-warning uppercase">
                Heatmap comparison unavailable
              </p>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
                The main recruitment comparison remains available, but measured
                heatmap evidence could not be loaded.
              </p>

              <ApiErrorReference error={heatmapComparison.error} />

              <button
                type="button"
                onClick={() => {
                  void heatmapComparison.refetch();
                }}
                className="mt-5 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold hover:bg-page"
              >
                Retry heatmap
              </button>
            </div>
          ) : heatmapComparison.data ? (
            <>
              <div className="mb-5 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-surface-secondary px-4 py-3 sm:px-5">
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-foreground">
                    Relative tournament occupation density
                  </p>

                  <p className="mt-1 max-w-3xl text-[11px] leading-5 text-muted">
                    Both pitches use the same shared density scale. Visual
                    intensity reflects observed tournament heatmap occupation,
                    not positional probability.
                  </p>
                </div>

                <div className="shrink-0">
                  <HeatmapDensityLegend />
                </div>
              </div>

              <div className="grid min-w-0 gap-5 md:grid-cols-2">
                <article className="min-w-0">
                  <div className="mb-3 flex items-center justify-between gap-3 px-1">
                    <div>
                      <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                        Target
                      </p>

                      <h3 className="mt-1 break-words text-lg font-bold">
                        {heatmapComparison.data.target.player_name}
                      </h3>
                    </div>
                  </div>

                  <HeatmapPitch
                    player={heatmapComparison.data.target}
                    scaleMax={sharedHeatmapMaximum}
                    showDensityLegend={false}
                  />
                </article>

                <article className="min-w-0">
                  <div className="mb-3 flex items-center justify-between gap-3 px-1">
                    <div>
                      <p className="text-xs font-semibold tracking-[0.12em] text-brand-navy uppercase">
                        Candidate
                      </p>

                      <h3 className="mt-1 break-words text-lg font-bold">
                        {heatmapComparison.data.candidate.player_name}
                      </h3>
                    </div>
                  </div>

                  <HeatmapPitch
                    player={heatmapComparison.data.candidate}
                    scaleMax={sharedHeatmapMaximum}
                    showDensityLegend={false}
                  />
                </article>
              </div>

              <dl className="mt-6 grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                <HeatmapEvidenceMetric
                  label="Measured similarity"
                  value={formatProfilePercentage(
                    heatmapComparison.data.similarity
                      .heatmap_similarity_score_pct,
                  )}
                  description="Overall measured similarity between the two tournament heatmap profiles."
                />

                <HeatmapEvidenceMetric
                  label="Cosine similarity"
                  value={formatProfilePercentage(
                    heatmapComparison.data.similarity
                      .heatmap_cosine_similarity_pct,
                  )}
                  description="Similarity in the full distribution of occupation density across grid cells."
                />

                <HeatmapEvidenceMetric
                  label="Occupation overlap"
                  value={formatProfilePercentage(
                    heatmapComparison.data.similarity.occupation_overlap_pct,
                  )}
                  description="How strongly the two players occupy the same areas of the pitch."
                />

                <HeatmapEvidenceMetric
                  label="Peak-zone similarity"
                  value={formatProfilePercentage(
                    heatmapComparison.data.similarity.peak_zone_similarity_pct,
                  )}
                  description="Similarity between the players' strongest occupation zones."
                />

                <HeatmapEvidenceMetric
                  label="Peak-zone distance"
                  value={formatProfileNumber(
                    heatmapComparison.data.similarity.peak_zone_distance,
                    {
                      maximumFractionDigits: 1,
                    },
                  )}
                  description="Distance between the strongest-density locations on the normalized pitch."
                />

                <HeatmapEvidenceMetric
                  label="Entropy similarity"
                  value={formatProfilePercentage(
                    heatmapComparison.data.similarity.entropy_similarity_pct,
                  )}
                  description="Similarity in how concentrated or dispersed the two occupation profiles are."
                />
              </dl>

              <div className="mt-5 rounded-xl border border-border bg-surface-secondary px-4 py-3 text-xs leading-5 text-muted">
                Pair evidence sample:{" "}
                <strong className="text-foreground">
                  {formatProfileNumber(
                    heatmapComparison.data.similarity
                      .target_matches_with_heatmap,
                  )}{" "}
                  target matches /{" "}
                  {formatProfileNumber(
                    heatmapComparison.data.similarity.target_heatmap_points,
                  )}{" "}
                  points
                </strong>
                {" · "}
                <strong className="text-foreground">
                  {formatProfileNumber(
                    heatmapComparison.data.similarity
                      .candidate_matches_with_heatmap,
                  )}{" "}
                  candidate matches /{" "}
                  {formatProfileNumber(
                    heatmapComparison.data.similarity.candidate_heatmap_points,
                  )}{" "}
                  points
                </strong>
                . No neutral recommendation fallback is presented as measured
                heatmap evidence.
              </div>
            </>
          ) : null}
        </div>
      </section>

      <section className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
        <div className="border-b border-border p-6 sm:p-7">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            Performance context
          </p>

          <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
            Quality, reliability and market context
          </h2>
        </div>

        <div className="min-w-0 max-w-full overflow-x-auto">
          <table className="w-full min-w-[46rem] border-collapse text-left">
            <thead>
              <tr className="border-b border-border bg-surface-secondary">
                <th className="px-6 py-4 text-xs font-semibold tracking-[0.1em] text-muted uppercase">
                  Metric
                </th>

                <th className="break-all px-6 py-4 text-xs font-semibold tracking-[0.1em] text-muted uppercase">
                  {target.player_name}
                </th>

                <th className="break-all px-6 py-4 text-xs font-semibold tracking-[0.1em] text-muted uppercase">
                  {candidate.player_name}
                </th>
              </tr>
            </thead>

            <tbody>
              {comparisonRows.map((row) => (
                <tr
                  key={row.label}
                  className="border-b border-border last:border-b-0"
                >
                  <th className="px-6 py-4 text-sm font-medium text-muted">
                    {row.label}
                  </th>

                  <td className="px-6 py-4 text-sm font-semibold">
                    {formatTextValue(row.target)}
                  </td>

                  <td className="px-6 py-4 text-sm font-semibold">
                    {formatTextValue(row.candidate)}
                  </td>
                </tr>
              ))}
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
              {evidenceItems.map((item) => (
                <div
                  key={item.label}
                  className="rounded-xl border border-border bg-page p-4"
                >
                  <dt className="text-xs leading-5 text-muted">{item.label}</dt>

                  <dd className="mt-2 font-bold">
                    {item.value ? "Yes" : "No"}
                  </dd>
                </div>
              ))}
            </dl>
          ) : null}
        </article>

        <aside className="h-fit rounded-2xl border border-border bg-surface-secondary p-6 lg:sticky lg:top-24">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            Decision context
          </p>

          <p className="mt-4 text-sm leading-6 text-muted">
            This comparison explains the recommendation produced with the
            selected thresholds. It should support, not replace, broader
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
