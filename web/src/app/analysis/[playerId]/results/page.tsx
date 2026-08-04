import Link from "next/link";
import {
  notFound,
} from "next/navigation";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  PageIntro,
} from "@/components/layout/page-intro";

type AnalysisResultsPageProps =
  Readonly<{
    params: Promise<{
      playerId: string;
    }>;
  }>;

export default async function AnalysisResultsPage({
  params,
}: AnalysisResultsPageProps) {
  const {
    playerId,
  } = await params;

  const parsedPlayerId =
    Number(playerId);

  if (
    !Number.isSafeInteger(
      parsedPlayerId,
    ) ||
    parsedPlayerId <= 0
  ) {
    notFound();
  }

  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow="Transfer intelligence"
        title="Recommendation results"
        description="The validated recruitment configuration has been preserved in the URL. Ranked scenario results will be connected in the next delivery."
        actions={
          <Link
            href={`/analysis/${parsedPlayerId}`}
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold transition-colors hover:bg-surface-secondary"
          >
            Adjust parameters
          </Link>
        }
      />

      <section className="mt-12 rounded-2xl border border-border bg-surface p-6 shadow-sm">
        <p className="font-semibold">
          Analysis configuration ready
        </p>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          Phase 5D.2 will submit these
          parameters to the typed transfer
          analysis endpoint and present all
          four recommendation modes.
        </p>
      </section>
    </PageContainer>
  );
}
