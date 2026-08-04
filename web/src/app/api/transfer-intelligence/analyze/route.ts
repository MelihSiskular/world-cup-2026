import {
  ANALYSIS_API_TIMEOUT_MS,
} from "@/lib/api/config";
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
  TransferAnalysisPayload,
} from "@/lib/api/types";

type UnknownRecord =
  Record<string, unknown>;

function isRecord(
  value: unknown,
): value is UnknownRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

export async function POST(
  request: Request,
): Promise<Response> {
  const requestId =
    getOrCreateRequestId(
      request.headers,
    );

  const contentType =
    request.headers
      .get("content-type")
      ?.toLowerCase() ?? "";

  if (
    !contentType.includes(
      "application/json",
    )
  ) {
    return createRequestErrorResponse(
      requestId,
      "The request body must use application/json.",
      {
        status: 415,
      },
    );
  }

  let parsedBody: unknown;

  try {
    parsedBody =
      await request.json();
  } catch {
    return createRequestErrorResponse(
      requestId,
      "The request body contains invalid JSON.",
    );
  }

  if (!isRecord(parsedBody)) {
    return createRequestErrorResponse(
      requestId,
      "The transfer analysis request must be a JSON object.",
    );
  }

  const payload =
    parsedBody as TransferAnalysisPayload;

  return handleOpenApiRequest(
    requestId,
    async () => {
      const client =
        createWc26ServerClient({
          requestId,
          timeoutMs:
            ANALYSIS_API_TIMEOUT_MS,
        });

      return client.POST(
        "/api/v1/transfer-intelligence/analyze",
        {
          body: payload,
        },
      );
    },
  );
}
