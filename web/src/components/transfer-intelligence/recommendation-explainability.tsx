import { useLocale, useTranslations } from "next-intl";

import type { TransferRecommendationResponse } from "@/lib/api/types";
import {
  formatProfileNumber,
  formatProfilePercentage,
} from "@/lib/players/profile-format";
import type { ProfileFormatContext } from "@/lib/players/profile-format";

type RecommendationExplainabilityProps = Readonly<{
  explainability: TransferRecommendationResponse["explainability"];
}>;

type Explainability = TransferRecommendationResponse["explainability"];

type ExplainabilityReason = Explainability["reasons"][number];

type ExplainabilitySignal = Explainability["signals"][number];

type SignalCopy = Readonly<{
  label: string;
  description: string;
}>;

function extractReasonPercentage(text: string): number | null {
  const match = text.match(/\((\d+(?:\.\d+)?)%\)$/);

  if (!match) {
    return null;
  }

  const value = Number(match[1]);

  return Number.isFinite(value) ? value : null;
}

export function RecommendationExplainability({
  explainability,
}: RecommendationExplainabilityProps) {
  const locale = useLocale();

  const translations = useTranslations("RecommendationExplainability");

  const formatContext: ProfileFormatContext = {
    locale,
  };

  const formatScore = (value: number): string =>
    formatProfileNumber(
      value,
      {
        maximumFractionDigits: 2,
      },
      formatContext,
    );

  const formatWeight = (value: number): string =>
    formatProfilePercentage(value * 100, formatContext);

  const signalCopies = translations.raw("signals") as Readonly<
    Record<string, SignalCopy>
  >;

  const bonusLabels = translations.raw("bonusLabels") as Readonly<
    Record<string, string>
  >;

  const evidenceLabels = {
    available: translations("evidence.available"),
    fallback: translations("evidence.fallback"),
    missing: translations("evidence.missing"),
  } as const;

  const formatReasonPercentage = (
    reason: ExplainabilityReason,
  ): string | null => {
    const value = extractReasonPercentage(reason.text);

    if (value === null) {
      return null;
    }

    return formatProfilePercentage(value, formatContext);
  };

  const localizeHeatmapZoneReason = (text: string): string | null => {
    let match = text.match(
      /^replicates the target's (.+) and (.+) occupation$/,
    );

    if (match) {
      return translations("reasons.heatmapZone.sameZones", {
        lateral: match[1]!,
        vertical: match[2]!,
      });
    }

    match = text.match(/^uses the same (.+), but operates more in the (.+)$/);

    if (match) {
      return translations("reasons.heatmapZone.sameLateral", {
        lateral: match[1]!,
        vertical: match[2]!,
      });
    }

    match = text.match(
      /^matches the target's (.+) depth with more (.+) occupation$/,
    );

    if (match) {
      return translations("reasons.heatmapZone.sameDepth", {
        vertical: match[1]!,
        lateral: match[2]!,
      });
    }

    match = text.match(/^operates mainly in the (.+) and (.+)$/);

    if (match) {
      return translations("reasons.heatmapZone.mainZones", {
        lateral: match[1]!,
        vertical: match[2]!,
      });
    }

    return null;
  };

  const localizeReason = (reason: ExplainabilityReason): string => {
    const percentage = formatReasonPercentage(reason);

    switch (reason.key) {
      case "same_final_role":
        return translations("reasons.sameFinalRole");

      case "same_archetype":
        return translations("reasons.sameArchetype");

      case "statistical_similarity":
        if (percentage === null) {
          return reason.text;
        }

        return translations(
          extractReasonPercentage(reason.text)! >= 75
            ? "reasons.statisticalSimilarity.veryStrong"
            : "reasons.statisticalSimilarity.good",
          {
            value: percentage,
          },
        );

      case "role_fit":
        if (percentage === null) {
          return reason.text;
        }

        return translations(
          extractReasonPercentage(reason.text)! >= 85
            ? "reasons.roleFit.elite"
            : "reasons.roleFit.strong",
          {
            value: percentage,
          },
        );

      case "spatial_similarity":
        if (percentage === null) {
          return reason.text;
        }

        return translations("reasons.spatialSimilarity", {
          value: percentage,
        });

      case "heatmap_similarity": {
        const value = extractReasonPercentage(reason.text);

        if (value === null || percentage === null) {
          return reason.text;
        }

        if (value >= 90) {
          return translations("reasons.heatmapSimilarity.elite", {
            value: percentage,
          });
        }

        if (value >= 82) {
          return translations("reasons.heatmapSimilarity.strong", {
            value: percentage,
          });
        }

        return translations("reasons.heatmapSimilarity.useful", {
          value: percentage,
        });
      }

      case "heatmap_overlap":
        if (percentage === null) {
          return reason.text;
        }

        return translations("reasons.heatmapOverlap", {
          value: percentage,
        });

      case "heatmap_structure":
        return translations("reasons.heatmapStructure");

      case "heatmap_zone":
        return localizeHeatmapZoneReason(reason.text) ?? reason.text;

      case "market_advantage":
        return translations(
          reason.text.startsWith("major")
            ? "reasons.marketAdvantage.major"
            : "reasons.marketAdvantage.useful",
        );

      case "development_age_upside":
        return translations(
          reason.text.startsWith("elite")
            ? "reasons.developmentAge.elite"
            : "reasons.developmentAge.strong",
        );

      case "data_reliability":
        return translations("reasons.dataReliability");

      case "balanced_profile":
        return translations("reasons.balancedProfile");

      default:
        return reason.text;
    }
  };

  const localizeSignalNote = (signal: ExplainabilitySignal): string | null => {
    if (!signal.note) {
      return null;
    }

    if (
      signal.key === "effective_heatmap_score_pct" &&
      signal.evidence_status === "fallback"
    ) {
      return translations("notes.heatmapFallback");
    }

    if (
      signal.key === "effective_heatmap_score_pct" &&
      signal.evidence_status === "missing"
    ) {
      return translations("notes.heatmapMissing");
    }

    if (signal.evidence_status === "missing") {
      return translations("notes.sourceMissing");
    }

    return signal.note;
  };

  const { score, signals, bonuses, reasons } = explainability;

  return (
    <section className="mt-6 overflow-hidden rounded-xl border border-brand/15 bg-surface-secondary">
      <div className="p-4">
        <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
          {translations("whyCandidate")}
        </p>

        <ul className="mt-3 grid gap-x-6 gap-y-1.5 sm:grid-cols-2">
          {reasons.map((reason) => (
            <li
              key={`${reason.group}:${reason.key}`}
              className="flex gap-2 text-sm leading-6 text-muted"
            >
              <span
                aria-hidden="true"
                className="mt-[0.65rem] size-1.5 shrink-0 rounded-full bg-brand"
              />

              <span className="break-words">{localizeReason(reason)}</span>
            </li>
          ))}
        </ul>

        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-1 border-t border-border/70 pt-3 text-xs">
          <span className="text-muted">
            {translations("weightedSignals")}{" "}
            <strong className="text-brand-dark">
              {formatScore(score.weighted_signal_total)}
            </strong>
          </span>

          <span className="text-muted">
            {translations("appliedBonuses")}{" "}
            <strong className="text-brand-dark">
              +{formatScore(score.bonus_total)}
            </strong>
          </span>
        </div>
      </div>

      <details className="group border-t border-border/70">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-3 text-sm font-semibold transition-colors hover:bg-surface sm:px-5">
          <span>{translations("viewBreakdown")}</span>

          <span
            aria-hidden="true"
            className="text-lg leading-none text-brand transition-transform group-open:rotate-45"
          >
            +
          </span>
        </summary>

        <div className="border-t border-border/70 bg-surface p-4 sm:p-5">
          <div>
            <p className="text-xs font-semibold tracking-[0.12em] text-muted uppercase">
              {translations("scoreComposition")}
            </p>

            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-lg border border-border bg-page p-3">
                <dt className="text-xs text-muted">
                  {translations("weightedSignals")}
                </dt>
                <dd className="mt-1 font-bold">
                  {formatScore(score.weighted_signal_total)}
                </dd>
              </div>

              <div className="rounded-lg border border-border bg-page p-3">
                <dt className="text-xs text-muted">
                  {translations("bonuses")}
                </dt>
                <dd className="mt-1 font-bold">
                  +{formatScore(score.bonus_total)}
                </dd>
              </div>

              <div className="rounded-lg border border-border bg-page p-3">
                <dt className="text-xs text-muted">
                  {translations("preClipScore")}
                </dt>
                <dd className="mt-1 font-bold">
                  {formatScore(score.pre_clip_score)}
                </dd>
              </div>

              <div className="rounded-lg border border-border bg-page p-3">
                <dt className="text-xs text-muted">
                  {translations("finalScore")}
                </dt>
                <dd className="mt-1 font-bold text-brand-dark">
                  {formatScore(score.final_score)}
                </dd>
              </div>
            </dl>

            {score.was_clipped ? (
              <p className="mt-2 text-xs leading-5 text-muted">
                {translations("clippedDescription")}
              </p>
            ) : null}
          </div>

          <div className="mt-6">
            <p className="text-xs font-semibold tracking-[0.12em] text-muted uppercase">
              {translations("weightedSignals")}
            </p>

            <div className="mt-3 divide-y divide-border rounded-xl border border-border">
              {signals.map((signal) => {
                const signalCopy = signalCopies[signal.key];

                const note = localizeSignalNote(signal);

                return (
                  <div
                    key={signal.key}
                    className="grid gap-3 p-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-semibold">
                          {signalCopy?.label ?? signal.label}
                        </p>

                        {signal.evidence_status !== "available" ? (
                          <span className="rounded-full border border-border px-2 py-0.5 text-[0.68rem] font-semibold text-muted">
                            {evidenceLabels[signal.evidence_status]}
                          </span>
                        ) : null}
                      </div>

                      <p className="mt-1 text-xs leading-5 text-muted">
                        {signalCopy?.description ?? signal.description}
                      </p>

                      {note ? (
                        <p className="mt-2 text-xs leading-5 text-muted">
                          {note}
                        </p>
                      ) : null}
                    </div>

                    <dl className="grid grid-cols-3 gap-3 text-right text-xs sm:min-w-64">
                      <div>
                        <dt className="text-muted">{translations("input")}</dt>
                        <dd className="mt-1 font-semibold">
                          {formatProfilePercentage(
                            signal.input_score,
                            formatContext,
                          )}
                        </dd>
                      </div>

                      <div>
                        <dt className="text-muted">{translations("weight")}</dt>
                        <dd className="mt-1 font-semibold">
                          {formatWeight(signal.weight)}
                        </dd>
                      </div>

                      <div>
                        <dt className="text-muted">
                          {translations("contribution")}
                        </dt>
                        <dd className="mt-1 font-bold text-brand-dark">
                          +{formatScore(signal.weighted_contribution)}
                        </dd>
                      </div>
                    </dl>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-6">
            <p className="text-xs font-semibold tracking-[0.12em] text-muted uppercase">
              {translations("modeBonuses")}
            </p>

            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {bonuses.map((bonus) => (
                <div
                  key={bonus.key}
                  className="flex items-center justify-between gap-3 rounded-lg border border-border bg-page p-3 text-sm"
                >
                  <div>
                    <p className="font-semibold">
                      {bonusLabels[bonus.key] ?? bonus.label}
                    </p>

                    <p className="mt-1 text-xs text-muted">
                      {bonus.applied
                        ? translations("applied")
                        : translations("notApplied")}
                    </p>
                  </div>

                  <span className="font-bold text-brand-dark">
                    {bonus.applied
                      ? `+${formatScore(bonus.applied_points)}`
                      : "—"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <p className="mt-6 border-t border-border pt-4 text-xs leading-5 text-muted">
            {translations("disclaimer")}
          </p>
        </div>
      </details>
    </section>
  );
}
