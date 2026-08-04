import {
  requestBrowserJson,
} from "@/lib/api/browser-client";
import type {
  PlayerSearchResponse,
} from "@/lib/api/types";
import {
  DEFAULT_PLAYER_SEARCH_LIMIT,
} from "@/lib/players/search-config";

export function searchPlayers(
  query: string,
  options: Readonly<{
    limit?: number;
    signal?: AbortSignal;
  }> = {},
): Promise<PlayerSearchResponse> {
  const searchParameters =
    new URLSearchParams({
      q: query,
      limit: String(
        options.limit ??
        DEFAULT_PLAYER_SEARCH_LIMIT,
      ),
    });

  return requestBrowserJson<PlayerSearchResponse>(
    `/api/players/search?${searchParameters.toString()}`,
    {
      signal: options.signal,
    },
  );
}
