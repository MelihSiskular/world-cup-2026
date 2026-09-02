"use client";

import { useQuery } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { ApiErrorReference } from "@/components/feedback/api-error-reference";
import { MultiPlayerComparisonEvidence } from "@/components/transfer-intelligence/multi-player-comparison-evidence";
import { MultiPlayerRoleMetrics } from "@/components/transfer-intelligence/multi-player-role-metrics";
import { fetchMultiPlayerComparison } from "@/lib/api/browser-transfer-intelligence";
import type {
  MultiPlayerComparisonCandidateResponse,
  MultiPlayerComparisonPlayerResponse,
} from "@/lib/api/types";
import {
  formatMarketValue,
  formatPlayerPosition,
  formatProfileNumber,
  formatProfilePercentage,
} from "@/lib/players/profile-format";
import type { MultiComparisonIdentifiers } from "@/lib/transfer-intelligence/multi-comparison-selection";

type MultiPlayerComparisonProps = Readonly<{
  identifiers: MultiComparisonIdentifiers;
}>;

type ComparisonMatrixRow = Readonly<{
  key: string;
  label: string;
  description: string;
  targetValue: string;
  candidateValues: readonly string[];
}>;

type ComparisonMatrixRowCopy = Readonly<{
  label: string;
  description: string;
}>;

type ComparisonMatrixCopy = Readonly<{
  unavailable: string;
  reference: string;
  yearsSuffix: string;
  positionLabels: Readonly<Record<string, string>>;
  rows: Readonly<{
    position: ComparisonMatrixRowCopy;
    role: ComparisonMatrixRowCopy;
    age: ComparisonMatrixRowCopy;
    marketValue: ComparisonMatrixRowCopy;
    minutes: ComparisonMatrixRowCopy;
    quality: ComparisonMatrixRowCopy;
    reliability: ComparisonMatrixRowCopy;
    statisticalSimilarity: ComparisonMatrixRowCopy;
    spatialSimilarity: ComparisonMatrixRowCopy;
    heatmapSimilarity: ComparisonMatrixRowCopy;
    roleFit: ComparisonMatrixRowCopy;
    marketAdvantage: ComparisonMatrixRowCopy;
  }>;
}>;

function formatOptionalAge(
  value: number | null | undefined,
  locale: string,
  copy: ComparisonMatrixCopy,
): string {
  if (value === null || value === undefined) {
    return copy.unavailable;
  }

  return `${formatProfileNumber(
    value,
    {
      maximumFractionDigits: 0,
    },
    {
      locale,
      missingValue: copy.unavailable,
    },
  )} ${copy.yearsSuffix}`;
}

function formatOptionalNumber(
  value: number | null | undefined,
  locale: string,
  unavailable: string,
): string {
  return formatProfileNumber(
    value,
    {},
    {
      locale,
      missingValue: unavailable,
    },
  );
}

function formatOptionalScore(
  value: number | null | undefined,
  locale: string,
  unavailable: string,
): string {
  if (value === null || value === undefined) {
    return unavailable;
  }

  return `${formatProfileNumber(
    value,
    {
      maximumFractionDigits: 1,
    },
    {
      locale,
      missingValue: unavailable,
    },
  )} / 100`;
}

function formatOptionalPercentage(
  value: number | null | undefined,
  locale: string,
  unavailable: string,
): string {
  return formatProfilePercentage(value, {
    locale,
    missingValue: unavailable,
  });
}

function formatOptionalMarketValue(
  player: MultiPlayerComparisonPlayerResponse,
  locale: string,
  unavailable: string,
): string {
  return formatMarketValue(
    player.market_value,
    player.market_value_currency ?? null,
    {
      locale,
      missingValue: unavailable,
    },
  );
}

function formatRole(
  player: MultiPlayerComparisonPlayerResponse,
  unavailable: string,
): string {
  return (
    player.final_role ?? player.archetype ?? player.spatial_role ?? unavailable
  );
}

