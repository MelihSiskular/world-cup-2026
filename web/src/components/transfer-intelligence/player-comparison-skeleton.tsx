export function PlayerComparisonSkeleton() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="space-y-6"
    >
      <section className="grid animate-pulse gap-4 lg:grid-cols-2">
        {Array.from({
          length: 2,
        }).map((_, index) => (
          <div
            key={index}
            className="h-72 rounded-3xl border border-border bg-surface p-6"
          >
            <div className="h-5 w-28 rounded bg-surface-secondary" />
            <div className="mt-6 h-10 w-56 rounded bg-surface-secondary" />
            <div className="mt-4 h-5 w-40 rounded bg-surface-secondary" />
            <div className="mt-8 h-24 rounded-xl bg-surface-secondary" />
          </div>
        ))}
      </section>

      <section className="grid animate-pulse gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({
          length: 4,
        }).map((_, index) => (
          <div
            key={index}
            className="h-28 rounded-2xl border border-border bg-surface"
          />
        ))}
      </section>

      <section className="h-[30rem] animate-pulse rounded-2xl border border-border bg-surface" />

      <span className="sr-only">
        Preparing player comparison…
      </span>
    </div>
  );
}
