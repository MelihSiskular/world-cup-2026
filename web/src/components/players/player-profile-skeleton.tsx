export function PlayerProfileSkeleton() {
  return (
    <div
      className="space-y-6"
      role="status"
      aria-live="polite"
      aria-label="Loading player profile"
    >
      <section className="animate-pulse rounded-3xl border border-border bg-surface p-6 sm:p-8">
        <div className="h-5 w-40 rounded bg-surface-secondary" />
        <div className="mt-6 h-11 w-72 max-w-full rounded bg-surface-secondary" />
        <div className="mt-4 h-5 w-52 rounded bg-surface-secondary" />

        <div className="mt-8 flex gap-3">
          <div className="h-11 w-40 rounded-xl bg-surface-secondary" />
          <div className="h-11 w-44 rounded-xl bg-surface-secondary" />
        </div>
      </section>

      <section className="grid animate-pulse gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({
          length: 4,
        }).map((_, index) => (
          <div
            key={index}
            className="h-32 rounded-2xl border border-border bg-surface p-5"
          >
            <div className="h-4 w-24 rounded bg-surface-secondary" />
            <div className="mt-5 h-8 w-20 rounded bg-surface-secondary" />
          </div>
        ))}
      </section>

      <section className="grid animate-pulse gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="h-96 rounded-2xl border border-border bg-surface" />
        <div className="h-96 rounded-2xl border border-border bg-surface" />
      </section>

      <span className="sr-only">
        Loading player scouting profile…
      </span>
    </div>
  );
}
