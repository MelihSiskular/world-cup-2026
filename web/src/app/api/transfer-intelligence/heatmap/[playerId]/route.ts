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

type HeatmapPlayerRouteContext =
  Readonly<{
    params: Promise<{
      playerId: string;
    }>;
  }>;

function parsePlayerId(
  value: string,
): number | null {
  const parsedValue = Number(value);

  if (
    !Number.isSafeInteger(parsedValue) ||
    parsedValue <= 0
  ) {
    return null;
  }

  return parsedValue;
}

export async function GET(
  request: Request,
  context: HeatmapPlayerRouteContext,
): Promise<Response> {
  const requestId =
    getOrCreateRequestId(
      request.headers,
    );

  const { playerId: rawPlayerId } =
    await context.params;

  const playerId =
    parsePlayerId(rawPlayerId);

  if (playerId === null) {
    return createRequestErrorResponse(
      requestId,
      "The player ID must be a positive integer.",
    );
  }

  return handleOpenApiRequest(
    requestId,
    async () => {
      const client =
        createWc26ServerClient({
          requestId,
        });

      return client.GET(
        "/api/v1/transfer-intelligence/heatmap/{player_id}",
        {
          params: {
            path: {
              player_id: playerId,
            },
          },
        },
      );
    },
  );
}
