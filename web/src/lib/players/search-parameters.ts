import {
  DEFAULT_PLAYER_SEARCH_LIMIT,
} from "@/lib/players/search-config";

export const PLAYER_SEARCH_SORT_FIELDS = [
  "relevance",
  "player_name",
  "age",
  "market_value",
  "minutes",
  "role_confidence",
  "data_reliability",
  "player_quality",
] as const;

export const PLAYER_SEARCH_SORT_DIRECTIONS = [
  "asc",
  "desc",
] as const;

export type PlayerSearchSortField =
  (typeof PLAYER_SEARCH_SORT_FIELDS)[number];

export type PlayerSearchSortDirection =
  (typeof PLAYER_SEARCH_SORT_DIRECTIONS)[number];

export type PlayerSearchParameters =
  Readonly<{
    query?: string;
    positions?: readonly string[];
    finalRoles?: readonly string[];
    archetypes?: readonly string[];
    countries?: readonly string[];
    minimumAge?: number;
    maximumAge?: number;
    minimumMarketValue?: number;
    maximumMarketValue?: number;
    minimumMinutes?: number;
    minimumRoleConfidence?: number;
    minimumDataReliability?: number;
    sortBy?: PlayerSearchSortField;
    sortDirection?: PlayerSearchSortDirection;
    offset?: number;
    limit?: number;
  }>;

export type NormalizedPlayerSearchParameters =
  Readonly<{
    query: string;
    positions: readonly string[];
    finalRoles: readonly string[];
    archetypes: readonly string[];
    countries: readonly string[];
    minimumAge?: number;
    maximumAge?: number;
    minimumMarketValue?: number;
    maximumMarketValue?: number;
    minimumMinutes?: number;
    minimumRoleConfidence?: number;
    minimumDataReliability?: number;
    sortBy?: PlayerSearchSortField;
    sortDirection?: PlayerSearchSortDirection;
    offset: number;
    limit: number;
  }>;

function normalizeValues(
  values: readonly string[] | undefined,
): readonly string[] {
  const normalized = new Map<
    string,
    string
  >();

  for (const value of values ?? []) {
    const displayValue =
      value.trim().replaceAll(
        /\s+/g,
        " ",
      );

    if (!displayValue) {
      continue;
    }

    const identity =
      displayValue.toLocaleLowerCase(
        "en",
      );

    if (!normalized.has(identity)) {
      normalized.set(
        identity,
        displayValue,
      );
    }
  }

  return [
    ...normalized.values(),
  ].sort((left, right) =>
    left.localeCompare(
      right,
      "en",
      {
        sensitivity: "base",
      },
    ),
  );
}

function normalizeOptionalNumber(
  value: number | undefined,
): number | undefined {
  if (
    value === undefined ||
    !Number.isFinite(value)
  ) {
    return undefined;
  }

  return value;
}

export function normalizePlayerSearchParameters(
  parameters: PlayerSearchParameters,
): NormalizedPlayerSearchParameters {
  const query =
    parameters.query
      ?.trim()
      .replaceAll(
        /\s+/g,
        " ",
      ) ?? "";

  const offset =
    Number.isSafeInteger(
      parameters.offset,
    ) &&
    (parameters.offset ?? 0) >= 0
      ? parameters.offset ?? 0
      : 0;

  const limit =
    Number.isSafeInteger(
      parameters.limit,
    ) &&
    (parameters.limit ?? 0) >= 1 &&
    (parameters.limit ?? 0) <= 25
      ? parameters.limit ??
        DEFAULT_PLAYER_SEARCH_LIMIT
      : DEFAULT_PLAYER_SEARCH_LIMIT;

  return {
    query,
    positions: normalizeValues(
      parameters.positions,
    ),
    finalRoles: normalizeValues(
      parameters.finalRoles,
    ),
    archetypes: normalizeValues(
      parameters.archetypes,
    ),
    countries: normalizeValues(
      parameters.countries,
    ),
    minimumAge:
      normalizeOptionalNumber(
        parameters.minimumAge,
      ),
    maximumAge:
      normalizeOptionalNumber(
        parameters.maximumAge,
      ),
    minimumMarketValue:
      normalizeOptionalNumber(
        parameters.minimumMarketValue,
      ),
    maximumMarketValue:
      normalizeOptionalNumber(
        parameters.maximumMarketValue,
      ),
    minimumMinutes:
      normalizeOptionalNumber(
        parameters.minimumMinutes,
      ),
    minimumRoleConfidence:
      normalizeOptionalNumber(
        parameters.minimumRoleConfidence,
      ),
    minimumDataReliability:
      normalizeOptionalNumber(
        parameters.minimumDataReliability,
      ),
    sortBy: parameters.sortBy,
    sortDirection:
      parameters.sortDirection,
    offset,
    limit,
  };
}

function appendValues(
  searchParameters: URLSearchParams,
  name: string,
  values: readonly string[],
): void {
  for (const value of values) {
    searchParameters.append(
      name,
      value,
    );
  }
}

function appendNumber(
  searchParameters: URLSearchParams,
  name: string,
  value: number | undefined,
): void {
  if (value === undefined) {
    return;
  }

  searchParameters.set(
    name,
    String(value),
  );
}