function formatPosition(
  player: MultiPlayerComparisonPlayerResponse,
  copy: ComparisonMatrixCopy,
): string {
  return formatPlayerPosition(player.position, {
    labels: copy.positionLabels,
    unavailable: copy.unavailable,
  });
}

function buildMatrixRows(
  target: MultiPlayerComparisonPlayerResponse,
  candidates: readonly MultiPlayerComparisonCandidateResponse[],
  locale: string,
  copy: ComparisonMatrixCopy,
): readonly ComparisonMatrixRow[] {
  return [
    {
      key: "position",
      ...copy.rows.position,
      targetValue: formatPosition(target, copy),
      candidateValues: candidates.map(({ player }) =>
        formatPosition(player, copy),
      ),
    },
    {
      key: "role",
      ...copy.rows.role,
      targetValue: formatRole(target, copy.unavailable),
      candidateValues: candidates.map(({ player }) =>
        formatRole(player, copy.unavailable),
      ),
    },
    {
      key: "age",
      ...copy.rows.age,
      targetValue: formatOptionalAge(target.age, locale, copy),
      candidateValues: candidates.map(({ player }) =>
        formatOptionalAge(player.age, locale, copy),
      ),
    },
    {
      key: "market-value",
      ...copy.rows.marketValue,
      targetValue: formatOptionalMarketValue(target, locale, copy.unavailable),
      candidateValues: candidates.map(({ player }) =>
        formatOptionalMarketValue(player, locale, copy.unavailable),
      ),
    },
    {
      key: "minutes",
      ...copy.rows.minutes,
      targetValue: formatOptionalNumber(
        target.minutes,
        locale,
        copy.unavailable,
      ),
      candidateValues: candidates.map(({ player }) =>
        formatOptionalNumber(player.minutes, locale, copy.unavailable),
      ),
    },
    {
      key: "quality",
      ...copy.rows.quality,
      targetValue: formatOptionalScore(
        target.player_quality_score,
        locale,
        copy.unavailable,
      ),
      candidateValues: candidates.map(({ player }) =>
        formatOptionalScore(
          player.player_quality_score,
          locale,
          copy.unavailable,
        ),
      ),
    },
    {
      key: "reliability",
      ...copy.rows.reliability,
      targetValue: formatOptionalPercentage(
        target.data_reliability_score,
        locale,
        copy.unavailable,
      ),
      candidateValues: candidates.map(({ player }) =>
        formatOptionalPercentage(
          player.data_reliability_score,
          locale,
          copy.unavailable,
        ),
      ),
    },
    {
      key: "statistical-similarity",
      ...copy.rows.statisticalSimilarity,
      targetValue: copy.reference,
      candidateValues: candidates.map(({ evidence }) =>
        formatOptionalPercentage(
          evidence.statistical_similarity_pct,
          locale,
          copy.unavailable,
        ),
      ),
    },
    {
      key: "spatial-similarity",
      ...copy.rows.spatialSimilarity,
      targetValue: copy.reference,
      candidateValues: candidates.map(({ evidence }) =>
        formatOptionalPercentage(
          evidence.spatial_similarity_pct,
          locale,
          copy.unavailable,
        ),
      ),
    },
    {
      key: "heatmap-similarity",
      ...copy.rows.heatmapSimilarity,
      targetValue: copy.reference,
      candidateValues: candidates.map(({ evidence }) =>
        formatOptionalPercentage(
          evidence.heatmap_similarity_score_pct,
          locale,
          copy.unavailable,
        ),
      ),
    },
    {
      key: "role-fit",
      ...copy.rows.roleFit,
      targetValue: copy.reference,
      candidateValues: candidates.map(({ evidence }) =>
        formatOptionalPercentage(
          evidence.role_fit_pct,
          locale,
          copy.unavailable,
        ),
      ),
    },
    {
      key: "market-advantage",
      ...copy.rows.marketAdvantage,
      targetValue: copy.reference,
      candidateValues: candidates.map(({ evidence }) =>
        formatOptionalPercentage(
          evidence.market_value_advantage_pct,
          locale,
          copy.unavailable,
        ),
      ),
    },
  ];
}

