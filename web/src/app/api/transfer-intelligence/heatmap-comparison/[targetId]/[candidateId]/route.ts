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
  HeatmapComparisonPath,
} from "@/lib/api/types";

type HeatmapComparisonRouteContext =
  Readonly<{
    params: Promise<{
      targetId: string;
      candidateId: string;
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
  context: HeatmapComparisonRouteContext,
): Promise<Response> {
  const requestId =
    getOrCreateRequestId(
      request.headers,
    );

  const {
    targetId: rawTargetId,
    candidateId: rawCandidateId,
  } = await context.params;

  const targetPlayerId =
    parsePlayerId(
      rawTargetId,
    );

  const candidatePlayerId =
    parsePlayerId(
      rawCandidateId,
    );

  if (
    targetPlayerId === null ||
    candidatePlayerId === null
  ) {
    return createRequestErrorResponse(
      requestId,
      "Heatmap comparison player IDs must be positive integers.",
    );
  }

  const path: HeatmapComparisonPath = {
    target_player_id:
      targetPlayerId,
    candidate_player_id:
      candidatePlayerId,
  };

  return handleOpenApiRequest(
    requestId,
    async () => {
      const client =
        createWc26ServerClient({
          requestId,
        });

      return client.GET(
        "/api/v1/transfer-intelligence/heatmap-comparison/{target_player_id}/{candidate_player_id}",
        {
          params: {
            path,
          },
        },
      );
    },
  );
}
