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
  MultiPlayerComparisonPath,
  MultiPlayerComparisonQuery,
} from "@/lib/api/types";
import {
  parseMultiComparisonIdentifiers,
} from "@/lib/transfer-intelligence/multi-comparison-selection";

type MultiPlayerComparisonRouteContext =
  Readonly<{
    params: Promise<{
      targetId: string;
    }>;
  }>;

export async function GET(
  request: Request,
  context:
    MultiPlayerComparisonRouteContext,
): Promise<Response> {
  const requestId =
    getOrCreateRequestId(
      request.headers,
    );

  const {
    targetId: rawTargetId,
  } = await context.params;

  const requestUrl =
    new URL(request.url);

  const validation =
    parseMultiComparisonIdentifiers(
      rawTargetId,
      requestUrl.searchParams.getAll(
        "candidates",
      ),
    );

  if (!validation.success) {
    return createRequestErrorResponse(
      requestId,
      validation.message,
    );
  }

  const path:
    MultiPlayerComparisonPath = {
      target_player_id:
        validation.values
          .targetPlayerId,
    };

  const query:
    MultiPlayerComparisonQuery = {
      candidate_player_ids:
        validation.values
          .candidatePlayerIds,
    };

  return handleOpenApiRequest(
    requestId,
    async () => {
      const client =
        createWc26ServerClient({
          requestId,
        });

      return client.GET(
        "/api/v1/transfer-intelligence/multi-comparison/{target_player_id}",
        {
          params: {
            path,
            query,
          },
        },
      );
    },
  );
}
