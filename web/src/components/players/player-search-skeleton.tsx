"use client";

import {
  useTranslations,
} from "next-intl";

export function PlayerSearchSkeleton() {
  const translations =
    useTranslations(
      "PlayerDiscovery",
    );
  return (
    <div
      className="space-y-4"
      role="status"
      aria-live="polite"
      aria-label={
        translations(
          "searchingPlayers",
        )
      }
    >
      {Array.from({
        length: 4,
      }).map((_, index) => (
        <div
          key={index}
          className="animate-pulse rounded-2xl border border-border bg-surface p-5"
        >
          <div className="h-5 w-24 rounded bg-surface-secondary" />
          <div className="mt-5 h-6 w-52 rounded bg-surface-secondary" />
          <div className="mt-3 h-4 w-32 rounded bg-surface-secondary" />

          <div className="mt-6 flex gap-3">
            <div className="h-8 w-40 rounded bg-surface-secondary" />
            <div className="h-8 w-32 rounded bg-surface-secondary" />
          </div>
        </div>
      ))}

      <span className="sr-only">
        {translations(
          "searchingCatalogue",
        )}
      </span>
    </div>
  );
}
