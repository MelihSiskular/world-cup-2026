import {
  useLocale,
  useTranslations,
} from "next-intl";

export type RadarProfileDimension = Readonly<{
  key: string;
  label: string;
  percentile: number | null;
}>;

export type RadarProfileSeries = Readonly<{
  player_id: number;
  player_name: string;
  available: boolean;
  dimensions: readonly RadarProfileDimension[];
}>;

type RadarProfileProps = Readonly<{
  primary: RadarProfileSeries;
  secondary?: RadarProfileSeries;
  ariaLabel?: string;
  showHeader?: boolean;
}>;

const VIEWBOX_WIDTH = 560;
const VIEWBOX_HEIGHT = 390;

const CENTER_X = VIEWBOX_WIDTH / 2;
const CENTER_Y = VIEWBOX_HEIGHT / 2;

const RADAR_RADIUS = 108;
const LABEL_RADIUS = 148;

const RING_LEVELS = [
  25,
  50,
  75,
  100,
] as const;

type Point = Readonly<{
  x: number;
  y: number;
}>;

function resolvePercentile(
  value: number | null | undefined,
): number | null {
  if (
    typeof value !== "number" ||
    !Number.isFinite(value) ||
    value < 0 ||
    value > 100
  ) {
    return null;
  }

  return value;
}

function pointForAxis(
  axisIndex: number,
  axisCount: number,
  radius: number,
): Point {
  const angle =
    -Math.PI / 2 +
    (axisIndex / axisCount) *
      Math.PI *
      2;

  return {
    x:
      CENTER_X +
      Math.cos(angle) * radius,
    y:
      CENTER_Y +
      Math.sin(angle) * radius,
  };
}

function polygonPoints(
  axisCount: number,
  radius: number,
): string {
  return Array.from(
    {
      length: axisCount,
    },
    (_, index) => {
      const point = pointForAxis(
        index,
        axisCount,
        radius,
      );

      return `${point.x},${point.y}`;
    },
  ).join(" ");
}

function seriesPolygonPoints(
  series: RadarProfileSeries,
): string | null {
  const points: string[] = [];

  for (
    let index = 0;
    index < series.dimensions.length;
    index += 1
  ) {
    const dimension =
      series.dimensions[index];

    if (!dimension) {
      return null;
    }

    const percentile =
      resolvePercentile(
        dimension.percentile,
      );

    if (percentile === null) {
      return null;
    }

    const point = pointForAxis(
      index,
      series.dimensions.length,
      RADAR_RADIUS *
        (percentile / 100),
    );

    points.push(
      `${point.x},${point.y}`,
    );
  }

  return points.join(" ");
}

function hasRenderableAxisContract(
  series: RadarProfileSeries,
): boolean {
  if (
    !series.available ||
    series.dimensions.length < 3
  ) {
    return false;
  }

  const keys = series.dimensions.map(
    (dimension) => dimension.key,
  );

  return (
    new Set(keys).size === keys.length
  );
}

function hasMatchingAxes(
  primary: RadarProfileSeries,
  secondary: RadarProfileSeries,
): boolean {
  if (
    primary.dimensions.length !==
    secondary.dimensions.length
  ) {
    return false;
  }

  return primary.dimensions.every(
    (dimension, index) =>
      dimension.key ===
      secondary.dimensions[index]?.key,
  );
}

function hasPartialEvidence(
  series: RadarProfileSeries,
): boolean {
  return series.dimensions.some(
    (dimension) =>
      resolvePercentile(
        dimension.percentile,
      ) === null,
  );
}

function labelAnchor(
  x: number,
): "start" | "middle" | "end" {
  if (
    Math.abs(
      x - CENTER_X,
    ) < 15
  ) {
    return "middle";
  }

  return x > CENTER_X
    ? "start"
    : "end";
}

function axisDescription(
  series: RadarProfileSeries,
  locale: string,
  unavailableLabel: string,
  percentileLabel: string,
): string {
  return series.dimensions
    .map((dimension) => {
      const percentile =
        resolvePercentile(
          dimension.percentile,
        );

      return `${dimension.label}: ${
        percentile === null
          ? unavailableLabel
          : `${new Intl.NumberFormat(
              locale,
              {
                minimumFractionDigits: 1,
                maximumFractionDigits: 1,
              },
            ).format(
              percentile,
            )} ${percentileLabel}`
      }`;
    })
    .join("; ");
}

