import {
  useLocale,
  useTranslations,
} from "next-intl";

import type {
  PlayerProfileResponse,
} from "@/lib/api/types";
import {
  formatProfileNumber,
} from "@/lib/players/profile-format";
import type {
  ProfileFormatContext,
} from "@/lib/players/profile-format";

type PlayerIntelligence = NonNullable<PlayerProfileResponse["intelligence"]>;

type PerformanceGroup = PlayerIntelligence["groups"][number];

type PerformanceMetric = PerformanceGroup["metrics"][number];

type PlayerPerformanceProfileProps = Readonly<{
  intelligence: PlayerProfileResponse["intelligence"];
}>;

function getGroupLabel(
  key: string,
  labels: Readonly<
    Record<string, string>
  >,
): string {
  return (
    labels[key] ??
    key
      .replaceAll("_", " ")
      .replace(/\b\w/g, (character) => character.toUpperCase())
  );
}

function clampPercentile(percentile: number): number {
  return Math.min(100, Math.max(0, percentile));
}

function formatMetricValue(
  metric: PerformanceMetric,
  context: ProfileFormatContext,
): string {
  const value = formatProfileNumber(
    metric.value,
    {
      maximumFractionDigits: 2,
    },
    context,
  );

  if (metric.unit === "percent") {
    return `${value}%`;
  }

  return value;
}

function getMetricDescription(
  metric: PerformanceMetric,
): string | null {
  const description =
    metric.unit === "per90"
      ? metric.label.replace(/\s+per\s+90$/i, "")
      : metric.label;

  const comparableShortLabel = metric.short_label
    .replace(/\s*\/\s*90$/i, "")
    .trim();

  return description.localeCompare(
    comparableShortLabel,
    undefined,
    {
      sensitivity: "base",
    },
  ) === 0
    ? null
    : description;
}

function balancePerformanceGroups(
  groups: readonly PerformanceGroup[],
): readonly [PerformanceGroup[], PerformanceGroup[]] {
  const columns: [
    PerformanceGroup[],
    PerformanceGroup[],
  ] = [[], []];

  const columnWeights: [number, number] = [0, 0];

  for (const group of groups) {
    const targetColumn: 0 | 1 =
      columnWeights[0] <= columnWeights[1]
        ? 0
        : 1;

    columns[targetColumn].push(group);

    columnWeights[targetColumn] +=
      group.metrics.length + 1;
  }

  return columns;
}

