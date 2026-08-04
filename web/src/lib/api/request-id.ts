export const REQUEST_ID_HEADER =
  "x-request-id";

const VALID_REQUEST_ID_PATTERN =
  /^[A-Za-z0-9._:-]{1,128}$/;

function normalizeRequestId(
  value: string | null,
): string | null {
  const normalizedValue = value?.trim();

  if (
    !normalizedValue ||
    !VALID_REQUEST_ID_PATTERN.test(
      normalizedValue,
    )
  ) {
    return null;
  }

  return normalizedValue;
}

export function getOrCreateRequestId(
  headers: Headers,
): string {
  return (
    normalizeRequestId(
      headers.get(REQUEST_ID_HEADER),
    ) ?? crypto.randomUUID()
  );
}

export function getResponseRequestId(
  response: Response,
  fallbackRequestId: string,
): string {
  return (
    normalizeRequestId(
      response.headers.get(
        REQUEST_ID_HEADER,
      ),
    ) ?? fallbackRequestId
  );
}
