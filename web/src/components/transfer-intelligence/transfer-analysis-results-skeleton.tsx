export function TransferAnalysisResultsSkeleton() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="space-y-6"
    >
      <section className="animate-pulse rounded-3xl border border-border bg-surface p-6 sm:p-8">
        <div className="h-4 w-36 rounded bg-surface-secondary" />
        <div className="mt-5 h-10 w-72 max-w-full rounded bg-surface-secondary" />

        <div className="mt-7 grid gap-3 sm:grid-cols-4">
          {Array.from({
            length: 4,
          }).map((_, index) => (
            <div
              key={index}
              className="h-20 rounded-xl bg-surface-secondary"
            />
          ))}
        </div>
      </section>

      <div className="grid animate-pulse gap-3 sm:grid-cols-4">
        {Array.from({
          length: 4,
        }).map((_, index) => (
          <div
            key={index}
            className="h-20 rounded-xl border border-border bg-surface"
          />
        ))}
      </div>

      <div className="space-y-4">
        {Array.from({
          length: 5,
        }).map((_, index) => (
          <div
            key={index}
            className="h-72 animate-pulse rounded-2xl border border-border bg-surface"
          />
        ))}
      </div>

      <span className="sr-only">
        Running transfer analysis…
      </span>
    </div>
  );
}
