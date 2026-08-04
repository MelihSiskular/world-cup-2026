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

type PlayerComparisonPageProps =
  Readonly<{
    params: Promise<{
      targetId: string;
      candidateId: string;
    }>;
  }>;

export default async function PlayerComparisonPage({
  params,
}: PlayerComparisonPageProps) {
  const {
    targetId,
    candidateId,
  } = await params;

  const parsedTargetId =
    Number(targetId);

  const parsedCandidateId =
    Number(candidateId);

  if (
    !Number.isSafeInteger(
      parsedTargetId,
    ) ||
    !Number.isSafeInteger(
      parsedCandidateId,
    ) ||
    parsedTargetId <= 0 ||
    parsedCandidateId <= 0 ||
    parsedTargetId ===
      parsedCandidateId
  ) {
    notFound();
  }

  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow="Player comparison"
        title="Compare target and candidate"
        description={`The comparison route connects target ${parsedTargetId} with candidate ${parsedCandidateId}. Detailed statistical and spatial comparison will be delivered in the next phase.`}
        actions={
          <Link
            href={`/players/${parsedCandidateId}`}
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
          >
            Open candidate profile
          </Link>
        }
      />

      <section className="mt-12 rounded-2xl border border-border bg-surface p-6 shadow-sm">
        <p className="font-semibold">
          Comparison identities ready
        </p>

        <p className="mt-2 text-sm leading-6 text-muted">
          Phase 5E will connect both player
          profiles, metric differences and
          spatial-role evidence to this route.
        </p>
      </section>
    </PageContainer>
  );
}
