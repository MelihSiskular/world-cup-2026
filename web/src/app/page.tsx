import Link from "next/link";

import {
  PageContainer,
} from "@/components/layout/page-container";

const productSteps = [
  {
    number: "01",
    title: "Find a player",
    description:
      "Search the World Cup 2026 player catalogue.",
  },
  {
    number: "02",
    title: "Inspect the profile",
    description:
      "Review role, spatial profile, reliability, quality and market context.",
  },
  {
    number: "03",
    title: "Analyze replacements",
    description:
      "Compare immediate, development, value and short-term alternatives.",
  },
] as const;

export default function HomePage() {
  return (
    <div>
      <section className="overflow-hidden border-b border-border bg-surface">
        <PageContainer className="relative py-16 sm:py-24 lg:py-28">
          <div
            aria-hidden="true"
            className="absolute -top-32 right-0 size-80 rounded-full bg-brand-accent/20 blur-3xl"
          />

          <div className="relative max-w-5xl">
            <h1 className="mt-1 text-5xl leading-[1.02] font-bold tracking-[-0.055em] text-balance sm:text-6xl lg:text-7xl">
              Find the right replacement.
              <span className="mt-2 block text-brand">
                Not just the most similar player.
              </span>
            </h1>

            <p className="mt-7 max-w-3xl text-lg leading-8 text-muted sm:text-xl">
              Combine statistical similarity, spatial role,
              reliability, market context and recruitment strategy
              in one structured decision-support workflow.
            </p>

            <div className="mt-9 flex flex-wrap gap-3">
              <Link
                href="/players"
                className="inline-flex min-h-12 items-center justify-center rounded-xl bg-brand px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-dark"
              >
                Search players
              </Link>

              <Link
                href="/methodology"
                className="inline-flex min-h-12 items-center justify-center rounded-xl border border-border bg-surface px-6 py-3 text-sm font-semibold text-foreground transition-colors hover:bg-surface-secondary"
              >
                View methodology
              </Link>
            </div>
          </div>
        </PageContainer>
      </section>

      <section>
        <PageContainer className="py-14 sm:py-18">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold tracking-[0.18em] text-brand uppercase">
                Product workflow
              </p>

              <h2 className="mt-3 text-3xl font-bold tracking-[-0.035em]">
                From player search to recruitment decision
              </h2>
            </div>


          </div>

          <div className="mt-5 grid gap-5 lg:grid-cols-3">
            {productSteps.map((step) => (
              <article
                key={step.number}
                className="rounded-2xl border border-border bg-surface p-4 shadow-sm"
              >
                <span className="font-mono text-sm font-semibold text-brand">
                  {step.number}
                </span>

                <h3 className="mt-2 text-xl font-bold tracking-[-0.025em]">
                  {step.title}
                </h3>

                <p className="mt-2 text-sm leading-6 text-muted">
                  {step.description}
                </p>
              </article>
            ))}
          </div>
        </PageContainer>
      </section>
    </div>
  );
}
