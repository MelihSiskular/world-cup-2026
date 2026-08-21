import Link from "next/link";

import {
  PlayerImage,
} from "@/components/players/player-image";
import {
  RecommendationExplainability,
} from "@/components/transfer-intelligence/recommendation-explainability";
import type {
  TransferModeName,
  TransferRecommendationResponse,
} from "@/lib/api/types";
import {
  createAnalysisSearchParameters,
} from "@/lib/transfer-intelligence/analysis-form";
import type {
  TransferAnalysisFormValues,
} from "@/lib/transfer-intelligence/analysis-form";
import {
  formatMarketValue,
  formatPlayerPosition,
  formatProfileNumber,
  formatProfilePercentage,
} from "@/lib/players/profile-format";
import {
  getRecommendationRank,
  getRecommendationScore,
  TRANSFER_MODE_DETAILS,
} from "@/lib/transfer-intelligence/result-config";

type TransferRecommendationCardVariant =
  | "featured"
  | "compact";

type TransferRecommendationCardProps =
  Readonly<{
    targetPlayerId: number;
    mode: TransferModeName;
    analysisValues:
      TransferAnalysisFormValues;
    recommendation:
      TransferRecommendationResponse;
    variant?: TransferRecommendationCardVariant;
  }>;

function formatMetricPercentage(
  value: number | null | undefined,
): string {
  return formatProfilePercentage(
    value,
  );
}

