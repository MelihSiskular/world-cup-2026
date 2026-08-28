import {
  Fragment,
} from "react";
import Link from "next/link";

import type {
  MultiPlayerComparisonCandidateResponse,
  MultiPlayerComparisonPlayerResponse,
  MultiPlayerComparisonResponse,
} from "@/lib/api/types";

type RoleMetricGroups =
  NonNullable<
    MultiPlayerComparisonResponse[
      "role_metrics"
    ]
  >;

type MultiPlayerRoleMetricsProps =
  Readonly<{
    target:
      MultiPlayerComparisonPlayerResponse;
    candidates:
      readonly MultiPlayerComparisonCandidateResponse[];
    groups: RoleMetricGroups;
  }>;

function formatMetricNumber(
  value: number,
  maximumFractionDigits: number,
): string {
  return new Intl.NumberFormat(
    "en-US",
    {
      maximumFractionDigits,
    },
  ).format(value);
}

function RoleMetricValue({
  total,
  per90,
}: Readonly<{
  total:
    | number
    | null
    | undefined;
  per90:
    | number
    | null
    | undefined;
}>) {
  if (
    total === null ||
    total === undefined ||
    per90 === null ||
    per90 === undefined
  ) {
    return (
      <span className="text-muted">
        Unavailable
      </span>
    );
  }

  const totalText =
    formatMetricNumber(
      total,
      Number.isInteger(total)
        ? 0
        : 2,
    );

  const per90Text =
    formatMetricNumber(
      per90,
      2,
    );

  return (
    <span className="font-semibold tabular-nums">
      <span aria-hidden="true">
        {totalText} (
        {per90Text}/90)
      </span>

      <span className="sr-only">
        {totalText} total,{" "}
        {per90Text} per 90
      </span>
    </span>
  );
}

export function MultiPlayerRoleMetrics({
  target,
  candidates,
  groups,
}: MultiPlayerRoleMetricsProps) {
  const players = [
    target,
    ...candidates.map(
      ({ player }) => player,
    ),
  ];

  return (
    <section
      aria-labelledby="role-metrics-title"
      className="w-full min-w-0 max-w-full overflow-hidden rounded-3xl border border-border bg-surface shadow-sm [contain:inline-size_layout_paint]"
    >
      <div className="border-b border-border p-5 sm:p-7">
        <p className="text-xs font-semibold tracking-[0.14em] text-brand uppercase">
          Role performance
        </p>

        <h2
          id="role-metrics-title"
          className="mt-2 text-2xl font-bold tracking-[-0.035em]"
        >
          Target final-role metrics
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          All players are evaluated
          against the duties of{" "}
          <span className="font-semibold text-foreground">
            {target.final_role ??
              "the target role"}
          </span>
          . Each value shows tournament
          total followed by the per-90
          rate.
        </p>
      </div>

      {groups.length === 0 ? (
        <p
          role="status"
          className="p-6 text-sm text-muted"
        >
          Role metric evidence is
          unavailable for this target.
        </p>
      ) : (
        <div
          role="region"
          aria-label="Scrollable target final-role metrics"
          tabIndex={0}
          className="w-0 min-w-full overflow-x-auto overscroll-x-contain"
        >
          <table
            aria-label="Target final-role metric comparison"
            className="min-w-[760px] w-full border-collapse text-left text-sm"
          >
            <thead className="bg-surface-secondary">
              <tr>
                <th
                  scope="col"
                  className="w-52 border-r border-border bg-surface-secondary px-5 py-4 font-bold sm:sticky sm:left-0 sm:z-10"
                >
                  Metric
                </th>

                {players.map(
                  (
                    player,
                    index,
                  ) => (
                    <th
                      key={
                        player.player_id
                      }
                      scope="col"
                      className="min-w-44 px-5 py-4"
                    >
                      <span className="block text-[10px] font-semibold tracking-[0.14em] text-muted uppercase">
                        {index === 0
                          ? "Target"
                          : `Candidate ${index}`}
                      </span>

                      <Link
                        href={`/players/${player.player_id}`}
                        className="mt-1 block break-words font-bold hover:text-brand"
                      >
                        {
                          player.player_name
                        }
                      </Link>
                    </th>
                  ),
                )}
              </tr>
            </thead>

            <tbody>
              {groups.map(
                (group) => (
                  <Fragment
                    key={group.key}
                  >
                    <tr>
                      <th
                        scope="colgroup"
                        colSpan={
                          players.length +
                          1
                        }
                        className="border-y border-border bg-page px-5 py-3 text-xs font-semibold tracking-[0.12em] text-brand uppercase"
                      >
                        {group.label}
                      </th>
                    </tr>

                    {group.metrics.map(
                      (metric) => (
                        <tr
                          key={
                            metric.key
                          }
                          className="border-b border-border last:border-b-0"
                        >
                          <th
                            scope="row"
                            className="border-r border-border bg-surface px-5 py-4 font-semibold sm:sticky sm:left-0 sm:z-10"
                          >
                            {
                              metric.label
                            }
                          </th>

                          {players.map(
                            (
                              player,
                            ) => {
                              const value =
                                metric.values.find(
                                  (
                                    item,
                                  ) =>
                                    item.player_id ===
                                    player.player_id,
                                );

                              return (
                                <td
                                  key={
                                    player.player_id
                                  }
                                  className="px-5 py-4"
                                >
                                  <RoleMetricValue
                                    total={
                                      value?.total
                                    }
                                    per90={
                                      value?.per90
                                    }
                                  />
                                </td>
                              );
                            },
                          )}
                        </tr>
                      ),
                    )}
                  </Fragment>
                ),
              )}
            </tbody>
          </table>
        </div>
      )}

      <p className="border-t border-border bg-page px-5 py-4 text-xs leading-5 text-muted">
        Metrics are selected from the
        target player&apos;s final-role
        duties. Missing tournament
        evidence is never replaced with
        zero.
      </p>
    </section>
  );
}
