"use client";

import { useQuery } from "@tanstack/react-query";
import {
  useLocale,
  useTranslations,
} from "next-intl";

import { ApiErrorReference } from "@/components/feedback/api-error-reference";
import {
  Link,
} from "@/i18n/navigation";
import { PlayerImage } from "@/components/players/player-image";
import {
  getHeatmapGridMaximum,
  HeatmapDensityLegend,
  HeatmapPitch,
} from "@/components/transfer-intelligence/heatmap-pitch";
import { PlayerComparisonSkeleton } from "@/components/transfer-intelligence/player-comparison-skeleton";
import { RadarProfile } from "@/components/transfer-intelligence/radar-profile";
import { RoleCompatibilityPanel } from "@/components/transfer-intelligence/role-compatibility-panel";
import { SpatialPositionPitch } from "@/components/transfer-intelligence/spatial-position-pitch";
import {
  fetchHeatmapComparison,
  fetchRadarComparison,
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
} from "@/lib/transfer-intelligence/analysis-form";
import type { TransferAnalysisFormValues } from "@/lib/transfer-intelligence/analysis-form";
import {
  createTransferAnalysisQueryOptions,
} from "@/lib/transfer-intelligence/analysis-query";
import {
  getRecommendationRank,
  getRecommendationScore,
} from "@/lib/transfer-intelligence/result-config";

type PlayerComparisonProps = Readonly<{
  targetPlayerId: number;
  candidatePlayerId: number;
  mode: TransferModeName;
  values: TransferAnalysisFormValues;
}>;

type ComparisonPlayer = TransferTargetResponse | TransferRecommendationResponse;

function getRecommendationReasons(
  value: string | null | undefined,
): readonly string[] {
  if (
    value === null ||
    value === undefined
  ) {
    return [];
  }

  return value
    .split(";")
    .map((reason) => reason.trim())
    .filter(Boolean);
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
    <article className="min-w-0 rounded-xl border border-border bg-surface px-4 py-4 shadow-sm">
      <p className="text-xs font-medium leading-4 text-muted">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold tracking-[-0.035em] text-brand-dark">
        {value}
      </p>

      <p className="sr-only">
        {description}
      </p>
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
    <div
      title={description}
      className="min-w-0 rounded-xl border border-border bg-page px-4 py-3.5"
    >
      <dt className="text-[11px] font-medium leading-4 text-muted">
        {label}
      </dt>

      <dd className="mt-1.5 text-2xl font-bold tracking-[-0.03em] text-brand-dark">
        {value}

        <span className="sr-only">
          . {description}
        </span>
      </dd>
    </div>
  );
}

