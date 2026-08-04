"use client";

import {
  useQuery,
} from "@tanstack/react-query";
import Link from "next/link";
import {
  useState,
} from "react";

import {
  ApiErrorReference,
} from "@/components/feedback/api-error-reference";
import {
  TransferAnalysisResultsSkeleton,
} from "@/components/transfer-intelligence/transfer-analysis-results-skeleton";
import {
  TransferRecommendationCard,
} from "@/components/transfer-intelligence/transfer-recommendation-card";
import {
  isBrowserApiError,
} from "@/lib/api/browser-client";
import {
  runTransferAnalysis,
} from "@/lib/api/browser-transfer-intelligence";
import type {
  TransferModeName,
  TransferRecommendationResponse,
} from "@/lib/api/types";
import {
  formatMarketValue,
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
  TRANSFER_MODE_DETAILS,
  TRANSFER_MODE_ORDER,
} from "@/lib/transfer-intelligence/result-config";

const DEFAULT_VISIBLE_RECOMMENDATIONS = 8;

type TransferAnalysisResultsProps =
  Readonly<{
    playerId: number;
    values: TransferAnalysisFormValues;
    initialMode: TransferModeName;
  }>;

export function TransferAnalysisResults({
  playerId,
  values,
  initialMode,
}: TransferAnalysisResultsProps) {
  const [
    activeMode,
    setActiveMode,
  ] = useState<TransferModeName>(
    initialMode,
  );

  const [
    showAllRecommendations,
    setShowAllRecommendations,
  ] = useState(false);

  const payload =
    createTransferAnalysisPayload(
      playerId,
      values,
    );

  const analysis =
    useQuery({
      queryKey: [
        "transfer-intelligence",
        "analysis",
        playerId,
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
      staleTime: 5 * 60 * 1000,
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

  if (analysis.isPending) {
    return (
      <TransferAnalysisResultsSkeleton />
    );
  }

  if (analysis.isError) {
    const playerNotFound =
      isBrowserApiError(
        analysis.error,
      ) &&
      analysis.error.status === 404;

    const datasetUnavailable =
      isBrowserApiError(
        analysis.error,
      ) &&
      analysis.error.status === 503;

    return (
      <section
        role="alert"
        className="rounded-2xl border border-error/25 bg-error/10 p-7"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-error uppercase">
          Analysis unavailable
        </p>

        <h2 className="mt-3 text-3xl font-bold tracking-[-0.035em]">
          {playerNotFound
            ? "The target player could not be found"
            : datasetUnavailable
              ? "The analytics datasets are unavailable"
              : "The transfer analysis could not be completed"}
        </h2>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">
          {analysis.error
            instanceof Error
            ? analysis.error.message
            : "The transfer analysis request failed."}
        </p>

        <ApiErrorReference
          error={analysis.error}
        />

        <div className="mt-7 flex flex-wrap gap-3">
          {!playerNotFound ? (
            <button
              type="button"
              onClick={() => {
                void analysis.refetch();
              }}
              className="rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
            >
              Retry analysis
            </button>
          ) : null}

          <Link
            href={`/analysis/${playerId}`}
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
          >
            Adjust parameters
          </Link>
        </div>
      </section>
    );
  }

  const {
    target,
    modes,
  } = analysis.data;

  const activeRecommendations =
    modes[activeMode]
      .recommendations as readonly TransferRecommendationResponse[];

  const visibleRecommendations =
    showAllRecommendations
      ? activeRecommendations
      : activeRecommendations.slice(
          0,
          DEFAULT_VISIBLE_RECOMMENDATIONS,
        );

  const queryString =
    createAnalysisSearchParameters(
      values,
    ).toString();

  const adjustParametersHref =
    `/analysis/${playerId}?${queryString}`;

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-3xl border border-border bg-surface shadow-sm">
        <div className="grid lg:grid-cols-[minmax(0,1fr)_20rem]">
          <div className="p-6 sm:p-8">
            <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
              Analysis target
            </p>

            <h2 className="mt-3 text-4xl font-bold tracking-[-0.045em]">
              {target.player_name}
            </h2>

            <p className="mt-2 font-semibold text-brand">
              {target.final_role ??
                target.archetype ??
                "Role unavailable"}
            </p>

            <p className="mt-2 text-sm text-muted">
              {target.national_team_name ??
                target.country_name ??
                "National team unavailable"}
              {" · "}
              {formatProfileNumber(
                target.appearances,
              )}{" "}
              appearances
              {" · "}
              {formatProfileNumber(
                target.minutes,
              )}{" "}
              minutes
            </p>

            <div className="mt-7 flex flex-wrap gap-2">
              <span className="rounded-lg border border-border bg-page px-3 py-2 text-xs font-medium">
                Minimum minutes:{" "}
                {values.minimumMinutes}
              </span>

              <span className="rounded-lg border border-border bg-page px-3 py-2 text-xs font-medium">
                Role confidence:{" "}
                {values.minimumRoleConfidence}%
              </span>

              <span className="rounded-lg border border-border bg-page px-3 py-2 text-xs font-medium">
                Heatmap fallback:{" "}
                {values.neutralHeatmapScore}%
              </span>

              <span className="rounded-lg border border-border bg-page px-3 py-2 text-xs font-medium">
                Budget:{" "}
                {values
                  .maximumMarketValueMillions ===
                undefined
                  ? "No limit"
                  : `€${values.maximumMarketValueMillions}M`}
              </span>
            </div>
          </div>

          <aside className="border-t border-border bg-surface-secondary p-6 lg:border-t-0 lg:border-l">
            <p className="text-sm font-semibold text-muted">
              Market value
            </p>

            <p className="mt-2 text-3xl font-bold tracking-[-0.04em] text-brand-dark">
              {formatMarketValue(
                target.market_value,
                target.market_value_currency,
              )}
            </p>

            <dl className="mt-6 space-y-4 text-sm">
              <div>
                <dt className="text-muted">
                  Player quality
                </dt>
                <dd className="mt-1 font-semibold">
                  {formatProfilePercentage(
                    target.player_quality_score,
                  )}
                </dd>
              </div>

              <div>
                <dt className="text-muted">
                  Role confidence
                </dt>
                <dd className="mt-1 font-semibold">
                  {formatProfilePercentage(
                    target.role_confidence_pct,
                  )}
                </dd>
              </div>
            </dl>

            <Link
              href={adjustParametersHref}
              className="mt-7 inline-flex rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold hover:bg-page"
            >
              Adjust parameters
            </Link>
          </aside>
        </div>
      </section>

      <section
        aria-label="Recruitment scenarios"
      >
        <div
          role="tablist"
          aria-label="Transfer recommendation modes"
          className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
        >
          {TRANSFER_MODE_ORDER.map(
            (modeName) => {
              const details =
                TRANSFER_MODE_DETAILS[
                  modeName
                ];

              const recommendationCount =
                modes[modeName]
                  .recommendations.length;

              const active =
                activeMode === modeName;

              return (
                <button
                  key={modeName}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => {
                    setActiveMode(
                      modeName,
                    );
                    setShowAllRecommendations(
                      false,
                    );
                  }}
                  className={[
                    "rounded-2xl border p-5 text-left transition",
                    active
                      ? "border-brand bg-brand-dark text-white shadow-sm"
                      : "border-border bg-surface hover:border-brand/35",
                  ].join(" ")}
                >
                  <span className="flex items-center justify-between gap-3">
                    <span className="font-bold">
                      {details.shortLabel}
                    </span>

                    <span
                      className={[
                        "rounded-full px-2.5 py-1 text-xs font-bold",
                        active
                          ? "bg-white/15 text-white"
                          : "bg-surface-secondary text-brand-dark",
                      ].join(" ")}
                    >
                      {recommendationCount}
                    </span>
                  </span>

                  <span
                    className={[
                      "mt-2 block text-xs leading-5",
                      active
                        ? "text-white/75"
                        : "text-muted",
                    ].join(" ")}
                  >
                    {details.description}
                  </span>
                </button>
              );
            },
          )}
        </div>
      </section>

      <section
        aria-labelledby="active-mode-heading"
      >
        <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
              Recruitment scenario
            </p>

            <h2
              id="active-mode-heading"
              className="mt-2 text-3xl font-bold tracking-[-0.035em]"
            >
              {
                TRANSFER_MODE_DETAILS[
                  activeMode
                ].label
              }
            </h2>
          </div>

          <p className="text-sm text-muted">
            {activeRecommendations.length}{" "}
            {activeRecommendations.length ===
            1
              ? "candidate"
              : "candidates"}
          </p>
        </div>

        {activeRecommendations.length ===
        0 ? (
          <div className="rounded-2xl border border-dashed border-border bg-surface p-8 text-center">
            <p className="font-semibold">
              No eligible candidates
            </p>

            <p className="mt-2 text-sm text-muted">
              Adjust the recruitment
              thresholds to expand the
              candidate pool.
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {visibleRecommendations.map(
                (recommendation) => (
                  <TransferRecommendationCard
                    key={
                      recommendation.player_id
                    }
                    targetPlayerId={
                      target.player_id
                    }
                    mode={activeMode}
                    analysisValues={values}
                    recommendation={
                      recommendation
                    }
                  />
                ),
              )}
            </div>

            {activeRecommendations.length >
            DEFAULT_VISIBLE_RECOMMENDATIONS ? (
              <div className="mt-6 text-center">
                <button
                  type="button"
                  onClick={() => {
                    setShowAllRecommendations(
                      (current) =>
                        !current,
                    );
                  }}
                  className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
                >
                  {showAllRecommendations
                    ? "Show top recommendations"
                    : `Show all ${activeRecommendations.length} candidates`}
                </button>
              </div>
            ) : null}
          </>
        )}
      </section>
    </div>
  );
}
