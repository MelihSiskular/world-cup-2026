import type { ReactNode } from "react";

import Link from "next/link";

import { CountryFlag } from "@/components/players/country-flag";
import { PlayerFeaturedMetrics } from "@/components/players/player-featured-metrics";
import { PlayerImage } from "@/components/players/player-image";
import { PlayerScoutingInsights } from "@/components/players/player-scouting-insights";
import { PlayerPerformanceProfile } from "@/components/players/player-performance-profile";
import {
  ShortlistAction,
} from "@/components/shortlists/shortlist-action";

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
  return (
    <section
      aria-labelledby="player-model-context-title"
      className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-6"
    >
      <div className="max-w-3xl">
        <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
          Model context
        </p>

        <h2
          id="player-model-context-title"
          className="mt-2 text-xl font-bold tracking-[-0.025em]"
        >
          Confidence behind the profile
        </h2>

        <p className="mt-2 text-sm leading-6 text-muted">
          Supporting quality and reliability signals used to interpret the
          tournament profile.
        </p>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Weighted rating"
          value={formatProfileNumber(player.weighted_rating, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
          description="Reliability-aware tournament performance rating"
        />

        <MetricCard
          label="Player quality"
          value={formatProfilePercentage(player.player_quality_score)}
          description="Combined performance-quality assessment"
        />

        <MetricCard
          label="Data reliability"
          value={formatProfilePercentage(player.data_reliability_score)}
          description="Confidence supported by available tournament data"
        />

        <MetricCard
          label="Role confidence"
          value={formatProfilePercentage(player.role_confidence_pct)}
          description="Confidence in the assigned tactical role"
        />
      </div>
    </section>
  );
}


export function PlayerProfileView({
  player,
  spatialProfile,
}: PlayerProfileViewProps) {
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
                  "Country unavailable"}
              </span>

              <span aria-hidden="true" className="text-border">
                ·
              </span>

              <span>
                {formatPlayerPosition(player.position)}
              </span>
            </div>

            <p className="mt-4 break-words text-lg font-semibold text-brand">
              {player.final_role ?? "Final role unavailable"}
            </p>

            <p className="mt-1.5 break-words text-sm leading-6 text-muted">
              {player.archetype ?? "Archetype unavailable"}
              {" · "}
              {player.spatial_role ?? "Spatial role unavailable"}
            </p>

            <dl className="mt-6 flex flex-wrap gap-x-8 gap-y-4 border-t border-border pt-5">
              <div>
                <dt className="text-xs font-medium text-muted">
                  Age
                </dt>

                <dd className="mt-1 text-sm font-bold">
                  {player.age === null
                    ? "Not reported"
                    : `${formatProfileNumber(player.age, {
                        maximumFractionDigits: 0,
                      })} years`}
                </dd>
              </div>

              <div>
                <dt className="text-xs font-medium text-muted">
                  Height
                </dt>

                <dd className="mt-1 text-sm font-bold">
                  {player.height_cm === null
                    ? "Not reported"
                    : `${formatProfileNumber(player.height_cm)} cm`}
                </dd>
              </div>

              <div>
                <dt className="text-xs font-medium text-muted">
                  Market value
                </dt>

                <dd className="mt-1 text-sm font-bold text-brand-dark">
                  {formatMarketValue(
                    player.market_value,
                    player.market_value_currency,
                  )}
                </dd>
              </div>
            </dl>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <Link
                href={`/analysis/${player.player_id}`}
                className="inline-flex min-h-12 w-full items-center justify-center rounded-xl bg-brand px-5 py-3 text-center text-sm font-semibold text-white transition-colors hover:bg-brand-dark sm:w-auto"
              >
                Run transfer analysis
              </Link>

              <ShortlistAction
                player={shortlistPlayer}
              />

              <Link
                href="/players"
                className="inline-flex min-h-12 w-full items-center justify-center rounded-xl border border-border bg-surface px-5 py-3 text-center text-sm font-semibold transition-colors hover:bg-surface-secondary sm:w-auto"
              >
                Back to player search
              </Link>
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
          Role interpretation
        </p>

        <h2
          id="player-role-interpretation-title"
          className="mt-3 text-2xl font-bold tracking-[-0.03em]"
        >
          How the player operates
        </h2>

        <dl className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <ProfileDetailCard
            label="Lateral profile"
            value={player.lateral_profile ?? "Not reported"}
          />

          <ProfileDetailCard
            label="Vertical profile"
            value={player.vertical_profile ?? "Not reported"}
          />

          <ProfileDetailCard
            label="Mobility profile"
            value={player.mobility_profile ?? "Not reported"}
          />

          <ProfileDetailCard
            label="Spatial reliability"
            value={formatUnitIntervalPercentage(
              player.spatial_reliability,
            )}
            accent
          />
        </dl>

        <div className="mt-6 border-t border-border pt-6">
          <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
            Tournament sample
          </p>

          <h3 className="mt-2 text-lg font-bold tracking-[-0.025em]">
            Participation context
          </h3>

          <dl className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <ProfileDetailCard
              label="Matches"
              value={formatProfileNumber(tournamentMatches)}
            />

            <ProfileDetailCard
              label="Starts"
              value={formatProfileNumber(tournamentStarts)}
            />

            <ProfileDetailCard
              label="Minutes"
              value={formatProfileNumber(tournamentMinutes)}
            />

            <ProfileDetailCard
              label="Primary formation"
              value={tournament?.primary_formation ?? "Not reported"}
            />
          </dl>


        </div>

        {roleReasonParts.length > 0 ? (
          <details className="group mt-5 overflow-hidden rounded-xl border border-border bg-surface-secondary">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-3.5 font-semibold text-brand-dark transition-colors hover:bg-page [&::-webkit-details-marker]:hidden">
              <span>View role assignment evidence</span>

              <span
                aria-hidden="true"
                className="text-lg leading-none text-muted transition-transform group-open:rotate-45"
              >
                +
              </span>
            </summary>

            <div className="border-t border-border px-5 py-4">
              <p className="text-xs leading-5 text-muted">
                Supporting model evidence used to interpret the player&apos;s
                tactical and spatial role.
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
