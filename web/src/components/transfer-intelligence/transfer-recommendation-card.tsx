import Link from "next/link";

import type {
  TransferModeName,
  TransferRecommendationResponse,
} from "@/lib/api/types";
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

type TransferRecommendationCardProps =
  Readonly<{
    targetPlayerId: number;
    mode: TransferModeName;
    recommendation:
      TransferRecommendationResponse;
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
  recommendation,
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
          .effective_heatmap_score_pct,
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

  return (
    <article className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
      <div className="grid lg:grid-cols-[minmax(0,1fr)_13rem]">
        <div className="p-5 sm:p-6">
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

          <div className="mt-5">
            <h3 className="text-2xl font-bold tracking-[-0.035em]">
              {recommendation.player_name}
            </h3>

            <p className="mt-1 text-sm font-medium text-muted">
              {recommendation
                .national_team_name ??
                recommendation.country_name ??
                "National team unavailable"}
            </p>

            <p className="mt-3 font-semibold text-brand">
              {recommendation.final_role ??
                recommendation.archetype ??
                "Role unavailable"}
            </p>
          </div>

          <dl className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
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

          <div className="mt-6 rounded-xl border border-brand/15 bg-surface-secondary p-4">
            <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
              Why recommended
            </p>

            <p className="mt-2 text-sm leading-6 text-muted">
              {
                recommendation
                  .why_recommended
              }
            </p>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href={`/compare/${targetPlayerId}/${recommendation.player_id}`}
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
