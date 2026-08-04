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
  title: "Players",
  description:
    "Search the World Cup 2026 player catalogue and open scouting profiles.",
};

const workflowItems = [
  {
    title: "Search",
    description:
      "Find players by name through the typed player catalogue API.",
  },
  {
    title: "Profile",
    description:
      "Inspect identity, role, reliability, performance and market context.",
  },
  {
    title: "Analyze",
    description:
      "Run replacement analysis using a stable player identifier.",
  },
] as const;

export default function PlayersPage() {
  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow="Player catalogue"
        title="Search and inspect tournament players"
        description="The catalogue API, stable player identities and profile contracts are connected. The interactive search workflow is the next product delivery."
      />

      <section className="mt-12 grid gap-5 md:grid-cols-3">
        {workflowItems.map((item) => (
          <article
            key={item.title}
            className="rounded-2xl border border-border bg-surface p-6 shadow-sm"
          >
            <div className="size-10 rounded-xl bg-surface-secondary" />

            <h2 className="mt-5 text-lg font-bold">
              {item.title}
            </h2>

            <p className="mt-2 text-sm leading-6 text-muted">
              {item.description}
            </p>
          </article>
        ))}
      </section>
    </PageContainer>
  );
}
