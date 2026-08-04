import "server-only";

import {
  createWebApiError,
  normalizeUpstreamError,
} from "@/lib/api/errors";
import {
  getResponseRequestId,
  REQUEST_ID_HEADER,
} from "@/lib/api/request-id";
import type {
  WebApiErrorCode,
} from "@/lib/api/types";

type OpenApiFetchResult = Readonly<{
  data?: unknown;
  error?: unknown;
  response: Response;
}>;

type HandleOpenApiRequestOptions =
  Readonly<{
    preserveNonSuccessBody?: boolean;
  }>;

const JSON_RESPONSE_HEADERS = {
  "cache-control": "no-store",
  "content-type": "application/json; charset=utf-8",
  "x-content-type-options": "nosniff",
} as const;

function createJsonResponse(
  body: unknown,
  status: number,
  requestId: string,
): Response {
  const headers = new Headers(
    JSON_RESPONSE_HEADERS,
  );

  headers.set(
    REQUEST_ID_HEADER,
    requestId,
  );

  return Response.json(body, {
    status,
    headers,
  });
}

function isTimeoutError(
  error: unknown,
): boolean {
  if (
    error instanceof DOMException &&
    (
      error.name === "AbortError" ||
      error.name === "TimeoutError"
    )
  ) {
    return true;
  }

  return (
    error instanceof Error &&
    (
      error.name === "AbortError" ||
      error.name === "TimeoutError" ||
      error.message
        .toLowerCase()
        .includes("timed out")
    )
  );
}

function logProxyFailure(
  error: unknown,
  requestId: string,
): void {
  const errorName =
    error instanceof Error
      ? error.name
      : "UnknownError";

  const errorMessage =
    error instanceof Error
      ? error.message
      : "Unknown route-handler error.";

  console.error(
    JSON.stringify({
      event: "wc26_web_api_proxy_failed",
      request_id: requestId,
      error_name: errorName,
      error_message: errorMessage,
    }),
  );
}

export function createRequestErrorResponse(
  requestId: string,
  message: string,
  options: Readonly<{
    code?: WebApiErrorCode;
    status?: number;
  }> = {},
): Response {
  return createJsonResponse(
    createWebApiError(
      options.code ?? "invalid_request",
      message,
    ),
    options.status ?? 400,
    requestId,
  );
}

export async function handleOpenApiRequest(
  requestId: string,
  operation: () => Promise<OpenApiFetchResult>,
  options: HandleOpenApiRequestOptions = {},
): Promise<Response> {
  try {
    const result = await operation();

    const responseRequestId =
      getResponseRequestId(
        result.response,
        requestId,
      );

    if (result.response.ok) {
      if (result.data === undefined) {
        return createJsonResponse(
          createWebApiError(
            "invalid_upstream_response",
            "The analytics API returned an empty success response.",
          ),
          502,
          responseRequestId,
        );
      }

      return createJsonResponse(
        result.data,
        result.response.status,
        responseRequestId,
      );
    }

    if (
      options.preserveNonSuccessBody &&
      result.error !== undefined
    ) {
      return createJsonResponse(
        result.error,
        result.response.status,
        responseRequestId,
      );
    }

    const normalizedError =
      normalizeUpstreamError(
        result.error,
        result.response.status,
      );

    const responseStatus =
      normalizedError.error.code ===
      "invalid_upstream_response"
        ? 502
        : result.response.status;

    return createJsonResponse(
      normalizedError,
      responseStatus,
      responseRequestId,
    );
  } catch (error) {
    logProxyFailure(
      error,
      requestId,
    );

    if (isTimeoutError(error)) {
      return createJsonResponse(
        createWebApiError(
          "upstream_timeout",
          "The analytics API did not respond in time.",
        ),
        504,
        requestId,
      );
    }

    return createJsonResponse(
      createWebApiError(
        "upstream_unavailable",
        "The analytics API is temporarily unavailable.",
      ),
      503,
      requestId,
    );
  }
}