export function TransferRecommendationCard({
  targetPlayerId,
  mode,
  analysisValues,
  recommendation,
  variant = "featured",
}: TransferRecommendationCardProps) {
  const score =
    getRecommendationScore(
      mode,
      recommendation,
    );

  const rank =
    getRecommendationRank(
      mode,
      recommendation,
    );

  const modeDetails =
    TRANSFER_MODE_DETAILS[mode];

  const comparisonParameters =
    createAnalysisSearchParameters(
      analysisValues,
    );

  comparisonParameters.set(
    "mode",
    mode,
  );

  const comparisonHref =
    `/compare/${targetPlayerId}/${recommendation.player_id}` +
    `?${comparisonParameters.toString()}`;

  const metrics = [
    {
      label: "Statistical similarity",
      value: formatMetricPercentage(
        recommendation
          .statistical_similarity_pct,
      ),
    },
    {
      label: "Spatial similarity",
      value: formatMetricPercentage(
        recommendation
          .spatial_similarity_pct,
      ),
    },
    {
      label: "Role fit",
      value: formatMetricPercentage(
        recommendation.role_fit_pct,
      ),
    },
    {
      label: "Market advantage",
      value: formatMetricPercentage(
        recommendation
          .market_value_advantage_pct,
      ),
    },
  ] as const;

  if (variant === "compact") {
    return (
      <article className="rounded-2xl border border-border bg-surface p-5 shadow-sm sm:p-6">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div className="flex min-w-0 items-start gap-4">
            <PlayerImage
              playerId={
                recommendation.player_id
              }
              playerName={
                recommendation.player_name
              }
              size="card"
              className="bg-page"
            />

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center justify-center rounded-full border border-brand/20 bg-brand/5 px-2.5 py-1 text-xs font-bold text-brand-dark">
                  {rank === null
                    ? "—"
                    : `#${rank}`}
                </span>

                <span className="rounded-full bg-surface-secondary px-2.5 py-1 text-xs font-semibold text-brand-dark">
                  {formatPlayerPosition(
                    recommendation.position,
                  )}
                </span>

                <span className="rounded-full border border-border px-2.5 py-1 text-xs font-medium text-muted">
                  {
                    recommendation
                      .recommendation_strength
                  }
                </span>
              </div>

              <h3 className="mt-3 break-words text-xl font-bold tracking-[-0.03em]">
                {
                  recommendation
                    .player_name
                }
              </h3>

              <p className="mt-1 text-sm text-muted">
                {recommendation
                  .national_team_name ??
                  recommendation
                    .country_name ??
                  "National team unavailable"}
              </p>

              <p className="mt-1.5 break-words text-sm font-semibold text-brand">
                {recommendation
                  .final_role ??
                  recommendation
                    .archetype ??
                  "Role unavailable"}
              </p>
            </div>
          </div>

          <dl className="grid gap-2 sm:grid-cols-2 xl:w-[30rem] xl:grid-cols-4">
            <div className="rounded-xl border border-border bg-page px-3 py-2.5">
              <dt className="text-[11px] leading-4 text-muted">
                {modeDetails.scoreLabel}
              </dt>

              <dd className="mt-1 font-bold text-brand-dark">
                {score === null
                  ? "—"
                  : formatProfileNumber(
                      score,
                      {
                        maximumFractionDigits: 1,
                      },
                    )}
              </dd>
            </div>

            <div className="rounded-xl border border-border bg-page px-3 py-2.5">
              <dt className="text-[11px] leading-4 text-muted">
                Statistical
              </dt>

              <dd className="mt-1 font-bold">
                {formatMetricPercentage(
                  recommendation
                    .statistical_similarity_pct,
                )}
              </dd>
            </div>

            <div className="rounded-xl border border-border bg-page px-3 py-2.5">
              <dt className="text-[11px] leading-4 text-muted">
                Spatial
              </dt>

              <dd className="mt-1 font-bold">
                {formatMetricPercentage(
                  recommendation
                    .spatial_similarity_pct,
                )}
              </dd>
            </div>

            <div className="rounded-xl border border-border bg-page px-3 py-2.5">
              <dt className="text-[11px] leading-4 text-muted">
                Role fit
              </dt>

              <dd className="mt-1 font-bold">
                {formatMetricPercentage(
                  recommendation
                    .role_fit_pct,
                )}
              </dd>
            </div>
          </dl>
        </div>

        <div className="mt-5 flex flex-wrap items-center justify-between gap-4 border-t border-border pt-4">
          <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted">
            <span>
              Market{" "}
              <strong className="font-semibold text-foreground">
                {formatMarketValue(
                  recommendation.market_value,
                  recommendation
                    .market_value_currency,
                )}
              </strong>
            </span>

            <span>
              Age{" "}
              <strong className="font-semibold text-foreground">
                {recommendation.age === null
                  ? "Not reported"
                  : `${formatProfileNumber(
                      recommendation.age,
                      {
                        maximumFractionDigits: 1,
                      },
                    )} years`}
              </strong>
            </span>

            <span>
              Minutes{" "}
              <strong className="font-semibold text-foreground">
                {formatProfileNumber(
                  recommendation.minutes,
                )}
              </strong>
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            <Link
              href={comparisonHref}
              className="rounded-xl bg-brand px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-brand-dark"
            >
              Compare
            </Link>

            <Link
              href={`/players/${recommendation.player_id}`}
              className="rounded-xl border border-border px-4 py-2 text-xs font-semibold transition-colors hover:bg-surface-secondary"
            >
              Profile
            </Link>
          </div>
        </div>
      </article>
    );
  }

  return (
    <article className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
      <div className="grid lg:grid-cols-[minmax(0,1fr)_13rem]">
        <div className="p-5 sm:p-6">
          <div className="flex items-start gap-4">
            <PlayerImage
              playerId={
                recommendation.player_id
              }
              playerName={
                recommendation.player_name
              }
              size="card"
              className="bg-page"
            />

            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex size-9 items-center justify-center rounded-xl bg-brand-dark text-sm font-bold text-white">
                  {rank ?? "—"}
                </span>

                <span className="rounded-full bg-surface-secondary px-3 py-1.5 text-xs font-semibold text-brand-dark">
                  {formatPlayerPosition(
                    recommendation.position,
                  )}
                </span>

                <span className="rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted">
                  {
                    recommendation
                      .recommendation_strength
                  }
                </span>
              </div>

              <div className="mt-3">
                <h3 className="break-words text-2xl font-bold tracking-[-0.035em]">
                  {
                    recommendation
                      .player_name
                  }
                </h3>

                <p className="mt-1 break-words text-sm font-medium text-muted">
                  {recommendation
                    .national_team_name ??
                    recommendation
                      .country_name ??
                    "National team unavailable"}
                </p>

                <p className="mt-2 break-words font-semibold text-brand">
                  {recommendation
                    .final_role ??
                    recommendation
                      .archetype ??
                    "Role unavailable"}
                </p>
              </div>
            </div>
          </div>

          <dl className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {metrics.map((metric) => (
              <div
                key={metric.label}
                className="rounded-xl border border-border bg-page p-3"
              >
                <dt className="text-xs leading-5 text-muted">
                  {metric.label}
                </dt>

                <dd className="mt-1 font-bold">
                  {metric.value}
                </dd>
              </div>
            ))}
          </dl>

          <RecommendationExplainability
            explainability={
              recommendation.explainability
            }
          />

          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              href={comparisonHref}
              className="rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-dark"
            >
              Compare with target
            </Link>

            <Link
              href={`/players/${recommendation.player_id}`}
              className="rounded-xl border border-border px-4 py-2.5 text-sm font-semibold transition-colors hover:bg-surface-secondary"
            >
              Open player profile
            </Link>
          </div>
        </div>

        <aside className="border-t border-border bg-surface-secondary p-5 lg:border-t-0 lg:border-l">
          <p className="text-xs font-semibold text-muted">
            {modeDetails.scoreLabel}
          </p>

          <p className="mt-2 text-3xl font-bold tracking-[-0.04em] text-brand-dark">
            {score === null
              ? "—"
              : formatProfileNumber(
                  score,
                  {
                    maximumFractionDigits: 1,
                  },
                )}
          </p>

          <dl className="mt-6 space-y-4 text-sm">
            <div>
              <dt className="text-muted">
                Market value
              </dt>
              <dd className="mt-1 font-semibold">
                {formatMarketValue(
                  recommendation.market_value,
                  recommendation
                    .market_value_currency,
                )}
              </dd>
            </div>

            <div>
              <dt className="text-muted">
                Age
              </dt>
              <dd className="mt-1 font-semibold">
                {recommendation.age === null
                  ? "Not reported"
                  : `${formatProfileNumber(
                      recommendation.age,
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
              <dd className="mt-1 font-semibold">
                {formatProfileNumber(
                  recommendation.minutes,
                )}
              </dd>
            </div>
          </dl>
        </aside>
      </div>
    </article>
  );
}
