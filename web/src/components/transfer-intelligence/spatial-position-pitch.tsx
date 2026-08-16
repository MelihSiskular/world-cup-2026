type SpatialPitchPlayer = Readonly<{
  playerId: number;
  playerName: string;
  meanX: number | null | undefined;
  meanY: number | null | undefined;
  xStd?: number | null;
  yStd?: number | null;
}>;

type SpatialPositionPitchProps = Readonly<{
  target: SpatialPitchPlayer;
  candidate: SpatialPitchPlayer;
}>;

const PITCH_LENGTH = 105;
const PITCH_WIDTH = 68;

function clampCoordinate(value: number): number {
  return Math.min(100, Math.max(0, value));
}

function projectX(value: number): number {
  return (clampCoordinate(value) / 100) * PITCH_LENGTH;
}

function projectY(value: number): number {
  /*
   * Analytical coordinates use an
   * origin compatible with the existing
   * Python pitch visualisation.
   *
   * SVG increases Y downwards, so the
   * display coordinate is inverted.
   */
  return PITCH_WIDTH - (clampCoordinate(value) / 100) * PITCH_WIDTH;
}

function hasPosition(player: SpatialPitchPlayer): player is SpatialPitchPlayer &
  Readonly<{
    meanX: number;
    meanY: number;
  }> {
  return (
    typeof player.meanX === "number" &&
    Number.isFinite(player.meanX) &&
    typeof player.meanY === "number" &&
    Number.isFinite(player.meanY)
  );
}

function projectSpreadX(value: number | null | undefined): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    return 0;
  }

  return (value / 100) * PITCH_LENGTH;
}

function projectSpreadY(value: number | null | undefined): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    return 0;
  }

  return (value / 100) * PITCH_WIDTH;
}

function PlayerPosition({
  player,
  kind,
}: Readonly<{
  player: SpatialPitchPlayer;
  kind: "target" | "candidate";
}>) {
  if (!hasPosition(player)) {
    return null;
  }

  const x = projectX(player.meanX);
  const y = projectY(player.meanY);

  const radiusX = projectSpreadX(player.xStd);

  const radiusY = projectSpreadY(player.yStd);

  const markerClassName =
    kind === "target"
      ? "fill-brand stroke-white"
      : "fill-transparent stroke-brand-dark";

  const spreadClassName =
    kind === "target"
      ? "fill-brand/10 stroke-brand/35"
      : "fill-transparent stroke-brand-dark/45";

  const labelClassName =
    kind === "target"
      ? "fill-white text-[3.2px] font-bold"
      : "fill-brand-dark text-[3.2px] font-bold";

  const label = kind === "target" ? "T" : "C";

  return (
    <g data-testid={`${kind}-spatial-position`}>
      {radiusX > 0 && radiusY > 0 ? (
        <ellipse
          cx={x}
          cy={y}
          rx={radiusX}
          ry={radiusY}
          className={spreadClassName}
          strokeWidth="0.55"
          strokeDasharray={kind === "candidate" ? "2.2 1.4" : undefined}
        />
      ) : null}

      <circle
        cx={x}
        cy={y}
        r={kind === "target" ? "3.2" : "3.8"}
        className={markerClassName}
        strokeWidth={kind === "target" ? "0.8" : "1.15"}
      />

      <text
        x={x}
        y={y + 0.2}
        textAnchor="middle"
        dominantBaseline="middle"
        className={labelClassName}
      >
        {label}
      </text>

      <title>
        {player.playerName}: mean position ({player.meanX.toFixed(1)},{" "}
        {player.meanY.toFixed(1)})
      </title>
    </g>
  );
}

function PitchLines() {
  return (
    <g
      aria-hidden="true"
      className="fill-none stroke-border"
      strokeWidth="0.55"
    >
      <rect
        x="0.5"
        y="0.5"
        width={PITCH_LENGTH - 1}
        height={PITCH_WIDTH - 1}
        rx="1.2"
      />

      <line
        x1={PITCH_LENGTH / 2}
        y1="0.5"
        x2={PITCH_LENGTH / 2}
        y2={PITCH_WIDTH - 0.5}
      />

      <circle cx={PITCH_LENGTH / 2} cy={PITCH_WIDTH / 2} r="9.15" />

      <circle
        cx={PITCH_LENGTH / 2}
        cy={PITCH_WIDTH / 2}
        r="0.9"
        className="fill-border"
      />

      <rect x="0.5" y={(PITCH_WIDTH - 40.32) / 2} width="16.5" height="40.32" />

      <rect
        x={PITCH_LENGTH - 17}
        y={(PITCH_WIDTH - 40.32) / 2}
        width="16.5"
        height="40.32"
      />

      <rect x="0.5" y={(PITCH_WIDTH - 18.32) / 2} width="5.5" height="18.32" />

      <rect
        x={PITCH_LENGTH - 6}
        y={(PITCH_WIDTH - 18.32) / 2}
        width="5.5"
        height="18.32"
      />

      <circle cx="11" cy={PITCH_WIDTH / 2} r="0.7" className="fill-border" />

      <circle
        cx={PITCH_LENGTH - 11}
        cy={PITCH_WIDTH / 2}
        r="0.7"
        className="fill-border"
      />
    </g>
  );
}

export function SpatialPositionPitch({
  target,
  candidate,
}: SpatialPositionPitchProps) {
  const hasTarget = hasPosition(target);

  const hasCandidate = hasPosition(candidate);

  if (!hasTarget && !hasCandidate) {
    return (
      <div className="flex min-h-64 items-center justify-center rounded-2xl border border-dashed border-border bg-page px-6 text-center text-sm leading-6 text-muted">
        Positional coordinates are not available for either player.
      </div>
    );
  }

  return (
    <div className="min-w-0">
      <div className="overflow-hidden rounded-2xl border border-border bg-page p-3 sm:p-4">
        <div className="mb-3 flex items-center justify-between gap-4 px-1">
          <span className="text-xs font-medium text-muted">Defensive</span>

          <span className="text-xs font-semibold text-brand">
            Attacking direction →
          </span>
        </div>

        <svg
          role="img"
          aria-label={`Spatial position comparison for ${target.playerName} and ${candidate.playerName}`}
          viewBox={`0 0 ${PITCH_LENGTH} ${PITCH_WIDTH}`}
          className="block h-auto w-full"
        >
          <rect
            width={PITCH_LENGTH}
            height={PITCH_WIDTH}
            rx="1.4"
            className="fill-surface-secondary"
          />

          <PitchLines />

          <PlayerPosition player={target} kind="target" />

          <PlayerPosition player={candidate} kind="candidate" />
        </svg>
      </div>

      <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs">
        <span className="flex items-center gap-2 text-muted">
          <span className="inline-flex size-5 items-center justify-center rounded-full bg-brand text-[0.65rem] font-bold text-white">
            T
          </span>
          {target.playerName}
        </span>

        <span className="flex items-center gap-2 text-muted">
          <span className="inline-flex size-5 items-center justify-center rounded-full bg-brand-dark text-[0.65rem] font-bold text-white">
            C
          </span>
          {candidate.playerName}
        </span>

        <span className="text-muted">
          Ellipses show positional dispersion when available.
        </span>
      </div>
    </div>
  );
}
