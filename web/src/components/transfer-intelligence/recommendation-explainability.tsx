import type {
  TransferRecommendationResponse,
} from "@/lib/api/types";
import {
  formatProfileNumber,
  formatProfilePercentage,
} from "@/lib/players/profile-format";

type RecommendationExplainabilityProps =
  Readonly<{
    explainability:
      TransferRecommendationResponse["explainability"];
  }>;

function formatScore(
  value: number,
): string {
  return formatProfileNumber(
    value,
    {
      maximumFractionDigits: 2,
    },
  );
}

function formatWeight(
  value: number,
): string {
  return formatProfilePercentage(
    value * 100,
  );
}

function getEvidenceLabel(
  status:
    | "available"
    | "fallback"
    | "missing",
): string {
  switch (status) {
    case "available":
      return "Direct evidence";

    case "fallback":
      return "Fallback input";

    case "missing":
      return "Missing input";
  }
}

export function RecommendationExplainability({
  explainability,
}: RecommendationExplainabilityProps) {
  const {
    score,
    signals,
    bonuses,
    reasons,
  } = explainability;

  return (
    <section className="mt-6 overflow-hidden rounded-xl border border-brand/15 bg-surface-secondary">
      <div className="p-4">
        <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
          Why this candidate
        </p>

        <ul className="mt-3 grid gap-x-6 gap-y-1.5 sm:grid-cols-2">
          {reasons.map((reason) => (
            <li
              key={`${reason.group}:${reason.key}`}
              className="flex gap-2 text-sm leading-6 text-muted"
            >
              <span
                aria-hidden="true"
                className="mt-[0.65rem] size-1.5 shrink-0 rounded-full bg-brand"
              />

              <span className="break-words">
                {reason.text}
              </span>
            </li>
          ))}
        </ul>

        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-1 border-t border-border/70 pt-3 text-xs">
          <span className="text-muted">
            Weighted signals{" "}
            <strong className="text-brand-dark">
              {formatScore(
                score.weighted_signal_total,
              )}
            </strong>
          </span>

          <span className="text-muted">
            Applied bonuses{" "}
            <strong className="text-brand-dark">
              +
              {formatScore(
                score.bonus_total,
              )}
            </strong>
          </span>
        </div>
      </div>

      <details className="group border-t border-border/70">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-3 text-sm font-semibold transition-colors hover:bg-surface sm:px-5">
          <span>
            View score breakdown
          </span>

          <span
            aria-hidden="true"
            className="text-lg leading-none text-brand transition-transform group-open:rotate-45"
          >
            +
          </span>
        </summary>

        <div className="border-t border-border/70 bg-surface p-4 sm:p-5">
          <div>
            <p className="text-xs font-semibold tracking-[0.12em] text-muted uppercase">
              Score composition
            </p>

            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-lg border border-border bg-page p-3">
                <dt className="text-xs text-muted">
                  Weighted signals
                </dt>

                <dd className="mt-1 font-bold">
                  {formatScore(
                    score.weighted_signal_total,
                  )}
                </dd>
              </div>

              <div className="rounded-lg border border-border bg-page p-3">
                <dt className="text-xs text-muted">
                  Bonuses
                </dt>

                <dd className="mt-1 font-bold">
                  +
                  {formatScore(
                    score.bonus_total,
                  )}
                </dd>
              </div>

              <div className="rounded-lg border border-border bg-page p-3">
                <dt className="text-xs text-muted">
                  Pre-clip score
                </dt>

                <dd className="mt-1 font-bold">
                  {formatScore(
                    score.pre_clip_score,
                  )}
                </dd>
              </div>

              <div className="rounded-lg border border-border bg-page p-3">
                <dt className="text-xs text-muted">
                  Final score
                </dt>

                <dd className="mt-1 font-bold text-brand-dark">
                  {formatScore(
                    score.final_score,
                  )}
                </dd>
              </div>
            </dl>

            {score.was_clipped ? (
              <p className="mt-2 text-xs leading-5 text-muted">
                The pre-clip score was
                constrained to the model&apos;s
                0–100 output range.
              </p>
            ) : null}
          </div>

          <div className="mt-6">
            <p className="text-xs font-semibold tracking-[0.12em] text-muted uppercase">
              Weighted signals
            </p>

            <div className="mt-3 divide-y divide-border rounded-xl border border-border">
              {signals.map(
                (signal) => (
                  <div
                    key={signal.key}
                    className="grid gap-3 p-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-semibold">
                          {signal.label}
                        </p>

                        {signal.evidence_status !==
                        "available" ? (
                          <span className="rounded-full border border-border px-2 py-0.5 text-[0.68rem] font-semibold text-muted">
                            {getEvidenceLabel(
                              signal.evidence_status,
                            )}
                          </span>
                        ) : null}
                      </div>

                      <p className="mt-1 text-xs leading-5 text-muted">
                        {
                          signal.description
                        }
                      </p>

                      {signal.note ? (
                        <p className="mt-2 text-xs leading-5 text-muted">
                          {signal.note}
                        </p>
                      ) : null}
                    </div>

                    <dl className="grid grid-cols-3 gap-3 text-right text-xs sm:min-w-64">
                      <div>
                        <dt className="text-muted">
                          Input
                        </dt>

                        <dd className="mt-1 font-semibold">
                          {formatProfilePercentage(
                            signal.input_score,
                          )}
                        </dd>
                      </div>

                      <div>
                        <dt className="text-muted">
                          Weight
                        </dt>

                        <dd className="mt-1 font-semibold">
                          {formatWeight(
                            signal.weight,
                          )}
                        </dd>
                      </div>

                      <div>
                        <dt className="text-muted">
                          Contribution
                        </dt>

                        <dd className="mt-1 font-bold text-brand-dark">
                          +
                          {formatScore(
                            signal.weighted_contribution,
                          )}
                        </dd>
                      </div>
                    </dl>
                  </div>
                ),
              )}
            </div>
          </div>

          <div className="mt-6">
            <p className="text-xs font-semibold tracking-[0.12em] text-muted uppercase">
              Mode bonuses
            </p>

            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {bonuses.map((bonus) => (
                <div
                  key={bonus.key}
                  className="flex items-center justify-between gap-3 rounded-lg border border-border bg-page p-3 text-sm"
                >
                  <div>
                    <p className="font-semibold">
                      {bonus.label}
                    </p>

                    <p className="mt-1 text-xs text-muted">
                      {bonus.applied
                        ? "Applied"
                        : "Not applied"}
                    </p>
                  </div>

                  <span className="font-bold text-brand-dark">
                    {bonus.applied
                      ? `+${formatScore(
                          bonus.applied_points,
                        )}`
                      : "—"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <p className="mt-6 border-t border-border pt-4 text-xs leading-5 text-muted">
            This score explains model fit
            within the selected recruitment
            scenario. It is not a probability
            that a transfer will succeed.
          </p>
        </div>
      </details>
    </section>
  );
}
