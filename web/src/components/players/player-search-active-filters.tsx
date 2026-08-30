"use client";

import {
  useLocale,
  useTranslations,
} from "next-intl";

import type {
  PlayerSearchFilterOptionResponse,
  PlayerSearchFiltersResponse,
} from "@/lib/api/types";
import {
  normalizePlayerSearchParameters,
} from "@/lib/players/search-parameters";
import type {
  PlayerSearchParameters,
} from "@/lib/players/search-parameters";

type PlayerSearchActiveFiltersProps =
  Readonly<{
    metadata: PlayerSearchFiltersResponse;
    parameters: PlayerSearchParameters;
    onChange: (
      parameters: PlayerSearchParameters,
    ) => void;
    onClear: () => void;
  }>;

type ActiveFilter =
  Readonly<{
    key: string;
    label: string;
    nextParameters:
      PlayerSearchParameters;
  }>;

function findOptionLabel(
  options:
    readonly PlayerSearchFilterOptionResponse[],
  value: string,
): string {
  return (
    options.find(
      (option) =>
        option.value === value,
    )?.label ?? value
  );
}

function formatNumber(
  value: number,
  locale: string,
): string {
  return value.toLocaleString(
    locale,
    {
      maximumFractionDigits: 1,
    },
  );
}

function formatMarketValue(
  value: number,
  locale: string,
): string {
  if (
    Math.abs(value) >=
    1_000_000
  ) {
    return `€${(
      value / 1_000_000
    ).toLocaleString(locale, {
      maximumFractionDigits: 1,
    })}M`;
  }

  if (
    Math.abs(value) >= 1_000
  ) {
    return `€${(
      value / 1_000
    ).toLocaleString(locale, {
      maximumFractionDigits: 0,
    })}K`;
  }

  return `€${value.toLocaleString(
    locale,
  )}`;
}

