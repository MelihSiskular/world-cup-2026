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
): string {
  if (
    value === null ||
    value === undefined ||
    value.trim() === ""
  ) {
    return "Not reported";
  }

  return value;
}

function TacticalProfileComparison({
  row,
}: Readonly<{
  row: TacticalProfileRow;
}>) {
  return (
    <div
      className="grid items-center gap-4 border-b border-border/70 py-4 last:border-b-0"
      style={{
        gridTemplateColumns:
          "7.5rem minmax(0, 1fr) 1.5rem minmax(0, 1fr)",
      }}
    >
      <p className="text-xs font-medium text-muted">
        {row.label}
      </p>

      <div className="min-w-0">
        <p className="text-[0.68rem] font-semibold tracking-[0.08em] text-muted uppercase sm:hidden">
          Target
        </p>

        <p className="mt-1 min-w-0 break-words text-sm font-semibold sm:mt-0">
          {formatRoleValue(
            row.target,
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
          Candidate
        </p>

        <p className="mt-1 min-w-0 break-words text-sm font-semibold sm:mt-0">
          {formatRoleValue(
            row.candidate,
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
  const rows: readonly TacticalProfileRow[] =
    [
      {
        label: "Final role",
        target: target.final_role,
        candidate:
          candidate.final_role,
      },
      {
        label: "Archetype",
        target: target.archetype,
        candidate:
          candidate.archetype,
      },
      {
        label: "Spatial role",
        target: target.spatial_role,
        candidate:
          candidate.spatial_role,
      },
      {
        label: "Lateral profile",
        target:
          target.lateral_profile,
        candidate:
          candidate.lateral_profile,
      },
      {
        label: "Vertical profile",
        target:
          target.vertical_profile,
        candidate:
          candidate.vertical_profile,
      },
      {
        label: "Mobility",
        target:
          target.mobility_profile,
        candidate:
          candidate.mobility_profile,
      },
      {
        label: "Role confidence",
        target:
          formatProfilePercentage(
            target.role_confidence_pct,
          ),
        candidate:
          formatProfilePercentage(
            candidate.role_confidence_pct,
          ),
      },
    ];

  return (
    <article className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
      <div className="border-b border-border p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div className="max-w-xl">
            <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
              Role compatibility
            </p>

            <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
              Tactical role alignment
            </h2>

            <p className="mt-2 text-sm leading-6 text-muted">
              Compare how the target and candidate are profiled across role,
              archetype, pitch zone and movement behaviour.
            </p>
          </div>

        </div>
      </div>

      <div className="p-5 sm:p-6">
        <p className="mb-4 text-xs font-semibold tracking-[0.12em] text-muted uppercase">
          Tactical profile
        </p>

        <div
          className="grid gap-4 border-b border-border pb-3"
          style={{
            gridTemplateColumns:
              "7.5rem minmax(0, 1fr) 1.5rem minmax(0, 1fr)",
          }}
        >
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
            />
          ))}
        </div>

      </div>
    </article>
  );
}
