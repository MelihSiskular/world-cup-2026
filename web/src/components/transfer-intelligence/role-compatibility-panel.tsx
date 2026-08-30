import {
  useLocale,
  useTranslations,
} from "next-intl";

import type {
  TransferRecommendationResponse,
  TransferTargetResponse,
} from "@/lib/api/types";
import {
  formatProfilePercentage,
} from "@/lib/players/profile-format";

type RoleCompatibilityPanelProps =
  Readonly<{
    target: TransferTargetResponse;
    candidate: TransferRecommendationResponse;
  }>;

type TacticalProfileRow =
  Readonly<{
    label: string;
    target: string | null | undefined;
    candidate: string | null | undefined;
  }>;

function formatRoleValue(
  value: string | null | undefined,
  missingValue: string,
): string {
  if (
    value === null ||
    value === undefined ||
    value.trim() === ""
  ) {
    return missingValue;
  }

  return value;
}

function TacticalProfileComparison({
  row,
  targetLabel,
  candidateLabel,
  missingValue,
}: Readonly<{
  row: TacticalProfileRow;
  targetLabel: string;
  candidateLabel: string;
  missingValue: string;
}>) {
  return (
    <div className="tactical-profile-row grid items-start gap-x-4 gap-y-2 border-b border-border/70 py-4 sm:items-center sm:gap-y-0 last:border-b-0">
      <p className="text-xs font-medium text-muted">
        {row.label}
      </p>

      <div className="min-w-0">
        <p className="text-[0.68rem] font-semibold tracking-[0.08em] text-muted uppercase sm:hidden">
          {targetLabel}
        </p>

        <p className="mt-1 min-w-0 break-words text-sm font-semibold sm:mt-0">
          {formatRoleValue(
            row.target,
            missingValue,
          )}
        </p>
      </div>

      <span
        aria-hidden="true"
        className="hidden text-center text-xs font-bold text-muted sm:block"
      >
        ↔
      </span>

      <div className="min-w-0">
        <p className="text-[0.68rem] font-semibold tracking-[0.08em] text-muted uppercase sm:hidden">
          {candidateLabel}
        </p>

        <p className="mt-1 min-w-0 break-words text-sm font-semibold sm:mt-0">
          {formatRoleValue(
            row.candidate,
            missingValue,
          )}
        </p>
      </div>
    </div>
  );
}

export function RoleCompatibilityPanel({
  target,
  candidate,
}: RoleCompatibilityPanelProps) {
  const locale = useLocale();
  const t = useTranslations(
    "RoleCompatibilityPanel",
  );

  const rows: readonly TacticalProfileRow[] =
    [
      {
        label: t("finalRole"),
        target: target.final_role,
        candidate:
          candidate.final_role,
      },
      {
        label: t("archetype"),
        target: target.archetype,
        candidate:
          candidate.archetype,
      },
      {
        label: t("spatialRole"),
        target: target.spatial_role,
        candidate:
          candidate.spatial_role,
      },
      {
        label: t("lateralProfile"),
        target:
          target.lateral_profile,
        candidate:
          candidate.lateral_profile,
      },
      {
        label: t("verticalProfile"),
        target:
          target.vertical_profile,
        candidate:
          candidate.vertical_profile,
      },
      {
        label: t("mobility"),
        target:
          target.mobility_profile,
        candidate:
          candidate.mobility_profile,
      },
      {
        label: t("roleConfidence"),
        target:
          formatProfilePercentage(
            target.role_confidence_pct,
            {
              locale,
              missingValue:
                t("notReported"),
            },
          ),
        candidate:
          formatProfilePercentage(
            candidate.role_confidence_pct,
            {
              locale,
              missingValue:
                t("notReported"),
            },
          ),
      },
    ];

  return (
    <article className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
      <div className="border-b border-border p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div className="max-w-xl">
            <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
              {t("eyebrow")}
            </p>

            <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
              {t("title")}
            </h2>

            <p className="mt-2 text-sm leading-6 text-muted">
              {t("description")}
            </p>
          </div>

        </div>
      </div>

      <div className="p-5 sm:p-6">
        <p className="mb-4 text-xs font-semibold tracking-[0.12em] text-muted uppercase">
          {t("profile")}
        </p>

        <div className="tactical-profile-header hidden gap-4 border-b border-border pb-3 sm:grid">
          <span />

          <p className="text-xs font-semibold tracking-[0.1em] text-muted uppercase">
            {target.player_name}
          </p>

          <span />

          <p className="text-xs font-semibold tracking-[0.1em] text-muted uppercase">
            {candidate.player_name}
          </p>
        </div>

        <div>
          {rows.map((row) => (
            <TacticalProfileComparison
              key={row.label}
              row={row}
              targetLabel={t("target")}
              candidateLabel={t(
                "candidate",
              )}
              missingValue={t(
                "notReported",
              )}
            />
          ))}
        </div>

      </div>
    </article>
  );
}
