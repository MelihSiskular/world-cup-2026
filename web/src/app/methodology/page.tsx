import type {
  Metadata,
} from "next";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  PageIntro,
} from "@/components/layout/page-intro";

export const metadata: Metadata = {
  title: "Methodology",
  description:
    "How WC26 Transfer Intelligence evaluates player replacements.",
};

const methodologySections = [
  {
    title: "Statistical similarity",
    description:
      "Compares position-relevant tournament performance using normalized and reliability-aware player features.",
  },
  {
    title: "Spatial fit",
    description:
      "Evaluates occupied zones, lateral and vertical profiles, heatmap overlap and positional behavior.",
  },
  {
    title: "Recruitment context",
    description:
      "Separates immediate, development, value and short-term recruitment scenarios instead of producing one universal ranking.",
  },
] as const;

export default function MethodologyPage() {
  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow="Methodology"
        title="Similarity is evidence, not the final decision"
        description="WC26 Transfer Intelligence combines statistical, spatial, reliability and market signals to support structured recruitment analysis."
      />

      <section className="mt-12 grid gap-5 lg:grid-cols-3">
        {methodologySections.map(
          (section) => (
            <article
              key={section.title}
              className="rounded-2xl border border-border bg-surface p-6 shadow-sm"
            >
              <div className="mb-5 size-2 rounded-full bg-brand" />

              <h2 className="text-xl font-bold tracking-[-0.025em]">
                {section.title}
              </h2>

              <p className="mt-3 text-sm leading-6 text-muted">
                {section.description}
              </p>
            </article>
          ),
        )}
      </section>

      <aside className="mt-8 rounded-2xl border border-brand/20 bg-surface-secondary p-6">
        <h2 className="font-bold text-brand-dark">
          Decision-support boundary
        </h2>

        <p className="mt-2 max-w-4xl text-sm leading-6 text-muted">
          Recommendation rankings are calculated by the FastAPI
          analytics service. The frontend displays those results and
          must not recreate or modify the underlying ranking logic.
        </p>
      </aside>
    </PageContainer>
  );
}
