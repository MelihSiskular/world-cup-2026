import {
  requestBrowserJson,
} from "@/lib/api/browser-client";
import type {
  HeatmapComparisonResponse,
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
