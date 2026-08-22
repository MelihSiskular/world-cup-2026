"use client";

import {
  zodResolver,
} from "@hookform/resolvers/zod";
import {
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  useRouter,
} from "next/navigation";
import {
  useForm,
} from "react-hook-form";

import {
  CountryFlag,
} from "@/components/players/country-flag";
import {
  PlayerImage,
} from "@/components/players/player-image";
import {
  fetchPlayerProfile,
} from "@/lib/api/browser-players";
import {
  createAnalysisSearchParameters,
  transferAnalysisFormSchema,
} from "@/lib/transfer-intelligence/analysis-form";
import {
  createTransferAnalysisQueryOptions,
} from "@/lib/transfer-intelligence/analysis-query";
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
    <div className="min-w-0">
      <label className="block">
        <span className="text-sm font-semibold text-foreground">
          {label}
        </span>

        <span className="mt-1 block text-xs leading-5 text-muted">
          {description}
        </span>

        <span className="mt-3 block">
          {children}
        </span>
      </label>

      {error ? (
        <p
          role="alert"
          className="mt-2 text-xs font-medium text-error"
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

  const queryClient =
    useQueryClient();

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

        void queryClient.prefetchQuery(
          createTransferAnalysisQueryOptions(
            playerId,
            values,
          ),
        );

        router.push(
          `/analysis/${playerId}/results?${parameters.toString()}`,
        );
      },
    );

  return (
    <div>
      <form
        onSubmit={submitAnalysis}
        className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-8"
      >
        <div>
          <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
            Recruitment search
          </p>

          <h2 className="mt-3 text-2xl font-bold tracking-[-0.03em]">
            Candidate pool
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
            Set the minimum evidence and budget constraints used to identify
            eligible replacement candidates.
          </p>
        </div>

        <section
          aria-label="Analysis target"
          className="mt-6 rounded-2xl border border-border bg-surface-secondary p-4 sm:p-5"
        >
          {playerProfile.isPending ? (
            <div
              className="animate-pulse"
              role="status"
            >
              <div className="h-5 w-40 rounded bg-border" />
              <div className="mt-2 h-4 w-56 rounded bg-border" />
            </div>
          ) : playerProfile.isError ? (
            <div
              className="rounded-xl border border-error/20 bg-error/10 p-4"
              role="alert"
            >
              <p className="font-semibold text-error">
                Target unavailable
              </p>

              <p className="mt-1 text-xs leading-5 text-muted">
                Return to player search and select the target again.
              </p>
            </div>
          ) : (
            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(28rem,34rem)] xl:items-center">
              <div className="flex min-w-0 items-center gap-4">
                <PlayerImage
                  playerId={playerProfile.data.player_id}
                  playerName={playerProfile.data.player_name}
                  size="target"
                />

                <div className="min-w-0">
                  <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
                    Analysis target
                  </p>

                  <h3 className="mt-2 break-words text-xl font-bold tracking-[-0.03em]">
                    {playerProfile.data.player_name}
                  </h3>

                  <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted">
                    <CountryFlag
                      countryAlpha3={playerProfile.data.country_alpha3}
                    />

                    <span>
                      {playerProfile.data.country_name ??
                        playerProfile.data.national_team_name ??
                        "Country unavailable"}
                    </span>

                    <span
                      aria-hidden="true"
                      className="text-border"
                    >
                      ·
                    </span>

                    <span>
                      {playerProfile.data.final_role}
                    </span>
                  </div>
                </div>
              </div>

              <dl className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                <div className="rounded-xl border border-border bg-surface px-4 py-3">
                  <dt className="text-[11px] font-medium leading-4 text-muted">
                    Tournament minutes
                  </dt>

                  <dd className="mt-1 text-lg font-bold tracking-[-0.02em]">
                    {playerProfile.data.minutes}
                  </dd>
                </div>

                <div className="rounded-xl border border-border bg-surface px-4 py-3">
                  <dt className="text-[11px] font-medium leading-4 text-muted">
                    Role confidence
                  </dt>

                  <dd className="mt-1 text-lg font-bold tracking-[-0.02em]">
                    {playerProfile.data.role_confidence_pct}%
                  </dd>
                </div>

                <div className="rounded-xl border border-border bg-surface px-4 py-3">
                  <dt className="text-[11px] font-medium leading-4 text-muted">
                    Player quality
                  </dt>

                  <dd className="mt-1 text-lg font-bold tracking-[-0.02em]">
                    {playerProfile.data.player_quality_score}%
                  </dd>
                </div>
              </dl>
            </div>
          )}
        </section>

        <div className="mt-8 grid gap-x-6 gap-y-7 md:grid-cols-3">
          <AnalysisField
            label="Tournament experience"
            description="Minimum World Cup minutes"
            error={
              errors.minimumMinutes
                ?.message
            }
          >
            <div className="relative">
              <input
                type="text"
                inputMode="numeric"
                {...register(
                  "minimumMinutes",
                  {
                    setValueAs: (value) =>
                      value === ""
                        ? Number.NaN
                        : Number(value),
                  },
                )}
                className="min-h-12 w-full rounded-xl border border-border bg-page px-4 pr-24 text-base font-semibold outline-none transition focus:border-brand focus:bg-surface"
              />

              <span className="pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 text-sm text-muted">
                min
              </span>
            </div>
          </AnalysisField>

          <AnalysisField
            label="Role evidence"
            description="Minimum tactical-role confidence"
            error={
              errors
                .minimumRoleConfidence
                ?.message
            }
          >
            <div className="relative">
              <input
                type="text"
                inputMode="decimal"
                {...register(
                  "minimumRoleConfidence",
                  {
                    setValueAs: (value) =>
                      value === ""
                        ? Number.NaN
                        : Number(value),
                  },
                )}
                className="min-h-12 w-full rounded-xl border border-border bg-page px-4 pr-12 text-base font-semibold outline-none transition focus:border-brand focus:bg-surface"
              />

              <span className="pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 text-sm text-muted">
                %
              </span>
            </div>
          </AnalysisField>

          <AnalysisField
            label="Budget ceiling"
            description="Maximum candidate market value"
            error={
              errors
                .maximumMarketValueMillions
                ?.message
            }
          >
            <div className="relative">
              <input
                type="text"
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
                className="min-h-12 w-full rounded-xl border border-border bg-page px-4 pr-12 text-base font-semibold outline-none transition placeholder:font-normal placeholder:text-muted/70 focus:border-brand focus:bg-surface"
              />

              <span className="pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 text-sm text-muted">
                €M
              </span>
            </div>
          </AnalysisField>
        </div>

        <details className="mt-8 border-y border-border">
          <summary className="flex w-fit cursor-pointer list-none items-center gap-3 py-4 [&::-webkit-details-marker]:hidden">
            <div>
              <span className="block text-sm font-semibold">
                Advanced settings
              </span>

              <span className="mt-0.5 block text-xs text-muted">
                Technical fallback behavior
              </span>
            </div>

            <span
              aria-hidden="true"
              className="flex size-6 shrink-0 items-center justify-center rounded-full border border-border bg-page text-sm font-semibold leading-none text-muted"
            >
              +
            </span>
          </summary>

          <div className="max-w-md pb-5">
            <AnalysisField
              label="Missing heatmap fallback"
              description="Used only when measured spatial evidence is unavailable"
              error={
                errors
                  .neutralHeatmapScore
                  ?.message
              }
            >
              <div className="relative">
                <input
                  type="text"
                  inputMode="decimal"
                  {...register(
                    "neutralHeatmapScore",
                    {
                      setValueAs: (value) =>
                      value === ""
                        ? Number.NaN
                        : Number(value),
                    },
                  )}
                  className="min-h-12 w-full rounded-xl border border-border bg-page px-4 pr-12 text-base font-semibold outline-none transition focus:border-brand focus:bg-surface"
                />

                <span className="pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 text-sm text-muted">
                  %
                </span>
              </div>
            </AnalysisField>

            <p className="mt-3 text-xs leading-5 text-muted">
              This fallback does not create spatial evidence. The configured
              value is used only when measured heatmap coverage is missing.
            </p>
          </div>
        </details>

        <p className="mt-7 text-sm leading-6 text-muted">
          Candidates are ranked independently for{" "}
          <span className="font-medium text-foreground">
            immediate impact
          </span>
          {" · "}
          <span className="font-medium text-foreground">
            development
          </span>
          {" · "}
          <span className="font-medium text-foreground">
            value
          </span>
          {" · "}
          <span className="font-medium text-foreground">
            short-term contribution
          </span>
          .
        </p>

        <div className="mt-7 flex flex-wrap items-center justify-between gap-4 border-t border-border pt-6">
          <p className="max-w-md text-xs leading-5 text-muted">
            Ranking combines tournament performance, tactical role, spatial
            evidence and market context.
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
            Find transfer alternatives
          </button>
        </div>
      </form>


    </div>
  );

}
