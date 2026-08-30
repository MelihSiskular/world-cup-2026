"use client";

import {
  useQuery,
} from "@tanstack/react-query";
import {
  useLocale,
  useTranslations,
} from "next-intl";
import {
  useState,
} from "react";

import {
  ApiErrorReference,
} from "@/components/feedback/api-error-reference";
import {
  getHeatmapGridMaximum,
  HeatmapDensityLegend,
  HeatmapPitch,
} from "@/components/transfer-intelligence/heatmap-pitch";
import {
  RadarProfile,
} from "@/components/transfer-intelligence/radar-profile";
import {
  fetchHeatmapComparison,
  fetchRadarComparison,
} from "@/lib/api/browser-transfer-intelligence";
import type {
  MultiPlayerComparisonCandidateResponse,
  MultiPlayerComparisonPlayerResponse,
} from "@/lib/api/types";
import {
  formatProfileNumber,
  formatProfilePercentage,
} from "@/lib/players/profile-format";

type MultiPlayerComparisonEvidenceProps =
  Readonly<{
    target:
      MultiPlayerComparisonPlayerResponse;
    candidates:
      readonly MultiPlayerComparisonCandidateResponse[];
  }>;

function formatEvidencePercentage(
  value:
    | number
    | null
    | undefined,
  locale: string,
  unavailable: string,
): string {
  return formatProfilePercentage(
    value,
    {
      locale,
      missingValue: unavailable,
    },
  );
}

function formatEvidenceNumber(
  value:
    | number
    | null
    | undefined,
  locale: string,
  unavailable: string,
): string {
  return formatProfileNumber(
    value,
    {
      maximumFractionDigits: 1,
    },
    {
      locale,
      missingValue: unavailable,
    },
  );
}

function HeatmapEvidenceMetric({
  label,
  value,
  description,
  unavailable,
}: Readonly<{
  label: string;
  value: string;
  description: string;
  unavailable: string;
}>) {
  return (
    <div
      title={description}
      className="min-w-0 rounded-xl border border-border bg-page px-4 py-3.5"
    >
      <dt className="text-[11px] font-medium leading-4 text-muted">
        {label}
      </dt>

      <dd
        className={[
          "mt-1.5 text-xl font-bold tracking-[-0.03em]",
          value ===
          unavailable
            ? "text-muted"
            : "text-brand-dark",
        ].join(
          " ",
        )}
      >
        {value}

        <span className="sr-only">
          . {description}
        </span>
      </dd>
    </div>
  );
}

function FocusedCandidateSelector({
  candidates,
  focusedCandidateId,
  onSelect,
  label,
}: Readonly<{
  candidates:
    readonly MultiPlayerComparisonCandidateResponse[];
  focusedCandidateId:
    | number
    | null;
  onSelect:
    (
      candidatePlayerId:
        number,
    ) => void;
  label: string;
}>) {
  return (
    <div
      role="group"
      aria-label={label}
      className="flex max-w-full flex-wrap justify-end gap-2"
    >
      {candidates.map(
        ({ player }) => {
          const selected =
            player.player_id ===
            focusedCandidateId;

          return (
            <button
              key={
                player.player_id
              }
              type="button"
              aria-pressed={
                selected
              }
              onClick={() => {
                onSelect(
                  player.player_id,
                );
              }}
              className={[
                "min-h-11 max-w-56 rounded-xl border px-4 py-2 text-sm font-semibold transition-colors",
                selected
                  ? "border-brand-dark bg-brand-dark text-white"
                  : "border-border bg-surface hover:bg-surface-secondary",
              ].join(
                " ",
              )}
            >
              <span className="block truncate">
                {
                  player.player_name
                }
              </span>
            </button>
          );
        },
      )}
    </div>
  );
}

