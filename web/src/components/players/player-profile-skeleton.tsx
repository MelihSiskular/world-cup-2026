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

function SkeletonMetricCard() {
  return (
    <div className="rounded-2xl border border-border bg-page p-4 sm:p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <SkeletonLine className="h-4 w-28" />
          <SkeletonLine className="mt-2 h-3 w-16" />
        </div>

        <SkeletonLine className="h-7 w-14 shrink-0" />
      </div>

      <div className="mt-5">
        <div className="flex items-center justify-between gap-4">
          <SkeletonLine className="h-3 w-32" />
          <SkeletonLine className="h-4 w-8" />
        </div>

        <SkeletonLine className="mt-2 h-1.5 w-full rounded-full" />
        <SkeletonLine className="mt-3 h-3 w-24" />
      </div>
    </div>
  );
}

function SkeletonInsightCard() {
  return (
    <div className="rounded-2xl border border-border bg-page p-4 sm:p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <SkeletonLine className="h-3 w-20" />
          <SkeletonLine className="mt-3 h-5 w-32" />
        </div>

        <div className="shrink-0">
          <SkeletonLine className="h-7 w-10" />
          <SkeletonLine className="mt-2 h-2.5 w-14" />
        </div>
      </div>

      <SkeletonLine className="mt-4 h-2 w-full rounded-full" />
      <SkeletonLine className="mt-4 h-3 w-full" />
      <SkeletonLine className="mt-2 h-3 w-4/5" />
    </div>
  );
}

function SkeletonContextCard() {
  return (
    <div className="rounded-2xl border border-border bg-surface p-4 shadow-sm">
      <SkeletonLine className="h-3 w-24" />
      <SkeletonLine className="mt-3 h-7 w-16" />
      <SkeletonLine className="mt-3 h-3 w-full" />
      <SkeletonLine className="mt-2 h-3 w-3/4" />
    </div>
  );
}

