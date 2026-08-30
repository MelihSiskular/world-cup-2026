import {
  useLocale,
  useTranslations,
} from "next-intl";

import {
  PlayerImage,
} from "@/components/players/player-image";
import {
  Link,
} from "@/i18n/navigation";
import {
  ShortlistAction,
} from "@/components/shortlists/shortlist-action";
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
  createShortlistSnapshotFromRecommendation,
} from "@/lib/shortlists/snapshot";
import {
  formatMarketValue,
  formatPlayerPosition,
  formatProfileNumber,
  formatProfilePercentage,
} from "@/lib/players/profile-format";
import type {
  ProfileFormatContext,
} from "@/lib/players/profile-format";
import {
  getRecommendationRank,
  getRecommendationScore,
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

export function TransferRecommendationCard({
  targetPlayerId,
  mode,
  analysisValues,
  recommendation,
  variant = "featured",
}: TransferRecommendationCardProps) {
  const locale = useLocale();

  const translations =
    useTranslations(
      "TransferRecommendationCard",
    );

  const formatContext:
    ProfileFormatContext = {
      locale,
      missingValue:
        translations(
          "notReported",
        ),
    };

  const positionOptions = {
    labels: {
      G: translations(
        "positionLabels.G",
      ),
      D: translations(
        "positionLabels.D",
      ),
      M: translations(
        "positionLabels.M",
      ),
      F: translations(
        "positionLabels.F",
      ),
    },
    unavailable:
      translations(
        "positionUnavailable",
      ),
  };

  const scoreLabels = {
    immediate: translations(
      "scoreLabels.immediate",
    ),
    development: translations(
      "scoreLabels.development",
    ),
    value: translations(
      "scoreLabels.value",
    ),
    short_term: translations(
      "scoreLabels.shortTerm",
    ),
  } as const;

  const formatMetricPercentage = (
    value: number | null | undefined,
  ): string =>
    formatProfilePercentage(
      value,
      formatContext,
    );

  const formatNumber = (
    value: number | null | undefined,
    options:
      Intl.NumberFormatOptions = {},
  ): string =>
    formatProfileNumber(
      value,
      options,
      formatContext,
    );

  const formatMarket = (
    value: number | null | undefined,
    currency: string | null | undefined,
  ): string =>
    formatMarketValue(
      value,
      currency,
      formatContext,
    );

  const formatPosition = (
    value: string | null | undefined,
  ): string =>
    formatPlayerPosition(
      value,
      positionOptions,
    );

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

  const shortlistPlayer =
    createShortlistSnapshotFromRecommendation(
      recommendation,
    );

  const metrics = [
    {
      label: translations(
        "statisticalSimilarity",
      ),
      value: formatMetricPercentage(
        recommendation
          .statistical_similarity_pct,
      ),
    },
    {
      label: translations(
        "spatialSimilarity",
      ),
      value: formatMetricPercentage(
        recommendation
          .spatial_similarity_pct,
      ),
    },
    {
      label: translations(
        "roleFit",
      ),
      value: formatMetricPercentage(
        recommendation.role_fit_pct,
      ),
    },
    {
      label: translations(
        "marketAdvantage",
      ),
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
                  {formatPosition(
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
                  translations("nationalTeamUnavailable")}
              </p>

              <p className="mt-1.5 break-words text-sm font-semibold text-brand">
                {recommendation
                  .final_role ??
                  recommendation
                    .archetype ??
                  translations("roleUnavailable")}
              </p>
            </div>
          </div>

          <dl className="grid gap-2 sm:grid-cols-2 xl:w-[30rem] xl:grid-cols-4">
            <div className="rounded-xl border border-border bg-page px-3 py-2.5">
              <dt className="text-[11px] leading-4 text-muted">
                {scoreLabels[mode]}
              </dt>

              <dd className="mt-1 font-bold text-brand-dark">
                {score === null
                  ? "—"
                  : formatNumber(
                      score,
                      {
                        maximumFractionDigits: 1,
                      },
                    )}
              </dd>
            </div>

            <div className="rounded-xl border border-border bg-page px-3 py-2.5">
              <dt className="text-[11px] leading-4 text-muted">
                {translations(
                  "statistical",
                )}
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
                {translations(
                  "spatial",
                )}
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
                {translations(
                  "roleFit",
                )}
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
              {translations(
                "market",
              )}{" "}
              <strong className="font-semibold text-foreground">
                {formatMarket(
                  recommendation.market_value,
                  recommendation
                    .market_value_currency,
                )}
              </strong>
            </span>

            <span>
              {translations(
                "age",
              )}{" "}
              <strong className="font-semibold text-foreground">
                {typeof recommendation.age !==
                "number"
                  ? translations(
                      "notReported",
                    )
                  : translations(
                      "ageYears",
                      {
                        age:
                          formatNumber(
                            recommendation.age,
                            {
                              maximumFractionDigits: 1,
                            },
                          ),
                      },
                    )}
              </strong>
            </span>

            <span>
              {translations(
                "minutes",
              )}{" "}
              <strong className="font-semibold text-foreground">
                {formatNumber(
                  recommendation.minutes,
                )}
              </strong>
            </span>
          </div>

          <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
            <Link
              href={comparisonHref}
              className="inline-flex min-h-11 flex-1 items-center justify-center rounded-xl bg-brand px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-brand-dark sm:flex-none"
            >
              {translations(
                "compare",
              )}
            </Link>

            <Link
              href={`/players/${recommendation.player_id}`}
              className="inline-flex min-h-11 flex-1 items-center justify-center rounded-xl border border-border px-4 py-2 text-xs font-semibold transition-colors hover:bg-surface-secondary sm:flex-none"
            >
              {translations(
                "profile",
              )}
            </Link>

            <ShortlistAction
              player={shortlistPlayer}
              variant="compact"
            />
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
                  {formatPosition(
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
                    translations("nationalTeamUnavailable")}
                </p>

                <p className="mt-2 break-words font-semibold text-brand">
                  {recommendation
                    .final_role ??
                    recommendation
                      .archetype ??
                    translations("roleUnavailable")}
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

          <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <Link
              href={comparisonHref}
              className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-brand px-4 py-2.5 text-center text-sm font-semibold text-white transition-colors hover:bg-brand-dark sm:w-auto"
            >
              {translations(
                "compareWithTarget",
              )}
            </Link>

            <Link
              href={`/players/${recommendation.player_id}`}
              className="inline-flex min-h-11 w-full items-center justify-center rounded-xl border border-border px-4 py-2.5 text-center text-sm font-semibold transition-colors hover:bg-surface-secondary sm:w-auto"
            >
              {translations(
                "openPlayerProfile",
              )}
            </Link>

            <ShortlistAction
              player={shortlistPlayer}
            />
          </div>
        </div>

        <aside className="border-t border-border bg-surface-secondary p-5 lg:border-t-0 lg:border-l">
          <p className="text-xs font-semibold text-muted">
            {scoreLabels[mode]}
          </p>

          <p className="mt-2 text-3xl font-bold tracking-[-0.04em] text-brand-dark">
            {score === null
              ? "—"
              : formatNumber(
                  score,
                  {
                    maximumFractionDigits: 1,
                  },
                )}
          </p>

          <dl className="mt-6 space-y-4 text-sm">
            <div>
              <dt className="text-muted">
                {translations(
                  "marketValue",
                )}
              </dt>
              <dd className="mt-1 font-semibold">
                {formatMarket(
                  recommendation.market_value,
                  recommendation
                    .market_value_currency,
                )}
              </dd>
            </div>

            <div>
              <dt className="text-muted">
                {translations(
                  "age",
                )}
              </dt>
              <dd className="mt-1 font-semibold">
                {typeof recommendation.age !==
                "number"
                  ? translations(
                      "notReported",
                    )
                  : translations(
                      "ageYears",
                      {
                        age:
                          formatNumber(
                            recommendation.age,
                            {
                              maximumFractionDigits: 1,
                            },
                          ),
                      },
                    )}
              </dd>
            </div>

            <div>
              <dt className="text-muted">
                {translations(
                  "tournamentMinutes",
                )}
              </dt>
              <dd className="mt-1 font-semibold">
                {formatNumber(
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
