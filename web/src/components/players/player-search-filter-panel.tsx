"use client";

import {
  useLocale,
  useTranslations,
} from "next-intl";
import {
  useId,
} from "react";

import {
  CountryFlag,
} from "@/components/players/country-flag";
import type {
  PlayerSearchFilterOptionResponse,
  PlayerSearchFilterRangeResponse,
  PlayerSearchFiltersResponse,
} from "@/lib/api/types";
import {
  normalizePlayerSearchParameters,
} from "@/lib/players/search-parameters";
import type {
  PlayerSearchParameters,
  PlayerSearchSortDirection,
  PlayerSearchSortField,
} from "@/lib/players/search-parameters";

type PlayerSearchFilterPanelProps =
  Readonly<{
    metadata: PlayerSearchFiltersResponse;
    parameters: PlayerSearchParameters;
    onChange: (
      parameters: PlayerSearchParameters,
    ) => void;
    onClear: () => void;
    className?: string;
  }>;

type OptionChecklistProps =
  Readonly<{
    label: string;
    options:
      readonly PlayerSearchFilterOptionResponse[];
    selectedValues: readonly string[];
    onToggle: (value: string) => void;
    defaultOpen?: boolean;
    showCountryFlags?: boolean;
    formatLabel?: (
      option:
        PlayerSearchFilterOptionResponse,
    ) => string;
  }>;

type NumericInputProps =
  Readonly<{
    label: string;
    value: number | undefined;
    onChange: (
      value: number | undefined,
    ) => void;
    minimum?: number;
    maximum?: number;
    step?: number;
    placeholder?: string;
    suffix?: string;
    scale?: number;
  }>;

function activeFilterCount(
  parameters: PlayerSearchParameters,
): number {
  const normalized =
    normalizePlayerSearchParameters(
      parameters,
    );

  return (
    normalized.positions.length +
    normalized.finalRoles.length +
    normalized.archetypes.length +
    normalized.countries.length +
    [
      normalized.minimumAge,
      normalized.maximumAge,
      normalized.minimumMarketValue,
      normalized.maximumMarketValue,
      normalized.minimumMinutes,
      normalized.minimumRoleConfidence,
      normalized.minimumDataReliability,
    ].filter(
      (value) =>
        value !== undefined,
    ).length
  );
}

function formatOptionLabel(
  option:
    PlayerSearchFilterOptionResponse,
): string {
  return option.label;
}

function formatRangeValue(
  value: number | null,
  locale: string,
  options: Readonly<{
    suffix?: string;
    divisor?: number;
  }> = {},
): string {
  if (value === null) {
    return "—";
  }

  const displayedValue =
    value /
    (options.divisor ?? 1);

  return `${displayedValue.toLocaleString(
    locale,
    {
      maximumFractionDigits:
        Math.abs(displayedValue) < 1
          ? 2
          : 1,
    },
  )}${options.suffix ?? ""}`;
}

function formatRange(
  range:
    PlayerSearchFilterRangeResponse,
  locale: string,
  options: Readonly<{
    suffix?: string;
    divisor?: number;
  }> = {},
): string {
  return `${formatRangeValue(
    range.minimum,
    locale,
    options,
  )}–${formatRangeValue(
    range.maximum,
    locale,
    options,
  )}`;
}

function parseNumericInput(
  value: string,
  scale: number,
): number | undefined {
  if (!value.trim()) {
    return undefined;
  }

  const parsedValue =
    Number(value);

  if (
    !Number.isFinite(parsedValue)
  ) {
    return undefined;
  }

  return parsedValue * scale;
}

