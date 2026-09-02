import { requestBrowserJson } from "@/lib/api/browser-client";
import { parseMultiComparisonIdentifiers } from "@/lib/transfer-intelligence/multi-comparison-selection";
import type {
  HeatmapComparisonResponse,
  HeatmapPlayerResponse,
  MultiPlayerComparisonResponse,
  RadarComparisonResponse,
  TransferAnalysisPayload,
  TransferAnalysisResponse,
} from "@/lib/api/types";

export function runTransferAnalysis(
  payload: TransferAnalysisPayload,
  signal?: AbortSignal,
): Promise<TransferAnalysisResponse> {
  return requestBrowserJson<TransferAnalysisResponse>(
    "/api/transfer-intelligence/analyze",
    {
      method: "POST",
      body: payload,
      signal,
    },
  );
}

export function fetchMultiPlayerComparison(
  targetPlayerId: number,
  candidatePlayerIds: readonly number[],
  signal?: AbortSignal,
  roleMetricScope: "target" | "all_players" = "target",
): Promise<MultiPlayerComparisonResponse> {
  const validation = parseMultiComparisonIdentifiers(
    targetPlayerId,
    candidatePlayerIds.join(","),
  );

  if (!validation.success) {
    return Promise.reject(new TypeError(validation.message));
  }

  const parameters = new URLSearchParams({
    candidates: validation.values.candidatePlayerIds.join(","),
  });

  if (roleMetricScope !== "target") {
    parameters.set("role_metric_scope", roleMetricScope);
  }

  return requestBrowserJson<MultiPlayerComparisonResponse>(
    "/api/transfer-intelligence/" +
      `multi-comparison/${validation.values.targetPlayerId}` +
      `?${parameters.toString()}`,
    {
      signal,
    },
  );
}

export function fetchPlayerHeatmap(
  playerId: number,
  signal?: AbortSignal,
): Promise<HeatmapPlayerResponse> {
  return requestBrowserJson<HeatmapPlayerResponse>(
    `/api/transfer-intelligence/heatmap/${playerId}`,
    {
      signal,
    },
  );
}

export function fetchHeatmapComparison(
  targetPlayerId: number,
  candidatePlayerId: number,
  signal?: AbortSignal,
): Promise<HeatmapComparisonResponse> {
  return requestBrowserJson<HeatmapComparisonResponse>(
    `/api/transfer-intelligence/heatmap-comparison/${targetPlayerId}/${candidatePlayerId}`,
    {
      signal,
    },
  );
}

export function fetchRadarComparison(
  targetPlayerId: number,
  candidatePlayerId: number,
  signal?: AbortSignal,
): Promise<RadarComparisonResponse> {
  return requestBrowserJson<RadarComparisonResponse>(
    `/api/transfer-intelligence/radar-comparison/${targetPlayerId}/${candidatePlayerId}`,
    {
      signal,
    },
  );
}
