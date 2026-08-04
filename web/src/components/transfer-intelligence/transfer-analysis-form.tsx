"use client";

import {
  zodResolver,
} from "@hookform/resolvers/zod";
import {
  useQuery,
} from "@tanstack/react-query";
import {
  useRouter,
} from "next/navigation";
import {
  useForm,
} from "react-hook-form";

import {
  fetchPlayerProfile,
} from "@/lib/api/browser-players";
import {
  createAnalysisSearchParameters,
  transferAnalysisFormSchema,
} from "@/lib/transfer-intelligence/analysis-form";
import type {
  TransferAnalysisFormValues,
} from "@/lib/transfer-intelligence/analysis-form";

type TransferAnalysisFormProps =
  Readonly<{
    playerId: number;
    initialValues: TransferAnalysisFormValues;
  }>;

type AnalysisFieldProps =
  Readonly<{
    label: string;
    description: string;
    error?: string;
    children: React.ReactNode;
  }>;

function AnalysisField({
  label,
  description,
  error,
  children,
}: AnalysisFieldProps) {
  return (
    <div className="rounded-2xl border border-border bg-page p-5">
      <label className="block">
        <span className="font-semibold">
          {label}
        </span>

        <span className="mt-1 block text-sm leading-6 text-muted">
          {description}
        </span>

        <span className="mt-4 block">
          {children}
        </span>
      </label>

      {error ? (
        <p
          role="alert"
          className="mt-2 text-sm font-medium text-error"
        >
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function TransferAnalysisForm({
  playerId,
  initialValues,
}: TransferAnalysisFormProps) {
  const router = useRouter();

  const playerProfile =
    useQuery({
      queryKey: [
        "players",
        "profile",
        playerId,
      ],
      queryFn: ({
        signal,
      }) =>
        fetchPlayerProfile(
          playerId,
          signal,
        ),
      staleTime:
        5 * 60 * 1000,
      retry: 1,
    });

  const {
    register,
    handleSubmit,
    formState: {
      errors,
      isSubmitting,
    },
  } = useForm<
    TransferAnalysisFormValues
  >({
    resolver:
      zodResolver(
        transferAnalysisFormSchema,
      ),
    defaultValues: initialValues,
  });

  const submitAnalysis =
    handleSubmit(
      async (
        values,
      ) => {
        const parameters =
          createAnalysisSearchParameters(
            values,
          );

        router.push(
          `/analysis/${playerId}/results?${parameters.toString()}`,
        );
      },
    );

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <form
        onSubmit={submitAnalysis}
        className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-8"
      >
        <div>
          <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
            Recruitment parameters
          </p>

          <h2 className="mt-3 text-2xl font-bold tracking-[-0.03em]">
            Define the candidate pool
          </h2>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
            These thresholds control which
            players are eligible before the
            four recruitment scenarios are
            ranked.
          </p>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <AnalysisField
            label="Minimum tournament minutes"
            description="Exclude candidates without enough tournament playing time."
            error={
              errors.minimumMinutes
                ?.message
            }
          >
            <div className="relative">
              <input
                type="number"
                min="0"
                step="10"
                inputMode="numeric"
                {...register(
                  "minimumMinutes",
                  {
                    valueAsNumber: true,
                  },
                )}
                className="min-h-12 w-full rounded-xl border border-border bg-surface px-4 pr-20 text-base font-semibold outline-none transition focus:border-brand"
              />

              <span className="pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 text-sm text-muted">
                minutes
              </span>
            </div>
          </AnalysisField>

          <AnalysisField
            label="Minimum role confidence"
            description="Require stronger confidence in each candidate's assigned tactical role."
            error={
              errors
                .minimumRoleConfidence
                ?.message
            }
          >
            <div className="relative">
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                inputMode="decimal"
                {...register(
                  "minimumRoleConfidence",
                  {
                    valueAsNumber: true,
                  },
                )}
                className="min-h-12 w-full rounded-xl border border-border bg-surface px-4 pr-12 text-base font-semibold outline-none transition focus:border-brand"
              />

              <span className="pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 text-sm text-muted">
                %
              </span>
            </div>
          </AnalysisField>

          <AnalysisField
            label="Maximum market value"
            description="Optional budget ceiling. Leave empty to analyze candidates at every value level."
            error={
              errors
                .maximumMarketValueMillions
                ?.message
            }
          >
            <div className="relative">
              <input
                type="number"
                min="0"
                step="1"
                inputMode="decimal"
                placeholder="No limit"
                {...register(
                  "maximumMarketValueMillions",
                  {
                    setValueAs: (
                      value,
                    ) =>
                      value === ""
                        ? undefined
                        : Number(
                            value,
                          ),
                  },
                )}
                className="min-h-12 w-full rounded-xl border border-border bg-surface px-4 pr-12 text-base font-semibold outline-none transition placeholder:font-normal placeholder:text-muted/70 focus:border-brand"
              />

              <span className="pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 text-sm text-muted">
                €M
              </span>
            </div>
          </AnalysisField>

          <AnalysisField
            label="Neutral heatmap score"
            description="Fallback spatial score for candidates without sufficient heatmap coverage."
            error={
              errors
                .neutralHeatmapScore
                ?.message
            }
          >
            <div className="relative">
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                inputMode="decimal"
                {...register(
                  "neutralHeatmapScore",
                  {
                    valueAsNumber: true,
                  },
                )}
                className="min-h-12 w-full rounded-xl border border-border bg-surface px-4 pr-12 text-base font-semibold outline-none transition focus:border-brand"
              />

              <span className="pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 text-sm text-muted">
                %
              </span>
            </div>
          </AnalysisField>
        </div>

        <div className="mt-8 rounded-2xl border border-brand/20 bg-surface-secondary p-5">
          <p className="font-semibold text-brand-dark">
            Four scenarios from one analysis
          </p>

          <p className="mt-2 text-sm leading-6 text-muted">
            The eligible candidate pool will
            be ranked independently for
            immediate impact, development
            potential, market value and
            short-term contribution.
          </p>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-border pt-6">
          <p className="text-xs leading-5 text-muted">
            Analysis uses tournament
            performance, role, spatial and
            market context.
          </p>

          <button
            type="submit"
            disabled={
              isSubmitting ||
              playerProfile.isPending ||
              playerProfile.isError
            }
            className="inline-flex min-h-12 items-center justify-center rounded-xl bg-brand px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50"
          >
            Continue to results
          </button>
        </div>
      </form>

      <aside className="h-fit rounded-2xl border border-border bg-surface-secondary p-6 lg:sticky lg:top-24">
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          Analysis target
        </p>

        {playerProfile.isPending ? (
          <div
            className="mt-5 animate-pulse"
            role="status"
          >
            <div className="h-7 w-40 rounded bg-border" />
            <div className="mt-3 h-4 w-28 rounded bg-border" />
            <div className="mt-6 h-20 rounded-xl bg-border" />
          </div>
        ) : playerProfile.isError ? (
          <div
            className="mt-5 rounded-xl border border-error/20 bg-error/10 p-4"
            role="alert"
          >
            <p className="font-semibold text-error">
              Target unavailable
            </p>

            <p className="mt-2 text-sm leading-5 text-muted">
              Return to player search and
              select the target again.
            </p>
          </div>
        ) : (
          <>
            <h2 className="mt-4 text-2xl font-bold tracking-[-0.03em]">
              {
                playerProfile.data
                  .player_name
              }
            </h2>

            <p className="mt-2 text-sm font-medium text-muted">
              {
                playerProfile.data
                  .national_team_name
              }
              {" · "}
              {
                playerProfile.data
                  .final_role
              }
            </p>

            <dl className="mt-6 space-y-4 text-sm">
              <div>
                <dt className="text-muted">
                  Tournament sample
                </dt>
                <dd className="mt-1 font-semibold">
                  {
                    playerProfile.data
                      .appearances
                  }{" "}
                  appearances ·{" "}
                  {
                    playerProfile.data
                      .minutes
                  }{" "}
                  minutes
                </dd>
              </div>

              <div>
                <dt className="text-muted">
                  Role confidence
                </dt>
                <dd className="mt-1 font-semibold">
                  {
                    playerProfile.data
                      .role_confidence_pct
                  }
                  %
                </dd>
              </div>

              <div>
                <dt className="text-muted">
                  Player quality
                </dt>
                <dd className="mt-1 font-semibold">
                  {
                    playerProfile.data
                      .player_quality_score
                  }
                  %
                </dd>
              </div>
            </dl>
          </>
        )}
      </aside>
    </div>
  );
}
