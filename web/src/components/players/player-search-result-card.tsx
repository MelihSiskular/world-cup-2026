"use client";

import {
  useQueryClient,
} from "@tanstack/react-query";
import Link from "next/link";

import {
  CountryFlag,
} from "@/components/players/country-flag";
import {
  PlayerImage,
} from "@/components/players/player-image";
import {
  ShortlistAction,
} from "@/components/shortlists/shortlist-action";
import {
  fetchPlayerProfile,
} from "@/lib/api/browser-players";
import type {
  PlayerSearchItemResponse,
} from "@/lib/api/types";
import {
  createShortlistSnapshotFromSearchPlayer,
} from "@/lib/shortlists/snapshot";

const positionLabels:
  Record<string, string> = {
    G: "Goalkeeper",
    D: "Defender",
    M: "Midfielder",
    F: "Forward",
  };

function formatPosition(
  position: string | null,
): string {
  if (!position) {
    return "Position unavailable";
  }

  return (
    positionLabels[position] ??
    position
  );
}

function formatAge(
  age: number | null,
): string {
  if (age === null) {
    return "Age unavailable";
  }

  return `${new Intl.NumberFormat(
    "en",
    {
      maximumFractionDigits: 0,
    },
  ).format(age)} years`;
}

function formatMarketValue(
  value: number | null,
  currency: string | null,
): string {
  if (
    value === null ||
    !currency
  ) {
    return "Market value unavailable";
  }

  try {
    return new Intl.NumberFormat(
      "en",
      {
        style: "currency",
        currency,
        notation: "compact",
        maximumFractionDigits: 1,
      },
    ).format(value);
  } catch {
    return `${value.toLocaleString("en")} ${currency}`;
  }
}

type PlayerSearchResultCardProps =
  Readonly<{
    player: PlayerSearchItemResponse;
  }>;

export function PlayerSearchResultCard({
  player,
}: PlayerSearchResultCardProps) {
  const queryClient =
    useQueryClient();

  const prefetchPlayerProfile =
    () => {
      void queryClient.prefetchQuery({
        queryKey: [
          "players",
          "profile",
          player.player_id,
        ],
        queryFn: ({
          signal,
        }) =>
          fetchPlayerProfile(
            player.player_id,
            signal,
          ),
        staleTime:
          5 * 60 * 1000,
      });
    };

  const shortlistPlayer =
    createShortlistSnapshotFromSearchPlayer(
      player,
    );

  return (
    <li className="group relative rounded-2xl border border-border bg-surface shadow-sm transition hover:-translate-y-0.5 hover:border-brand/35 hover:shadow-md">
      <Link
        href={`/players/${player.player_id}`}
        aria-label={`Open ${player.player_name} scouting profile`}
        onMouseEnter={
          prefetchPlayerProfile
        }
        onFocus={
          prefetchPlayerProfile
        }
        className="absolute inset-0 rounded-2xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
      >
        <span className="sr-only">
          Open {player.player_name} scouting
          profile
        </span>
      </Link>

      <div className="pointer-events-none p-5">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 items-start gap-4">
            <PlayerImage
              playerId={player.player_id}
              playerName={player.player_name}
              size="card"
            />

            <div className="min-w-0">
              <h2 className="min-w-0 break-words text-xl font-bold tracking-[-0.025em] transition-colors group-hover:text-brand">
                {player.player_name}
              </h2>

              <div className="mt-1 flex min-w-0 items-center gap-2">
                <CountryFlag
                  countryAlpha3={
                    player.country_alpha3
                  }
                  className="w-4"
                />

                <p className="min-w-0 break-words text-sm font-medium text-muted">
                  {player.national_team_name ??
                    "National team unavailable"}
                </p>
              </div>

              <div className="mt-4 space-y-1.5 text-sm">
                {player.final_role ? (
                  <p className="min-w-0 break-words text-base leading-6">
                    <span className="font-semibold text-brand">
                      Final role:
                    </span>{" "}
                    <span className="font-semibold text-brand-dark">
                      {player.final_role}
                    </span>
                  </p>
                ) : null}

                {player.archetype ? (
                  <p className="min-w-0 break-words">
                    <span className="font-semibold text-brand-navy">
                      Archetype:
                    </span>{" "}
                    <span className="font-medium text-foreground">
                      {player.archetype}
                    </span>
                  </p>
                ) : null}

                {player.spatial_role ? (
                  <p className="min-w-0 break-words">
                    <span className="font-semibold text-warning">
                      Spatial role:
                    </span>{" "}
                    <span className="font-medium text-foreground">
                      {player.spatial_role}
                    </span>
                  </p>
                ) : null}
              </div>
            </div>
          </div>

          <dl className="grid shrink-0 grid-cols-2 gap-x-8 gap-y-3 border-t border-border pt-4 text-sm sm:block sm:min-w-44 sm:border-t-0 sm:pt-0 sm:text-right">
            <div>
              <dt className="text-xs font-medium text-muted">
                Age
              </dt>
              <dd className="mt-1 font-semibold">
                {formatAge(
                  player.age,
                )}
              </dd>
            </div>

            <div className="sm:mt-4">
              <dt className="text-xs font-medium text-muted">
                Market value
              </dt>
              <dd className="mt-1 font-semibold text-brand-dark">
                {formatMarketValue(
                  player.market_value,
                  player.market_value_currency,
                )}
              </dd>
            </div>

            <div className="sm:mt-4">
              <dt className="text-xs font-medium text-muted">
                Position
              </dt>
              <dd className="mt-1 font-semibold">
                {formatPosition(
                  player.position,
                )}
              </dd>
            </div>
          </dl>
        </div>

        <div className="mt-5 flex flex-col gap-3 border-t border-border pt-4 sm:flex-row sm:items-center sm:justify-between">
          <span className="flex items-center gap-2 text-sm text-muted">
            Open scouting profile

            <span
              aria-hidden="true"
              className="font-semibold text-brand transition-transform group-hover:translate-x-1"
            >
              →
            </span>
          </span>

          <div className="pointer-events-auto relative z-10">
            <ShortlistAction
              player={shortlistPlayer}
              variant="compact"
            />
          </div>
        </div>
      </div>
    </li>
  );
}
