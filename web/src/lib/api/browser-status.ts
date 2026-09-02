import {
  requestBrowserJson,
} from "@/lib/api/browser-client";
import type {
  HealthResponse,
  ReadinessResponse,
} from "@/lib/api/types";

export function fetchApiHealth(
  signal?: AbortSignal,
): Promise<HealthResponse> {
  return requestBrowserJson<HealthResponse>(
    "/api/status/health",
    {
      signal,
    },
  );
}

export function fetchApiReadiness(
  signal?: AbortSignal,
): Promise<ReadinessResponse> {
  return requestBrowserJson<ReadinessResponse>(
    "/api/status/ready",
    {
      signal,
      acceptedStatuses: [503],
    },
  );
}
