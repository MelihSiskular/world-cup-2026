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

type TransferAnalysisPageProps =
  Readonly<{
    params: Promise<{
      playerId: string;
    }>;
  }>;

export default async function TransferAnalysisPage({
  params,
}: TransferAnalysisPageProps) {
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
        title="Configure replacement analysis"
        description={`The analysis route is connected to player ${parsedPlayerId}. Recruitment parameters and recommendation modes will be added in the next product phase.`}
        actions={
          <Link
            href={`/players/${parsedPlayerId}`}
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold transition-colors hover:bg-surface-secondary"
          >
            Back to player profile
          </Link>
        }
      />

      <section className="mt-12 rounded-2xl border border-border bg-surface p-6 shadow-sm">
        <p className="font-semibold">
          Typed analysis contract ready
        </p>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          The backend already exposes immediate,
          development, value and short-term
          recommendation modes. The next phase will
          connect the analysis form and results
          experience to this route.
        </p>
      </section>
    </PageContainer>
  );
}
