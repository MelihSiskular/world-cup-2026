import Link from "next/link";

import type {
  PlayerProfileResponse,
} from "@/lib/api/types";
import {
  formatMarketValue,
  formatPlayerPosition,
  formatProfileNumber,
  formatProfilePercentage,
  formatUnitIntervalPercentage,
} from "@/lib/players/profile-format";

type PlayerProfileViewProps =
  Readonly<{
    player: PlayerProfileResponse;
  }>;

type MetricCardProps =
  Readonly<{
    label: string;
    value: string;
    description: string;
  }>;

function getPlayerInitials(
  playerName: string,
): string {
  return playerName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function MetricCard({
  label,
  value,
  description,
}: MetricCardProps) {
  return (
    <article className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
      <p className="text-sm font-semibold text-muted">
        {label}
      </p>

      <p className="mt-3 text-3xl font-bold tracking-[-0.04em]">
        {value}
      </p>

      <p className="mt-2 text-xs leading-5 text-muted">
        {description}
      </p>
    </article>
  );
}

function DetailRow({
  label,
  value,
}: Readonly<{
  label: string;
  value: string;
}>) {
  return (
    <div className="flex items-start justify-between gap-6 border-b border-border py-3 last:border-b-0">
      <dt className="text-sm text-muted">
        {label}
      </dt>

      <dd className="text-right text-sm font-semibold">
        {value}
      </dd>
    </div>
  );
}

export function PlayerProfileView({
  player,
}: PlayerProfileViewProps) {
  const roleReasonParts =
    player.role_reason
      ?.split("|")
      .map((part) => part.trim())
      .filter(Boolean) ?? [];

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-3xl border border-border bg-surface shadow-sm">
        <div className="grid lg:grid-cols-[minmax(0,1fr)_19rem]">
          <div className="p-6 sm:p-8">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
              <div className="flex size-18 shrink-0 items-center justify-center rounded-2xl bg-brand-dark text-xl font-bold text-white">
                {getPlayerInitials(
                  player.player_name,
                )}
              </div>

              <div className="min-w-0">
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full bg-surface-secondary px-3 py-1.5 text-xs font-semibold text-brand-dark">
                    {formatPlayerPosition(
                      player.position,
                    )}
                  </span>

                  <span className="rounded-full border border-border px-3 py-1.5 text-xs font-semibold text-muted">
                    {player.national_team_name ??
                      "National team unavailable"}
                  </span>

                  <span className="rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted">
                    ID {player.player_id}
                  </span>
                </div>

                <h1 className="mt-5 break-words text-4xl font-bold tracking-[-0.045em] sm:text-5xl">
                  {player.player_name}
                </h1>

                <p className="mt-3 break-words text-lg font-medium text-brand">
                  {player.final_role ??
                    "Final role unavailable"}
                </p>

                <p className="mt-2 break-words text-sm text-muted">
                  {player.archetype ??
                    "Archetype unavailable"}
                  {" · "}
                  {player.spatial_role ??
                    "Spatial role unavailable"}
                </p>
              </div>
            </div>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href={`/analysis/${player.player_id}`}
                className="inline-flex min-h-12 items-center justify-center rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-dark"
              >
                Run transfer analysis
              </Link>

              <Link
                href="/players"
                className="inline-flex min-h-12 items-center justify-center rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold transition-colors hover:bg-surface-secondary"
              >
                Back to player search
              </Link>
            </div>
          </div>

          <aside className="border-t border-border bg-surface-secondary p-6 lg:border-t-0 lg:border-l">
            <p className="text-sm font-semibold text-muted">
              Estimated market value
            </p>

            <p className="mt-3 text-3xl font-bold tracking-[-0.04em] text-brand-dark">
              {formatMarketValue(
                player.market_value,
                player.market_value_currency,
              )}
            </p>

            <dl className="mt-7">
              <DetailRow
                label="Age"
                value={
                  player.age === null
                    ? "Not reported"
                    : `${formatProfileNumber(
                        player.age,
                        {
                          maximumFractionDigits: 1,
                        },
                      )} years`
                }
              />

              <DetailRow
                label="Height"
                value={
                  player.height_cm === null
                    ? "Not reported"
                    : `${formatProfileNumber(
                        player.height_cm,
                      )} cm`
                }
              />

              <DetailRow
                label="Country"
                value={
                  player.country_name ??
                  "Not reported"
                }
              />
            </dl>
          </aside>
        </div>
      </section>

      <section
        aria-label="Player profile scores"
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        <MetricCard
          label="Weighted rating"
          value={formatProfileNumber(
            player.weighted_rating,
            {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            },
          )}
          description="Reliability-aware tournament performance rating"
        />

        <MetricCard
          label="Player quality"
          value={formatProfilePercentage(
            player.player_quality_score,
          )}
          description="Combined performance-quality assessment"
        />

        <MetricCard
          label="Data reliability"
          value={formatProfilePercentage(
            player.data_reliability_score,
          )}
          description="Confidence supported by available tournament data"
        />

        <MetricCard
          label="Role confidence"
          value={formatProfilePercentage(
            player.role_confidence_pct,
          )}
          description="Confidence in the assigned tactical role"
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <article className="rounded-2xl border border-border bg-surface p-6 shadow-sm sm:p-7">
          <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
            Role interpretation
          </p>

          <h2 className="mt-3 text-2xl font-bold tracking-[-0.03em]">
            How the player operates
          </h2>

          <div className="mt-7 grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-border bg-page p-4">
              <p className="text-xs font-semibold text-muted">
                Statistical archetype
              </p>

              <p className="mt-2 font-bold">
                {player.archetype ??
                  "Not reported"}
              </p>
            </div>

            <div className="rounded-xl border border-border bg-page p-4">
              <p className="text-xs font-semibold text-muted">
                Spatial role
              </p>

              <p className="mt-2 font-bold">
                {player.spatial_role ??
                  "Not reported"}
              </p>
            </div>

            <div className="rounded-xl border border-border bg-page p-4">
              <p className="text-xs font-semibold text-muted">
                Final role
              </p>

              <p className="mt-2 font-bold">
                {player.final_role ??
                  "Not reported"}
              </p>
            </div>
          </div>

          <dl className="mt-7 rounded-xl border border-border px-5">
            <DetailRow
              label="Lateral profile"
              value={
                player.lateral_profile ??
                "Not reported"
              }
            />

            <DetailRow
              label="Vertical profile"
              value={
                player.vertical_profile ??
                "Not reported"
              }
            />

            <DetailRow
              label="Mobility profile"
              value={
                player.mobility_profile ??
                "Not reported"
              }
            />

            <DetailRow
              label="Spatial reliability"
              value={formatUnitIntervalPercentage(
                player.spatial_reliability,
              )}
            />
          </dl>

          {roleReasonParts.length > 0 ? (
            <div className="mt-7 rounded-xl border border-brand/20 bg-surface-secondary p-5">
              <h3 className="font-bold text-brand-dark">
                Role assignment evidence
              </h3>

              <ul className="mt-4 space-y-3 text-sm leading-6 text-muted">
                {roleReasonParts.map(
                  (reason) => (
                    <li
                      key={reason}
                      className="flex gap-3"
                    >
                      <span
                        aria-hidden="true"
                        className="mt-2 size-1.5 shrink-0 rounded-full bg-brand"
                      />

                      <span>{reason}</span>
                    </li>
                  ),
                )}
              </ul>
            </div>
          ) : null}
        </article>

        <aside className="h-fit rounded-2xl border border-border bg-surface p-6 shadow-sm lg:sticky lg:top-24">
          <p className="text-sm font-semibold tracking-[0.15em] text-brand uppercase">
            Tournament context
          </p>

          <h2 className="mt-3 text-xl font-bold tracking-[-0.025em]">
            Sample and participation
          </h2>

          <dl className="mt-6">
            <DetailRow
              label="Appearances"
              value={formatProfileNumber(
                player.appearances,
              )}
            />

            <DetailRow
              label="Starts"
              value={formatProfileNumber(
                player.starts,
              )}
            />

            <DetailRow
              label="Minutes"
              value={formatProfileNumber(
                player.minutes,
              )}
            />

            <DetailRow
              label="Start rate"
              value={
                player.appearances &&
                player.starts !== null
                  ? formatProfilePercentage(
                      (
                        player.starts /
                        player.appearances
                      ) * 100,
                    )
                  : "Not reported"
              }
            />
          </dl>

          <div className="mt-6 rounded-xl bg-surface-secondary p-4">
            <p className="text-xs font-semibold text-brand-dark">
              Analysis boundary
            </p>

            <p className="mt-2 text-xs leading-5 text-muted">
              Tournament performance is a
              decision-support sample and
              should be combined with club,
              league and long-term scouting
              context.
            </p>
          </div>
        </aside>
      </section>
    </div>
  );
}
