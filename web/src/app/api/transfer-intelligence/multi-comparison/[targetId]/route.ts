import { getOrCreateRequestId } from "@/lib/api/request-id";
import {
  createRequestErrorResponse,
  handleOpenApiRequest,
} from "@/lib/api/route-handler";
import { createWc26ServerClient } from "@/lib/api/server-client";
import type {
  MultiPlayerComparisonPath,
  MultiPlayerComparisonQuery,
} from "@/lib/api/types";
import { parseMultiComparisonIdentifiers } from "@/lib/transfer-intelligence/multi-comparison-selection";

type MultiPlayerComparisonRouteContext = Readonly<{
  params: Promise<{
    targetId: string;
  }>;
}>;

export async function GET(
  request: Request,
  context: MultiPlayerComparisonRouteContext,
): Promise<Response> {
  const requestId = getOrCreateRequestId(request.headers);

  const { targetId: rawTargetId } = await context.params;

  const requestUrl = new URL(request.url);

  const validation = parseMultiComparisonIdentifiers(
    rawTargetId,
    requestUrl.searchParams.getAll("candidates"),
  );

  if (!validation.success) {
    return createRequestErrorResponse(requestId, validation.message);
  }

  const roleMetricScope = requestUrl.searchParams.get("role_metric_scope");

  if (
    roleMetricScope !== null &&
    roleMetricScope !== "target" &&
    roleMetricScope !== "all_players"
  ) {
    return createRequestErrorResponse(
      requestId,
      "Role metric scope must be target or all_players.",
    );
  }

  const path: MultiPlayerComparisonPath = {
    target_player_id: validation.values.targetPlayerId,
  };

  const query: MultiPlayerComparisonQuery = {
    candidate_player_ids: validation.values.candidatePlayerIds,
    role_metric_scope: roleMetricScope ?? "target",
  };

  return handleOpenApiRequest(requestId, async () => {
    const client = createWc26ServerClient({
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
  });
}
