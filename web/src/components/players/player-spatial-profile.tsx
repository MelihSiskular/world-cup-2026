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

function formatEvidenceNumber(
  value: number | null | undefined,
): string {
  if (
    typeof value !== "number" ||
    !Number.isFinite(value)
  ) {
    return "—";
  }

  return value.toLocaleString("en-US");
}

export function PlayerSpatialProfile({
  playerName,
  heatmap,
  isPending,
  isError,
  onRetry,
}: PlayerSpatialProfileProps) {
  return (
    <div
      className="min-w-0"
      aria-label="Player spatial profile"
    >
      <div>
        <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
          Spatial profile
        </p>

        <h2 className="mt-1.5 text-lg font-bold tracking-[-0.025em]">
          Tournament occupation
        </h2>

        <p className="mt-1 text-xs leading-5 text-muted">
          Observed heatmap density with the
          player&apos;s average tournament position.
        </p>
      </div>

      {isPending ? (
        <div
          data-testid="spatial-profile-loading"
          className="mt-3 aspect-[105/68] w-full animate-pulse rounded-2xl border border-border bg-surface-secondary"
        />
      ) : isError ? (
        <div className="mt-3 flex min-h-48 flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-page px-6 text-center">
          <p className="text-sm font-semibold">
            Spatial profile unavailable
          </p>

          <p className="mt-2 text-xs leading-5 text-muted">
            The tournament heatmap for {playerName} could not be loaded.
          </p>

          <button
            type="button"
            onClick={onRetry}
            className="mt-4 rounded-lg border border-border bg-surface px-3 py-2 text-xs font-semibold transition-colors hover:bg-surface-secondary"
          >
            Retry spatial data
          </button>
        </div>
      ) : heatmap === null ||
        !heatmap.available ? (
        <div className="mt-3 flex min-h-48 items-center justify-center rounded-2xl border border-dashed border-border bg-page px-6 text-center">
          <div>
            <p className="text-sm font-semibold">
              Spatial data unavailable
            </p>

            <p className="mt-2 text-xs leading-5 text-muted">
              No measured tournament heatmap is available for {playerName}.
            </p>
          </div>
        </div>
      ) : (
        <>
          <div className="mt-3">
            <HeatmapPitch
              player={heatmap}
              showAveragePosition
              showDensityLegend={false}
              showEvidenceSummary={false}
            />
          </div>

          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-muted">
            <span>
              <strong className="font-semibold text-foreground">
                {formatEvidenceNumber(
                  heatmap.matches_with_heatmap,
                )}
              </strong>{" "}
              matches
            </span>

            <span>
              <strong className="font-semibold text-foreground">
                {formatEvidenceNumber(
                  heatmap.heatmap_point_count,
                )}
              </strong>{" "}
              observed points
            </span>
          </div>
        </>
      )}
    </div>
  );
}