function RadarSeriesShape({
  series,
  variant,
}: Readonly<{
  series: RadarProfileSeries;
  variant:
    | "primary"
    | "secondary";
}>) {
  const completePolygon =
    seriesPolygonPoints(series);

  const pointClassName =
    variant === "primary"
      ? "fill-brand stroke-surface"
      : "fill-brand-navy stroke-surface";

  const polygonClassName =
    variant === "primary"
      ? "fill-brand stroke-brand"
      : "fill-brand-navy stroke-brand-navy";

  return (
    <g
      data-testid={`radar-series-${variant}`}
      aria-hidden="true"
    >
      {completePolygon ? (
        <polygon
          data-testid={`radar-polygon-${variant}`}
          points={completePolygon}
          className={polygonClassName}
          fillOpacity={
            variant === "primary"
              ? 0.14
              : 0.09
          }
          strokeWidth="2.5"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
        />
      ) : null}

      {series.dimensions.map(
        (
          dimension,
          index,
        ) => {
          const percentile =
            resolvePercentile(
              dimension.percentile,
            );

          if (
            percentile === null
          ) {
            return null;
          }

          const point =
            pointForAxis(
              index,
              series.dimensions.length,
              RADAR_RADIUS *
                (percentile / 100),
            );

          return (
            <circle
              key={dimension.key}
              data-testid={`radar-point-${variant}-${dimension.key}`}
              data-percentile={
                percentile
              }
              cx={point.x}
              cy={point.y}
              r="4.25"
              className={
                pointClassName
              }
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
            />
          );
        },
      )}
    </g>
  );
}

