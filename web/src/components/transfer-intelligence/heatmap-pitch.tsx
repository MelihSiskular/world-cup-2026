import type {
  HeatmapPlayerResponse,
} from "@/lib/api/types";

type HeatmapPitchProps =
  Readonly<{
    player: HeatmapPlayerResponse;
    scaleMax?: number | null;
  }>;

const PITCH_LENGTH = 105;
const PITCH_WIDTH = 68;

const DISPLAY_FLOOR_RATIO = 0.16;
const DISPLAY_GAMMA = 1.75;
const MAX_HEATMAP_OPACITY = 0.82;

function isFiniteNonNegative(
  value: number,
): boolean {
  return (
    Number.isFinite(value) &&
    value >= 0
  );
}

export function getHeatmapGridMaximum(
  grid:
    HeatmapPlayerResponse["grid"],
): number {
  if (!grid) {
    return 0;
  }

  let maximum = 0;

  for (const row of grid) {
    for (const value of row) {
      if (
        isFiniteNonNegative(value) &&
        value > maximum
      ) {
        maximum = value;
      }
    }
  }

  return maximum;
}

function resolveScaleMaximum(
  grid:
    NonNullable<
      HeatmapPlayerResponse["grid"]
    >,
  scaleMax:
    number | null | undefined,
): number {
  const localMaximum =
    getHeatmapGridMaximum(grid);

  if (
    typeof scaleMax !== "number" ||
    !Number.isFinite(scaleMax) ||
    scaleMax <= 0
  ) {
    return localMaximum;
  }

  /*
   * Never allow a caller-provided scale
   * below the player's genuine peak.
   * This prevents accidental saturation.
   */
  return Math.max(
    scaleMax,
    localMaximum,
  );
}

function heatmapOpacity(
  value: number,
  scaleMaximum: number,
): number {
  if (
    !isFiniteNonNegative(value) ||
    value <= 0 ||
    scaleMaximum <= 0
  ) {
    return 0;
  }

  const normalized = Math.min(
    1,
    Math.max(
      0,
      value / scaleMaximum,
    ),
  );

  const adjusted = Math.min(
    1,
    Math.max(
      0,
      (
        normalized -
        DISPLAY_FLOOR_RATIO
      ) /
        (
          1 -
          DISPLAY_FLOOR_RATIO
        ),
    ),
  );

  return (
    Math.pow(
      adjusted,
      DISPLAY_GAMMA,
    ) *
    MAX_HEATMAP_OPACITY
  );
}

function hasRenderableGrid(
  player: HeatmapPlayerResponse,
): boolean {
  const {
    available,
    grid,
    grid_width: gridWidth,
    grid_height: gridHeight,
  } = player;

  if (
    !available ||
    !grid ||
    typeof gridWidth !== "number" ||
    typeof gridHeight !== "number" ||
    gridWidth < 2 ||
    gridHeight < 2 ||
    grid.length !== gridHeight
  ) {
    return false;
  }

  return grid.every(
    (row) =>
      row.length === gridWidth &&
      row.every(
        isFiniteNonNegative,
      ),
  );
}

function PitchLines() {
  const penaltyAreaHeight = 40.32;
  const sixYardHeight = 18.32;
  const goalWidth = 7.32;

  const penaltyAreaY =
    (
      PITCH_WIDTH -
      penaltyAreaHeight
    ) / 2;

  const sixYardY =
    (
      PITCH_WIDTH -
      sixYardHeight
    ) / 2;

  const goalY =
    (
      PITCH_WIDTH -
      goalWidth
    ) / 2;

  return (
    <g
      aria-hidden="true"
      className="fill-none stroke-border"
      strokeWidth="0.55"
    >
      <rect
        x="0.5"
        y="0.5"
        width={
          PITCH_LENGTH - 1
        }
        height={
          PITCH_WIDTH - 1
        }
        rx="1.2"
      />

      <line
        x1={PITCH_LENGTH / 2}
        y1="0.5"
        x2={PITCH_LENGTH / 2}
        y2={PITCH_WIDTH - 0.5}
      />

      <circle
        cx={PITCH_LENGTH / 2}
        cy={PITCH_WIDTH / 2}
        r="9.15"
      />

      <circle
        cx={PITCH_LENGTH / 2}
        cy={PITCH_WIDTH / 2}
        r="0.75"
        className="fill-border"
      />

      <rect
        x="0.5"
        y={penaltyAreaY}
        width="16.5"
        height={penaltyAreaHeight}
      />

      <rect
        x={PITCH_LENGTH - 17}
        y={penaltyAreaY}
        width="16.5"
        height={penaltyAreaHeight}
      />

      <rect
        x="0.5"
        y={sixYardY}
        width="5.5"
        height={sixYardHeight}
      />

      <rect
        x={PITCH_LENGTH - 6}
        y={sixYardY}
        width="5.5"
        height={sixYardHeight}
      />

      <circle
        cx="11"
        cy={PITCH_WIDTH / 2}
        r="0.65"
        className="fill-border"
      />

      <circle
        cx={PITCH_LENGTH - 11}
        cy={PITCH_WIDTH / 2}
        r="0.65"
        className="fill-border"
      />

      <path
        d={[
          `M -1.5 ${goalY}`,
          `L 0 ${goalY}`,
          `L 0 ${goalY + goalWidth}`,
          `L -1.5 ${goalY + goalWidth}`,
          "Z",
        ].join(" ")}
      />

      <path
        d={[
          `M ${PITCH_LENGTH + 1.5} ${goalY}`,
          `L ${PITCH_LENGTH} ${goalY}`,
          `L ${PITCH_LENGTH} ${goalY + goalWidth}`,
          `L ${PITCH_LENGTH + 1.5} ${goalY + goalWidth}`,
          "Z",
        ].join(" ")}
      />
    </g>
  );
}

