import {
  queryOptions,
} from "@tanstack/react-query";

import {
  isBrowserApiError,
} from "@/lib/api/browser-client";
import {
  runTransferAnalysis,
} from "@/lib/api/browser-transfer-intelligence";
import {
  createTransferAnalysisPayload,
} from "@/lib/transfer-intelligence/analysis-form";
import type {
  TransferAnalysisFormValues,
} from "@/lib/transfer-intelligence/analysis-form";

export const TRANSFER_ANALYSIS_STALE_TIME_MS =
  5 * 60 * 1000;

export function createTransferAnalysisQueryKey(
  playerId: number,
  values: TransferAnalysisFormValues,
) {
  return [
    "transfer-intelligence",
    "analysis",
    playerId,
    values.minimumMinutes,
    values.minimumRoleConfidence,
    values.maximumMarketValueMillions ??
      null,
    values.neutralHeatmapScore,
  ] as const;
}

export function createTransferAnalysisQueryOptions(
  playerId: number,
  values: TransferAnalysisFormValues,
) {
  const payload =
    createTransferAnalysisPayload(
      playerId,
      values,
    );

  return queryOptions({
    queryKey:
      createTransferAnalysisQueryKey(
        playerId,
        values,
      ),
    queryFn: ({
      signal,
    }) =>
      runTransferAnalysis(
        payload,
        signal,
      ),
    staleTime:
      TRANSFER_ANALYSIS_STALE_TIME_MS,
    retry: (
      failureCount,
      error,
    ) => {
      if (
        isBrowserApiError(error) &&
        (
          error.status === 400 ||
          error.status === 404
        )
      ) {
        return false;
      }

      return failureCount < 1;
    },
  });
}
