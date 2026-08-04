import type {
  DeploymentIdentityResponse,
  HealthResponse,
  ReadinessResponse,
} from "@/lib/api/types";

type RequestJsonOptions =
  Readonly<{
    signal?: AbortSignal;
    acceptedStatuses?: readonly number[];
  }>;

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

async function requestJson<T>(
  path: string,
  options: RequestJsonOptions = {},
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

export function fetchApiHealth(
  signal?: AbortSignal,
): Promise<HealthResponse> {
  return requestJson<HealthResponse>(
    "/api/status/health",
    {
      signal,
    },
  );
}

export function fetchApiReadiness(
  signal?: AbortSignal,
): Promise<ReadinessResponse> {
  return requestJson<ReadinessResponse>(
    "/api/status/ready",
    {
      signal,
      acceptedStatuses: [503],
    },
  );
}

export function fetchDeploymentIdentity(
  signal?: AbortSignal,
): Promise<DeploymentIdentityResponse> {
  return requestJson<DeploymentIdentityResponse>(
    "/api/status/deployment",
    {
      signal,
    },
  );
}
