import {
  getOrCreateRequestId,
} from "@/lib/api/request-id";
import {
  createRequestErrorResponse,
  handleOpenApiRequest,
} from "@/lib/api/route-handler";
import {
  createWc26ServerClient,
} from "@/lib/api/server-client";
import type {
  PlayerSearchQuery,
} from "@/lib/api/types";
import {
  MINIMUM_PLAYER_SEARCH_LENGTH,
} from "@/lib/players/search-config";
import {
  PLAYER_SEARCH_SORT_DIRECTIONS,
  PLAYER_SEARCH_SORT_FIELDS,
} from "@/lib/players/search-parameters";

const MINIMUM_LIMIT = 1;
const MAXIMUM_LIMIT = 25;

type NumberConstraints =
  Readonly<{
    integer?: boolean;
    minimum?: number;
    maximum?: number;
  }>;

function parseOptionalNumber(
  searchParameters: URLSearchParams,
  name: string,
  constraints: NumberConstraints = {},
): number | null | undefined {
  const source =
    searchParameters.get(name);

  if (source === null) {
    return undefined;
  }

  if (!source.trim()) {
    return null;
  }

  const value = Number(source);

  if (
    !Number.isFinite(value) ||
    (
      constraints.integer &&
      !Number.isSafeInteger(value)
    ) ||
    (
      constraints.minimum !==
        undefined &&
      value < constraints.minimum
    ) ||
    (
      constraints.maximum !==
        undefined &&
      value > constraints.maximum
    )
  ) {
    return null;
  }

  return value;
}

function readRepeatedValues(
  searchParameters: URLSearchParams,
  name: string,
): readonly string[] {
  return [
    ...new Set(
      searchParameters
        .getAll(name)
        .map((value) =>
          value
            .trim()
            .replaceAll(
              /\s+/g,
              " ",
            ),
        )
        .filter(Boolean),
    ),
  ];
}

function invalidNumberResponse(
  requestId: string,
): Response {
  return createRequestErrorResponse(
    requestId,
    "One or more numeric player filters are invalid.",
  );
}

