"use client";

import {
  useQuery,
} from "@tanstack/react-query";
import {
  useLocale,
  useTranslations,
} from "next-intl";
import {
  type KeyboardEvent,
  useState,
} from "react";

import {
  ApiErrorReference,
} from "@/components/feedback/api-error-reference";
import {
  Link,
} from "@/i18n/navigation";
import {
  PlayerImage,
} from "@/components/players/player-image";
import {
  TransferAnalysisResultsSkeleton,
} from "@/components/transfer-intelligence/transfer-analysis-results-skeleton";
import {
  TransferRecommendationCard,
} from "@/components/transfer-intelligence/transfer-recommendation-card";
import {
  isBrowserApiError,
} from "@/lib/api/browser-client";
import type {
  TransferModeName,
  TransferRecommendationResponse,
} from "@/lib/api/types";
import {
  formatMarketValue,
} from "@/lib/players/profile-format";
import {
  createAnalysisSearchParameters,
} from "@/lib/transfer-intelligence/analysis-form";
import type {
  TransferAnalysisFormValues,
} from "@/lib/transfer-intelligence/analysis-form";
import {
  createTransferAnalysisQueryOptions,
} from "@/lib/transfer-intelligence/analysis-query";
import {
  TRANSFER_MODE_ORDER,
} from "@/lib/transfer-intelligence/result-config";

const DEFAULT_VISIBLE_RECOMMENDATIONS = 8;

type TransferAnalysisResultsProps =
  Readonly<{
    playerId: number;
    values: TransferAnalysisFormValues;
    initialMode: TransferModeName;
  }>;

