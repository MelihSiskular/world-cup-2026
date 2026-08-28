import type {
  components,
  paths,
} from "@/lib/api/generated/schema";

export type ApiErrorCode =
  components["schemas"]["ApiErrorCode"];

export type ApiErrorDetail =
  components["schemas"]["ApiErrorDetail"];

export type ApiErrorResponse =
  components["schemas"]["ApiErrorResponse"];

export type ValidationError =
  components["schemas"]["ValidationError"];

export type HttpValidationError =
  components["schemas"]["HTTPValidationError"];

export type HealthResponse =
  components["schemas"]["HealthResponse"];

export type ReadinessResponse =
  components["schemas"]["ReadinessResponse"];

export type DeploymentIdentityResponse =
  components["schemas"]["DeploymentIdentityResponse"];

export type PlayerSearchItemResponse =
  components["schemas"]["PlayerSearchItemResponse"];

export type PlayerSearchResponse =
  components["schemas"]["PlayerSearchResponse"];

export type PlayerSearchFilterOptionResponse =
  components["schemas"]["PlayerSearchFilterOptionResponse"];

export type PlayerSearchFilterRangeResponse =
  components["schemas"]["PlayerSearchFilterRangeResponse"];

export type PlayerSearchFiltersResponse =
  components["schemas"]["PlayerSearchFiltersResponse"];


export type PlayerProfileResponse =
  components["schemas"]["PlayerProfileResponse"];

export type HeatmapPlayerResponse =
  components["schemas"]["HeatmapPlayerResponse"];

export type HeatmapSimilarityResponse =
  components["schemas"]["HeatmapSimilarityResponse"];

export type HeatmapComparisonResponse =
  components["schemas"]["HeatmapComparisonResponse"];

export type MultiPlayerComparisonPlayerResponse =
  components["schemas"]["MultiPlayerComparisonPlayerResponse"];

export type MultiPlayerComparisonEvidenceResponse =
  components["schemas"]["MultiPlayerComparisonEvidenceResponse"];

export type MultiPlayerComparisonCandidateResponse =
  components["schemas"]["MultiPlayerComparisonCandidateResponse"];

export type MultiPlayerComparisonResponse =
  components["schemas"]["MultiPlayerComparisonResponse"];

export type RadarDimensionResponse =
  components["schemas"]["RadarDimensionResponse"];

export type RadarPlayerResponse =
  components["schemas"]["RadarPlayerResponse"];

export type RadarComparisonMetadataResponse =
  components["schemas"]["RadarComparisonMetadataResponse"];

export type RadarComparisonResponse =
  components["schemas"]["RadarComparisonResponse"];

export type TransferAnalysisPayload =
  components["schemas"]["TransferAnalysisPayload"];

export type TransferTargetResponse =
  components["schemas"]["TransferTargetResponse"];

export type ImmediateTransferRecommendationResponse =
  components["schemas"]["ImmediateTransferRecommendationResponse"];

export type DevelopmentTransferRecommendationResponse =
  components["schemas"]["DevelopmentTransferRecommendationResponse"];

export type ValueTransferRecommendationResponse =
  components["schemas"]["ValueTransferRecommendationResponse"];

export type ShortTermTransferRecommendationResponse =
  components["schemas"]["ShortTermTransferRecommendationResponse"];

export type ImmediateTransferModeResponse =
  components["schemas"]["ImmediateTransferModeResponse"];

export type DevelopmentTransferModeResponse =
  components["schemas"]["DevelopmentTransferModeResponse"];

export type ValueTransferModeResponse =
  components["schemas"]["ValueTransferModeResponse"];

export type ShortTermTransferModeResponse =
  components["schemas"]["ShortTermTransferModeResponse"];

export type TransferModesResponse =
  components["schemas"]["TransferModesResponse"];

export type TransferAnalysisResponse =
  components["schemas"]["TransferAnalysisResponse"];

export type TransferModeName =
  keyof TransferModesResponse;

export type TransferModeResponse =
  TransferModesResponse[TransferModeName];

export type TransferRecommendationResponse =
  | ImmediateTransferRecommendationResponse
  | DevelopmentTransferRecommendationResponse
  | ValueTransferRecommendationResponse
  | ShortTermTransferRecommendationResponse;

export type PlayerSearchQuery =
  paths["/api/v1/players/search"]["get"]["parameters"]["query"];

export type PlayerProfilePath =
  paths["/api/v1/players/{player_id}"]["get"]["parameters"]["path"];


export type MultiPlayerComparisonPath =
  paths[
    "/api/v1/transfer-intelligence/multi-comparison/{target_player_id}"
  ]["get"]["parameters"]["path"];

export type MultiPlayerComparisonQuery =
  paths[
    "/api/v1/transfer-intelligence/multi-comparison/{target_player_id}"
  ]["get"]["parameters"]["query"];

export type HeatmapComparisonPath =
  paths[
    "/api/v1/transfer-intelligence/heatmap-comparison/{target_player_id}/{candidate_player_id}"
  ]["get"]["parameters"]["path"];

export type RadarComparisonPath =
  paths[
    "/api/v1/transfer-intelligence/radar-comparison/{target_player_id}/{candidate_player_id}"
  ]["get"]["parameters"]["path"];

export type WebApiErrorCode =
  | ApiErrorCode
  | "invalid_request"
  | "validation_error"
  | "upstream_unavailable"
  | "upstream_timeout"
  | "invalid_upstream_response";

export type WebApiErrorDetail = Readonly<{
  code: WebApiErrorCode;
  message: string;
}>;

export type WebApiErrorResponse = Readonly<{
  error: WebApiErrorDetail;
}>;

export type NormalizedApiError =
  | ApiErrorResponse
  | WebApiErrorResponse;