function OptionChecklist({
  label,
  options,
  selectedValues,
  onToggle,
  defaultOpen = false,
  showCountryFlags = false,
  formatLabel = formatOptionLabel,
}: OptionChecklistProps) {
  const translations =
    useTranslations(
      "PlayerDiscovery",
    );
  const descriptionId = useId();

  return (
    <details
      className="group border-t border-border first:border-t-0"
      open={defaultOpen || undefined}
    >
      <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 py-3 text-sm font-semibold [&::-webkit-details-marker]:hidden">
        <span>{label}</span>

        <span className="flex items-center gap-2">
          {selectedValues.length > 0 ? (
            <span className="rounded-full bg-brand/10 px-2 py-0.5 text-[11px] font-semibold text-brand">
              {selectedValues.length}
            </span>
          ) : null}

          <span
            aria-hidden="true"
            className="text-base leading-none text-muted transition-transform group-open:rotate-45"
          >
            +
          </span>
        </span>
      </summary>

      <p
        id={descriptionId}
        className="sr-only"
      >
        {translations(
          "optionChecklistDescription",
        )}
      </p>

      <fieldset
        aria-describedby={descriptionId}
        className="max-h-56 space-y-1 overflow-y-auto pb-4 pr-1"
      >
        <legend className="sr-only">
          {label}
        </legend>

        {options.map(
          (option) => {
            const checked =
              selectedValues.includes(
                option.value,
              );

            return (
              <label
                key={option.value}
                className={[
                  "flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border px-3 py-2 text-sm transition-colors",
                  checked
                    ? "border-brand/30 bg-brand/10"
                    : "border-transparent hover:bg-surface-secondary",
                ].join(" ")}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  aria-label={
                    translations(
                      "filterOptionCount",
                      {
                        label:
                          formatLabel(
                            option,
                          ),
                        count:
                          option.count,
                      },
                    )
                  }
                  onChange={() => {
                    onToggle(
                      option.value,
                    );
                  }}
                  className="size-4 shrink-0 accent-brand"
                />

                {showCountryFlags ? (
                  <CountryFlag
                    countryAlpha3={
                      option.country_alpha3
                    }
                    className="w-4"
                  />
                ) : null}

                <span className="min-w-0 flex-1 break-words font-medium">
                  {formatLabel(
                    option,
                  )}
                </span>

                <span className="shrink-0 text-xs text-muted">
                  {option.count}
                </span>
              </label>
            );
          },
        )}
      </fieldset>
    </details>
  );
}

function NumericInput({
  label,
  value,
  onChange,
  minimum,
  maximum,
  step = 1,
  placeholder,
  suffix,
  scale = 1,
}: NumericInputProps) {
  const inputId = useId();

  const displayedValue =
    value === undefined
      ? ""
      : value / scale;

  return (
    <div>
      <label
        htmlFor={inputId}
        className="text-xs font-semibold text-muted"
      >
        {label}
      </label>

      <div className="relative mt-1.5">
        <input
          id={inputId}
          type="number"
          inputMode="decimal"
          value={displayedValue}
          min={minimum}
          max={maximum}
          step={step}
          placeholder={placeholder}
          onChange={(event) => {
            onChange(
              parseNumericInput(
                event.target.value,
                scale,
              ),
            );
          }}
          className={[
            "min-h-11 w-full rounded-xl border border-border bg-page px-3 py-2 text-sm font-semibold outline-none transition",
            "hover:border-brand/40 focus:border-brand focus:bg-surface",
            suffix ? "pr-10" : "",
          ].join(" ")}
        />

        {suffix ? (
          <span className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-xs font-semibold text-muted">
            {suffix}
          </span>
        ) : null}
      </div>
    </div>
  );
}

