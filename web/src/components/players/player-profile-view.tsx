import {
  useLocale,
  useTranslations,
} from "next-intl";
import type {
  ReactNode,
} from "react";

import { CountryFlag } from "@/components/players/country-flag";
import { PlayerFeaturedMetrics } from "@/components/players/player-featured-metrics";
import { PlayerImage } from "@/components/players/player-image";
import { PlayerScoutingInsights } from "@/components/players/player-scouting-insights";
import { PlayerPerformanceProfile } from "@/components/players/player-performance-profile";
import {
  ShortlistAction,
} from "@/components/shortlists/shortlist-action";
import {
  Link,
} from "@/i18n/navigation";

import type { PlayerProfileResponse } from "@/lib/api/types";
import {
  createShortlistSnapshotFromProfile,
} from "@/lib/shortlists/snapshot";
import {
  formatMarketValue,
  formatPlayerPosition,
  formatProfileNumber,
  formatProfilePercentage,
  formatUnitIntervalPercentage,
} from "@/lib/players/profile-format";

type PlayerProfileViewProps = Readonly<{
  player: PlayerProfileResponse;
  spatialProfile?: ReactNode;
}>;

type MetricCardProps = Readonly<{
  label: string;
  value: string;
  description: string;
}>;

function MetricCard({ label, value, description }: MetricCardProps) {
  return (
    <article className="rounded-2xl border border-border bg-surface p-4 shadow-sm">
      <p className="text-xs font-semibold text-muted">{label}</p>

      <p className="mt-2 text-xl font-bold tracking-[-0.03em]">{value}</p>

      <p className="mt-1.5 text-xs leading-5 text-muted">{description}</p>
    </article>
  );
}

type ProfileDetailCardProps = Readonly<{
  label: string;
  value: string;
  accent?: boolean;
}>;

function ProfileDetailCard({
  label,
  value,
  accent = false,
}: ProfileDetailCardProps) {
  return (
    <div className="rounded-xl border border-border bg-page p-4">
      <dt className="text-xs font-semibold text-muted">
        {label}
      </dt>

      <dd
        className={`mt-2 min-w-0 break-words font-bold${
          accent ? " text-brand-dark" : ""
        }`}
      >
        {value}
      </dd>
    </div>
  );
}

