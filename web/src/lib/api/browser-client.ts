type UnknownRecord =
  Record<string, unknown>;

export type BrowserRequestOptions =
  Readonly<{
    signal?: AbortSignal;
    acceptedStatuses?: readonly number[];
    method?: "GET" | "POST";
    body?: unknown;
  }>;

type BrowserApiErrorOptions =
  Readonly<{
    status: number;
    code: string | null;
    message: string;
    requestId: string | null;
  }>;

export class BrowserApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly requestId: string | null;

  constructor({
    status,
    code,
    message,
    requestId,
  }: BrowserApiErrorOptions) {
    super(message);

    this.name = "BrowserApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

function isRecord(
  value: unknown,
): value is UnknownRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function getErrorDetail(
  value: unknown,
): Readonly<{
  code: string | null;
  message: string | null;
}> {
  if (!isRecord(value)) {
    return {
      code: null,
      message: null,
    };
  }

  const error = value.error;

  if (!isRecord(error)) {
    return {
      code: null,
      message: null,
    };
  }

  return {
    code:
      typeof error.code === "string"
        ? error.code
        : null,
    message:
      typeof error.message === "string"
        ? error.message
        : null,
  };
}

export function isBrowserApiError(
  error: unknown,
): error is BrowserApiError {
  return error instanceof BrowserApiError;
}

export async function requestBrowserJson<T>(
  path: string,
  options: BrowserRequestOptions = {},
): Promise<T> {
  const hasBody =
    options.body !== undefined;

  const headers:
    Record<string, string> = {
      accept: "application/json",
    };

  if (hasBody) {
    headers["content-type"] =
      "application/json";
  }

  const response = await fetch(path, {
    method:
      options.method ??
      (hasBody ? "POST" : "GET"),
    headers,
    body:
      hasBody
        ? JSON.stringify(options.body)
        : undefined,
    cache: "no-store",
    signal: options.signal,
  });

  const body: unknown =
    await response
      .json()
      .catch(() => null);

  const acceptedStatuses =
    options.acceptedStatuses ?? [];

  if (
    !response.ok &&
    !acceptedStatuses.includes(
      response.status,
    )
  ) {
    const errorDetail =
      getErrorDetail(body);

    throw new BrowserApiError({
      status: response.status,
      code: errorDetail.code,
      message:
        errorDetail.message ??
        `The API request failed with HTTP ${response.status}.`,
      requestId:
        response.headers.get(
          "x-request-id",
        ),
    });
  }

  return body as T;
}