export function createPlayerSearchUrlParameters(
  parameters: PlayerSearchParameters,
): URLSearchParams {
  const normalized =
    normalizePlayerSearchParameters(
      parameters,
    );

  const searchParameters =
    new URLSearchParams();

  if (normalized.query) {
    searchParameters.set(
      "q",
      normalized.query,
    );
  }

  appendValues(
    searchParameters,
    "position",
    normalized.positions,
  );
  appendValues(
    searchParameters,
    "final_role",
    normalized.finalRoles,
  );
  appendValues(
    searchParameters,
    "archetype",
    normalized.archetypes,
  );
  appendValues(
    searchParameters,
    "country",
    normalized.countries,
  );

  appendNumber(
    searchParameters,
    "min_age",
    normalized.minimumAge,
  );
  appendNumber(
    searchParameters,
    "max_age",
    normalized.maximumAge,
  );
  appendNumber(
    searchParameters,
    "min_market_value",
    normalized.minimumMarketValue,
  );
  appendNumber(
    searchParameters,
    "max_market_value",
    normalized.maximumMarketValue,
  );
  appendNumber(
    searchParameters,
    "min_minutes",
    normalized.minimumMinutes,
  );
  appendNumber(
    searchParameters,
    "min_role_confidence",
    normalized.minimumRoleConfidence,
  );
  appendNumber(
    searchParameters,
    "min_data_reliability",
    normalized.minimumDataReliability,
  );

  if (normalized.sortBy) {
    searchParameters.set(
      "sort_by",
      normalized.sortBy,
    );
  }

  if (normalized.sortDirection) {
    searchParameters.set(
      "sort_direction",
      normalized.sortDirection,
    );
  }

  if (normalized.offset > 0) {
    searchParameters.set(
      "offset",
      String(
        normalized.offset,
      ),
    );
  }

  searchParameters.set(
    "limit",
    String(
      normalized.limit,
    ),
  );

  return searchParameters;
}

export function createPlayerSearchPageUrlParameters(
  parameters: PlayerSearchParameters,
): URLSearchParams {
  const searchParameters =
    createPlayerSearchUrlParameters(
      parameters,
    );

  if (
    searchParameters.get(
      "limit",
    ) ===
    String(
      DEFAULT_PLAYER_SEARCH_LIMIT,
    )
  ) {
    searchParameters.delete(
      "limit",
    );
  }

  return searchParameters;
}

function readOptionalNumber(
  searchParameters: URLSearchParams,
  name: string,
): number | undefined {
  const value =
    searchParameters.get(name);

  if (
    value === null ||
    !value.trim()
  ) {
    return undefined;
  }

  const parsed = Number(value);

  return Number.isFinite(parsed)
    ? parsed
    : undefined;
}

function readSortField(
  value: string | null,
): PlayerSearchSortField | undefined {
  return PLAYER_SEARCH_SORT_FIELDS.find(
    (candidate) =>
      candidate === value,
  );
}

function readSortDirection(
  value: string | null,
): PlayerSearchSortDirection | undefined {
  return PLAYER_SEARCH_SORT_DIRECTIONS.find(
    (candidate) =>
      candidate === value,
  );
}

export function readPlayerSearchUrlParameters(
  searchParameters: URLSearchParams,
): NormalizedPlayerSearchParameters {
  return normalizePlayerSearchParameters({
    query:
      searchParameters.get("q") ??
      undefined,
    positions:
      searchParameters.getAll(
        "position",
      ),
    finalRoles:
      searchParameters.getAll(
        "final_role",
      ),
    archetypes:
      searchParameters.getAll(
        "archetype",
      ),
    countries:
      searchParameters.getAll(
        "country",
      ),
    minimumAge:
      readOptionalNumber(
        searchParameters,
        "min_age",
      ),
    maximumAge:
      readOptionalNumber(
        searchParameters,
        "max_age",
      ),
    minimumMarketValue:
      readOptionalNumber(
        searchParameters,
        "min_market_value",
      ),
    maximumMarketValue:
      readOptionalNumber(
        searchParameters,
        "max_market_value",
      ),
    minimumMinutes:
      readOptionalNumber(
        searchParameters,
        "min_minutes",
      ),
    minimumRoleConfidence:
      readOptionalNumber(
        searchParameters,
        "min_role_confidence",
      ),
    minimumDataReliability:
      readOptionalNumber(
        searchParameters,
        "min_data_reliability",
      ),
    sortBy: readSortField(
      searchParameters.get(
        "sort_by",
      ),
    ),
    sortDirection:
      readSortDirection(
        searchParameters.get(
          "sort_direction",
        ),
      ),
    offset:
      readOptionalNumber(
        searchParameters,
        "offset",
      ),
    limit:
      readOptionalNumber(
        searchParameters,
        "limit",
      ),
  });
}

export function hasPlayerSearchCriteria(
  parameters: PlayerSearchParameters,
): boolean {
  const normalized =
    normalizePlayerSearchParameters(
      parameters,
    );

  return Boolean(
    normalized.query ||
      normalized.positions.length ||
      normalized.finalRoles.length ||
      normalized.archetypes.length ||
      normalized.countries.length ||
      normalized.minimumAge !==
        undefined ||
      normalized.maximumAge !==
        undefined ||
      normalized.minimumMarketValue !==
        undefined ||
      normalized.maximumMarketValue !==
        undefined ||
      normalized.minimumMinutes !==
        undefined ||
      normalized.minimumRoleConfidence !==
        undefined ||
      normalized.minimumDataReliability !==
        undefined,
  );
}

export function createPlayerSearchQueryKey(
  parameters: PlayerSearchParameters,
): readonly [
  "players",
  "search",
  string,
] {
  return [
    "players",
    "search",
    createPlayerSearchUrlParameters(
      parameters,
    ).toString(),
  ];
}