export function PlayerProfileSkeleton({
  label,
}: Readonly<{
  label: string;
}>) {
  return (
    <div
      className="space-y-6"
      role="status"
      aria-live="polite"
      aria-label={label}
    >
      <section className="animate-pulse rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-8">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(20rem,26rem)] lg:items-start">
          <div className="flex flex-col gap-7 sm:flex-row sm:items-start">
            <div className="size-42 shrink-0 rounded-3xl border border-border bg-surface-secondary sm:size-44" />

            <div className="min-w-0 flex-1">
              <SkeletonLine className="h-11 w-72 max-w-full sm:h-12" />

              <div className="mt-4 flex items-center gap-2">
                <div className="size-5 rounded-full bg-surface-secondary" />
                <SkeletonLine className="h-4 w-28" />
                <SkeletonLine className="h-4 w-20" />
              </div>

              <SkeletonLine className="mt-5 h-6 w-64 max-w-full" />
              <SkeletonLine className="mt-3 h-4 w-52 max-w-full" />

              <div className="mt-6 flex flex-wrap gap-x-8 gap-y-4 border-t border-border pt-5">
                {Array.from({
                  length: 3,
                }).map((_, index) => (
                  <div
                    key={index}
                    className="min-w-20"
                  >
                    <SkeletonLine className="h-3 w-14" />
                    <SkeletonLine className="mt-2 h-4 w-20" />
                  </div>
                ))}
              </div>

              <div className="mt-7 flex flex-wrap gap-3">
                <div className="h-12 w-44 rounded-xl bg-surface-secondary" />
                <div className="h-12 w-40 rounded-xl bg-surface-secondary" />
              </div>
            </div>
          </div>

          <div className="min-w-0">
            <SkeletonLine className="h-3 w-24" />
            <SkeletonLine className="mt-2 h-5 w-44" />
            <SkeletonLine className="mt-2 h-3 w-full" />
            <SkeletonLine className="mt-1.5 h-3 w-4/5" />

            <div className="mt-3 aspect-[105/68] w-full rounded-2xl border border-border bg-surface-secondary" />

            <div className="mt-3 flex gap-4">
              <SkeletonLine className="h-3 w-16" />
              <SkeletonLine className="h-3 w-24" />
            </div>
          </div>
        </div>
      </section>

      <section className="animate-pulse rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7">
        <div className="max-w-3xl">
          <SkeletonLine className="h-4 w-36" />
          <SkeletonLine className="mt-4 h-7 w-64 max-w-full" />
          <SkeletonLine className="mt-4 h-4 w-full max-w-xl" />
          <SkeletonLine className="mt-2 h-4 w-4/5 max-w-lg" />
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({
            length: 6,
          }).map((_, index) => (
            <SkeletonMetricCard
              key={index}
            />
          ))}
        </div>
      </section>

      <section className="animate-pulse rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7">
        <div className="max-w-3xl">
          <SkeletonLine className="h-4 w-36" />
          <SkeletonLine className="mt-4 h-7 w-52" />
          <SkeletonLine className="mt-4 h-4 w-full max-w-xl" />
          <SkeletonLine className="mt-2 h-4 w-3/4 max-w-lg" />
        </div>

        <div className="mt-7 grid gap-7 xl:grid-cols-[minmax(0,2fr)_minmax(18rem,0.85fr)]">
          <div className="min-w-0">
            <div className="flex items-end justify-between gap-4">
              <div>
                <SkeletonLine className="h-3 w-20" />
                <SkeletonLine className="mt-3 h-6 w-40" />
              </div>

              <SkeletonLine className="h-6 w-20 rounded-full" />
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <SkeletonInsightCard />
              <SkeletonInsightCard />
            </div>
          </div>

          <div className="min-w-0 xl:border-l xl:border-border xl:pl-7">
            <div className="flex items-end justify-between gap-4">
              <div>
                <SkeletonLine className="h-3 w-20" />
                <SkeletonLine className="mt-3 h-6 w-36" />
              </div>

              <SkeletonLine className="h-6 w-20 rounded-full" />
            </div>

            <div className="mt-4">
              <SkeletonInsightCard />
            </div>
          </div>
        </div>
      </section>

      <section className="grid animate-pulse items-start gap-5 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-6">
        <article className="rounded-2xl border border-border bg-surface p-5 shadow-sm sm:p-6">
          <SkeletonLine className="h-4 w-32" />
          <SkeletonLine className="mt-4 h-7 w-56" />

          <div className="mt-5 grid gap-3 md:grid-cols-3">
            {Array.from({
              length: 3,
            }).map((_, index) => (
              <div
                key={index}
                className="rounded-xl border border-border bg-page p-4"
              >
                <SkeletonLine className="h-3 w-24" />
                <SkeletonLine className="mt-3 h-5 w-32 max-w-full" />
              </div>
            ))}
          </div>

          <div className="mt-5 rounded-xl border border-border px-5">
            {Array.from({
              length: 4,
            }).map((_, index) => (
              <div
                key={index}
                className="flex items-center justify-between gap-6 border-b border-border py-4 last:border-b-0"
              >
                <SkeletonLine className="h-4 w-24" />
                <SkeletonLine className="h-4 w-28" />
              </div>
            ))}
          </div>

          <div className="mt-5 h-12 rounded-xl border border-border bg-surface-secondary" />
        </article>

        <aside className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
          <SkeletonLine className="h-4 w-32" />
          <SkeletonLine className="mt-4 h-6 w-44" />
          <SkeletonLine className="mt-4 h-4 w-full" />
          <SkeletonLine className="mt-2 h-4 w-4/5" />

          <div className="mt-6">
            {Array.from({
              length: 6,
            }).map((_, index) => (
              <div
                key={index}
                className="flex items-center justify-between gap-5 border-b border-border py-3 last:border-b-0"
              >
                <SkeletonLine className="h-3 w-24" />
                <SkeletonLine className="h-4 w-16" />
              </div>
            ))}
          </div>

          <div className="mt-6 rounded-xl border border-border bg-surface-secondary p-4">
            <SkeletonLine className="h-3 w-24" />
            <SkeletonLine className="mt-3 h-4 w-full" />
            <SkeletonLine className="mt-2 h-4 w-4/5" />
          </div>
        </aside>
      </section>

      <section className="animate-pulse rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-6">
        <SkeletonLine className="h-3 w-28" />
        <SkeletonLine className="mt-3 h-6 w-56" />
        <SkeletonLine className="mt-3 h-4 w-full max-w-xl" />

        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({
            length: 4,
          }).map((_, index) => (
            <SkeletonContextCard
              key={index}
            />
          ))}
        </div>
      </section>

      <section className="animate-pulse space-y-5">
        <div className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-7">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl flex-1">
              <SkeletonLine className="h-4 w-40" />
              <SkeletonLine className="mt-4 h-7 w-52" />
              <SkeletonLine className="mt-4 h-4 w-full max-w-xl" />
              <SkeletonLine className="mt-2 h-4 w-3/4 max-w-lg" />
            </div>

            <div className="w-full max-w-md rounded-2xl border border-border bg-surface-secondary p-4">
              <SkeletonLine className="h-3 w-28" />
              <SkeletonLine className="mt-3 h-3 w-full" />
              <SkeletonLine className="mt-2 h-3 w-4/5" />
            </div>
          </div>
        </div>

        <div className="grid items-start gap-5 xl:grid-cols-2">
          {Array.from({
            length: 2,
          }).map((_, index) => (
            <div
              key={index}
              className="overflow-hidden rounded-3xl border border-border bg-surface shadow-sm"
            >
              <div className="border-b border-border bg-surface-secondary/55 px-5 py-5 sm:px-6">
                <SkeletonLine className="h-3 w-20" />
                <SkeletonLine className="mt-3 h-6 w-40" />
              </div>

              <div className="space-y-5 px-5 py-5 sm:px-6">
                {Array.from({
                  length: 2,
                }).map((_, metricIndex) => (
                  <div
                    key={metricIndex}
                    className="grid gap-5 border-b border-border pb-5 last:border-b-0 last:pb-0 lg:grid-cols-[minmax(0,1fr)_7.5rem_minmax(13rem,0.9fr)]"
                  >
                    <div>
                      <SkeletonLine className="h-5 w-32" />
                      <SkeletonLine className="mt-2 h-3 w-44 max-w-full" />
                    </div>

                    <div className="lg:text-right">
                      <SkeletonLine className="h-6 w-14 lg:ml-auto" />
                      <SkeletonLine className="mt-2 h-3 w-12 lg:ml-auto" />
                    </div>

                    <div>
                      <div className="flex items-center justify-between gap-4">
                        <SkeletonLine className="h-3 w-28" />
                        <SkeletonLine className="h-4 w-8" />
                      </div>

                      <SkeletonLine className="mt-2 h-2 w-full rounded-full" />
                      <SkeletonLine className="mt-3 h-3 w-32" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <span className="sr-only">
        {label}
      </span>
    </div>
  );
}