function PlayerModelContext({
  player,
}: Readonly<{
  player: PlayerProfileResponse;
}>) {
  const locale =
    useLocale();

  const translations =
    useTranslations(
      "PlayerProfile",
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

  return (
    <section
      aria-labelledby="player-model-context-title"
      className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-6"
    >
      <div className="max-w-3xl">
        <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
          {translations(
            "modelContextEyebrow",
          )}
        </p>

        <h2
          id="player-model-context-title"
          className="mt-2 text-xl font-bold tracking-[-0.025em]"
        >
          {translations(
          "modelConfidenceTitle",
        )}
        </h2>

        <p className="mt-2 text-sm leading-6 text-muted">
          {translations(
          "modelConfidenceDescription",
        )}
        </p>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label={translations(
            "weightedRating",
          )}
          value={formatProfileNumber(
            player.weighted_rating,
            {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            },
            formatContext,
          )}
          description={translations(
            "weightedRatingDescription",
          )}
        />

        <MetricCard
          label={translations(
            "playerQuality",
          )}
          value={formatProfilePercentage(
            player.player_quality_score,
            formatContext,
          )}
          description={translations(
            "playerQualityDescription",
          )}
        />

        <MetricCard
          label={translations(
            "dataReliability",
          )}
          value={formatProfilePercentage(
            player.data_reliability_score,
            formatContext,
          )}
          description={translations(
            "dataReliabilityDescription",
          )}
        />

        <MetricCard
          label={translations(
            "roleConfidence",
          )}
          value={formatProfilePercentage(
            player.role_confidence_pct,
            formatContext,
          )}
          description={translations(
            "roleConfidenceDescription",
          )}
        />
      </div>
    </section>
  );
}


export function PlayerProfileView({
  player,
  spatialProfile,
}: PlayerProfileViewProps) {
  const locale =
    useLocale();

  const translations =
    useTranslations(
      "PlayerProfile",
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

  const positionOptions = {
    unavailable:
      translations(
        "positionUnavailable",
      ),
    labels: {
      G: translations(
        "positionLabels.goalkeeper",
      ),
      D: translations(
        "positionLabels.defender",
      ),
      M: translations(
        "positionLabels.midfielder",
      ),
      F: translations(
        "positionLabels.forward",
      ),
    },
  };

  const roleReasonParts =
    player.role_reason
      ?.split("|")
      .map((part) => part.trim())
      .filter(Boolean) ?? [];

  const tournament = player.tournament ?? null;

  const tournamentMatches =
    tournament === null ? player.appearances : tournament.matches;

  const tournamentStarts =
    tournament === null ? player.starts : tournament.starts;

  const tournamentMinutes =
    tournament === null ? player.minutes : tournament.minutes;

  const shortlistPlayer =
    createShortlistSnapshotFromProfile(
      player,
    );

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-8">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(20rem,26rem)] lg:items-center">
          <div className="flex min-w-0 flex-col gap-7 sm:flex-row sm:items-start">
            <PlayerImage
              playerId={player.player_id}
              playerName={player.player_name}
              size="profile"
              priority
            />

            <div className="min-w-0 flex-1">
            <h1 className="min-w-0 [overflow-wrap:anywhere] text-4xl font-bold tracking-[-0.045em] sm:text-5xl">
              {player.player_name}
            </h1>

            <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-2 text-sm font-semibold text-muted">
              <CountryFlag
                countryAlpha3={player.country_alpha3}
              />

              <span>
                {player.country_name ??
                  player.national_team_name ??
                  translations(
                    "countryUnavailable",
                  )}
              </span>

              <span aria-hidden="true" className="text-border">
                ·
              </span>

              <span>
                {formatPlayerPosition(
                  player.position,
                  positionOptions,
                )}
              </span>
            </div>

            <p className="mt-4 break-words text-lg font-semibold text-brand">
              {player.final_role ??
                translations(
                  "finalRoleUnavailable",
                )}
            </p>

            <p className="mt-1.5 break-words text-sm leading-6 text-muted">
              {player.archetype ??
                translations(
                  "archetypeUnavailable",
                )}
              {" · "}
              {player.spatial_role ??
                translations(
                  "spatialRoleUnavailable",
                )}
            </p>

            <dl className="mt-6 flex flex-wrap gap-x-8 gap-y-4 border-t border-border pt-5">
              <div>
                <dt className="text-xs font-medium text-muted">
                  {translations(
                    "ageLabel",
                  )}
                </dt>

                <dd className="mt-1 text-sm font-bold">
                  {player.age === null
                    ? commonTranslations(
                        "notReported",
                      )
                    : translations(
                        "ageYears",
                        {
                          value:
                            formatProfileNumber(
                              player.age,
                              {
                                maximumFractionDigits: 0,
                              },
                              formatContext,
                            ),
                        },
                      )}
                </dd>
              </div>

              <div>
                <dt className="text-xs font-medium text-muted">
                  {translations(
                    "heightLabel",
                  )}
                </dt>

                <dd className="mt-1 text-sm font-bold">
                  {player.height_cm === null
                    ? commonTranslations(
                        "notReported",
                      )
                    : translations(
                        "heightCentimeters",
                        {
                          value:
                            formatProfileNumber(
                              player.height_cm,
                              {},
                              formatContext,
                            ),
                        },
                      )}
                </dd>
              </div>

              <div>
                <dt className="text-xs font-medium text-muted">
                  {translations(
                    "marketValueLabel",
                  )}
                </dt>

                <dd className="mt-1 text-sm font-bold text-brand-dark">
                  {formatMarketValue(
                    player.market_value,
                    player.market_value_currency,
                    formatContext,
                  )}
                </dd>
              </div>
            </dl>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center lg:flex-nowrap">
              <Link
                href="/players"
                aria-label={translations(
                  "backToSearch",
                )}
                className="inline-flex min-h-12 w-full shrink-0 items-center justify-center gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-center text-sm font-semibold transition-colors hover:bg-surface-secondary sm:w-auto"
              >
                <svg
                  aria-hidden="true"
                  viewBox="0 0 24 24"
                  className="size-4 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M19 12H5m7-7-7 7 7 7" />
                </svg>

                <span>
                  {translations(
                    "back",
                  )}
                </span>
              </Link>

              <Link
                href={`/analysis/${player.player_id}`}
                className="inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-brand px-5 py-3 text-center text-sm font-semibold text-white transition-colors hover:bg-brand-dark sm:w-auto"
              >
                {translations(
                  "runTransferAnalysis",
                )}
              </Link>

              <ShortlistAction
                player={shortlistPlayer}
              />
            </div>
          </div>
        </div>

          {spatialProfile ? (
            <div className="flex min-w-0 items-center justify-center">
              {spatialProfile}
            </div>
          ) : null}
        </div>
      </section>

      <PlayerFeaturedMetrics intelligence={player.intelligence} />

      <PlayerScoutingInsights intelligence={player.intelligence} />

      <section
        aria-labelledby="player-role-interpretation-title"
        className="rounded-2xl border border-border bg-surface p-5 shadow-sm sm:p-6"
      >
        <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
          {translations(
          "roleInterpretationEyebrow",
        )}
        </p>

        <h2
          id="player-role-interpretation-title"
          className="mt-3 text-2xl font-bold tracking-[-0.03em]"
        >
          {translations(
          "roleInterpretationTitle",
        )}
        </h2>

        <dl className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <ProfileDetailCard
            label={translations(
              "lateralProfile",
            )}
            value={
              player.lateral_profile ??
              commonTranslations(
                "notReported",
              )
            }
          />

          <ProfileDetailCard
            label={translations(
              "verticalProfile",
            )}
            value={
              player.vertical_profile ??
              commonTranslations(
                "notReported",
              )
            }
          />

          <ProfileDetailCard
            label={translations(
              "mobilityProfile",
            )}
            value={
              player.mobility_profile ??
              commonTranslations(
                "notReported",
              )
            }
          />

          <ProfileDetailCard
            label={translations(
              "spatialReliability",
            )}
            value={formatUnitIntervalPercentage(
              player.spatial_reliability,
              formatContext,
            )}
            accent
          />
        </dl>

        <div className="mt-6 border-t border-border pt-6">
          <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
            {translations(
              "tournamentSample",
            )}
          </p>

          <h3 className="mt-2 text-lg font-bold tracking-[-0.025em]">
            {translations(
            "participationContext",
          )}
          </h3>

          <dl className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <ProfileDetailCard
              label={translations(
                "matches",
              )}
              value={formatProfileNumber(
                tournamentMatches,
                {},
                formatContext,
              )}
            />

            <ProfileDetailCard
              label={translations(
                "starts",
              )}
              value={formatProfileNumber(
                tournamentStarts,
                {},
                formatContext,
              )}
            />

            <ProfileDetailCard
              label={translations(
                "minutes",
              )}
              value={formatProfileNumber(
                tournamentMinutes,
                {},
                formatContext,
              )}
            />

            <ProfileDetailCard
              label={translations(
                "primaryFormation",
              )}
              value={
                tournament?.primary_formation ??
                commonTranslations(
                  "notReported",
                )
              }
            />
          </dl>


        </div>

        {roleReasonParts.length > 0 ? (
          <details className="group mt-5 overflow-hidden rounded-xl border border-border bg-surface-secondary">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-3.5 font-semibold text-brand-dark transition-colors hover:bg-page [&::-webkit-details-marker]:hidden">
              <span>
                {translations(
                  "viewRoleEvidence",
                )}
              </span>

              <span
                aria-hidden="true"
                className="text-lg leading-none text-muted transition-transform group-open:rotate-45"
              >
                +
              </span>
            </summary>

            <div className="border-t border-border px-5 py-4">
              <p className="text-xs leading-5 text-muted">
                {translations(
                "roleEvidenceDescription",
              )}
              </p>

              <ul className="mt-4 space-y-3 text-sm leading-6 text-muted">
                {roleReasonParts.map((reason) => (
                  <li key={reason} className="flex gap-3">
                    <span
                      aria-hidden="true"
                      className="mt-2 size-1.5 shrink-0 rounded-full bg-brand"
                    />

                    <span className="min-w-0 break-words">
                      {reason}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </details>
        ) : null}
      </section>

      <PlayerModelContext player={player} />

      <PlayerPerformanceProfile intelligence={player.intelligence} />
    </div>
  );
}
