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

function EvidenceBadge({
  label,
  value,
}: Readonly<{
  label: string;
  value: boolean | null | undefined;
}>) {
  if (typeof value !== "boolean") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full border border-border bg-page px-3 py-1.5 text-xs font-semibold text-muted">
        <span
          aria-hidden="true"
          className="size-1.5 rounded-full bg-muted"
        />
        {label} unavailable
      </span>
    );
  }

  return (
    <span
      className={
        value
          ? "inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3 py-1.5 text-xs font-semibold text-brand-dark"
          : "inline-flex items-center gap-2 rounded-full border border-border bg-page px-3 py-1.5 text-xs font-semibold text-muted"
      }
    >
      <span
        aria-hidden="true"
        className={
          value
            ? "size-1.5 rounded-full bg-brand"
            : "size-1.5 rounded-full bg-muted"
        }
      />

      {label}

      <span className="font-bold">
        {value ? "Yes" : "No"}
      </span>
    </span>
  );
}

function TacticalProfileComparison({
  row,
}: Readonly<{
  row: TacticalProfileRow;
}>) {
  return (
    <div className="grid gap-3 border-b border-border/70 py-3 last:border-b-0 sm:grid-cols-[8.5rem_minmax(0,1fr)_1.5rem_minmax(0,1fr)] sm:items-center sm:gap-3">
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
    ];

  return (
    <article className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
      <div className="border-b border-border p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
              Role compatibility
            </p>

            <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">
              Tactical role alignment
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
              Compare the target and candidate
              across the tactical role evidence
              already used by the recruitment
              model.
            </p>
          </div>

          <div className="min-w-32 rounded-2xl border border-brand/15 bg-surface-secondary px-4 py-3 text-right">
            <p className="text-xs font-medium text-muted">
              Role fit
            </p>

            <p className="mt-1 text-3xl font-bold tracking-[-0.04em] text-brand-dark">
              {formatProfilePercentage(
                candidate.role_fit_pct,
              )}
            </p>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          <EvidenceBadge
            label="Same final role"
            value={
              candidate.same_final_role
            }
          />

          <EvidenceBadge
            label="Same archetype"
            value={
              candidate.same_archetype
            }
          />
        </div>
      </div>

      <div className="p-5 sm:p-6">
        <div className="hidden grid-cols-[8.5rem_minmax(0,1fr)_1.5rem_minmax(0,1fr)] gap-3 border-b border-border pb-3 sm:grid">
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

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-border bg-page p-4">
            <p className="text-xs text-muted">
              Target role confidence
            </p>

            <p className="mt-2 text-lg font-bold">
              {formatProfilePercentage(
                target.role_confidence_pct,
              )}
            </p>
          </div>

          <div className="rounded-xl border border-border bg-page p-4">
            <p className="text-xs text-muted">
              Candidate role confidence
            </p>

            <p className="mt-2 text-lg font-bold">
              {formatProfilePercentage(
                candidate.role_confidence_pct,
              )}
            </p>
          </div>
        </div>
      </div>
    </article>
  );
}
