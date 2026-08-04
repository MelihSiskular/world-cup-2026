type UnknownRecord =
  Record<string, unknown>;

export type BrowserRequestOptions =
  Readonly<{
    signal?: AbortSignal;
    acceptedStatuses?: readonly number[];
  }>;

function isRecord(
  value: unknown,
): value is UnknownRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function getErrorMessage(
  value: unknown,
): string | null {
  if (!isRecord(value)) {
    return null;
  }

  const error = value.error;

  if (
    !isRecord(error) ||
    typeof error.message !== "string"
  ) {
    return null;
  }

  return error.message;
}

export async function requestBrowserJson<T>(
  path: string,
  options: BrowserRequestOptions = {},
): Promise<T> {
  const response = await fetch(path, {
    headers: {
      accept: "application/json",
    },
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
    throw new Error(
      getErrorMessage(body) ??
        `The API request failed with HTTP ${response.status}.`,
    );
  }

  return body as T;
}
