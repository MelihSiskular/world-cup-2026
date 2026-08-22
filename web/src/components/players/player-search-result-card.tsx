"use client";

import {
  useQueryClient,
} from "@tanstack/react-query";
import Link from "next/link";

import {
  fetchPlayerProfile,
} from "@/lib/api/browser-players";
import type {
  PlayerSearchItemResponse,
} from "@/lib/api/types";

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
      maximumFractionDigits: 1,
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

  return (
    <li>
      <Link
        href={`/players/${player.player_id}`}
        onMouseEnter={
          prefetchPlayerProfile
        }
        onFocus={
          prefetchPlayerProfile
        }
        className="group block rounded-2xl border border-border bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-brand/35 hover:shadow-md"
      >
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-surface-secondary px-2.5 py-1 text-xs font-semibold text-brand-dark">
                {formatPosition(
                  player.position,
                )}
              </span>

              <span className="text-xs text-muted">
                Player ID{" "}
                {player.player_id}
              </span>
            </div>

            <h2 className="mt-4 break-words text-xl font-bold tracking-[-0.025em] transition-colors group-hover:text-brand">
              {player.player_name}
            </h2>

            <p className="mt-1 break-words text-sm font-medium text-muted">
              {player.national_team_name ??
                "National team unavailable"}
            </p>

            <div className="mt-5 flex flex-wrap gap-2">
              {player.final_role ? (
                <span className="max-w-full break-words rounded-lg border border-border bg-page px-3 py-1.5 text-xs font-medium">
                  {player.final_role}
                </span>
              ) : null}

              {player.archetype ? (
                <span className="max-w-full break-words rounded-lg border border-border bg-page px-3 py-1.5 text-xs font-medium text-muted">
                  {player.archetype}
                </span>
              ) : null}
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
          </dl>
        </div>

        <div className="mt-5 flex items-center justify-between border-t border-border pt-4 text-sm">
          <span className="text-muted">
            Open scouting profile
          </span>

          <span
            aria-hidden="true"
            className="font-semibold text-brand transition-transform group-hover:translate-x-1"
          >
            →
          </span>
        </div>
      </Link>
    </li>
  );
}
