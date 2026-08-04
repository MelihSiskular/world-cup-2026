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
import {
  PlayerComparison,
} from "@/components/transfer-intelligence/player-comparison";
import {
  createAnalysisSearchParameters,
  parseAnalysisSearchParameters,
} from "@/lib/transfer-intelligence/analysis-form";
import type {
  AnalysisSearchParameters,
} from "@/lib/transfer-intelligence/analysis-form";
import {
  parseTransferMode,
} from "@/lib/transfer-intelligence/result-config";

type PlayerComparisonPageProps =
  Readonly<{
    params: Promise<{
      targetId: string;
      candidateId: string;
    }>;
    searchParams:
      Promise<AnalysisSearchParameters>;
  }>;

export default async function PlayerComparisonPage({
  params,
  searchParams,
}: PlayerComparisonPageProps) {
  const [
    resolvedParams,
    resolvedSearchParams,
  ] = await Promise.all([
    params,
    searchParams,
  ]);

  const parsedTargetId =
    Number(
      resolvedParams.targetId,
    );

  const parsedCandidateId =
    Number(
      resolvedParams.candidateId,
    );

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

  const parsedParameters =
    parseAnalysisSearchParameters(
      resolvedSearchParams,
    );

  const mode =
    parseTransferMode(
      resolvedSearchParams.mode,
    );

  if (
    !parsedParameters.success ||
    mode === null
  ) {
    return (
      <PageContainer className="py-14 sm:py-20">
        <PageIntro
          eyebrow="Player comparison"
          title="Invalid comparison configuration"
          description={
            parsedParameters.success
              ? "A valid recruitment scenario is required."
              : parsedParameters.message
          }
          actions={
            <Link
              href={`/analysis/${parsedTargetId}`}
              className="rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
            >
              Configure analysis
            </Link>
          }
        />

        <section className="mt-12 rounded-2xl border border-warning/25 bg-warning/10 p-6">
          <p className="font-semibold text-warning">
            The comparison context is incomplete
          </p>

          <p className="mt-2 text-sm leading-6 text-muted">
            Return to transfer analysis and
            select a candidate from one of
            the recommendation scenarios.
          </p>
        </section>
      </PageContainer>
    );
  }

  const resultParameters =
    createAnalysisSearchParameters(
      parsedParameters.values,
    );

  resultParameters.set(
    "mode",
    mode,
  );

  const resultsHref =
    `/analysis/${parsedTargetId}/results` +
    `?${resultParameters.toString()}`;

  return (
    <PageContainer className="py-10 sm:py-14">
      <PageIntro
        eyebrow="Player comparison"
        title="Target versus candidate"
        description="Compare tactical role, tournament performance, reliability, market context and the evidence behind the recruitment recommendation."
        actions={
          <Link
            href={resultsHref}
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
          >
            Back to recommendations
          </Link>
        }
      />

      <div className="mt-10">
        <PlayerComparison
          targetPlayerId={
            parsedTargetId
          }
          candidatePlayerId={
            parsedCandidateId
          }
          mode={mode}
          values={
            parsedParameters.values
          }
        />
      </div>
    </PageContainer>
  );
}