export function MultiPlayerComparisonEvidence({
  target,
  candidates,
}: MultiPlayerComparisonEvidenceProps) {
  const locale = useLocale();
  const t = useTranslations(
    "MultiPlayerComparisonEvidence",
  );

  const formatPercentage = (
    value:
      | number
      | null
      | undefined,
  ) =>
    formatEvidencePercentage(
      value,
      locale,
      t("unavailable"),
    );

  const formatNumber = (
    value:
      | number
      | null
      | undefined,
  ) =>
    formatEvidenceNumber(
      value,
      locale,
      t("unavailable"),
    );

  const [
    preferredCandidateId,
    setPreferredCandidateId,
  ] = useState<number | null>(
    candidates[0]
      ?.player.player_id ??
      null,
  );

  const focusedCandidate =
    candidates.find(
      ({ player }) =>
        player.player_id ===
        preferredCandidateId,
    ) ??
    candidates[0] ??
    null;

  const focusedCandidateId =
    focusedCandidate
      ?.player.player_id ??
    null;

  const radarComparison =
    useQuery({
      queryKey: [
        "transfer-intelligence",
        "multi-player-comparison",
        "radar",
        target.player_id,
        focusedCandidateId,
      ],
      queryFn: ({
        signal,
      }) => {
        if (
          focusedCandidateId ===
          null
        ) {
          return Promise.reject(
            new Error(
              "A focused candidate is required.",
            ),
          );
        }

        return fetchRadarComparison(
          target.player_id,
          focusedCandidateId,
          signal,
        );
      },
      enabled:
        focusedCandidateId !==
        null,
      staleTime:
        5 * 60 * 1000,
      retry: false,
    });

  const heatmapComparison =
    useQuery({
      queryKey: [
        "transfer-intelligence",
        "multi-player-comparison",
        "heatmap",
        target.player_id,
        focusedCandidateId,
      ],
      queryFn: ({
        signal,
      }) => {
        if (
          focusedCandidateId ===
          null
        ) {
          return Promise.reject(
            new Error(
              "A focused candidate is required.",
            ),
          );
        }

        return fetchHeatmapComparison(
          target.player_id,
          focusedCandidateId,
          signal,
        );
      },
      enabled:
        focusedCandidateId !==
        null,
      staleTime:
        5 * 60 * 1000,
      retry: false,
    });

  if (
    focusedCandidate === null
  ) {
    return null;
  }

  const sharedHeatmapMaximum =
    heatmapComparison.data
      ? Math.max(
          getHeatmapGridMaximum(
            heatmapComparison
              .data.target.grid,
          ),
          getHeatmapGridMaximum(
            heatmapComparison
              .data.candidate.grid,
          ),
        )
      : null;

  return (
    <section
      aria-label={t("sectionLabel")}
      className="space-y-6"
    >
      <p
        aria-live="polite"
        className="sr-only"
      >
        {t("showingEvidence", {
          target:
            target.player_name,
          candidate:
            focusedCandidate
              .player.player_name,
        })}
      </p>

      <section
        aria-label={t("radar.sectionLabel")}
        className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm"
      >
        <div className="border-b border-border p-6 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
                {t("radar.eyebrow")}
              </p>

              <h3 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
                {t("radar.title")}
              </h3>

              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
                {t("radar.description")}
              </p>
            </div>

            <FocusedCandidateSelector
              candidates={
                candidates
              }
              focusedCandidateId={
                focusedCandidateId
              }
              onSelect={
                setPreferredCandidateId
              }
              label={t(
                "radar.candidateSelector",
              )}
            />
          </div>
        </div>

        <div className="p-5 sm:p-6">
          {radarComparison.isPending ? (
            <div
              role="status"
              aria-label={t("radar.loading")}
              aria-busy="true"
              className="min-h-96 animate-pulse rounded-2xl bg-surface-secondary motion-reduce:animate-none"
            />
          ) : radarComparison.isError ? (
            <div
              role="alert"
              className="rounded-2xl border border-warning/25 bg-warning/10 p-6"
            >
              <p className="text-sm font-semibold tracking-[0.12em] text-warning uppercase">
                {t("radar.unavailable")}
              </p>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
                {t(
                  "radar.unavailableDescription",
                )}
              </p>

              <ApiErrorReference
                error={
                  radarComparison.error
                }
              />

              <button
                type="button"
                onClick={() => {
                  void radarComparison
                    .refetch();
                }}
                className="mt-5 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold hover:bg-page"
              >
                {t("radar.retry")}
              </button>
            </div>
          ) : radarComparison.data ? (
            radarComparison
              .data.comparison
              .overlay_available ? (
              <RadarProfile
                primary={
                  radarComparison
                    .data.target
                }
                secondary={
                  radarComparison
                    .data.candidate
                }
                showHeader={
                  false
                }
              />
            ) : (
              <>
                <p className="mb-5 rounded-xl border border-border bg-surface-secondary px-4 py-3 text-xs leading-5 text-muted">
                  {t(
                    "radar.incompatible",
                  )}
                </p>

                <div className="grid min-w-0 gap-5 lg:grid-cols-2">
                  <article className="min-w-0">
                    <p className="mb-3 break-words text-sm font-bold">
                      {
                        radarComparison
                          .data.target
                          .player_name
                      }
                    </p>

                    <RadarProfile
                      primary={
                        radarComparison
                          .data.target
                      }
                      showHeader={
                        false
                      }
                    />
                  </article>

                  <article className="min-w-0">
                    <p className="mb-3 break-words text-sm font-bold">
                      {
                        radarComparison
                          .data.candidate
                          .player_name
                      }
                    </p>

                    <RadarProfile
                      primary={
                        radarComparison
                          .data.candidate
                      }
                      showHeader={
                        false
                      }
                    />
                  </article>
                </div>
              </>
            )
          ) : null}
        </div>
      </section>

      <section
        aria-label={t("heatmap.sectionLabel")}
        className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm"
      >
        <div className="border-b border-border p-6 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
                {t("heatmap.eyebrow")}
              </p>

              <h3 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
                {t("heatmap.title")}
              </h3>

              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
                {t(
                  "heatmap.description",
                )}
              </p>
            </div>

            <FocusedCandidateSelector
              candidates={
                candidates
              }
              focusedCandidateId={
                focusedCandidateId
              }
              onSelect={
                setPreferredCandidateId
              }
              label={t(
                "heatmap.candidateSelector",
              )}
            />
          </div>
        </div>

        <div className="p-5 sm:p-6">
          {heatmapComparison.isPending ? (
            <div
              role="status"
              aria-label={t("heatmap.loading")}
              aria-busy="true"
              className="grid gap-5 md:grid-cols-2"
            >
              <div className="min-h-72 animate-pulse rounded-2xl bg-surface-secondary motion-reduce:animate-none" />
              <div className="min-h-72 animate-pulse rounded-2xl bg-surface-secondary motion-reduce:animate-none" />
            </div>
          ) : heatmapComparison.isError ? (
            <div
              role="alert"
              className="rounded-2xl border border-warning/25 bg-warning/10 p-6"
            >
              <p className="text-sm font-semibold tracking-[0.12em] text-warning uppercase">
                {t("heatmap.unavailable")}
              </p>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
                {t(
                  "heatmap.unavailableDescription",
                )}
              </p>

              <ApiErrorReference
                error={
                  heatmapComparison
                    .error
                }
              />

              <button
                type="button"
                onClick={() => {
                  void heatmapComparison
                    .refetch();
                }}
                className="mt-5 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold hover:bg-page"
              >
                {t("heatmap.retry")}
              </button>
            </div>
          ) : heatmapComparison.data ? (
            <>
              <div className="mb-5 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-surface-secondary px-4 py-3 sm:px-5">
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-foreground">
                    {t(
                      "heatmap.sharedScale",
                    )}
                  </p>

                  <p className="mt-1 max-w-3xl text-[11px] leading-5 text-muted">
                    {t(
                      "heatmap.sharedScaleDescription",
                    )}
                  </p>
                </div>

                <HeatmapDensityLegend />
              </div>

              <div className="grid min-w-0 gap-5 md:grid-cols-2">
                <article className="min-w-0">
                  <p className="mb-3 break-words text-sm font-bold">
                    {
                      heatmapComparison
                        .data.target
                        .player_name
                    }
                  </p>

                  <HeatmapPitch
                    player={
                      heatmapComparison
                        .data.target
                    }
                    scaleMax={
                      sharedHeatmapMaximum
                    }
                    showDensityLegend={
                      false
                    }
                  />
                </article>

                <article className="min-w-0">
                  <p className="mb-3 break-words text-sm font-bold">
                    {
                      heatmapComparison
                        .data.candidate
                        .player_name
                    }
                  </p>

                  <HeatmapPitch
                    player={
                      heatmapComparison
                        .data.candidate
                    }
                    scaleMax={
                      sharedHeatmapMaximum
                    }
                    showDensityLegend={
                      false
                    }
                  />
                </article>
              </div>

              <dl
                aria-label={t("heatmap.metricsLabel")}
                className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
              >
                <HeatmapEvidenceMetric
                  unavailable={t(
                    "unavailable",
                  )}
                  label={t("heatmap.metrics.measuredSimilarity")}
                  value={
                    formatPercentage(
                      heatmapComparison
                        .data.similarity
                        .heatmap_similarity_score_pct,
                    )
                  }
                  description={t("heatmap.metrics.measuredSimilarityDescription")}
                />

                <HeatmapEvidenceMetric
                  unavailable={t(
                    "unavailable",
                  )}
                  label={t("heatmap.metrics.cosineSimilarity")}
                  value={
                    formatPercentage(
                      heatmapComparison
                        .data.similarity
                        .heatmap_cosine_similarity_pct,
                    )
                  }
                  description={t("heatmap.metrics.cosineSimilarityDescription")}
                />

                <HeatmapEvidenceMetric
                  unavailable={t(
                    "unavailable",
                  )}
                  label={t("heatmap.metrics.occupationOverlap")}
                  value={
                    formatPercentage(
                      heatmapComparison
                        .data.similarity
                        .occupation_overlap_pct,
                    )
                  }
                  description={t("heatmap.metrics.occupationOverlapDescription")}
                />

                <HeatmapEvidenceMetric
                  unavailable={t(
                    "unavailable",
                  )}
                  label={t("heatmap.metrics.peakZoneSimilarity")}
                  value={
                    formatPercentage(
                      heatmapComparison
                        .data.similarity
                        .peak_zone_similarity_pct,
                    )
                  }
                  description={t("heatmap.metrics.peakZoneSimilarityDescription")}
                />

                <HeatmapEvidenceMetric
                  unavailable={t(
                    "unavailable",
                  )}
                  label={t("heatmap.metrics.peakZoneDistance")}
                  value={
                    formatNumber(
                      heatmapComparison
                        .data.similarity
                        .peak_zone_distance,
                    )
                  }
                  description={t("heatmap.metrics.peakZoneDistanceDescription")}
                />

                <HeatmapEvidenceMetric
                  unavailable={t(
                    "unavailable",
                  )}
                  label={t("heatmap.metrics.entropySimilarity")}
                  value={
                    formatPercentage(
                      heatmapComparison
                        .data.similarity
                        .entropy_similarity_pct,
                    )
                  }
                  description={t("heatmap.metrics.entropySimilarityDescription")}
                />
              </dl>
            </>
          ) : null}
        </div>
      </section>
    </section>
  );
}