function DensityLegend() {
  const opacitySteps = [
    0.08,
    0.2,
    0.38,
    0.6,
    MAX_HEATMAP_OPACITY,
  ];

  return (
    <div
      aria-label="Relative occupation density legend"
      className="flex items-center gap-2"
    >
      <span className="text-[11px] font-medium text-muted">
        Low
      </span>

      <div
        className="flex gap-1"
        aria-hidden="true"
      >
        {opacitySteps.map(
          (opacity) => (
            <span
              key={opacity}
              className="h-2.5 w-5 rounded-sm bg-brand"
              style={{
                opacity,
              }}
            />
          ),
        )}
      </div>

      <span className="text-[11px] font-medium text-muted">
        High
      </span>
    </div>
  );
}

function formatEvidenceNumber(
  value:
    number | null | undefined,
): string {
  if (
    typeof value !== "number" ||
    !Number.isFinite(value)
  ) {
    return "—";
  }

  return value.toLocaleString(
    "en-US",
  );
}

function formatEntropy(
  value:
    number | null | undefined,
): string {
  if (
    typeof value !== "number" ||
    !Number.isFinite(value)
  ) {
    return "—";
  }

  return value.toFixed(3);
}

export function HeatmapPitch({
  player,
  scaleMax,
}: HeatmapPitchProps) {
  if (!hasRenderableGrid(player)) {
    return (
      <div
        data-testid="heatmap-unavailable"
        className="flex min-h-64 items-center justify-center rounded-2xl border border-dashed border-border bg-page px-6 text-center text-sm leading-6 text-muted"
      >
        Tournament heatmap data are not
        available for{" "}
        {player.player_name}.
      </div>
    );
  }

  /*
   * hasRenderableGrid has established
   * these values as present and valid.
   */
  const grid = player.grid;
  const gridWidth =
    player.grid_width;
  const gridHeight =
    player.grid_height;

  if (
    !grid ||
    typeof gridWidth !== "number" ||
    typeof gridHeight !== "number"
  ) {
    return null;
  }

  const scaleMaximum =
    resolveScaleMaximum(
      grid,
      scaleMax,
    );

  const cellWidth =
    PITCH_LENGTH / gridWidth;

  const cellHeight =
    PITCH_WIDTH / gridHeight;

  return (
    <div className="min-w-0">
      <div className="overflow-hidden rounded-2xl border border-border bg-page p-3 sm:p-4">
        <div className="mb-3 flex items-center justify-between gap-4 px-1">
          <span className="text-xs font-medium text-muted">
            Defensive
          </span>

          <span className="text-xs font-semibold text-brand">
            Attacking direction →
          </span>
        </div>

        <svg
          role="img"
          aria-label={`Tournament heatmap for ${player.player_name}`}
          viewBox="-2 0 109 68"
          className="block h-auto w-full"
        >
          <rect
            x="0"
            y="0"
            width={PITCH_LENGTH}
            height={PITCH_WIDTH}
            rx="1.2"
            className="fill-surface-secondary"
          />

          <g
            aria-hidden="true"
            data-testid="heatmap-cells"
          >
            {grid.flatMap(
              (
                row,
                rowIndex,
              ) =>
                row.map(
                  (
                    density,
                    columnIndex,
                  ) => {
                    /*
                     * Grid row zero is the
                     * analytical lower edge.
                     *
                     * SVG Y increases downward,
                     * so row order is inverted
                     * for display. This matches
                     * matplotlib origin="lower".
                     */
                    const y =
                      PITCH_WIDTH -
                      (
                        rowIndex + 1
                      ) *
                        cellHeight;

                    const x =
                      columnIndex *
                      cellWidth;

                    return (
                      <rect
                        key={
                          `${rowIndex}-${columnIndex}`
                        }
                        data-testid={
                          `heatmap-cell-${rowIndex}-${columnIndex}`
                        }
                        data-heatmap-cell="true"
                        data-density={
                          density
                        }
                        x={x}
                        y={y}
                        width={
                          cellWidth
                        }
                        height={
                          cellHeight
                        }
                        className="fill-brand"
                        opacity={
                          heatmapOpacity(
                            density,
                            scaleMaximum,
                          )
                        }
                      />
                    );
                  },
                ),
            )}
          </g>

          <PitchLines />
        </svg>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
          <div>
            <p className="text-xs font-semibold text-foreground">
              Relative tournament
              occupation density
            </p>

            <p className="mt-1 text-[11px] leading-5 text-muted">
              Visual intensity reflects
              observed tournament heatmap
              occupation, not positional
              probability.
            </p>
          </div>

          <DensityLegend />
        </div>

        <dl className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
          <div className="rounded-xl bg-surface px-3 py-2.5">
            <dt className="text-muted">
              Matches
            </dt>
            <dd className="mt-1 font-bold text-brand-dark">
              {formatEvidenceNumber(
                player.matches_with_heatmap,
              )}
            </dd>
          </div>

          <div className="rounded-xl bg-surface px-3 py-2.5">
            <dt className="text-muted">
              Points
            </dt>
            <dd className="mt-1 font-bold text-brand-dark">
              {formatEvidenceNumber(
                player.heatmap_point_count,
              )}
            </dd>
          </div>

          <div className="rounded-xl bg-surface px-3 py-2.5">
            <dt className="text-muted">
              Entropy
            </dt>
            <dd className="mt-1 font-bold text-brand-dark">
              {formatEntropy(
                player.heatmap_entropy,
              )}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
