import type { PlayerProfileResponse } from "@/lib/api/types";
import { formatProfileNumber } from "@/lib/players/profile-format";

type PlayerIntelligence = NonNullable<PlayerProfileResponse["intelligence"]>;

type PlayerInsight = PlayerIntelligence["strengths"][number];

type InsightTone = "strength" | "watch_out";

type InsightCardProps = Readonly<{
  insight: PlayerInsight;
  tone: InsightTone;
}>;

type PlayerScoutingInsightsProps = Readonly<{
  intelligence: PlayerProfileResponse["intelligence"];
}>;

function clampPercentile(percentile: number): number {
  return Math.min(100, Math.max(0, percentile));
}

function InsightCard({ insight, tone }: InsightCardProps) {
  const isStrength = tone === "strength";

  return (
    <article
      className={[
        "rounded-2xl border p-4 sm:p-5",
        isStrength
          ? "border-brand/20 bg-surface"
          : "border-amber-200 bg-amber-50/50",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p
            className={[
              "text-[0.7rem] font-semibold tracking-[0.12em] uppercase",
              isStrength ? "text-brand" : "text-amber-700",
            ].join(" ")}
          >
            {insight.group_label}
          </p>

          <h3 className="mt-2 break-words text-lg font-bold tracking-[-0.02em]">
            {insight.metric_short_label}
          </h3>
        </div>

        <div className="shrink-0 text-right">
          <p className="text-2xl font-bold tracking-[-0.04em]">
            {formatProfileNumber(insight.percentile, {
              maximumFractionDigits: 1,
            })}
          </p>

          <p className="text-[0.65rem] font-semibold tracking-[0.08em] text-muted uppercase">
            percentile
          </p>
        </div>
      </div>

      <div
        role="progressbar"
        aria-label={`${insight.metric_short_label} performance percentile`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={insight.percentile}
        className="mt-4 h-2 overflow-hidden rounded-full bg-border/70"
      >
        <div
          className={[
            "h-full rounded-full",
            isStrength ? "bg-brand" : "bg-amber-500",
          ].join(" ")}
          style={{
            width: `${clampPercentile(insight.percentile)}%`,
          }}
        />
      </div>

      <p className="mt-3 text-xs leading-5 text-muted">{insight.evidence}</p>
    </article>
  );
}

function EmptyInsightState({
  children,
}: Readonly<{
  children: string;
}>) {
  return (
    <div className="rounded-2xl border border-dashed border-border bg-page p-5 text-sm leading-6 text-muted">
      {children}
    </div>
  );
}

export function PlayerScoutingInsights({
  intelligence,
}: PlayerScoutingInsightsProps) {
  if (!intelligence) {
    return (
      <section
        aria-labelledby="scouting-insights-title"
        className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7"
      >
        <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
          Scouting intelligence
        </p>

        <h2
          id="scouting-insights-title"
          className="mt-3 text-2xl font-bold tracking-[-0.03em]"
        >
          Scouting insights
        </h2>

        <div className="mt-5">
          <EmptyInsightState>
            Position-aware scouting insights were not reported for this player.
          </EmptyInsightState>
        </div>
      </section>
    );
  }

  const strengths = intelligence.strengths;

  const watchOuts = intelligence.watch_outs;

  return (
    <section
      aria-labelledby="scouting-insights-title"
      className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7"
    >
      <div className="max-w-3xl">
        <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
          Scouting intelligence
        </p>

        <h2
          id="scouting-insights-title"
          className="mt-3 text-2xl font-bold tracking-[-0.03em]"
        >
          Scouting insights
        </h2>

        <p className="mt-3 text-sm leading-6 text-muted">
          Position-aware performance signals derived from same-position
          percentile comparisons across the tournament sample.
        </p>
      </div>

      <div className="mt-7 grid gap-7 xl:grid-cols-[minmax(0,2fr)_minmax(18rem,0.85fr)]">
        <div className="min-w-0">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                Strengths
              </p>

              <h3 className="mt-2 text-xl font-bold tracking-[-0.025em]">
                Standout signals
              </h3>
            </div>

            <span className="shrink-0 rounded-full bg-surface-secondary px-3 py-1 text-xs font-semibold text-muted">
              {strengths.length} surfaced
            </span>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {strengths.length > 0 ? (
              strengths.map((insight) => (
                <InsightCard
                  key={insight.metric_key}
                  insight={insight}
                  tone="strength"
                />
              ))
            ) : (
              <div className="md:col-span-2">
                <EmptyInsightState>
                  No standout strengths were surfaced by the current
                  position-aware profile.
                </EmptyInsightState>
              </div>
            )}
          </div>
        </div>

        <div className="min-w-0 xl:border-l xl:border-border xl:pl-7">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold tracking-[0.12em] text-amber-700 uppercase">
                Watch-outs
              </p>

              <h3 className="mt-2 text-xl font-bold tracking-[-0.025em]">
                Areas to review
              </h3>
            </div>

            <span className="shrink-0 rounded-full bg-surface-secondary px-3 py-1 text-xs font-semibold text-muted">
              {watchOuts.length} surfaced
            </span>
          </div>

          <div className="mt-4 space-y-3">
            {watchOuts.length > 0 ? (
              watchOuts.map((insight) => (
                <InsightCard
                  key={insight.metric_key}
                  insight={insight}
                  tone="watch_out"
                />
              ))
            ) : (
              <EmptyInsightState>
                No watch-out signals were surfaced by the current position-aware
                profile.
              </EmptyInsightState>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