export function RadarProfile({
  primary,
  secondary,
  ariaLabel,
  showHeader = true,
}: RadarProfileProps) {
  const locale = useLocale();
  const t = useTranslations(
    "RadarProfile",
  );

  if (
    !hasRenderableAxisContract(
      primary,
    )
  ) {
    return (
      <div
        data-testid="radar-unavailable"
        className="flex min-h-72 items-center justify-center rounded-2xl border border-dashed border-border bg-page px-6 text-center text-sm leading-6 text-muted"
      >
        {t("unavailable", {
          playerName:
            primary.player_name,
        })}
      </div>
    );
  }

  if (
    secondary &&
    !hasRenderableAxisContract(
      secondary,
    )
  ) {
    return (
      <div
        data-testid="radar-unavailable"
        className="flex min-h-72 items-center justify-center rounded-2xl border border-dashed border-border bg-page px-6 text-center text-sm leading-6 text-muted"
      >
        {t("unavailable", {
          playerName:
            secondary.player_name,
        })}
      </div>
    );
  }

  if (
    secondary &&
    !hasMatchingAxes(
      primary,
      secondary,
    )
  ) {
    return (
      <div
        data-testid="radar-incompatible"
        className="flex min-h-72 items-center justify-center rounded-2xl border border-dashed border-border bg-page px-6 text-center text-sm leading-6 text-muted"
      >
        {t("incompatible")}
      </div>
    );
  }

  const resolvedAriaLabel =
    ariaLabel ??
    (secondary
      ? t("comparisonAriaLabel", {
          primaryPlayer:
            primary.player_name,
          secondaryPlayer:
            secondary.player_name,
        })
      : t("singleAriaLabel", {
          playerName:
            primary.player_name,
        }));

  const primaryPartial =
    hasPartialEvidence(primary);

  const secondaryPartial =
    secondary
      ? hasPartialEvidence(
          secondary,
        )
      : false;

  return (
    <div className="mx-auto w-full min-w-0 max-w-2xl">
      <div className="overflow-hidden rounded-2xl border border-border bg-page p-3 sm:p-5">
        {showHeader ? (
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3 px-1">
            <p className="text-xs font-semibold text-foreground">
              {t("title")}
            </p>

            <span className="rounded-full border border-border bg-surface px-3 py-1 text-[11px] font-semibold text-muted">
              {t("scale")}
            </span>
          </div>
        ) : null}

        <svg
          role="img"
          aria-label={
            resolvedAriaLabel
          }
          viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
          className="block h-auto w-full"
        >
          <desc>
            {axisDescription(
              primary,
              locale,
              t("axisUnavailable"),
              t("axisPercentile"),
            )}
            {secondary
              ? `. ${axisDescription(
                  secondary,
                  locale,
                  t(
                    "axisUnavailable",
                  ),
                  t(
                    "axisPercentile",
                  ),
                )}`
              : ""}
          </desc>

          <g
            aria-hidden="true"
            data-testid="radar-grid"
          >
            {RING_LEVELS.map(
              (level) => {
                const radius =
                  RADAR_RADIUS *
                  (level / 100);

                return (
                  <polygon
                    key={level}
                    data-testid={`radar-ring-${level}`}
                    points={polygonPoints(
                      primary
                        .dimensions
                        .length,
                      radius,
                    )}
                    className="fill-none stroke-border"
                    strokeWidth={
                      level === 100
                        ? 1.4
                        : 0.8
                    }
                    vectorEffect="non-scaling-stroke"
                  />
                );
              },
            )}

            {primary.dimensions.map(
              (
                dimension,
                index,
              ) => {
                const outerPoint =
                  pointForAxis(
                    index,
                    primary
                      .dimensions
                      .length,
                    RADAR_RADIUS,
                  );

                return (
                  <line
                    key={
                      dimension.key
                    }
                    data-testid={`radar-axis-${dimension.key}`}
                    x1={CENTER_X}
                    y1={CENTER_Y}
                    x2={
                      outerPoint.x
                    }
                    y2={
                      outerPoint.y
                    }
                    className="stroke-border"
                    strokeWidth="0.8"
                    vectorEffect="non-scaling-stroke"
                  />
                );
              },
            )}

            {RING_LEVELS.map(
              (level) => (
                <text
                  key={level}
                  x={
                    CENTER_X + 7
                  }
                  y={
                    CENTER_Y -
                    RADAR_RADIUS *
                      (level /
                        100) +
                    4
                  }
                  className="fill-muted text-[9px]"
                >
                  {level}
                </text>
              ),
            )}
          </g>

          <RadarSeriesShape
            series={primary}
            variant="primary"
          />

          {secondary ? (
            <RadarSeriesShape
              series={secondary}
              variant="secondary"
            />
          ) : null}

          <g
            aria-hidden="true"
            data-testid="radar-labels"
          >
            {primary.dimensions.map(
              (
                dimension,
                index,
              ) => {
                const labelPoint =
                  pointForAxis(
                    index,
                    primary
                      .dimensions
                      .length,
                    LABEL_RADIUS,
                  );

                const words =
                  dimension.label.split(
                    " ",
                  );

                return (
                  <text
                    key={
                      dimension.key
                    }
                    x={labelPoint.x}
                    y={
                      labelPoint.y
                    }
                    textAnchor={labelAnchor(
                      labelPoint.x,
                    )}
                    className="fill-foreground text-[11px] font-semibold"
                  >
                    {words.map(
                      (
                        word,
                        wordIndex,
                      ) => (
                        <tspan
                          key={`${dimension.key}-${word}`}
                          x={
                            labelPoint.x
                          }
                          dy={
                            wordIndex ===
                            0
                              ? 0
                              : 13
                          }
                        >
                          {word}
                        </tspan>
                      ),
                    )}
                  </text>
                );
              },
            )}
          </g>
        </svg>

        <div
          aria-label={t("legendAriaLabel")}
          className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-border px-1 pt-4"
        >
          <span className="inline-flex min-w-0 items-center gap-2 text-xs font-semibold">
            <span
              aria-hidden="true"
              className="h-2.5 w-2.5 shrink-0 rounded-full bg-brand"
            />
            <span className="truncate">
              {primary.player_name}
            </span>
          </span>

          {secondary ? (
            <span className="inline-flex min-w-0 items-center gap-2 text-xs font-semibold">
              <span
                aria-hidden="true"
                className="h-2.5 w-2.5 shrink-0 rounded-full bg-brand-navy"
              />
              <span className="truncate">
                {
                  secondary.player_name
                }
              </span>
            </span>
          ) : null}
        </div>

        {primaryPartial ||
        secondaryPartial ? (
          <p
            data-testid="radar-partial-evidence"
            className="mt-4 rounded-xl border border-warning/20 bg-warning/10 px-4 py-3 text-xs leading-5 text-muted"
          >
            {t("partialEvidence")}
          </p>
        ) : null}

        <p className="mt-4 px-1 text-[11px] leading-5 text-muted">
          {t("guidance")}
        </p>
      </div>
    </div>
  );
}
