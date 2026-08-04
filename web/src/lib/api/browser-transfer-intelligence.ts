import {
  requestBrowserJson,
} from "@/lib/api/browser-client";
import type {
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
