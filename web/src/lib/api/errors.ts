import type {
  ApiErrorResponse,
  HttpValidationError,
  NormalizedApiError,
  ValidationError,
  WebApiErrorCode,
  WebApiErrorResponse,
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

function isValidationError(
  value: unknown,
): value is ValidationError {
  if (!isRecord(value)) {
    return false;
  }

  return (
    Array.isArray(value.loc) &&
    typeof value.msg === "string" &&
    typeof value.type === "string"
  );
}

export function isApiErrorResponse(
  value: unknown,
): value is ApiErrorResponse {
  if (!isRecord(value)) {
    return false;
  }

  const error = value.error;

  if (!isRecord(error)) {
    return false;
  }

  return (
    typeof error.code === "string" &&
    typeof error.message === "string"
  );
}

export function isHttpValidationError(
  value: unknown,
): value is HttpValidationError {
  if (!isRecord(value)) {
    return false;
  }

  if (value.detail === undefined) {
    return true;
  }

  return (
    Array.isArray(value.detail) &&
    value.detail.every(isValidationError)
  );
}

export function createWebApiError(
  code: WebApiErrorCode,
  message: string,
): WebApiErrorResponse {
  return {
    error: {
      code,
      message,
    },
  };
}

function formatValidationMessage(
  error: HttpValidationError,
): string {
  const messages = error.detail
    ?.map((item) => item.msg.trim())
    .filter(Boolean);

  if (!messages?.length) {
    return "The request could not be validated.";
  }

  return messages
    .slice(0, 3)
    .join(" ");
}

export function normalizeUpstreamError(
  body: unknown,
  status: number,
): NormalizedApiError {
  if (isApiErrorResponse(body)) {
    return body;
  }

  if (isHttpValidationError(body)) {
    return createWebApiError(
      "validation_error",
      formatValidationMessage(body),
    );
  }

  return createWebApiError(
    "invalid_upstream_response",
    `The analytics API returned HTTP ${status} without a recognized error response.`,
  );
}