export function PlayerSearchActiveFilters({
  metadata,
  parameters,
  onChange,
  onClear,
}: PlayerSearchActiveFiltersProps) {
  const locale =
    useLocale();
  const translations =
    useTranslations(
      "PlayerDiscovery",
    );

  const positionLabels:
    Readonly<Record<string, string>> = {
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
    };

  const normalized =
    normalizePlayerSearchParameters(
      parameters,
    );

  const filters:
    ActiveFilter[] = [];

  for (
    const value of
    normalized.positions
  ) {
    filters.push({
      key: `position:${value}`,
      label:
        translations(
          "positionFilter",
          {
            value:
              positionLabels[value] ??
              findOptionLabel(
                metadata.positions,
                value,
              ),
          },
        ),
      nextParameters: {
        ...normalized,
        positions:
          normalized.positions.filter(
            (selectedValue) =>
              selectedValue !==
              value,
          ),
        offset: 0,
      },
    });
  }

  for (
    const value of
    normalized.finalRoles
  ) {
    filters.push({
      key: `final-role:${value}`,
      label:
        translations(
          "finalRoleFilter",
          {
            value:
              findOptionLabel(
                metadata.final_roles,
                value,
              ),
          },
        ),
      nextParameters: {
        ...normalized,
        finalRoles:
          normalized.finalRoles.filter(
            (selectedValue) =>
              selectedValue !==
              value,
          ),
        offset: 0,
      },
    });
  }

  for (
    const value of
    normalized.archetypes
  ) {
    filters.push({
      key: `archetype:${value}`,
      label:
        translations(
          "archetypeFilter",
          {
            value:
              findOptionLabel(
                metadata.archetypes,
                value,
              ),
          },
        ),
      nextParameters: {
        ...normalized,
        archetypes:
          normalized.archetypes.filter(
            (selectedValue) =>
              selectedValue !==
              value,
          ),
        offset: 0,
      },
    });
  }

  for (
    const value of
    normalized.countries
  ) {
    filters.push({
      key: `country:${value}`,
      label:
        translations(
          "nationalityFilter",
          {
            value:
              findOptionLabel(
                metadata.countries,
                value,
              ),
          },
        ),
      nextParameters: {
        ...normalized,
        countries:
          normalized.countries.filter(
            (selectedValue) =>
              selectedValue !==
              value,
          ),
        offset: 0,
      },
    });
  }

  if (
    normalized.minimumAge !==
    undefined
  ) {
    filters.push({
      key: "minimum-age",
      label:
        translations(
          "minimumAgeFilter",
          {
            value:
              formatNumber(
                normalized.minimumAge,
                locale,
              ),
          },
        ),
      nextParameters: {
        ...normalized,
        minimumAge: undefined,
        offset: 0,
      },
    });
  }

  if (
    normalized.maximumAge !==
    undefined
  ) {
    filters.push({
      key: "maximum-age",
      label:
        translations(
          "maximumAgeFilter",
          {
            value:
              formatNumber(
                normalized.maximumAge,
                locale,
              ),
          },
        ),
      nextParameters: {
        ...normalized,
        maximumAge: undefined,
        offset: 0,
      },
    });
  }

  if (
    normalized.minimumMarketValue !==
    undefined
  ) {
    filters.push({
      key: "minimum-market-value",
      label:
        translations(
          "minimumValueFilter",
          {
            value:
              formatMarketValue(
                normalized.minimumMarketValue,
                locale,
              ),
          },
        ),
      nextParameters: {
        ...normalized,
        minimumMarketValue:
          undefined,
        offset: 0,
      },
    });
  }

  if (
    normalized.maximumMarketValue !==
    undefined
  ) {
    filters.push({
      key: "maximum-market-value",
      label:
        translations(
          "maximumValueFilter",
          {
            value:
              formatMarketValue(
                normalized.maximumMarketValue,
                locale,
              ),
          },
        ),
      nextParameters: {
        ...normalized,
        maximumMarketValue:
          undefined,
        offset: 0,
      },
    });
  }

  if (
    normalized.minimumMinutes !==
    undefined
  ) {
    filters.push({
      key: "minimum-minutes",
      label:
        translations(
          "minimumMinutesFilter",
          {
            value:
              formatNumber(
                normalized.minimumMinutes,
                locale,
              ),
          },
        ),
      nextParameters: {
        ...normalized,
        minimumMinutes: undefined,
        offset: 0,
      },
    });
  }

  if (
    normalized.minimumRoleConfidence !==
    undefined
  ) {
    filters.push({
      key: "minimum-role-confidence",
      label:
        translations(
          "minimumRoleConfidenceFilter",
          {
            value:
              formatNumber(
                normalized.minimumRoleConfidence,
                locale,
              ),
          },
        ),
      nextParameters: {
        ...normalized,
        minimumRoleConfidence:
          undefined,
        offset: 0,
      },
    });
  }

  if (
    normalized.minimumDataReliability !==
    undefined
  ) {
    filters.push({
      key: "minimum-data-reliability",
      label:
        translations(
          "minimumDataReliabilityFilter",
          {
            value:
              formatNumber(
                normalized.minimumDataReliability,
                locale,
              ),
          },
        ),
      nextParameters: {
        ...normalized,
        minimumDataReliability:
          undefined,
        offset: 0,
      },
    });
  }

  if (filters.length === 0) {
    return null;
  }

  return (
    <section
      aria-labelledby="active-player-filters-title"
      className="mb-4 rounded-2xl border border-border bg-surface px-4 py-4 shadow-sm"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2
          id="active-player-filters-title"
          className="text-xs font-semibold tracking-[0.12em] text-muted uppercase"
        >
          {translations(
            "activeFiltersTitle",
          )}
        </h2>

        <button
          type="button"
          onClick={onClear}
          className="min-h-10 rounded-xl px-3 py-2 text-xs font-semibold text-brand-dark transition-colors hover:bg-surface-secondary"
        >
          {translations(
            "clearFilters",
          )}
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {filters.map(
          (filter) => (
            <button
              key={filter.key}
              type="button"
              aria-label={
                translations(
                  "removeFilter",
                  {
                    label:
                      filter.label,
                  },
                )
              }
              onClick={() => {
                onChange(
                  filter.nextParameters,
                );
              }}
              className="inline-flex min-h-10 max-w-full items-center gap-2 rounded-full border border-brand/20 bg-brand/10 px-3 py-2 text-left text-xs font-semibold text-brand-dark transition-colors hover:border-brand/35 hover:bg-brand/15"
            >
              <span className="min-w-0 break-words">
                {filter.label}
              </span>

              <span
                aria-hidden="true"
                className="shrink-0 text-base leading-none"
              >
                ×
              </span>
            </button>
          ),
        )}
      </div>
    </section>
  );
}