function MetricRow({
  metric,
}: Readonly<{
  metric: PerformanceMetric;
}>) {
  const locale =
    useLocale();

  const translations =
    useTranslations(
      "PlayerPerformanceProfile",
    );

  const commonTranslations =
    useTranslations(
      "Common",
    );

  const formatContext = {
    locale,
    missingValue:
      commonTranslations(
        "notReported",
      ),
  };

  const percentile =
    metric.performance_percentile;

  const hasPercentile =
    percentile !== null &&
    percentile !== undefined;

  const description = getMetricDescription(metric);

  return (
    <article className="py-4 first:pt-0 last:pb-0">
      <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_6rem_minmax(10rem,0.9fr)] md:items-center md:gap-4">
        <div className="min-w-0">
          <p className="break-words text-sm font-bold tracking-[-0.015em]">
            {metric.short_label}
          </p>

          {description ? (
            <p className="mt-1 break-words text-xs leading-5 text-muted">
              {description}
            </p>
          ) : null}
        </div>

        <div className="flex items-end justify-between gap-4 md:block md:text-right">
          <p className="text-xs font-semibold text-muted md:hidden">
            {translations(
              "value",
            )}
          </p>

          <div>
            <p className="text-lg font-bold tracking-[-0.03em]">
              {formatMetricValue(
                metric,
                formatContext,
              )}
            </p>

            {metric.unit === "raw" ? (
              <p className="mt-1 text-[0.65rem] font-semibold tracking-[0.08em] text-muted uppercase">
                {translations(
                  "rawValue",
                )}
              </p>
            ) : null}
          </div>
        </div>

        <div className="min-w-0">
          {hasPercentile ? (
            <>
              <div className="flex items-center justify-between gap-4">
                <p className="text-xs font-semibold text-muted md:hidden">
                  {translations(
                    "percentile",
                  )}
                </p>

                <p className="ml-auto shrink-0 text-sm font-bold text-brand-dark">
                  {formatProfileNumber(
                    percentile,
                    {
                      maximumFractionDigits: 1,
                    },
                    formatContext,
                  )}
                </p>
              </div>

              <div
                role="progressbar"
                aria-label={translations(
                  "percentileAriaLabel",
                  {
                    metric:
                      metric.short_label,
                  },
                )}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={percentile}
                className="mt-2 h-2 overflow-hidden rounded-full bg-border/70"
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

              <p className="mt-1.5 text-right text-[0.7rem] leading-5 text-muted">
                {translations(
                  "peerSample",
                  {
                    count:
                      formatProfileNumber(
                        metric.peer_count,
                        {},
                        formatContext,
                      ),
                  },
                )}
              </p>
            </>
          ) : (
            <div className="rounded-xl border border-dashed border-border bg-page px-3 py-3">
              <div className="flex items-center justify-between gap-4">
                <p className="text-xs font-semibold text-muted">
                  {translations(
                    "percentileUnavailable",
                  )}
                </p>

                <p className="shrink-0 text-[0.7rem] font-semibold text-muted">
                  {translations(
                    "peerSampleCompact",
                    {
                      count:
                        formatProfileNumber(
                          metric.peer_count,
                          {},
                          formatContext,
                        ),
                    },
                  )}
                </p>
              </div>

              <p className="mt-1 text-xs leading-5 text-muted">
                {translations(
                  "reportedValueRetained",
                )}
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
  const translations =
    useTranslations(
      "PlayerPerformanceProfile",
    );

  const groupLabels = {
    creation:
      translations(
        "groups.creation",
      ),
    progression:
      translations(
        "groups.progression",
      ),
    possession:
      translations(
        "groups.possession",
      ),
    defending:
      translations(
        "groups.defending",
      ),
    scoring:
      translations(
        "groups.scoring",
      ),
    physical:
      translations(
        "groups.physical",
      ),
    goalkeeping:
      translations(
        "groups.goalkeeping",
      ),
  };

  return (
    <section
      aria-labelledby={`performance-group-${group.key}`}
      className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm"
    >
      <header className="border-b border-border bg-surface-secondary/55 px-5 py-3.5 sm:px-6">
        <h3
          id={`performance-group-${group.key}`}
          className="min-w-0 break-words text-lg font-bold tracking-[-0.025em]"
        >
          {getGroupLabel(
            group.key,
            groupLabels,
          )}
        </h3>

      </header>

      <div className="divide-y divide-border px-5 py-4 sm:px-6">
        {group.metrics.map((metric) => (
          <MetricRow
            key={metric.key}
            metric={metric}
          />
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
  const translations =
    useTranslations(
      "PlayerPerformanceProfile",
    );

  return (
    <section
      aria-labelledby="performance-profile-title"
      className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7"
    >
      <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
        {translations(
          "eyebrow",
        )}
      </p>

      <h2
        id="performance-profile-title"
        className="mt-3 text-2xl font-bold tracking-[-0.03em]"
      >
        {translations(
          "title",
        )}
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
  const translations =
    useTranslations(
      "PlayerPerformanceProfile",
    );

  if (!intelligence) {
    return (
      <EmptyPerformanceState>
        {translations(
          "unavailable",
        )}
      </EmptyPerformanceState>
    );
  }

  if (intelligence.groups.length === 0) {
    return (
      <EmptyPerformanceState>
        {translations(
          "empty",
        )}
      </EmptyPerformanceState>
    );
  }

  const [leftGroups, rightGroups] =
    balancePerformanceGroups(
      intelligence.groups,
    );

  return (
    <section
      aria-labelledby="performance-profile-title"
      className="space-y-5"
    >
      <div className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
              {translations(
                "eyebrow",
              )}
            </p>

            <h2
              id="performance-profile-title"
              className="mt-3 text-2xl font-bold tracking-[-0.03em]"
            >
              {translations(
                "title",
              )}
            </h2>

            <p className="mt-3 text-sm leading-6 text-muted">
              {translations(
                "description",
              )}
            </p>
          </div>

          <aside
            aria-labelledby="performance-profile-guide-title"
            className="w-full max-w-md rounded-2xl border border-brand/15 bg-surface-secondary px-4 py-3"
          >
            <p
              id="performance-profile-guide-title"
              className="text-xs font-semibold text-brand-dark"
            >
              {translations(
                "guideTitle",
              )}
            </p>

            <div className="mt-3 grid grid-cols-[minmax(0,1fr)_3.5rem_minmax(6.5rem,0.9fr)] items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2.5">
              <div className="min-w-0">
                <p className="text-xs font-bold">
                  {translations(
                    "exampleMetric",
                  )}
                </p>

                <p className="mt-0.5 text-[0.65rem] text-muted">
                  {translations(
                    "illustrative",
                  )}
                </p>
              </div>

              <p className="text-right text-sm font-bold">
                X.XX
              </p>

              <div className="min-w-0">
                <p className="text-right text-xs font-bold text-brand-dark">
                  75.0
                </p>

                <div
                  aria-hidden="true"
                  className="mt-1 h-1.5 overflow-hidden rounded-full bg-border/70"
                >
                  <div className="h-full w-3/4 rounded-full bg-brand" />
                </div>

                <p className="mt-1 text-right text-[0.6rem] text-muted">
                  {translations(
                    "peerSamplePlaceholder",
                  )}
                </p>
              </div>
            </div>

            <p className="mt-2 text-[0.7rem] leading-5 text-muted">
              {translations(
                "guideDescription",
              )}
            </p>
          </aside>
        </div>
      </div>

      <div
        data-testid="performance-group-layout"
        className="grid items-start gap-5 xl:grid-cols-2"
      >
        <div
          data-testid="performance-group-column"
          className="space-y-5"
        >
          {leftGroups.map((group) => (
            <MetricGroup
              key={group.key}
              group={group}
            />
          ))}
        </div>

        <div
          data-testid="performance-group-column"
          className="space-y-5"
        >
          {rightGroups.map((group) => (
            <MetricGroup
              key={group.key}
              group={group}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
