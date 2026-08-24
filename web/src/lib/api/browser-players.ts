import {
  requestBrowserJson,
} from "@/lib/api/browser-client";
import type {
  PlayerProfileResponse,
  PlayerSearchFiltersResponse,
  PlayerSearchResponse,
} from "@/lib/api/types";
import {
  createPlayerSearchUrlParameters,
} from "@/lib/players/search-parameters";
import type {
  PlayerSearchParameters,
} from "@/lib/players/search-parameters";

export function searchPlayers(
  parameters: PlayerSearchParameters,
  options: Readonly<{
    signal?: AbortSignal;
  }> = {},
): Promise<PlayerSearchResponse> {
  const searchParameters =
    createPlayerSearchUrlParameters(
      parameters,
    );

  return requestBrowserJson<PlayerSearchResponse>(
    `/api/players/search?${searchParameters.toString()}`,
    {
      signal: options.signal,
    },
  );
}

export function fetchPlayerSearchFilters(
  signal?: AbortSignal,
): Promise<PlayerSearchFiltersResponse> {
  return requestBrowserJson<PlayerSearchFiltersResponse>(
    "/api/players/search/filters",
    {
      signal,
    },
  );
}

export function fetchPlayerProfile(
  playerId: number,
  signal?: AbortSignal,
): Promise<PlayerProfileResponse> {
  return requestBrowserJson<PlayerProfileResponse>(
    `/api/players/${playerId}`,
    {
      signal,
    },
  );
}
