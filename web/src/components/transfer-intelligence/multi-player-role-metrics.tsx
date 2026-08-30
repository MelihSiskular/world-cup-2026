"use client";

import {
  useLocale,
  useTranslations,
} from "next-intl";
import {
  Fragment,
} from "react";

import {
  Link,
} from "@/i18n/navigation";

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
  locale: string,
): string {
  return new Intl.NumberFormat(
    locale,
    {
      maximumFractionDigits,
    },
  ).format(value);
}

function RoleMetricValue({
  total,
  per90,
  locale,
  unavailable,
  accessibleLabel,
}: Readonly<{
  total:
    | number
    | null
    | undefined;
  per90:
    | number
    | null
    | undefined;
  locale: string;
  unavailable: string;
  accessibleLabel: (
    total: string,
    per90: string,
  ) => string;
}>) {
  if (
    total === null ||
    total === undefined ||
    per90 === null ||
    per90 === undefined
  ) {
    return (
      <span className="text-muted">
        {unavailable}
      </span>
    );
  }

  const totalText =
    formatMetricNumber(
      total,
      Number.isInteger(total)
        ? 0
        : 2,
      locale,
    );

  const per90Text =
    formatMetricNumber(
      per90,
      2,
      locale,
    );

  return (
    <span className="font-semibold tabular-nums">
      <span aria-hidden="true">
        {totalText} (
        {per90Text}/90)
      </span>

      <span className="sr-only">
        {accessibleLabel(
          totalText,
          per90Text,
        )}
      </span>
    </span>
  );
}

export function MultiPlayerRoleMetrics({
  target,
  candidates,
  groups,
}: MultiPlayerRoleMetricsProps) {
  const locale = useLocale();
  const t = useTranslations(
    "MultiPlayerRoleMetrics",
  );

  const groupLabels =
    t.raw("groups") as Readonly<
      Record<string, string>
    >;

  const metricLabels =
    t.raw("metrics") as Readonly<
      Record<string, string>
    >;

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
          {t("eyebrow")}
        </p>

        <h2
          id="role-metrics-title"
          className="mt-2 text-2xl font-bold tracking-[-0.035em]"
        >
          {t("title")}
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          {t("descriptionBeforeRole")}{" "}
          <span className="font-semibold text-foreground">
            {target.final_role ??
              t("targetRoleFallback")}
          </span>
          {t("descriptionAfterRole")}
        </p>
      </div>

      {groups.length === 0 ? (
        <p
          role="status"
          className="p-6 text-sm text-muted"
        >
          {t("unavailableDescription")}
        </p>
      ) : (
        <div
          role="region"
          aria-label={t("scrollRegionLabel")}
          tabIndex={0}
          className="w-0 min-w-full overflow-x-auto overscroll-x-contain"
        >
          <table
            aria-label={t("tableLabel")}
            className="min-w-[760px] w-full border-collapse text-left text-sm"
          >
            <thead className="bg-surface-secondary">
              <tr>
                <th
                  scope="col"
                  className="w-52 border-r border-border bg-surface-secondary px-5 py-4 font-bold sm:sticky sm:left-0 sm:z-10"
                >
                  {t("metric")}
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
                          ? t("target")
                          : t(
                              "candidate",
                              {
                                index,
                              },
                            )}
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
                        {groupLabels[
                          group.key
                        ] ??
                          group.label}
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
                            {metricLabels[
                              metric.key
                            ] ??
                              metric.label}
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
                                    locale={
                                      locale
                                    }
                                    unavailable={t(
                                      "unavailable",
                                    )}
                                    accessibleLabel={(
                                      totalText,
                                      per90Text,
                                    ) =>
                                      t(
                                        "valueLabel",
                                        {
                                          total:
                                            totalText,
                                          per90:
                                            per90Text,
                                        },
                                      )
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
        {t("guidance")}
      </p>
    </section>
  );
}
