"use client";

import {
  useQuery,
} from "@tanstack/react-query";
import {
  useTranslations,
} from "next-intl";

import {
  ApiErrorReference,
} from "@/components/feedback/api-error-reference";
import {
  PlayerProfileSkeleton,
} from "@/components/players/player-profile-skeleton";
import {
  PlayerSpatialProfile,
} from "@/components/players/player-spatial-profile";
import {
  PlayerProfileView,
} from "@/components/players/player-profile-view";
import {
  isBrowserApiError,
} from "@/lib/api/browser-client";
import {
  fetchPlayerProfile,
} from "@/lib/api/browser-players";
import {
  Link,
} from "@/i18n/navigation";
import {
  fetchPlayerHeatmap,
} from "@/lib/api/browser-transfer-intelligence";

type PlayerProfileProps =
  Readonly<{
    playerId: number;
  }>;

export function PlayerProfile({
  playerId,
}: PlayerProfileProps) {
  const translations =
    useTranslations(
      "PlayerProfile",
    );

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
      staleTime: 5 * 60 * 1000,
      retry: (
        failureCount,
        error,
      ) => {
        if (
          isBrowserApiError(error) &&
          error.status === 404
        ) {
          return false;
        }

        return failureCount < 1;
      },
    });

  const playerHeatmap =
    useQuery({
      queryKey: [
        "transfer-intelligence",
        "heatmap",
        playerId,
      ],
      queryFn: ({
        signal,
      }) =>
        fetchPlayerHeatmap(
          playerId,
          signal,
        ),
      enabled: playerProfile.isSuccess,
      staleTime: 5 * 60 * 1000,
      retry: (
        failureCount,
        error,
      ) => {
        if (
          isBrowserApiError(error) &&
          error.status === 404
        ) {
          return false;
        }

        return failureCount < 1;
      },
    });

  if (playerProfile.isPending) {
    return (
      <PlayerProfileSkeleton
        label={translations(
          "loadingProfile",
        )}
      />
    );
  }

  if (playerProfile.isError) {
    const playerNotFound =
      isBrowserApiError(
        playerProfile.error,
      ) &&
      playerProfile.error.status === 404;

    return (
      <section
        className={[
          "rounded-2xl border p-7 shadow-sm",
          playerNotFound
            ? "border-border bg-surface"
            : "border-error/25 bg-error/10",
        ].join(" ")}
        role="alert"
      >
        <p
          className={[
            "text-sm font-semibold tracking-[0.14em] uppercase",
            playerNotFound
              ? "text-brand"
              : "text-error",
          ].join(" ")}
        >
          {translations(
            playerNotFound
              ? "notFoundEyebrow"
              : "unavailableEyebrow",
          )}
        </p>

        <h1 className="mt-3 text-3xl font-bold tracking-[-0.035em]">
          {translations(
            playerNotFound
              ? "notFoundTitle"
              : "loadFailedTitle",
          )}
        </h1>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">
          {translations(
            playerNotFound
              ? "notFoundDescription"
              : "loadFailedDescription",
          )}
        </p>

        <ApiErrorReference
          error={playerProfile.error}
        />

        <div className="mt-7 flex flex-wrap gap-3">
          {!playerNotFound ? (
            <button
              type="button"
              onClick={() => {
                void playerProfile.refetch();
              }}
              className="rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-dark"
            >
              {translations(
                "retryProfile",
              )}
            </button>
          ) : null}

          <Link
            href="/players"
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold transition-colors hover:bg-surface-secondary"
          >
            {translations(
              "returnToSearch",
            )}
          </Link>
        </div>
      </section>
    );
  }

  return (
    <PlayerProfileView
      player={playerProfile.data}
      spatialProfile={
        <PlayerSpatialProfile
          playerName={
            playerProfile.data.player_name
          }
          heatmap={
            playerHeatmap.data ?? null
          }
          isPending={
            playerHeatmap.isPending
          }
          isError={
            playerHeatmap.isError
          }
          onRetry={() => {
            void playerHeatmap.refetch();
          }}
        />
      }
    />
  );
}