export async function GET(
  request: Request,
): Promise<Response> {
  const requestId =
    getOrCreateRequestId(
      request.headers,
    );

  const requestUrl =
    new URL(request.url);

  const queryValue =
    requestUrl.searchParams
      .get("q")
      ?.trim()
      .replaceAll(
        /\s+/g,
        " ",
      ) || undefined;

  if (
    queryValue !== undefined &&
    queryValue.length <
      MINIMUM_PLAYER_SEARCH_LENGTH
  ) {
    return createRequestErrorResponse(
      requestId,
      `A player search query must contain at least ${MINIMUM_PLAYER_SEARCH_LENGTH} characters.`,
    );
  }

  const positions =
    readRepeatedValues(
      requestUrl.searchParams,
      "position",
    );
  const finalRoles =
    readRepeatedValues(
      requestUrl.searchParams,
      "final_role",
    );
  const archetypes =
    readRepeatedValues(
      requestUrl.searchParams,
      "archetype",
    );
  const countries =
    readRepeatedValues(
      requestUrl.searchParams,
      "country",
    );

  const minimumAge =
    parseOptionalNumber(
      requestUrl.searchParams,
      "min_age",
      {
        minimum: 0,
      },
    );
  const maximumAge =
    parseOptionalNumber(
      requestUrl.searchParams,
      "max_age",
      {
        minimum: 0,
      },
    );
  const minimumMarketValue =
    parseOptionalNumber(
      requestUrl.searchParams,
      "min_market_value",
      {
        minimum: 0,
      },
    );
  const maximumMarketValue =
    parseOptionalNumber(
      requestUrl.searchParams,
      "max_market_value",
      {
        minimum: 0,
      },
    );
  const minimumMinutes =
    parseOptionalNumber(
      requestUrl.searchParams,
      "min_minutes",
      {
        minimum: 0,
      },
    );
  const minimumRoleConfidence =
    parseOptionalNumber(
      requestUrl.searchParams,
      "min_role_confidence",
      {
        minimum: 0,
        maximum: 100,
      },
    );
  const minimumDataReliability =
    parseOptionalNumber(
      requestUrl.searchParams,
      "min_data_reliability",
      {
        minimum: 0,
        maximum: 100,
      },
    );
  const offset =
    parseOptionalNumber(
      requestUrl.searchParams,
      "offset",
      {
        integer: true,
        minimum: 0,
      },
    );
  const limit =
    parseOptionalNumber(
      requestUrl.searchParams,
      "limit",
      {
        integer: true,
        minimum: MINIMUM_LIMIT,
        maximum: MAXIMUM_LIMIT,
      },
    );

  if (
    minimumAge === null ||
    maximumAge === null ||
    minimumMarketValue === null ||
    maximumMarketValue === null ||
    minimumMinutes === null ||
    minimumRoleConfidence === null ||
    minimumDataReliability === null ||
    offset === null ||
    limit === null
  ) {
    return invalidNumberResponse(
      requestId,
    );
  }

  if (
    minimumAge !== undefined &&
    maximumAge !== undefined &&
    minimumAge > maximumAge
  ) {
    return createRequestErrorResponse(
      requestId,
      "Minimum age cannot exceed maximum age.",
    );
  }

  if (
    minimumMarketValue !==
      undefined &&
    maximumMarketValue !==
      undefined &&
    minimumMarketValue >
      maximumMarketValue
  ) {
    return createRequestErrorResponse(
      requestId,
      "Minimum market value cannot exceed maximum market value.",
    );
  }

  const sortBy =
    requestUrl.searchParams
      .get("sort_by")
      ?.trim() || undefined;

  const sortDirection =
    requestUrl.searchParams
      .get("sort_direction")
      ?.trim() || undefined;

  const allowedSortFields:
    ReadonlySet<string> =
      new Set(
        PLAYER_SEARCH_SORT_FIELDS,
      );

  const allowedSortDirections:
    ReadonlySet<string> =
      new Set(
        PLAYER_SEARCH_SORT_DIRECTIONS,
      );

  if (
    sortBy !== undefined &&
    !allowedSortFields.has(
      sortBy,
    )
  ) {
    return createRequestErrorResponse(
      requestId,
      "The player sort field is invalid.",
    );
  }

  if (
    sortDirection !== undefined &&
    !allowedSortDirections.has(
      sortDirection,
    )
  ) {
    return createRequestErrorResponse(
      requestId,
      "The player sort direction is invalid.",
    );
  }

  const hasFilter =
    positions.length > 0 ||
    finalRoles.length > 0 ||
    archetypes.length > 0 ||
    countries.length > 0 ||
    minimumAge !== undefined ||
    maximumAge !== undefined ||
    minimumMarketValue !==
      undefined ||
    maximumMarketValue !==
      undefined ||
    minimumMinutes !== undefined ||
    minimumRoleConfidence !==
      undefined ||
    minimumDataReliability !==
      undefined;

  if (
    queryValue === undefined &&
    !hasFilter
  ) {
    return createRequestErrorResponse(
      requestId,
      "A player name or at least one scouting filter is required.",
    );
  }

  const query: PlayerSearchQuery = {
    ...(queryValue
      ? {
          q: queryValue,
        }
      : {}),
    ...(positions.length
      ? {
          position: positions,
        }
      : {}),
    ...(finalRoles.length
      ? {
          final_role: finalRoles,
        }
      : {}),
    ...(archetypes.length
      ? {
          archetype: archetypes,
        }
      : {}),
    ...(countries.length
      ? {
          country: countries,
        }
      : {}),
    ...(minimumAge !== undefined
      ? {
          min_age: minimumAge,
        }
      : {}),
    ...(maximumAge !== undefined
      ? {
          max_age: maximumAge,
        }
      : {}),
    ...(minimumMarketValue !==
    undefined
      ? {
          min_market_value:
            minimumMarketValue,
        }
      : {}),
    ...(maximumMarketValue !==
    undefined
      ? {
          max_market_value:
            maximumMarketValue,
        }
      : {}),
    ...(minimumMinutes !==
    undefined
      ? {
          min_minutes:
            minimumMinutes,
        }
      : {}),
    ...(minimumRoleConfidence !==
    undefined
      ? {
          min_role_confidence:
            minimumRoleConfidence,
        }
      : {}),
    ...(minimumDataReliability !==
    undefined
      ? {
          min_data_reliability:
            minimumDataReliability,
        }
      : {}),
    ...(sortBy
      ? {
          sort_by: sortBy,
        }
      : {}),
    ...(sortDirection
      ? {
          sort_direction:
            sortDirection,
        }
      : {}),
    ...(offset !== undefined
      ? {
          offset,
        }
      : {}),
    ...(limit !== undefined
      ? {
          limit,
        }
      : {}),
  };

  return handleOpenApiRequest(
    requestId,
    async () => {
      const client =
        createWc26ServerClient({
          requestId,
        });

      return client.GET(
        "/api/v1/players/search",
        {
          params: {
            query,
          },
        },
      );
    },
  );
}
