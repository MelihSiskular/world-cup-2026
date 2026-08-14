import type { PlayerProfileResponse } from "@/lib/api/types";
import { formatProfileNumber } from "@/lib/players/profile-format";

type PlayerIntelligence = NonNullable<PlayerProfileResponse["intelligence"]>;

type PerformanceGroup = PlayerIntelligence["groups"][number];

type PerformanceMetric = PerformanceGroup["metrics"][number];

type PlayerPerformanceProfileProps = Readonly<{
  intelligence: PlayerProfileResponse["intelligence"];
}>;

const GROUP_LABELS: Readonly<Record<string, string>> = {
  creation: "Chance creation",
  progression: "Ball progression",
  possession: "Possession",
  defending: "Defensive contribution",
  scoring: "Scoring threat",
  physical: "Physical output",
  goalkeeping: "Goalkeeping",
};

function getGroupLabel(key: string): string {
  return (
    GROUP_LABELS[key] ??
    key
      .replaceAll("_", " ")
      .replace(/\b\w/g, (character) => character.toUpperCase())
  );
}

function clampPercentile(percentile: number): number {
  return Math.min(100, Math.max(0, percentile));
}

function formatMetricValue(metric: PerformanceMetric): string {
  const value = formatProfileNumber(metric.value, {
    maximumFractionDigits: 2,
  });

  if (metric.unit === "percent") {
    return `${value}%`;
  }

  return value;
}

function formatMetricUnit(unit: string): string {
  switch (unit) {
    case "per90":
      return "Per 90";

    case "percent":
      return "Percentage";

    case "raw":
      return "Raw value";

    default:
      return unit;
  }
}

function MetricRow({
  metric,
}: Readonly<{
  metric: PerformanceMetric;
}>) {
  const percentile = metric.performance_percentile;

  const hasPercentile = percentile !== null && percentile !== undefined;

  return (
    <article className="py-5 first:pt-0 last:pb-0">
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_7.5rem_minmax(13rem,0.9fr)] lg:items-center">
        <div className="min-w-0">
          <p className="break-words text-base font-bold tracking-[-0.015em]">
            {metric.short_label}
          </p>

          <p className="mt-1 break-words text-xs leading-5 text-muted">
            {metric.label}
          </p>
        </div>

        <div className="flex items-end justify-between gap-4 lg:block lg:text-right">
          <p className="text-xs font-semibold tracking-[0.08em] text-muted uppercase lg:hidden">
            Value
          </p>

          <div>
            <p className="text-xl font-bold tracking-[-0.03em]">
              {formatMetricValue(metric)}
            </p>

            <p className="mt-1 text-[0.65rem] font-semibold tracking-[0.08em] text-muted uppercase">
              {formatMetricUnit(metric.unit)}
            </p>
          </div>
        </div>

        <div className="min-w-0">
          {hasPercentile ? (
            <>
              <div className="flex items-center justify-between gap-4">
                <p className="text-xs font-semibold text-muted">
                  Performance percentile
                </p>

                <p className="shrink-0 text-sm font-bold text-brand-dark">
                  {formatProfileNumber(percentile, {
                    maximumFractionDigits: 1,
                  })}
                </p>
              </div>

              <div
                role="progressbar"
                aria-label={`${metric.short_label} performance percentile`}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={percentile}
                className="mt-2 h-2 overflow-hidden rounded-full bg-border/70"
              >
                <div
                  className="h-full rounded-full bg-brand"
                  style={{
                    width: `${clampPercentile(percentile)}%`,
                  }}
                />
              </div>

              <p className="mt-2 text-[0.7rem] leading-5 text-muted">
                Compared with{" "}
                <span className="font-semibold text-foreground">
                  {formatProfileNumber(metric.peer_count)}
                </span>{" "}
                eligible same-position players.
              </p>
            </>
          ) : (
            <div className="rounded-xl border border-dashed border-border bg-page px-3 py-3">
              <div className="flex items-center justify-between gap-4">
                <p className="text-xs font-semibold text-muted">
                  Percentile unavailable
                </p>

                <p className="shrink-0 text-[0.7rem] font-semibold text-muted">
                  n=
                  {formatProfileNumber(metric.peer_count)}
                </p>
              </div>

              <p className="mt-1 text-xs leading-5 text-muted">
                The reported value remains available, but eligible comparison
                evidence is insufficient.
              </p>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

function MetricGroup({
  group,
}: Readonly<{
  group: PerformanceGroup;
}>) {
  return (
    <section
      aria-labelledby={`performance-group-${group.key}`}
      className="overflow-hidden rounded-3xl border border-border bg-surface shadow-sm"
    >
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-border bg-surface-secondary/55 px-5 py-5 sm:px-6">
        <div className="min-w-0">
          <p className="text-[0.7rem] font-semibold tracking-[0.14em] text-brand uppercase">
            Metric group
          </p>

          <h3
            id={`performance-group-${group.key}`}
            className="mt-2 break-words text-xl font-bold tracking-[-0.025em]"
          >
            {getGroupLabel(group.key)}
          </h3>
        </div>

        <span className="shrink-0 rounded-full border border-border bg-surface px-3 py-1 text-xs font-semibold text-muted">
          {group.metrics.length}{" "}
          {group.metrics.length === 1 ? "metric" : "metrics"}
        </span>
      </header>

      <div className="divide-y divide-border px-5 py-5 sm:px-6">
        {group.metrics.map((metric) => (
          <MetricRow key={metric.key} metric={metric} />
        ))}
      </div>
    </section>
  );
}

function EmptyPerformanceState({
  children,
}: Readonly<{
  children: string;
}>) {
  return (
    <section
      aria-labelledby="performance-profile-title"
      className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7"
    >
      <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
        Performance intelligence
      </p>

      <h2
        id="performance-profile-title"
        className="mt-3 text-2xl font-bold tracking-[-0.03em]"
      >
        Performance profile
      </h2>

      <p className="mt-5 rounded-2xl border border-dashed border-border bg-page p-5 text-sm leading-6 text-muted">
        {children}
      </p>
    </section>
  );
}

export function PlayerPerformanceProfile({
  intelligence,
}: PlayerPerformanceProfileProps) {
  if (!intelligence) {
    return (
      <EmptyPerformanceState>
        Position-aware performance metrics were not reported for this player.
      </EmptyPerformanceState>
    );
  }

  if (intelligence.groups.length === 0) {
    return (
      <EmptyPerformanceState>
        No position-aware performance metrics were available for this player.
      </EmptyPerformanceState>
    );
  }

  return (
    <section aria-labelledby="performance-profile-title" className="space-y-5">
      <div className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
              Performance intelligence
            </p>

            <h2
              id="performance-profile-title"
              className="mt-3 text-2xl font-bold tracking-[-0.03em]"
            >
              Performance profile
            </h2>

            <p className="mt-3 text-sm leading-6 text-muted">
              Position-specific tournament metrics with raw or per-90 output and
              same-position percentile context.
            </p>
          </div>

          <div className="max-w-md rounded-2xl border border-brand/15 bg-surface-secondary px-4 py-3">
            <p className="text-xs font-semibold text-brand-dark">
              How to read the profile
            </p>

            <p className="mt-1 text-xs leading-5 text-muted">
              Higher performance percentile is always more favorable. Raw and
              per-90 values remain visible even when percentile evidence is
              unavailable.
            </p>
          </div>
        </div>
      </div>

      <div className="grid items-start gap-5 xl:grid-cols-2">
        {intelligence.groups.map((group) => (
          <MetricGroup key={group.key} group={group} />
        ))}
      </div>
    </section>
  );
}