function MultiPlayerComparisonSkeleton({
  label,
}: Readonly<{
  label: string;
}>) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={label}
      className="animate-pulse space-y-5 motion-reduce:animate-none"
    >
      <div className="h-24 rounded-3xl border border-border bg-surface-secondary" />

      <div className="overflow-hidden rounded-3xl border border-border bg-surface">
        <div className="h-16 border-b border-border bg-surface-secondary" />

        {Array.from({
          length: 8,
        }).map((_, index) => (
          <div
            key={index}
            className="grid grid-cols-4 gap-4 border-b border-border px-5 py-4 last:border-b-0"
          >
            <div className="h-4 rounded bg-surface-secondary" />
            <div className="h-4 rounded bg-surface-secondary" />
            <div className="h-4 rounded bg-surface-secondary" />
            <div className="h-4 rounded bg-surface-secondary" />
          </div>
        ))}
      </div>

      <span className="sr-only">{label}</span>
    </div>
  );
}

export function MultiPlayerComparison({
  identifiers,
}: MultiPlayerComparisonProps) {
  const locale = useLocale();
  const t = useTranslations("MultiPlayerComparison");

  const matrixCopy: ComparisonMatrixCopy = {
    unavailable: t("unavailable"),
    reference: t("reference"),
    yearsSuffix: t("yearsSuffix"),
    positionLabels: {
      G: t("positions.goalkeeper"),
      D: t("positions.defender"),
      M: t("positions.midfielder"),
      F: t("positions.forward"),
    },
    rows: {
      position: {
        label: t("rows.position.label"),
        description: t("rows.position.description"),
      },
      role: {
        label: t("rows.role.label"),
        description: t("rows.role.description"),
      },
      age: {
        label: t("rows.age.label"),
        description: t("rows.age.description"),
      },
      marketValue: {
        label: t("rows.marketValue.label"),
        description: t("rows.marketValue.description"),
      },
      minutes: {
        label: t("rows.minutes.label"),
        description: t("rows.minutes.description"),
      },
      quality: {
        label: t("rows.quality.label"),
        description: t("rows.quality.description"),
      },
      reliability: {
        label: t("rows.reliability.label"),
        description: t("rows.reliability.description"),
      },
      statisticalSimilarity: {
        label: t("rows.statisticalSimilarity.label"),
        description: t("rows.statisticalSimilarity.description"),
      },
      spatialSimilarity: {
        label: t("rows.spatialSimilarity.label"),
        description: t("rows.spatialSimilarity.description"),
      },
      heatmapSimilarity: {
        label: t("rows.heatmapSimilarity.label"),
        description: t("rows.heatmapSimilarity.description"),
      },
      roleFit: {
        label: t("rows.roleFit.label"),
        description: t("rows.roleFit.description"),
      },
      marketAdvantage: {
        label: t("rows.marketAdvantage.label"),
        description: t("rows.marketAdvantage.description"),
      },
    },
  };

  const comparison = useQuery({
    queryKey: [
      "transfer-intelligence",
      "multi-player-comparison",
      identifiers.targetPlayerId,
      ...identifiers.candidatePlayerIds,
      "all_players",
    ],
    queryFn: ({ signal }) =>
      fetchMultiPlayerComparison(
        identifiers.targetPlayerId,
        identifiers.candidatePlayerIds,
        signal,
        "all_players",
      ),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  if (comparison.isPending) {
    return <MultiPlayerComparisonSkeleton label={t("loading")} />;
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
            : t("comparisonRequestFailed")}
        </p>

        <ApiErrorReference error={comparison.error} />

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

  const {
    target,
    candidates,
    role_metrics: roleMetrics = [],
  } = comparison.data;

  if (candidates.length === 0) {
    return (
      <section className="rounded-2xl border border-warning/25 bg-warning/10 p-7">
        <p className="text-sm font-semibold tracking-[0.14em] text-warning uppercase">
          {t("candidatesUnavailable")}
        </p>

        <h2 className="mt-3 text-3xl font-bold tracking-[-0.035em]">
          {t("noCandidatesTitle")}
        </h2>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">
          {t("noCandidatesDescription")}
        </p>

        <Link
          href="/shortlists"
          className="mt-7 inline-flex rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
        >
          {t("returnToShortlists")}
        </Link>
      </section>
    );
  }

  const rows = buildMatrixRows(target, candidates, locale, matrixCopy);

  return (
    <div className="min-w-0 space-y-8">
      <section
        aria-labelledby="multi-comparison-overview-title"
        className="overflow-hidden rounded-3xl border border-border bg-surface shadow-sm"
      >
        <div className="border-b border-border px-5 py-6 sm:px-7">
          <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
            {t("overviewEyebrow")}
          </p>

          <h2
            id="multi-comparison-overview-title"
            className="mt-2 text-2xl font-bold tracking-[-0.035em]"
          >
            {t("overviewTitle")}
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
            {t("candidateSummary", {
              count: candidates.length,
              target: target.player_name,
            })}
          </p>
        </div>

        <div
          role="region"
          aria-label={t("scrollRegionLabel")}
          tabIndex={0}
          className="overflow-x-auto focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/25"
        >
          <table className="w-full min-w-[54rem] border-collapse text-left text-sm">
            <caption className="sr-only">{t("tableCaption")}</caption>

            <thead className="bg-surface-secondary">
              <tr>
                <th
                  scope="col"
                  className="sticky left-0 z-10 w-48 border-b border-r border-border bg-surface-secondary px-5 py-4 font-semibold"
                >
                  {t("metric")}
                </th>

                <th
                  scope="col"
                  className="min-w-48 border-b border-border px-5 py-4"
                >
                  <span className="block text-[11px] font-semibold tracking-[0.12em] text-brand uppercase">
                    {t("target")}
                  </span>

                  <Link
                    href={`/players/${target.player_id}`}
                    className="mt-1 block break-words font-bold hover:text-brand"
                  >
                    {target.player_name}
                  </Link>
                </th>

                {candidates.map((candidate, index) => (
                  <th
                    key={candidate.player.player_id}
                    scope="col"
                    className="min-w-48 border-b border-border px-5 py-4"
                  >
                    <span className="block text-[11px] font-semibold tracking-[0.12em] text-muted uppercase">
                      {t("candidateLabel", {
                        index: index + 1,
                      })}
                    </span>

                    <Link
                      href={`/players/${candidate.player.player_id}`}
                      className="mt-1 block break-words font-bold hover:text-brand"
                    >
                      {candidate.player.player_name}
                    </Link>
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.key}
                  className="border-b border-border last:border-b-0"
                >
                  <th
                    scope="row"
                    title={row.description}
                    className="sticky left-0 z-10 border-r border-border bg-surface px-5 py-4 font-semibold"
                  >
                    {row.label}

                    <span className="sr-only">. {row.description}</span>
                  </th>

                  <td className="px-5 py-4 font-medium">{row.targetValue}</td>

                  {row.candidateValues.map((value, index) => (
                    <td
                      key={`${row.key}-${candidates[index]?.player.player_id ?? index}`}
                      className={[
                        "px-5 py-4 font-medium",
                        value === matrixCopy.unavailable ? "text-muted" : "",
                      ].join(" ")}
                    >
                      {value}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="border-t border-border bg-page px-5 py-4 sm:px-7">
          <p className="text-xs leading-5 text-muted">
            {t("referenceGuidance")}
          </p>
        </div>
      </section>

      <MultiPlayerRoleMetrics
        target={target}
        candidates={candidates}
        groups={roleMetrics}
        variant="all_players"
      />

      <MultiPlayerComparisonEvidence target={target} candidates={candidates} />
    </div>
  );
}