export function PlayerSearchFilterPanel({
  metadata,
  parameters,
  onChange,
  onClear,
  className = "",
}: PlayerSearchFilterPanelProps) {
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

  const filterCount =
    activeFilterCount(
      normalized,
    );

  function update(
    patch:
      Partial<PlayerSearchParameters>,
  ): void {
    onChange({
      ...normalized,
      ...patch,
      offset: 0,
    });
  }

  function toggleValue(
    key:
      | "positions"
      | "finalRoles"
      | "archetypes"
      | "countries",
    value: string,
  ): void {
    const selectedValues =
      normalized[key];

    update({
      [key]:
        selectedValues.includes(
          value,
        )
          ? selectedValues.filter(
              (selectedValue) =>
                selectedValue !==
                value,
            )
          : [
              ...selectedValues,
              value,
            ],
    });
  }

  const selectedSort =
    normalized.sortBy &&
    normalized.sortDirection
      ? `${normalized.sortBy}:${normalized.sortDirection}`
      : "recommended";

  return (
    <section
      aria-labelledby="advanced-player-filters-title"
      className={[
        "rounded-3xl border border-border bg-surface p-5 shadow-sm",
        className,
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
            {translations("filterEyebrow")}
          </p>

          <h2
            id="advanced-player-filters-title"
            className="mt-2 text-lg font-bold tracking-[-0.025em]"
          >
            {translations("advancedFilters")}
          </h2>

          <p className="mt-1 text-xs leading-5 text-muted">
            {translations(
              "catalogueSummary",
              {
                count:
                  metadata.player_count,
              },
            )}
          </p>
        </div>

        {filterCount > 0 ? (
          <span className="shrink-0 rounded-full bg-brand/10 px-2.5 py-1 text-xs font-semibold text-brand">
            {translations(
              "activeFilterCount",
              {
                count:
                  filterCount,
              },
            )}
          </span>
        ) : null}
      </div>

      <div className="mt-5 border-y border-border">
        <OptionChecklist
          label={translations("position")}
          options={metadata.positions}
          selectedValues={
            normalized.positions
          }
          onToggle={(value) => {
            toggleValue(
              "positions",
              value,
            );
          }}
          defaultOpen
          formatLabel={(
            option,
          ) =>
            positionLabels[
              option.value
            ] ??
            option.label
          }
        />

        <OptionChecklist
          label={translations("finalRole")}
          options={metadata.final_roles}
          selectedValues={
            normalized.finalRoles
          }
          onToggle={(value) => {
            toggleValue(
              "finalRoles",
              value,
            );
          }}
        />

        <OptionChecklist
          label={translations("archetype")}
          options={metadata.archetypes}
          selectedValues={
            normalized.archetypes
          }
          onToggle={(value) => {
            toggleValue(
              "archetypes",
              value,
            );
          }}
        />

        <OptionChecklist
          label={translations("nationality")}
          options={metadata.countries}
          selectedValues={
            normalized.countries
          }
          onToggle={(value) => {
            toggleValue(
              "countries",
              value,
            );
          }}
          showCountryFlags
        />

        <details className="group border-t border-border">
          <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 py-3 text-sm font-semibold [&::-webkit-details-marker]:hidden">
            <span>
              {translations("recruitmentCriteria")}
            </span>

            <span
              aria-hidden="true"
              className="text-base leading-none text-muted transition-transform group-open:rotate-45"
            >
              +
            </span>
          </summary>

          <div className="grid gap-3 pb-5 sm:grid-cols-2 lg:grid-cols-1">
            <div className="grid grid-cols-2 gap-3">
              <NumericInput
                label={translations("minimumAge")}
                value={
                  normalized.minimumAge
                }
                minimum={
                  metadata.age.minimum ??
                  undefined
                }
                maximum={
                  metadata.age.maximum ??
                  undefined
                }
                step={0.1}
                placeholder={translations("minimumPlaceholder")}
                onChange={(value) => {
                  update({
                    minimumAge:
                      value,
                  });
                }}
              />

              <NumericInput
                label={translations("maximumAge")}
                value={
                  normalized.maximumAge
                }
                minimum={
                  metadata.age.minimum ??
                  undefined
                }
                maximum={
                  metadata.age.maximum ??
                  undefined
                }
                step={0.1}
                placeholder={translations("maximumPlaceholder")}
                onChange={(value) => {
                  update({
                    maximumAge:
                      value,
                  });
                }}
              />
            </div>

            <p className="-mt-1 text-[11px] text-muted sm:col-span-2 lg:col-span-1">
              {translations(
                "ageRange",
                {
                  range:
                    formatRange(
                      metadata.age,
                      locale,
                    ),
                },
              )}
            </p>

            <div className="grid grid-cols-2 gap-3">
              <NumericInput
                label={translations("minimumValue")}
                value={
                  normalized.minimumMarketValue
                }
                minimum={
                  metadata.market_value.minimum ===
                  null
                    ? undefined
                    : metadata.market_value.minimum /
                      1_000_000
                }
                maximum={
                  metadata.market_value.maximum ===
                  null
                    ? undefined
                    : metadata.market_value.maximum /
                      1_000_000
                }
                step={0.1}
                placeholder={translations("minimumPlaceholder")}
                suffix="€M"
                scale={1_000_000}
                onChange={(value) => {
                  update({
                    minimumMarketValue:
                      value,
                  });
                }}
              />

              <NumericInput
                label={translations("maximumValue")}
                value={
                  normalized.maximumMarketValue
                }
                minimum={
                  metadata.market_value.minimum ===
                  null
                    ? undefined
                    : metadata.market_value.minimum /
                      1_000_000
                }
                maximum={
                  metadata.market_value.maximum ===
                  null
                    ? undefined
                    : metadata.market_value.maximum /
                      1_000_000
                }
                step={0.1}
                placeholder={translations("maximumPlaceholder")}
                suffix="€M"
                scale={1_000_000}
                onChange={(value) => {
                  update({
                    maximumMarketValue:
                      value,
                  });
                }}
              />
            </div>

            <p
              aria-label={
                translations(
                  "marketValueRangeLabel",
                )
              }
              className="-mt-1 text-[11px] text-muted sm:col-span-2 lg:col-span-1"
            >
              {translations(
                "valueRange",
                {
                  range:
                    formatRange(
                      metadata.market_value,
                      locale,
                      {
                        suffix: "M",
                        divisor:
                          1_000_000,
                      },
                    ),
                  currency:
                    metadata.market_value_currency ??
                    "",
                },
              )}
            </p>

            <NumericInput
              label={translations("minimumTournamentMinutes")}
              value={
                normalized.minimumMinutes
              }
              minimum={
                metadata.minutes.minimum ??
                undefined
              }
              maximum={
                metadata.minutes.maximum ??
                undefined
              }
              step={30}
              placeholder={translations("minutesExample")}
              onChange={(value) => {
                update({
                  minimumMinutes:
                    value,
                });
              }}
            />

            <p className="-mt-1 text-[11px] text-muted sm:col-span-2 lg:col-span-1">
              {translations(
                "observedMinutesRange",
                {
                  range:
                    formatRange(
                      metadata.minutes,
                      locale,
                    ),
                },
              )}
            </p>

            <NumericInput
              label={translations("minimumRoleConfidence")}
              value={
                normalized.minimumRoleConfidence
              }
              minimum={
                metadata.role_confidence.minimum ??
                undefined
              }
              maximum={
                metadata.role_confidence.maximum ??
                undefined
              }
              step={1}
              placeholder={translations("roleConfidenceExample")}
              suffix="%"
              onChange={(value) => {
                update({
                  minimumRoleConfidence:
                    value,
                });
              }}
            />

            <NumericInput
              label={translations("minimumDataReliability")}
              value={
                normalized.minimumDataReliability
              }
              minimum={
                metadata.data_reliability.minimum ??
                undefined
              }
              maximum={
                metadata.data_reliability.maximum ??
                undefined
              }
              step={1}
              placeholder={translations("dataReliabilityExample")}
              suffix="%"
              onChange={(value) => {
                update({
                  minimumDataReliability:
                    value,
                });
              }}
            />
          </div>
        </details>
      </div>

      <div className="mt-5">
        <label
          htmlFor="player-search-sort"
          className="text-xs font-semibold text-muted"
        >
          {translations("sortResults")}
        </label>

        <select
          id="player-search-sort"
          value={selectedSort}
          onChange={(event) => {
            if (
              event.target.value ===
              "recommended"
            ) {
              update({
                sortBy:
                  undefined,
                sortDirection:
                  undefined,
              });
              return;
            }

            const [
              sortBy,
              sortDirection,
            ] =
              event.target.value.split(
                ":",
              ) as [
                PlayerSearchSortField,
                PlayerSearchSortDirection,
              ];

            update({
              sortBy,
              sortDirection,
            });
          }}
          className="mt-1.5 min-h-11 w-full rounded-xl border border-border bg-page px-3 py-2 text-sm font-semibold outline-none transition hover:border-brand/40 focus:border-brand focus:bg-surface"
        >
          <option value="recommended">
            {translations("sortRecommended")}
          </option>
          <option value="player_name:asc">
            {translations("sortPlayerName")}
          </option>
          <option value="age:asc">
            {translations("sortYoungest")}
          </option>
          <option value="market_value:asc">
            {translations("sortLowestValue")}
          </option>
          <option value="minutes:desc">
            {translations("sortMostMinutes")}
          </option>
          <option value="role_confidence:desc">
            {translations("sortHighestRoleConfidence")}
          </option>
          <option value="data_reliability:desc">
            {translations("sortHighestDataReliability")}
          </option>
          <option value="player_quality:desc">
            {translations("sortHighestPlayerQuality")}
          </option>
        </select>
      </div>

      <button
        type="button"
        onClick={onClear}
        disabled={filterCount === 0}
        aria-label={translations("clearAllFilters")}
        className="mt-4 min-h-11 w-full rounded-xl border border-border bg-surface px-4 py-2 text-sm font-semibold text-brand-dark transition-colors enabled:hover:bg-surface-secondary disabled:cursor-not-allowed disabled:opacity-45"
      >
        {translations("clearAll")}
      </button>
    </section>
  );
}
