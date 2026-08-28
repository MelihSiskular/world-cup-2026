"use client";

import {
  useQuery,
} from "@tanstack/react-query";
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
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "Unavailable";
  }

  return formatProfilePercentage(
    value,
  );
}

function formatEvidenceNumber(
  value:
    | number
    | null
    | undefined,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "Unavailable";
  }

  return formatProfileNumber(
    value,
    {
      maximumFractionDigits: 1,
    },
  );
}

function HeatmapEvidenceMetric({
  label,
  value,
  description,
}: Readonly<{
  label: string;
  value: string;
  description: string;
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
          "Unavailable"
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

export function MultiPlayerComparisonEvidence({
  target,
  candidates,
}: MultiPlayerComparisonEvidenceProps) {
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
      aria-labelledby="focused-comparison-title"
      className="space-y-6"
    >
      <div className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-7">
        <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
          Focused evidence
        </p>

        <h2
          id="focused-comparison-title"
          className="mt-2 text-2xl font-bold tracking-[-0.035em]"
        >
          Inspect one candidate pair
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          Choose one candidate for
          detailed radar and heatmap
          evidence. The overview matrix
          remains unchanged.
        </p>

        <div
          role="group"
          aria-label="Focused comparison candidate"
          className="mt-5 flex flex-wrap gap-2"
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
                    setPreferredCandidateId(
                      player.player_id,
                    );
                  }}
                  className={[
                    "min-h-11 rounded-xl border px-4 py-2 text-sm font-semibold transition-colors",
                    selected
                      ? "border-brand bg-brand text-white"
                      : "border-border bg-surface hover:bg-surface-secondary",
                  ].join(
                    " ",
                  )}
                >
                  {player.player_name}
                </button>
              );
            },
          )}
        </div>

        <p
          aria-live="polite"
          className="mt-4 text-xs leading-5 text-muted"
        >
          Showing detailed evidence for{" "}
          <span className="font-semibold text-foreground">
            {target.player_name}
          </span>{" "}
          and{" "}
          <span className="font-semibold text-foreground">
            {
              focusedCandidate
                .player.player_name
            }
          </span>
          .
        </p>
      </div>

      <section
        aria-label="Focused playing style radar comparison"
        className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm"
      >
        <div className="border-b border-border p-6 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
                Playing style
              </p>

              <h3 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
                Position-relative radar
              </h3>

              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
                Compare the selected
                pair using their
                position-relative
                playing-style
                percentiles.
              </p>
            </div>

            {radarComparison.data ? (
              <span
                className={
                  radarComparison
                    .data.comparison
                    .overlay_available
                    ? "rounded-full border border-success/20 bg-success/10 px-3 py-1.5 text-xs font-semibold text-success"
                    : "rounded-full border border-border bg-page px-3 py-1.5 text-xs font-semibold text-muted"
                }
              >
                {
                  radarComparison
                    .data.comparison
                    .overlay_available
                    ? "Shared position overlay"
                    : "Separate position profiles"
                }
              </span>
            ) : null}
          </div>
        </div>

        <div className="p-5 sm:p-6">
          {radarComparison.isPending ? (
            <div
              role="status"
              aria-label="Loading focused radar comparison"
              aria-busy="true"
              className="min-h-96 animate-pulse rounded-2xl bg-surface-secondary motion-reduce:animate-none"
            />
          ) : radarComparison.isError ? (
            <div
              role="alert"
              className="rounded-2xl border border-warning/25 bg-warning/10 p-6"
            >
              <p className="text-sm font-semibold tracking-[0.12em] text-warning uppercase">
                Radar comparison
                unavailable
              </p>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
                The overview matrix
                remains available, but
                the focused radar could
                not be loaded.
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
                Retry radar
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
                  These profiles cannot
                  share one compatible
                  radar axis contract.
                  They are shown
                  separately.
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
        aria-label="Focused heatmap profile comparison"
        className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm"
      >
        <div className="border-b border-border p-6 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
                Heatmap profile
              </p>

              <h3 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
                Measured tournament
                occupation
              </h3>

              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
                Compare where the
                selected players
                occupied the pitch
                using measured
                tournament evidence.
              </p>
            </div>

            {heatmapComparison.data ? (
              <span
                className={
                  heatmapComparison
                    .data.similarity
                    .available
                    ? "rounded-full border border-success/20 bg-success/10 px-3 py-1.5 text-xs font-semibold text-success"
                    : "rounded-full border border-border bg-page px-3 py-1.5 text-xs font-semibold text-muted"
                }
              >
                {
                  heatmapComparison
                    .data.similarity
                    .available
                    ? "Measured pair evidence"
                    : "Pair evidence unavailable"
                }
              </span>
            ) : null}
          </div>
        </div>

        <div className="p-5 sm:p-6">
          {heatmapComparison.isPending ? (
            <div
              role="status"
              aria-label="Loading focused heatmap comparison"
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
                Heatmap comparison
                unavailable
              </p>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
                The overview matrix
                remains available, but
                the focused heatmap
                evidence could not be
                loaded.
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
                Retry heatmap
              </button>
            </div>
          ) : heatmapComparison.data ? (
            <>
              <div className="mb-5 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-surface-secondary px-4 py-3 sm:px-5">
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-foreground">
                    Shared density scale
                  </p>

                  <p className="mt-1 max-w-3xl text-[11px] leading-5 text-muted">
                    Both pitches use the
                    same relative
                    occupation-density
                    scale.
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
                aria-label="Focused heatmap evidence metrics"
                className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
              >
                <HeatmapEvidenceMetric
                  label="Measured similarity"
                  value={
                    formatEvidencePercentage(
                      heatmapComparison
                        .data.similarity
                        .heatmap_similarity_score_pct,
                    )
                  }
                  description="Overall measured similarity between the two tournament heatmap profiles."
                />

                <HeatmapEvidenceMetric
                  label="Cosine similarity"
                  value={
                    formatEvidencePercentage(
                      heatmapComparison
                        .data.similarity
                        .heatmap_cosine_similarity_pct,
                    )
                  }
                  description="Similarity across the complete occupation-density grid."
                />

                <HeatmapEvidenceMetric
                  label="Occupation overlap"
                  value={
                    formatEvidencePercentage(
                      heatmapComparison
                        .data.similarity
                        .occupation_overlap_pct,
                    )
                  }
                  description="How strongly both players occupy the same pitch areas."
                />

                <HeatmapEvidenceMetric
                  label="Peak-zone similarity"
                  value={
                    formatEvidencePercentage(
                      heatmapComparison
                        .data.similarity
                        .peak_zone_similarity_pct,
                    )
                  }
                  description="Similarity between the strongest occupation zones."
                />

                <HeatmapEvidenceMetric
                  label="Peak-zone distance"
                  value={
                    formatEvidenceNumber(
                      heatmapComparison
                        .data.similarity
                        .peak_zone_distance,
                    )
                  }
                  description="Distance between the strongest-density locations."
                />

                <HeatmapEvidenceMetric
                  label="Entropy similarity"
                  value={
                    formatEvidencePercentage(
                      heatmapComparison
                        .data.similarity
                        .entropy_similarity_pct,
                    )
                  }
                  description="Similarity in occupation-profile concentration."
                />
              </dl>
            </>
          ) : null}
        </div>
      </section>
    </section>
  );
}
