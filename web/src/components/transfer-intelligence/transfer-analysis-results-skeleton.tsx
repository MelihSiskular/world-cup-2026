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

function SkeletonTargetMetric() {
  return (
    <div className="rounded-xl border border-border bg-surface-secondary px-4 py-3">
      <SkeletonLine className="h-3 w-20" />
      <SkeletonLine className="mt-2 h-6 w-16" />
    </div>
  );
}

function SkeletonFeaturedRecommendation() {
  return (
    <article className="overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
      <div className="grid lg:grid-cols-[minmax(0,1fr)_13rem]">
        <div className="p-5 sm:p-6">
          <div className="flex items-start gap-4">
            <div className="size-18 shrink-0 rounded-2xl border border-border bg-surface-secondary" />

            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <div className="size-9 rounded-xl bg-surface-secondary" />
                <SkeletonLine className="h-7 w-24 rounded-full" />
                <SkeletonLine className="h-7 w-28 rounded-full" />
              </div>

              <SkeletonLine className="mt-4 h-8 w-56 max-w-full" />
              <SkeletonLine className="mt-2 h-4 w-28" />
              <SkeletonLine className="mt-3 h-5 w-52 max-w-full" />
            </div>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({
              length: 4,
            }).map((_, index) => (
              <div
                key={index}
                className="rounded-xl border border-border bg-page p-3"
              >
                <SkeletonLine className="h-3 w-24" />
                <SkeletonLine className="mt-2 h-5 w-14" />
              </div>
            ))}
          </div>

          <div className="mt-5 rounded-xl border border-border bg-page p-4">
            <SkeletonLine className="h-3 w-32" />
            <SkeletonLine className="mt-3 h-4 w-full" />
            <SkeletonLine className="mt-2 h-4 w-5/6" />
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <div className="h-10 w-40 rounded-xl bg-surface-secondary" />
            <div className="h-10 w-36 rounded-xl bg-surface-secondary" />
          </div>
        </div>

        <aside className="border-t border-border bg-surface-secondary p-5 lg:border-t-0 lg:border-l">
          <SkeletonLine className="h-3 w-24" />
          <SkeletonLine className="mt-3 h-9 w-16" />

          <div className="mt-6 space-y-4">
            {Array.from({
              length: 3,
            }).map((_, index) => (
              <div key={index}>
                <SkeletonLine className="h-3 w-20" />
                <SkeletonLine className="mt-2 h-4 w-24" />
              </div>
            ))}
          </div>
        </aside>
      </div>
    </article>
  );
}

function SkeletonCompactRecommendation() {
  return (
    <article className="rounded-2xl border border-border bg-surface p-5 shadow-sm sm:p-6">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex min-w-0 items-start gap-4">
          <div className="size-18 shrink-0 rounded-2xl border border-border bg-surface-secondary" />

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <SkeletonLine className="h-6 w-10 rounded-full" />
              <SkeletonLine className="h-6 w-24 rounded-full" />
              <SkeletonLine className="h-6 w-28 rounded-full" />
            </div>

            <SkeletonLine className="mt-4 h-7 w-48 max-w-full" />
            <SkeletonLine className="mt-2 h-4 w-24" />
            <SkeletonLine className="mt-3 h-4 w-44 max-w-full" />
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-2 xl:w-[30rem] xl:grid-cols-4">
          {Array.from({
            length: 4,
          }).map((_, index) => (
            <div
              key={index}
              className="rounded-xl border border-border bg-page px-3 py-2.5"
            >
              <SkeletonLine className="h-3 w-16" />
              <SkeletonLine className="mt-2 h-5 w-12" />
            </div>
          ))}
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-4 border-t border-border pt-4">
        <div className="flex flex-wrap gap-5">
          <SkeletonLine className="h-3 w-24" />
          <SkeletonLine className="h-3 w-20" />
          <SkeletonLine className="h-3 w-24" />
        </div>

        <div className="flex gap-2">
          <div className="h-9 w-20 rounded-xl bg-surface-secondary" />
          <div className="h-9 w-20 rounded-xl bg-surface-secondary" />
        </div>
      </div>
    </article>
  );
}

export function TransferAnalysisResultsSkeleton() {
  const translations =
    useTranslations(
      "TransferAnalysisResults",
    );

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={translations(
        "runningAnalysis",
      )}
      className="animate-pulse space-y-10 motion-reduce:animate-none"
    >
      <section className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex min-w-0 items-center gap-4">
            <div className="size-20 shrink-0 rounded-2xl border border-border bg-surface-secondary" />

            <div className="min-w-0">
              <SkeletonLine className="h-3 w-24" />
              <SkeletonLine className="mt-3 h-8 w-56 max-w-full" />
              <SkeletonLine className="mt-3 h-4 w-48 max-w-full" />
              <SkeletonLine className="mt-2 h-4 w-60 max-w-full" />
            </div>
          </div>

          <div className="grid gap-2 sm:grid-cols-3 xl:min-w-[31rem]">
            <SkeletonTargetMetric />
            <SkeletonTargetMetric />
            <SkeletonTargetMetric />
          </div>
        </div>

        <div className="mt-5 border-t border-border pt-5">
          <div className="h-10 w-44 rounded-xl bg-surface-secondary" />
        </div>
      </section>

      <section>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="max-w-2xl flex-1">
            <SkeletonLine className="h-3 w-28" />
            <SkeletonLine className="mt-3 h-9 w-64 max-w-full" />
            <SkeletonLine className="mt-3 h-4 w-full max-w-xl" />
            <SkeletonLine className="mt-2 h-4 w-4/5 max-w-lg" />
          </div>

          <div className="xl:text-right">
            <SkeletonLine className="mb-3 h-3 w-36 xl:ml-auto" />

            <div className="flex flex-wrap gap-2 xl:justify-end">
              {Array.from({
                length: 4,
              }).map((_, index) => (
                <div
                  key={index}
                  className="h-10 w-28 rounded-xl border border-border bg-surface"
                />
              ))}
            </div>
          </div>
        </div>

        <section className="mt-10 sm:mt-12">
          <div className="mb-5">
            <SkeletonLine className="h-3 w-36" />
            <SkeletonLine className="mt-2 h-6 w-72 max-w-full" />
          </div>

          <SkeletonFeaturedRecommendation />
        </section>

        <section className="mt-8">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div>
              <SkeletonLine className="h-3 w-28" />
              <SkeletonLine className="mt-2 h-6 w-64 max-w-full" />
            </div>

            <SkeletonLine className="h-4 w-24" />
          </div>

          <div className="space-y-4">
            <SkeletonCompactRecommendation />
            <SkeletonCompactRecommendation />
          </div>
        </section>
      </section>

      <span className="sr-only">
        {translations(
          "runningAnalysis",
        )}
      </span>
    </div>
  );
}