function PlayerIdentityCard({
  label,
  player,
  score,
  scoreLabel,
  scenarioLabel,
}: Readonly<{
  label: string;
  player: ComparisonPlayer;
  score?: number | null;
  scoreLabel?: string;
  scenarioLabel?: string;
}>) {
  const locale = useLocale();
  const t = useTranslations(
    "PlayerComparison",
  );

  const formatContext = {
    locale,
    missingValue:
      t("notReported"),
  };

  const formattedScenarioScore =
    score === undefined
      ? null
      : score === null
        ? "—"
        : formatProfileNumber(
            score,
            {
              maximumFractionDigits: 1,
            },
            formatContext,
          );

  return (
    <article className="min-w-0 rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            {label}
          </p>

          {scenarioLabel ? (
            <span className="rounded-full border border-brand/20 bg-brand/5 px-2.5 py-1 text-[11px] font-semibold text-brand-dark">
              {scenarioLabel}
            </span>
          ) : null}

          {score !== undefined ? (
            <span
              title={
                scoreLabel ??
                t("scenarioScore")
              }
              className="rounded-full bg-brand-dark px-2.5 py-1 text-[11px] font-bold text-white"
            >
              <span className="sr-only">
                {scoreLabel ??
                  t("scenarioScore")}{" "}
              </span>
              {t("score")}{" "}
              {formattedScenarioScore}
            </span>
          ) : null}
        </div>

        <span className="rounded-full bg-surface-secondary px-3 py-1.5 text-xs font-semibold text-brand-dark">
          {formatPlayerPosition(
            player.position,
            {
              labels: {
                G: t(
                  "positionLabels.G",
                ),
                D: t(
                  "positionLabels.D",
                ),
                M: t(
                  "positionLabels.M",
                ),
                F: t(
                  "positionLabels.F",
                ),
              },
              unavailable:
                t(
                  "positionUnavailable",
                ),
            },
          )}
        </span>
      </div>

      <div className="mt-5 flex min-w-0 items-start gap-4">
        <PlayerImage
          playerId={
            player.player_id
          }
          playerName={
            player.player_name
          }
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
              t(
                "nationalTeamUnavailable",
              )}
          </p>

          <p className="mt-3 break-words font-semibold text-brand">
            {player.final_role ??
              player.archetype ??
              t(
                "roleUnavailable",
              )}
          </p>
        </div>
      </div>

      <dl className="mt-7 grid grid-cols-2 gap-x-4 gap-y-5 rounded-2xl bg-surface-secondary p-5 text-sm sm:grid-cols-3">
        <div className="min-w-0">
          <dt className="text-muted">
            {t("marketValue")}
          </dt>

          <dd className="mt-1 font-bold">
            {formatMarketValue(
              player.market_value,
              player.market_value_currency,
              formatContext,
            )}
          </dd>
        </div>

        <div className="min-w-0">
          <dt className="text-muted">
            {t("age")}
          </dt>

          <dd className="mt-1 font-bold">
            {player.age === null
              ? t("notReported")
              : t("ageYears", {
                  value:
                    formatProfileNumber(
                      player.age,
                      {
                        maximumFractionDigits:
                          0,
                      },
                      formatContext,
                    ),
                })}
          </dd>
        </div>

        <div className="min-w-0">
          <dt className="text-muted">
            {t("tournamentMinutes")}
          </dt>

          <dd className="mt-1 font-bold">
            {formatProfileNumber(
              player.minutes,
              {},
              formatContext,
            )}
          </dd>
        </div>

        <div className="min-w-0 border-t border-border pt-4 sm:border-t-0 sm:pt-0">
          <dt className="text-muted">
            {t("weightedRating")}
          </dt>

          <dd className="mt-1 font-bold">
            {formatProfileNumber(
              player.weighted_rating,
              {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              },
              formatContext,
            )}
          </dd>
        </div>

        <div className="min-w-0 border-t border-border pt-4 sm:border-t-0 sm:pt-0">
          <dt className="text-muted">
            {t("roleConfidence")}
          </dt>

          <dd className="mt-1 font-bold">
            {formatProfilePercentage(
              player.role_confidence_pct,
              formatContext,
            )}
          </dd>
        </div>

        <div className="min-w-0 border-t border-border pt-4 sm:border-t-0 sm:pt-0">
          <dt className="text-muted">
            {t("dataReliability")}
          </dt>

          <dd className="mt-1 font-bold">
            {formatProfilePercentage(
              player.data_reliability_score,
              formatContext,
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
  const locale = useLocale();
  const t = useTranslations(
    "PlayerComparison",
  );

  const formatContext = {
    locale,
    missingValue:
      t("notReported"),
  };

  const formatPercentage = (
    value:
      | number
      | null
      | undefined,
  ) =>
    formatProfilePercentage(
      value,
      formatContext,
    );

  const formatNumber = (
    value:
      | number
      | null
      | undefined,
    options:
      Intl.NumberFormatOptions = {},
  ) =>
    formatProfileNumber(
      value,
      options,
      formatContext,
    );

  const comparison =
    useQuery(
      createTransferAnalysisQueryOptions(
        targetPlayerId,
        values,
      ),
    );

  const supplementalCandidateIsEligible =
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
    enabled: supplementalCandidateIsEligible,
    staleTime: 5 * 60 * 1000,

    /*
     * Heatmaps are supplemental evidence.
     * Keep failure isolated to this panel
     * and let the explicit retry control
     * handle another request.
     */
    retry: false,
  });

  const radarComparison = useQuery({
    queryKey: [
      "transfer-intelligence",
      "radar-comparison",
      targetPlayerId,
      candidatePlayerId,
    ],
    queryFn: ({ signal }) =>
      fetchRadarComparison(
        targetPlayerId,
        candidatePlayerId,
        signal,
      ),
    enabled: supplementalCandidateIsEligible,
    staleTime: 5 * 60 * 1000,

    /*
     * Radar profiles are supplemental
     * playing-style evidence. A radar
     * failure must not invalidate the
     * recruitment comparison.
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
          {t("comparisonUnavailable")}
        </p>

        <h2 className="mt-3 text-3xl font-bold tracking-[-0.035em]">
          {t("comparisonFailedTitle")}
        </h2>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">
          {comparison.error instanceof Error
            ? comparison.error.message
            : t("requestFailed")}
        </p>

        <ApiErrorReference
          error={comparison.error}
          label={t("requestId")}
        />

        <button
          type="button"
          onClick={() => {
            void comparison.refetch();
          }}
          className="mt-7 rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
        >
          {t("retryComparison")}
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
          {t("candidateUnavailable")}
        </p>

        <h2 className="mt-3 text-3xl font-bold tracking-[-0.035em]">
          {t("candidateIneligibleTitle")}
        </h2>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">
          {t("candidateIneligibleDescription")}
        </p>

        <Link
          href={resultsHref}
          className="mt-7 inline-flex rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
        >
          {t("returnToRecommendations")}
        </Link>
      </section>
    );
  }

  const candidateScore = getRecommendationScore(mode, candidate);

  const candidateRank = getRecommendationRank(mode, candidate);

  const modeKey =
    mode === "short_term"
      ? "shortTerm"
      : mode;

  const scenarioLabel =
    t(
      `modes.${modeKey}.label`,
    );

  const scenarioShortLabel =
    t(
      `modes.${modeKey}.shortLabel`,
    );

  const scenarioScoreLabel =
    t(
      `modes.${modeKey}.scoreLabel`,
    );

  const sharedHeatmapMaximum = heatmapComparison.data
    ? Math.max(
        getHeatmapGridMaximum(heatmapComparison.data.target.grid),
        getHeatmapGridMaximum(heatmapComparison.data.candidate.grid),
      )
    : 0;

  const comparisonMetrics = [
    {
      label: t("metrics.statisticalSimilarity"),
      value: formatPercentage(candidate.statistical_similarity_pct),
      description:
        t("metrics.statisticalSimilarityDescription"),
    },
    {
      label: t("metrics.spatialSimilarity"),
      value: formatPercentage(candidate.spatial_similarity_pct),
      description:
        t("metrics.spatialSimilarityDescription"),
    },
    {
      label: t("metrics.heatmapSimilarity"),
      value: formatPercentage(candidate.heatmap_similarity_score_pct),
      description:
        t("metrics.heatmapSimilarityDescription"),
    },
    {
      label: t("metrics.roleFit"),
      value: formatPercentage(candidate.role_fit_pct),
      description: t("metrics.roleFitDescription"),
    },
    {
      label: t("metrics.marketAdvantage"),
      value: formatPercentage(candidate.market_value_advantage_pct),
      description: t("metrics.marketAdvantageDescription"),
    },
  ] as const;

  const evidenceItems = [
    {
      label: t("sameFinalRole"),
      value: candidate.same_final_role,
    },
    {
      label: t("sameArchetype"),
      value: candidate.same_archetype,
    },
    {
      label: t("directHeatmapEvidence"),
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

  const recommendationReasons =
    getRecommendationReasons(
      candidate.why_recommended,
    );

  return (
    <div className="space-y-8">
      <section className="grid gap-4 lg:grid-cols-2">
        <PlayerIdentityCard
          label={t("targetPlayer")}
          player={target}
        />

        <PlayerIdentityCard
          label={t("candidateRank", {
            rank:
              candidateRank ?? "—",
          })}
          player={candidate}
          scenarioLabel={
            scenarioShortLabel
          }
          score={candidateScore}
          scoreLabel={
            scenarioScoreLabel
          }
        />
      </section>

      <section
        aria-label={t("comparisonIndicators")}
        className="comparison-indicator-grid grid gap-3 py-5"
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

      <div className="py-1">
        <section
          aria-label={t("recommendationEvidence")}
          className="overflow-hidden rounded-3xl border border-border bg-surface shadow-sm"
        >
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border px-5 py-5 sm:px-7 sm:py-6">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
              {t("recommendationEvidence")}
            </p>

            <h2 className="mt-2 text-2xl font-bold tracking-[-0.035em]">
              {t("whyCandidate", {
                player:
                  candidate.player_name,
              })}
            </h2>

            <p className="mt-2 text-sm leading-6 text-muted">
              {t(
                "recommendationContext",
                {
                  scenario:
                    scenarioLabel.toLocaleLowerCase(
                      locale,
                    ),
                },
              )}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="rounded-full border border-brand/20 bg-brand/5 px-3 py-1.5 text-xs font-semibold text-brand-dark">
              {candidate.recommendation_strength}
            </span>

            <span className="rounded-full border border-border bg-page px-3 py-1.5 text-xs font-semibold text-muted">
              {t("rankBadge", {
                rank:
                  candidateRank ?? "—",
              })}
            </span>
          </div>
        </div>

        <div className="grid gap-6 p-5 sm:p-7 lg:grid-cols-[minmax(0,1.35fr)_minmax(18rem,0.65fr)]">
          <div className="min-w-0">
            <p className="text-xs font-semibold tracking-[0.12em] text-muted uppercase">
              {t("whyRecommended")}
            </p>

            {recommendationReasons.length > 0 ? (
              <ul className="mt-4 grid gap-3 sm:grid-cols-2">
                {recommendationReasons.map(
                  (reason) => (
                    <li
                      key={reason}
                      className="flex min-w-0 gap-3 rounded-xl border border-border bg-surface-secondary px-4 py-3.5 text-sm leading-6 text-foreground"
                    >
                      <span
                        aria-hidden="true"
                        className="mt-2 size-1.5 shrink-0 rounded-full bg-brand"
                      />

                      <span>
                        {reason}
                      </span>
                    </li>
                  ),
                )}
              </ul>
            ) : (
              <p className="mt-4 rounded-xl border border-border bg-surface-secondary px-4 py-4 text-sm leading-6 text-muted">
                {t("explanationUnavailable")}
              </p>
            )}
          </div>

          <div className="min-w-0">
            <p className="text-xs font-semibold tracking-[0.12em] text-muted uppercase">
              {t("evidenceChecks")}
            </p>

            {evidenceItems.length > 0 ? (
              <dl className="mt-4 grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                {evidenceItems.map(
                  (item) => (
                    <div
                      key={item.label}
                      className={[
                        "flex items-center justify-between gap-4 rounded-xl border px-4 py-3.5",
                        item.value
                          ? "border-brand/15 bg-brand/5"
                          : "border-border bg-page",
                      ].join(" ")}
                    >
                      <dt className="text-sm font-medium text-foreground">
                        {item.label}
                      </dt>

                      <dd
                        className={[
                          "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold",
                          item.value
                            ? "border-brand/20 bg-surface text-brand-dark"
                            : "border-border bg-surface text-muted",
                        ].join(" ")}
                      >
                        <span
                          aria-hidden="true"
                          className={[
                            "size-1.5 rounded-full",
                            item.value
                              ? "bg-brand"
                              : "bg-muted",
                          ].join(" ")}
                        />

                        {item.value
                          ? t("yes")
                          : t("no")}
                      </dd>
                    </div>
                  ),
                )}
              </dl>
            ) : (
              <p className="mt-4 text-sm text-muted">
                {t("noEvidenceChecks")}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-border px-5 py-4 sm:px-7">
          <p className="max-w-2xl text-xs leading-5 text-muted">
            {t("recommendationDisclaimer")}
          </p>

          <div className="flex flex-wrap gap-2">
            <Link
              href={`/players/${candidate.player_id}`}
              className="rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-dark"
            >
              {t("candidateProfile")}
            </Link>

            <Link
              href={`/players/${target.player_id}`}
              className="rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold transition-colors hover:bg-page"
            >
              {t("targetProfile")}
            </Link>
          </div>
        </div>
      </section>
      </div>

      <section
        aria-labelledby="tactical-spatial-fit-heading"
      >
        <div className="mb-6">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            {t("tacticalSpatialEyebrow")}
          </p>

          <h2
            id="tactical-spatial-fit-heading"
            className="mt-2 text-2xl font-bold tracking-[-0.03em]"
          >
            {t("tacticalSpatialTitle")}
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
            {t("tacticalSpatialDescription")}
          </p>
        </div>

        <div className="grid min-w-0 gap-6 md:grid-cols-2">
          <RoleCompatibilityPanel target={target} candidate={candidate} />

        <article className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
          <div className="border-b border-border p-5 sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
                  {t("spatialProfile")}
                </p>

                <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
                  {t("spatialTitle")}
                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
                  {t("spatialDescription")}
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
                <dt className="text-xs text-muted">
                  {t("lateralSimilarity")}
                </dt>

                <dd className="mt-2 text-lg font-bold">
                  {formatPercentage(
                    candidate.lateral_profile_similarity_pct,
                  )}
                </dd>
              </div>

              <div className="rounded-xl border border-border bg-page p-4">
                <dt className="text-xs text-muted">
                  {t("verticalSimilarity")}
                </dt>

                <dd className="mt-2 text-lg font-bold">
                  {formatPercentage(
                    candidate.vertical_profile_similarity_pct,
                  )}
                </dd>
              </div>
            </dl>

            <p className="mt-4 text-xs leading-5 text-muted">
              {t("spatialGuidance")}
            </p>
          </div>
        </article>
        </div>
      </section>

      <section
        aria-label={t("radar.regionLabel")}
        className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm"
      >
        <div className="border-b border-border p-6 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
                {t("radar.eyebrow")}
              </p>

              <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
                {t("radar.title")}
              </h2>

              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
                {t("radar.description")}
              </p>
            </div>

            {radarComparison.data ? (
              <span
                className={
                  radarComparison.data.comparison.overlay_available
                    ? "rounded-full border border-success/20 bg-success/10 px-3 py-1.5 text-xs font-semibold text-success"
                    : "rounded-full border border-border bg-page px-3 py-1.5 text-xs font-semibold text-muted"
                }
              >
                {radarComparison.data.comparison.overlay_available
                  ? t(
                      "radar.sharedOverlay",
                    )
                  : t(
                      "radar.separateProfiles",
                    )}
              </span>
            ) : null}
          </div>
        </div>

        <div className="p-5 sm:p-6">
          {radarComparison.isPending ? (
            <div
              role="status"
              aria-label={t("radar.loading")}
              aria-busy="true"
              className="min-h-96 animate-pulse rounded-2xl bg-surface-secondary"
            />
          ) : radarComparison.isError ? (
            <div
              role="alert"
              className="rounded-2xl border border-warning/25 bg-warning/10 p-6"
            >
              <p className="text-sm font-semibold tracking-[0.12em] text-warning uppercase">
                {t("radar.unavailable")}
              </p>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
                {t(
                  "radar.unavailableDescription",
                )}
              </p>

              <ApiErrorReference
                error={
                  radarComparison.error
                }
                label={t("requestId")}
              />

              <button
                type="button"
                onClick={() => {
                  void radarComparison.refetch();
                }}
                className="mt-5 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold hover:bg-page"
              >
                {t("radar.retry")}
              </button>
            </div>
          ) : radarComparison.data ? (
            radarComparison.data.comparison.overlay_available ? (
              <div
                className="comparison-radar-layout grid min-w-0 gap-5"
              >
                <div className="min-w-0">
                  <RadarProfile
                    primary={radarComparison.data.target}
                    secondary={radarComparison.data.candidate}
                    showHeader={false}
                  />
                </div>

                <aside className="min-w-0 rounded-2xl border border-border bg-surface-secondary p-4 sm:p-5">
                  <div className="border-b border-border pb-4">
                    <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                      {t("radar.percentilesTitle")}
                    </p>

                    <p className="mt-2 text-xs leading-5 text-muted">
                      {t(
                        "radar.percentilesDescription",
                      )}
                    </p>
                  </div>

                  <div
                    className="comparison-percentile-grid mt-4 grid items-center gap-x-2 border-b border-border pb-3 sm:gap-x-3"
                  >
                    <span />

                    <div className="flex min-w-0 items-center justify-center gap-1.5 text-center">
                      <span
                        aria-hidden="true"
                        className="size-2 shrink-0 rounded-full bg-brand"
                      />

                      <p className="min-w-0 [overflow-wrap:anywhere] text-[11px] font-semibold leading-4 text-foreground">
                        {radarComparison.data.target.player_name}
                      </p>
                    </div>

                    <div className="flex min-w-0 items-center justify-center gap-1.5 text-center">
                      <span
                        aria-hidden="true"
                        className="size-2 shrink-0 rounded-full bg-brand-navy"
                      />

                      <p className="min-w-0 [overflow-wrap:anywhere] text-[11px] font-semibold leading-4 text-foreground">
                        {radarComparison.data.candidate.player_name}
                      </p>
                    </div>
                  </div>

                  <dl>
                    {radarComparison.data.target.dimensions.map(
                      (
                        dimension,
                        index,
                      ) => {
                        const candidateDimension =
                          radarComparison.data.candidate.dimensions[
                            index
                          ];

                        return (
                          <div
                            key={dimension.key}
                            className="comparison-percentile-grid grid items-center gap-x-2 border-b border-border/70 py-3 sm:gap-x-3 last:border-b-0"
                          >
                            <dt className="min-w-0 text-xs font-medium leading-5 text-muted">
                              {dimension.label}
                            </dt>

                            <dd className="text-center text-sm font-bold text-brand-dark">
                              {formatPercentage(
                                dimension.percentile,
                              )}
                            </dd>

                            <dd className="text-center text-sm font-bold text-brand-navy">
                              {formatPercentage(
                                candidateDimension?.percentile ??
                                  null,
                              )}
                            </dd>
                          </div>
                        );
                      },
                    )}
                  </dl>

                  <p className="mt-2 border-t border-border pt-4 text-[11px] leading-5 text-muted">
                    {t(
                      "radar.percentileGuidance",
                    )}
                  </p>
                </aside>
              </div>
            ) : (
              <>
                <div className="mb-5 rounded-xl border border-border bg-surface-secondary px-4 py-3 text-xs leading-5 text-muted sm:px-5">
                  {t(
                    "radar.incompatibleDescription",
                  )}
                </div>

                <div className="grid min-w-0 gap-5 lg:grid-cols-2">
                  <article className="min-w-0">
                    <div className="mb-3 px-1">
                      <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                        {t("target")}
                      </p>

                      <h3 className="mt-1 break-words text-lg font-bold">
                        {radarComparison.data.target.player_name}
                      </h3>
                    </div>

                    <RadarProfile
                      primary={radarComparison.data.target}
                      showHeader={false}
                    />
                  </article>

                  <article className="min-w-0">
                    <div className="mb-3 px-1">
                      <p className="text-xs font-semibold tracking-[0.12em] text-brand-navy uppercase">
                        {t("candidate")}
                      </p>

                      <h3 className="mt-1 break-words text-lg font-bold">
                        {radarComparison.data.candidate.player_name}
                      </h3>
                    </div>

                    <RadarProfile
                      primary={radarComparison.data.candidate}
                      showHeader={false}
                    />
                  </article>
                </div>
              </>
            )
          ) : null}

        </div>
      </section>

      <section
        aria-label={t("heatmap.regionLabel")}
        className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm"
      >
        <div className="border-b border-border p-6 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
                {t("heatmap.eyebrow")}
              </p>

              <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
                {t("heatmap.title")}
              </h2>

              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
                {t("heatmap.description")}
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
                  ? t(
                      "heatmap.measuredEvidence",
                    )
                  : t(
                      "heatmap.evidenceUnavailable",
                    )}
              </span>
            ) : null}
          </div>
        </div>

        <div className="p-5 sm:p-6">
          {heatmapComparison.isPending ? (
            <div
              role="status"
              aria-label={t("heatmap.loading")}
              aria-busy="true"
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
                {t("heatmap.unavailable")}
              </p>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
                {t(
                  "heatmap.unavailableDescription",
                )}
              </p>

              <ApiErrorReference
                error={
                  heatmapComparison.error
                }
                label={t("requestId")}
              />

              <button
                type="button"
                onClick={() => {
                  void heatmapComparison.refetch();
                }}
                className="mt-5 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold hover:bg-page"
              >
                {t("heatmap.retry")}
              </button>
            </div>
          ) : heatmapComparison.data ? (
            <>
              <div className="mb-5 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-surface-secondary px-4 py-3 sm:px-5">
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-foreground">
                    {t("heatmap.densityTitle")}
                  </p>

                  <p className="mt-1 max-w-3xl text-[11px] leading-5 text-muted">
                    {t(
                      "heatmap.densityDescription",
                    )}
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
                        {t("target")}
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
                        {t("candidate")}
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

              <dl
                aria-label={t("heatmap.metricsLabel")}
                className="heatmap-evidence-grid mt-6 grid gap-3"
              >
                <HeatmapEvidenceMetric
                  label={t("heatmap.metrics.measuredSimilarity")}
                  value={formatPercentage(
                    heatmapComparison.data.similarity
                      .heatmap_similarity_score_pct,
                  )}
                  description={t("heatmap.metrics.measuredSimilarityDescription")}
                />

                <HeatmapEvidenceMetric
                  label={t("heatmap.metrics.cosineSimilarity")}
                  value={formatPercentage(
                    heatmapComparison.data.similarity
                      .heatmap_cosine_similarity_pct,
                  )}
                  description={t("heatmap.metrics.cosineSimilarityDescription")}
                />

                <HeatmapEvidenceMetric
                  label={t("heatmap.metrics.occupationOverlap")}
                  value={formatPercentage(
                    heatmapComparison.data.similarity.occupation_overlap_pct,
                  )}
                  description={t("heatmap.metrics.occupationOverlapDescription")}
                />

                <HeatmapEvidenceMetric
                  label={t("heatmap.metrics.peakZoneSimilarity")}
                  value={formatPercentage(
                    heatmapComparison.data.similarity.peak_zone_similarity_pct,
                  )}
                  description={t("heatmap.metrics.peakZoneSimilarityDescription")}
                />

                <HeatmapEvidenceMetric
                  label={t("heatmap.metrics.peakZoneDistance")}
                  value={formatNumber(
                    heatmapComparison.data.similarity.peak_zone_distance,
                    {
                      maximumFractionDigits: 1,
                    },
                  )}
                  description={t("heatmap.metrics.peakZoneDistanceDescription")}
                />

                <HeatmapEvidenceMetric
                  label={t("heatmap.metrics.entropySimilarity")}
                  value={formatPercentage(
                    heatmapComparison.data.similarity.entropy_similarity_pct,
                  )}
                  description={t("heatmap.metrics.entropySimilarityDescription")}
                />
              </dl>

            </>
          ) : null}
        </div>
      </section>



    </div>
  );
}
