"use client";

import {
  zodResolver,
} from "@hookform/resolvers/zod";
import {
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  useLocale,
  useTranslations,
} from "next-intl";
import {
  useTransition,
} from "react";
import {
  useForm,
} from "react-hook-form";

import {
  CountryFlag,
} from "@/components/players/country-flag";
import {
  useRouter,
} from "@/i18n/navigation";
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
  const locale = useLocale();

  const translations =
    useTranslations(
      "TransferAnalysisForm",
    );

  const numberFormatter =
    new Intl.NumberFormat(
      locale,
      {
        maximumFractionDigits: 1,
      },
    );

  const router = useRouter();

  const queryClient =
    useQueryClient();

  const [
    isNavigating,
    startNavigation,
  ] = useTransition();

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
      (
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

        startNavigation(() => {
          router.push(
            `/analysis/${playerId}/results?${parameters.toString()}`,
          );
        });
      },
    );

  const submittingAnalysis =
    isSubmitting ||
    isNavigating;

  return (
    <div>
      <form
        onSubmit={submitAnalysis}
        className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-8"
      >
        <div>
          <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
            {translations(
              "recruitmentSearch",
            )}
          </p>

          <h2 className="mt-3 text-2xl font-bold tracking-[-0.03em]">
            {translations(
              "candidatePool",
            )}
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
            {translations(
              "description",
            )}
          </p>
        </div>

        <section
          aria-label={translations(
            "analysisTargetAriaLabel",
          )}
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
                {translations(
                  "targetUnavailable",
                )}
              </p>

              <p className="mt-1 text-xs leading-5 text-muted">
                {translations(
                  "targetUnavailableDescription",
                )}
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
                    {translations(
                      "analysisTarget",
                    )}
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
                        translations(
                          "countryUnavailable",
                        )}
                    </span>

                    <span
                      aria-hidden="true"
                      className="text-border"
                    >
                      ·
                    </span>

                    <span>
                      {playerProfile.data.final_role ??
                        translations(
                          "roleUnavailable",
                        )}
                    </span>
                  </div>
                </div>
              </div>

              <dl className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                <div className="rounded-xl border border-border bg-surface px-4 py-3">
                  <dt className="text-[11px] font-medium leading-4 text-muted">
                    {translations(
                      "tournamentMinutes",
                    )}
                  </dt>

                  <dd className="mt-1 text-lg font-bold tracking-[-0.02em]">
                    {playerProfile.data.minutes ===
                    null
                      ? translations(
                          "metricUnavailable",
                        )
                      : numberFormatter.format(
                          playerProfile.data.minutes,
                        )}
                  </dd>
                </div>

                <div className="rounded-xl border border-border bg-surface px-4 py-3">
                  <dt className="text-[11px] font-medium leading-4 text-muted">
                    {translations(
                      "roleConfidence",
                    )}
                  </dt>

                  <dd className="mt-1 text-lg font-bold tracking-[-0.02em]">
                    {playerProfile.data.role_confidence_pct ===
                    null
                      ? translations(
                          "metricUnavailable",
                        )
                      : `${numberFormatter.format(
                          playerProfile.data.role_confidence_pct,
                        )}%`}
                  </dd>
                </div>

                <div className="rounded-xl border border-border bg-surface px-4 py-3">
                  <dt className="text-[11px] font-medium leading-4 text-muted">
                    {translations(
                      "playerQuality",
                    )}
                  </dt>

                  <dd className="mt-1 text-lg font-bold tracking-[-0.02em]">
                    {playerProfile.data.player_quality_score ===
                    null
                      ? translations(
                          "metricUnavailable",
                        )
                      : `${numberFormatter.format(
                          playerProfile.data.player_quality_score,
                        )}%`}
                  </dd>
                </div>
              </dl>
            </div>
          )}
        </section>

        <div className="mt-8 grid gap-x-6 gap-y-7 md:grid-cols-3">
          <AnalysisField
            label={translations(
              "tournamentExperience",
            )}
            description={translations(
              "minimumWorldCupMinutes",
            )}
            error={
              errors.minimumMinutes
                ? translations(
                    "validation.minimumMinutes",
                  )
                : undefined
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
                {translations(
                  "minutesUnit",
                )}
              </span>
            </div>
          </AnalysisField>

          <AnalysisField
            label={translations(
              "roleEvidence",
            )}
            description={translations(
              "minimumRoleConfidence",
            )}
            error={
              errors
                .minimumRoleConfidence
                ? translations(
                    "validation.roleConfidence",
                  )
                : undefined
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
            label={translations(
              "budgetCeiling",
            )}
            description={translations(
              "maximumMarketValue",
            )}
            error={
              errors
                .maximumMarketValueMillions
                ? translations(
                    "validation.marketValue",
                  )
                : undefined
            }
          >
            <div className="relative">
              <input
                type="text"
                inputMode="decimal"
                placeholder={translations(
                  "noLimit",
                )}
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
                {translations(
                  "advancedSettings",
                )}
              </span>

              <span className="mt-0.5 block text-xs text-muted">
                {translations(
                  "technicalFallbackBehavior",
                )}
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
              label={translations(
                "missingHeatmapFallback",
              )}
              description={translations(
                "missingHeatmapDescription",
              )}
              error={
                errors
                  .neutralHeatmapScore
                  ? translations(
                      "validation.heatmapFallback",
                    )
                  : undefined
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
              {translations(
                "fallbackExplanation",
              )}
            </p>
          </div>
        </details>

        <p className="mt-7 text-sm leading-6 text-muted">
          {translations(
            "rankingPrefix",
          )}{" "}
          <span className="font-medium text-foreground">
            {translations(
              "immediateImpact",
            )}
          </span>
          {" · "}
          <span className="font-medium text-foreground">
            {translations(
              "development",
            )}
          </span>
          {" · "}
          <span className="font-medium text-foreground">
            {translations(
              "value",
            )}
          </span>
          {" · "}
          <span className="font-medium text-foreground">
            {translations(
              "shortTermContribution",
            )}
          </span>
          .
        </p>

        <div className="mt-7 flex flex-col gap-4 border-t border-border pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="max-w-md text-xs leading-5 text-muted">
            {translations(
              "rankingDescription",
            )}
          </p>

          <button
            type="submit"
            disabled={
              submittingAnalysis ||
              playerProfile.isPending ||
              playerProfile.isError
            }
            aria-busy={
              isNavigating
            }
            className="inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-brand px-6 py-3 text-center text-sm font-semibold text-white transition-colors hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
          >
            {submittingAnalysis
              ? translations(
                  "openingRecommendations",
                )
              : translations(
                  "findAlternatives",
                )}
          </button>
        </div>
      </form>


    </div>
  );

}
