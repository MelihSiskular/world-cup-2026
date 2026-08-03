const foundationItems = [
  "Next.js App Router",
  "Strict TypeScript",
  "Tailwind CSS",
  "WC26 design tokens",
] as const;

export default function HomePage() {
  return (
    <main className="min-h-screen bg-page px-6 py-12 text-foreground sm:px-10 lg:px-16">
      <section className="mx-auto flex min-h-[calc(100vh-6rem)] max-w-6xl items-center">
        <div className="w-full">
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-2 text-sm font-medium text-brand-dark shadow-sm">
            <span
              aria-hidden="true"
              className="size-2 rounded-full bg-brand-accent"
            />
            Phase 5 · Web Product Foundation
          </div>

          <div className="max-w-4xl">
            <p className="mb-4 text-sm font-semibold tracking-[0.18em] text-brand uppercase">
              WC26 Transfer Intelligence
            </p>

            <h1 className="text-4xl leading-tight font-bold tracking-[-0.04em] text-balance sm:text-6xl lg:text-7xl">
              Find the right replacement.
              <span className="block text-brand">
                Not just the most similar player.
              </span>
            </h1>

            <p className="mt-7 max-w-2xl text-lg leading-8 text-muted">
              A professional football scouting and player replacement
              analysis product powered by World Cup 2026 data.
            </p>
          </div>

          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {foundationItems.map((item) => (
              <div
                key={item}
                className="rounded-2xl border border-border bg-surface p-5 shadow-sm"
              >
                <div className="mb-4 size-2 rounded-full bg-brand" />
                <p className="font-semibold">{item}</p>
              </div>
            ))}
          </div>

          <div className="mt-10 rounded-2xl border border-brand/20 bg-surface-secondary p-5 text-sm leading-6 text-muted">
            The frontend foundation is running. Player search, profiles,
            transfer analysis and comparison workflows will be added in the
            next Phase 5 steps.
          </div>
        </div>
      </section>
    </main>
  );
}
