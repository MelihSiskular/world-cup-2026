import {
  useTranslations,
} from "next-intl";

function SkeletonLine({
  className,
}: Readonly<{
  className: string;
}>) {
  return (
    <div
      className={`rounded bg-surface-secondary ${className}`}
    />
  );
}

function SkeletonIdentityCard() {
  return (
    <article className="min-w-0 rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <SkeletonLine className="h-4 w-28" />
          <SkeletonLine className="h-6 w-20 rounded-full" />
        </div>

        <SkeletonLine className="h-7 w-20 rounded-full" />
      </div>

      <div className="mt-5 flex items-start gap-4">
        <div className="size-20 shrink-0 rounded-2xl border border-border bg-surface-secondary" />

        <div className="min-w-0 flex-1">
          <SkeletonLine className="h-9 w-56 max-w-full" />
          <SkeletonLine className="mt-3 h-4 w-28" />
          <SkeletonLine className="mt-3 h-5 w-48 max-w-full" />
        </div>
      </div>

      <div className="mt-7 grid grid-cols-2 gap-x-4 gap-y-5 rounded-2xl bg-surface-secondary p-5 sm:grid-cols-3">
        {Array.from({
          length: 6,
        }).map((_, index) => (
          <div
            key={index}
            className={
              index >= 3
                ? "border-t border-border pt-4 sm:border-t-0 sm:pt-0"
                : ""
            }
          >
            <div className="h-3 w-20 rounded bg-surface" />
            <div className="mt-2 h-5 w-16 rounded bg-surface" />
          </div>
        ))}
      </div>
    </article>
  );
}

function SkeletonComparisonMetric() {
  return (
    <article className="min-w-0 rounded-xl border border-border bg-surface px-4 py-4 shadow-sm">
      <SkeletonLine className="h-3 w-24" />
      <SkeletonLine className="mt-3 h-8 w-16" />
    </article>
  );
}

function SkeletonEvidencePanel() {
  return (
    <section className="overflow-hidden rounded-3xl border border-border bg-surface shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border px-5 py-5 sm:px-7 sm:py-6">
        <div className="max-w-3xl flex-1">
          <SkeletonLine className="h-3 w-40" />
          <SkeletonLine className="mt-3 h-8 w-64 max-w-full" />
          <SkeletonLine className="mt-3 h-4 w-full max-w-xl" />
        </div>

        <div className="flex gap-2">
          <SkeletonLine className="h-7 w-20 rounded-full" />
          <SkeletonLine className="h-7 w-20 rounded-full" />
        </div>
      </div>

      <div className="grid gap-6 p-5 sm:p-7 lg:grid-cols-[minmax(0,1.35fr)_minmax(18rem,0.65fr)]">
        <div>
          <SkeletonLine className="h-3 w-32" />

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {Array.from({
              length: 2,
            }).map((_, index) => (
              <div
                key={index}
                className="rounded-xl border border-border bg-surface-secondary px-4 py-4"
              >
                <SkeletonLine className="h-4 w-full" />
                <SkeletonLine className="mt-2 h-4 w-4/5" />
              </div>
            ))}
          </div>
        </div>

        <div>
          <SkeletonLine className="h-3 w-28" />

          <div className="mt-4 space-y-3">
            {Array.from({
              length: 3,
            }).map((_, index) => (
              <div
                key={index}
                className="flex items-center justify-between rounded-xl border border-border bg-page px-4 py-3.5"
              >
                <SkeletonLine className="h-4 w-28" />
                <SkeletonLine className="h-7 w-14 rounded-full" />
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-border px-5 py-4 sm:px-7">
        <SkeletonLine className="h-3 w-80 max-w-full" />

        <div className="flex gap-2">
          <div className="h-10 w-32 rounded-xl bg-surface-secondary" />
          <div className="h-10 w-28 rounded-xl bg-surface-secondary" />
        </div>
      </div>
    </section>
  );
}

export function PlayerComparisonSkeleton() {
  const t = useTranslations(
    "PlayerComparison",
  );

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={t("preparing")}
      className="animate-pulse space-y-8 motion-reduce:animate-none"
    >
      <section className="grid gap-4 lg:grid-cols-2">
        <SkeletonIdentityCard />
        <SkeletonIdentityCard />
      </section>

      <section
        aria-hidden="true"
        className="comparison-indicator-grid grid gap-3 py-5"
      >
        {Array.from({
          length: 5,
        }).map((_, index) => (
          <SkeletonComparisonMetric
            key={index}
          />
        ))}
      </section>

      <div className="py-1">
        <SkeletonEvidencePanel />
      </div>

      <span className="sr-only">
        {t("preparing")}
      </span>
    </div>
  );
}
