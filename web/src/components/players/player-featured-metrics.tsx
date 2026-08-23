import type { PlayerProfileResponse } from "@/lib/api/types";
import { formatProfileNumber } from "@/lib/players/profile-format";

type PlayerIntelligence =
  NonNullable<PlayerProfileResponse["intelligence"]>;

type PerformanceGroup =
  PlayerIntelligence["groups"][number];

type PerformanceMetric =
  PerformanceGroup["metrics"][number];

type PlayerFeaturedMetricsProps = Readonly<{
  intelligence: PlayerProfileResponse["intelligence"];
}>;

const FEATURED_METRIC_LIMIT = 6;

function selectFeaturedMetrics(
  groups: readonly PerformanceGroup[],
): PerformanceMetric[] {
  const selected: PerformanceMetric[] = [];
  const selectedKeys = new Set<string>();

  for (const group of groups) {
    const metric = group.metrics[0];

    if (!metric || selectedKeys.has(metric.key)) {
      continue;
    }

    selected.push(metric);
    selectedKeys.add(metric.key);

    if (selected.length === FEATURED_METRIC_LIMIT) {
      return selected;
    }
  }

  for (const group of groups) {
    for (const metric of group.metrics.slice(1)) {
      if (selectedKeys.has(metric.key)) {
        continue;
      }

      selected.push(metric);
      selectedKeys.add(metric.key);

      if (selected.length === FEATURED_METRIC_LIMIT) {
        return selected;
      }
    }
  }

  return selected;
}

function formatMetricValue(
  metric: PerformanceMetric,
): string {
  const value = formatProfileNumber(
    metric.value,
    {
      maximumFractionDigits: 2,
    },
  );

  if (metric.unit === "percent") {
    return `${value}%`;
  }

  return value;
}

function formatMetricUnit(
  metric: PerformanceMetric,
): string {
  switch (metric.unit) {
    case "per90":
      return "Per 90";

    case "percent":
      return "Percentage";

    case "raw":
      return "Tournament total";

    default:
      return metric.unit;
  }
}

function clampPercentile(
  percentile: number,
): number {
  return Math.min(
    100,
    Math.max(0, percentile),
  );
}

function FeaturedMetricCard({
  metric,
}: Readonly<{
  metric: PerformanceMetric;
}>) {
  const percentile =
    metric.performance_percentile;

  return (
    <article className="rounded-2xl border border-border bg-page p-4 sm:p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="break-words text-sm font-bold tracking-[-0.015em]">
            {metric.short_label}
          </h3>

          <p className="mt-1 text-xs text-muted">
            {formatMetricUnit(metric)}
          </p>
        </div>

        <p className="shrink-0 text-2xl font-bold tracking-[-0.04em] text-brand-dark">
          {formatMetricValue(metric)}
        </p>
      </div>

      {percentile !== null &&
      percentile !== undefined ? (
        <div className="mt-5">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-medium text-muted">
              Same-position percentile
            </p>

            <p className="text-sm font-bold">
              {formatProfileNumber(
                percentile,
                {
                  maximumFractionDigits: 1,
                },
              )}
            </p>
          </div>

          <div
            role="progressbar"
            aria-label={`${metric.short_label} performance percentile`}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={percentile}
            className="mt-2 h-1.5 overflow-hidden rounded-full bg-border/70"
          >
            <div
              className="h-full rounded-full bg-brand"
              style={{
                width: `${clampPercentile(
                  percentile,
                )}%`,
              }}
            />
          </div>

          <p className="mt-2 text-[0.7rem] leading-5 text-muted">
            Compared with{" "}
            <span className="font-semibold text-foreground">
              {formatProfileNumber(
                metric.peer_count,
              )}
            </span>{" "}
            eligible peers.
          </p>
        </div>
      ) : (
        <p className="mt-5 text-xs leading-5 text-muted">
          Same-position percentile unavailable.
        </p>
      )}
    </article>
  );
}

export function PlayerFeaturedMetrics({
  intelligence,
}: PlayerFeaturedMetricsProps) {
  if (!intelligence) {
    return null;
  }

  const metrics =
    selectFeaturedMetrics(
      intelligence.groups,
    );

  if (metrics.length === 0) {
    return null;
  }

  return (
    <section
      aria-labelledby="featured-performance-title"
      className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7"
    >
      <div className="max-w-3xl">
        <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
          Featured performance
        </p>

        <h2
          id="featured-performance-title"
          className="mt-3 text-2xl font-bold tracking-[-0.03em]"
        >
          Position-relevant metrics
        </h2>

        <p className="mt-3 text-sm leading-6 text-muted">
          A quick read of the player&apos;s tournament output for this
          position. Full metric detail remains available below.
        </p>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {metrics.map((metric) => (
          <FeaturedMetricCard
            key={metric.key}
            metric={metric}
          />
        ))}
      </div>
    </section>
  );
}