export function TransferAnalysisResults({
  playerId,
  values,
  initialMode,
}: TransferAnalysisResultsProps) {
  const locale = useLocale();

  const translations =
    useTranslations(
      "TransferAnalysisResults",
    );

  const numberFormatter =
    new Intl.NumberFormat(
      locale,
      {
        maximumFractionDigits: 1,
      },
    );

  const modeTranslations = {
    immediate: {
      label: translations(
        "modes.immediate.label",
      ),
      shortLabel: translations(
        "modes.immediate.shortLabel",
      ),
      description: translations(
        "modes.immediate.description",
      ),
    },
    development: {
      label: translations(
        "modes.development.label",
      ),
      shortLabel: translations(
        "modes.development.shortLabel",
      ),
      description: translations(
        "modes.development.description",
      ),
    },
    value: {
      label: translations(
        "modes.value.label",
      ),
      shortLabel: translations(
        "modes.value.shortLabel",
      ),
      description: translations(
        "modes.value.description",
      ),
    },
    short_term: {
      label: translations(
        "modes.shortTerm.label",
      ),
      shortLabel: translations(
        "modes.shortTerm.shortLabel",
      ),
      description: translations(
        "modes.shortTerm.description",
      ),
    },
  } as const;

  const [
    activeMode,
    setActiveMode,
  ] = useState<TransferModeName>(
    initialMode,
  );

  const [
    showAllRecommendations,
    setShowAllRecommendations,
  ] = useState(false);

  function selectMode(
    modeName: TransferModeName,
  ): void {
    setActiveMode(
      modeName,
    );

    setShowAllRecommendations(
      false,
    );
  }

  function handleModeKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    modeName: TransferModeName,
  ): void {
    const currentIndex =
      TRANSFER_MODE_ORDER.indexOf(
        modeName,
      );

    let nextIndex: number;

    switch (event.key) {
      case "ArrowRight":
        nextIndex =
          (currentIndex + 1) %
          TRANSFER_MODE_ORDER.length;
        break;

      case "ArrowLeft":
        nextIndex =
          (
            currentIndex -
            1 +
            TRANSFER_MODE_ORDER.length
          ) %
          TRANSFER_MODE_ORDER.length;
        break;

      case "Home":
        nextIndex = 0;
        break;

      case "End":
        nextIndex =
          TRANSFER_MODE_ORDER.length -
          1;
        break;

      default:
        return;
    }

    event.preventDefault();

    const nextMode =
      TRANSFER_MODE_ORDER[
        nextIndex
      ];

    if (nextMode === undefined) {
      return;
    }

    selectMode(
      nextMode,
    );

    const tabList =
      event.currentTarget.closest(
        '[role="tablist"]',
      );

    const tabs =
      tabList?.querySelectorAll<HTMLButtonElement>(
        '[role="tab"]',
      );

    tabs?.[nextIndex]?.focus();
  }

  const analysis =
    useQuery(
      createTransferAnalysisQueryOptions(
        playerId,
        values,
      ),
    );

  if (analysis.isPending) {
    return (
      <TransferAnalysisResultsSkeleton />
    );
  }

  if (analysis.isError) {
    const playerNotFound =
      isBrowserApiError(
        analysis.error,
      ) &&
      analysis.error.status === 404;

    const datasetUnavailable =
      isBrowserApiError(
        analysis.error,
      ) &&
      analysis.error.status === 503;

    return (
      <section
        role="alert"
        className="rounded-2xl border border-error/25 bg-error/10 p-7"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-error uppercase">
          {translations(
            "analysisUnavailable",
          )}
        </p>

        <h2 className="mt-3 text-3xl font-bold tracking-[-0.035em]">
          {playerNotFound
            ? translations(
                "playerNotFound",
              )
            : datasetUnavailable
              ? translations(
                  "datasetsUnavailable",
                )
              : translations(
                  "analysisFailed",
                )}
        </h2>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">
          {translations(
            "requestFailed",
          )}
        </p>

        <ApiErrorReference
          error={analysis.error}
          label={translations(
            "requestId",
          )}
        />

        <div className="mt-7 flex flex-wrap gap-3">
          {!playerNotFound ? (
            <button
              type="button"
              onClick={() => {
                void analysis.refetch();
              }}
              className="rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
            >
              {translations(
                "retryAnalysis",
              )}
            </button>
          ) : null}

          <Link
            href={`/analysis/${playerId}`}
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
          >
            {translations(
              "adjustParameters",
            )}
          </Link>
        </div>
      </section>
    );
  }

  const {
    target,
    modes,
  } = analysis.data;

  const activeRecommendations =
    modes[activeMode]
      .recommendations as readonly TransferRecommendationResponse[];

  const featuredRecommendation =
    activeRecommendations[0] ??
    null;

  const remainingRecommendations =
    activeRecommendations.slice(1);

  const visibleRemainingRecommendations =
    showAllRecommendations
      ? remainingRecommendations
      : remainingRecommendations.slice(
          0,
          Math.max(
            DEFAULT_VISIBLE_RECOMMENDATIONS - 1,
            0,
          ),
        );

  const queryString =
    createAnalysisSearchParameters(
      values,
    ).toString();

  const adjustParametersHref =
    `/analysis/${playerId}?${queryString}`;

  return (
    <div className="space-y-10">
      <section className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex min-w-0 items-center gap-4">
            <PlayerImage
              playerId={target.player_id}
              playerName={target.player_name}
              size="target"
              priority
            />

            <div className="min-w-0">
              <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
                {translations(
                  "analysisTarget",
                )}
              </p>

              <h2 className="mt-2 break-words text-2xl font-bold tracking-[-0.035em]">
                {target.player_name}
              </h2>

              <p className="mt-1 break-words text-sm font-semibold text-brand">
                {target.final_role ??
                  target.archetype ??
                  translations(
                    "roleUnavailable",
                  )}
              </p>

              <p className="mt-1 text-sm text-muted">
                {target.national_team_name ??
                  target.country_name ??
                  translations(
                    "nationalTeamUnavailable",
                  )}
                {" · "}
                {typeof target.appearances !==
                "number"
                  ? translations(
                      "notReported",
                    )
                  : numberFormatter.format(
                      target.appearances,
                    )}{" "}
                {translations(
                  "appearances",
                )}
                {" · "}
                {typeof target.minutes !==
                "number"
                  ? translations(
                      "notReported",
                    )
                  : numberFormatter.format(
                      target.minutes,
                    )}{" "}
                {translations(
                  "minutes",
                )}
              </p>
            </div>
          </div>

          <div className="grid gap-2 sm:grid-cols-3 xl:min-w-[31rem]">
            <div className="rounded-xl border border-border bg-surface-secondary px-4 py-3">
              <p className="text-xs text-muted">
                {translations(
                  "marketValue",
                )}
              </p>

              <p className="mt-1 text-lg font-bold tracking-[-0.02em]">
                {formatMarketValue(
                  target.market_value,
                  target.market_value_currency,
                )}
              </p>
            </div>

            <div className="rounded-xl border border-border bg-surface-secondary px-4 py-3">
              <p className="text-xs text-muted">
                {translations(
                  "playerQuality",
                )}
              </p>

              <p className="mt-1 text-lg font-bold tracking-[-0.02em]">
                {typeof target.player_quality_score !==
                "number"
                  ? translations(
                      "notReported",
                    )
                  : `${numberFormatter.format(
                      target.player_quality_score,
                    )}%`}
              </p>
            </div>

            <div className="rounded-xl border border-border bg-surface-secondary px-4 py-3">
              <p className="text-xs text-muted">
                {translations(
                  "roleConfidence",
                )}
              </p>

              <p className="mt-1 text-lg font-bold tracking-[-0.02em]">
                {typeof target.role_confidence_pct !==
                "number"
                  ? translations(
                      "notReported",
                    )
                  : `${numberFormatter.format(
                      target.role_confidence_pct,
                    )}%`}
              </p>
            </div>
          </div>
        </div>

        <div className="mt-5 border-t border-border pt-5">
          <Link
            href={adjustParametersHref}
            className="inline-flex rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-semibold transition-colors hover:bg-surface-secondary"
          >
            {translations(
              "adjustCriteria",
            )}
          </Link>
        </div>
      </section>



      <section
        aria-labelledby="active-mode-heading"
      >
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
              {translations(
                "activeScenario",
              )}
            </p>

            <h2
              id="active-mode-heading"
              className="mt-2 text-3xl font-bold tracking-[-0.035em]"
            >
              {
                modeTranslations[
                  activeMode
                ].label
              }
            </h2>

            <p className="mt-2 text-sm leading-6 text-muted">
              {
                modeTranslations[
                  activeMode
                ].description
              }
            </p>
          </div>

          <div className="xl:text-right">
            <p className="mb-2 text-xs font-semibold tracking-[0.14em] text-brand uppercase">
              {translations(
                "recruitmentStrategy",
              )}
            </p>

            <div
              role="tablist"
              aria-label={translations(
                "modeTabsAriaLabel",
              )}
              className="grid w-full max-w-2xl grid-cols-2 gap-2 sm:flex sm:w-auto sm:flex-wrap xl:justify-end"
            >
            {TRANSFER_MODE_ORDER.map(
              (modeName) => {
                const details =
                  modeTranslations[
                    modeName
                  ];

                const recommendationCount =
                  modes[modeName]
                    .recommendations.length;

                const active =
                  activeMode === modeName;

                return (
                  <button
                    key={modeName}
                    type="button"
                    role="tab"
                    aria-selected={active}
                    tabIndex={
                      active
                        ? 0
                        : -1
                    }
                    onClick={() => {
                      selectMode(
                        modeName,
                      );
                    }}
                    onKeyDown={(event) => {
                      handleModeKeyDown(
                        event,
                        modeName,
                      );
                    }}
                    className={[
                      "inline-flex min-h-11 min-w-0 items-center justify-between gap-2 rounded-xl border px-3 py-2 text-sm font-semibold transition sm:justify-center sm:px-3.5",
                      active
                        ? "border-brand bg-brand-dark text-white shadow-sm"
                        : "border-border bg-surface text-foreground hover:border-brand/35 hover:bg-surface-secondary",
                    ].join(" ")}
                  >
                    <span>
                      {details.shortLabel}
                    </span>

                    <span
                      className={[
                        "rounded-full px-2 py-0.5 text-xs font-bold",
                        active
                          ? "bg-white/15 text-white"
                          : "bg-page text-brand-dark",
                      ].join(" ")}
                    >
                      {recommendationCount}
                    </span>
                  </button>
                );
              },
            )}
            </div>
          </div>
        </div>

        {featuredRecommendation === null ? (
          <div className="rounded-2xl border border-dashed border-border bg-surface p-8 text-center">
            <p className="font-semibold">
              {translations(
                "noCandidates",
              )}
            </p>

            <p className="mt-2 text-sm text-muted">
              {translations(
                "noCandidatesDescription",
              )}
            </p>
          </div>
        ) : (
          <>
            <section
              aria-labelledby="leading-recommendation-heading"
              className="mt-10 sm:mt-12"
            >
              <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
                    {translations(
                      "leadingRecommendation",
                    )}
                  </p>

                  <h3
                    id="leading-recommendation-heading"
                    className="mt-1 text-xl font-bold tracking-[-0.025em]"
                  >
                    {translations(
                      "leadingRecommendationTitle",
                    )}
                  </h3>
                </div>
              </div>

              <TransferRecommendationCard
                targetPlayerId={
                  target.player_id
                }
                mode={activeMode}
                analysisValues={values}
                recommendation={
                  featuredRecommendation
                }
                variant="featured"
              />
            </section>

            {remainingRecommendations.length >
            0 ? (
              <section
                aria-labelledby="other-candidates-heading"
                className="mt-8"
              >
                <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
                      {translations(
                        "otherCandidates",
                      )}
                    </p>

                    <h3
                      id="other-candidates-heading"
                      className="mt-1 text-xl font-bold tracking-[-0.025em]"
                    >
                      {translations(
                        "otherCandidatesTitle",
                      )}
                    </h3>
                  </div>

                  <p className="text-sm text-muted">
                    {translations(
                      "alternativeCount",
                      {
                        count:
                          remainingRecommendations.length,
                      },
                    )}
                  </p>
                </div>

                <div className="space-y-4">
                  {visibleRemainingRecommendations.map(
                    (recommendation) => (
                      <TransferRecommendationCard
                        key={
                          recommendation.player_id
                        }
                        targetPlayerId={
                          target.player_id
                        }
                        mode={activeMode}
                        analysisValues={values}
                        recommendation={
                          recommendation
                        }
                        variant="compact"
                      />
                    ),
                  )}
                </div>

                {activeRecommendations.length >
                DEFAULT_VISIBLE_RECOMMENDATIONS ? (
                  <div className="mt-6 text-center">
                    <button
                      type="button"
                      onClick={() => {
                        setShowAllRecommendations(
                          (current) =>
                            !current,
                        );
                      }}
                      className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold transition-colors hover:bg-surface-secondary"
                    >
                      {showAllRecommendations
                        ? translations(
                            "showTopRecommendations",
                          )
                        : translations(
                            "showAllCandidates",
                            {
                              count:
                                activeRecommendations.length,
                            },
                          )}
                    </button>
                  </div>
                ) : null}
              </section>
            ) : null}
          </>
        )}
      </section>
    </div>
  );

}
