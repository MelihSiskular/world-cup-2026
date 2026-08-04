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

const MINIMUM_LIMIT = 1;
const MAXIMUM_LIMIT = 25;

function parseLimit(
  value: string | null,
): number | undefined {
  if (value === null) {
    return undefined;
  }

  const parsedValue = Number(value);

  if (
    !Number.isSafeInteger(parsedValue) ||
    parsedValue < MINIMUM_LIMIT ||
    parsedValue > MAXIMUM_LIMIT
  ) {
    return Number.NaN;
  }

  return parsedValue;
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
      ?.trim() ?? "";

  if (!queryValue) {
    return createRequestErrorResponse(
      requestId,
      "A player search query is required.",
    );
  }

  const limit = parseLimit(
    requestUrl.searchParams.get(
      "limit",
    ),
  );

  if (
    limit !== undefined &&
    Number.isNaN(limit)
  ) {
    return createRequestErrorResponse(
      requestId,
      "The result limit must be an integer between 1 and 25.",
    );
  }

  const query: PlayerSearchQuery =
    limit === undefined
      ? {
          q: queryValue,
        }
      : {
          q: queryValue,
          limit,
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
