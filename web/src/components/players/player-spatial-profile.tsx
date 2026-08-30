import {
  useTranslations,
} from "next-intl";

import {
  HeatmapPitch,
} from "@/components/transfer-intelligence/heatmap-pitch";
import type {
  HeatmapPlayerResponse,
} from "@/lib/api/types";

type PlayerSpatialProfileProps =
  Readonly<{
    playerName: string;
    heatmap: HeatmapPlayerResponse | null;
    isPending: boolean;
    isError: boolean;
    onRetry: () => void;
  }>;

export function PlayerSpatialProfile({
  playerName,
  heatmap,
  isPending,
  isError,
  onRetry,
}: PlayerSpatialProfileProps) {
  const translations =
    useTranslations(
      "PlayerSpatialProfile",
    );

  return (
    <div
      className="mx-auto w-full min-w-0"
      aria-label={translations(
        "regionLabel",
      )}
    >
      {isPending ? (
        <div
          data-testid="spatial-profile-loading"
          role="status"
          aria-label={translations(
            "loading",
          )}
          className="aspect-[105/68] w-full animate-pulse rounded-2xl border border-border bg-surface-secondary"
        />
      ) : isError ? (
        <div className="flex min-h-48 flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-page px-6 text-center">
          <p className="text-sm font-semibold">
            {translations(
              "profileUnavailable",
            )}
          </p>

          <p className="mt-2 text-xs leading-5 text-muted [overflow-wrap:anywhere]">
            {translations(
              "loadFailedDescription",
              {
                player:
                  playerName,
              },
            )}
          </p>

          <button
            type="button"
            onClick={onRetry}
            className="mt-4 rounded-lg border border-border bg-surface px-3 py-2 text-xs font-semibold transition-colors hover:bg-surface-secondary"
          >
            {translations(
              "retry",
            )}
          </button>
        </div>
      ) : heatmap === null ||
        !heatmap.available ? (
        <div className="flex min-h-48 items-center justify-center rounded-2xl border border-dashed border-border bg-page px-6 text-center">
          <div>
            <p className="text-sm font-semibold">
              {translations(
                "dataUnavailable",
              )}
            </p>

            <p className="mt-2 text-xs leading-5 text-muted [overflow-wrap:anywhere]">
              {translations(
                "dataUnavailableDescription",
                {
                  player:
                    playerName,
                },
              )}
            </p>
          </div>
        </div>
      ) : (
        <HeatmapPitch
          player={heatmap}
          showAveragePosition
          showDensityLegend={false}
          showEvidenceSummary={false}
        />
      )}
    </div>
  );
}
