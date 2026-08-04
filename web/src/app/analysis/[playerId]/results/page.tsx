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
  TransferAnalysisResults,
} from "@/components/transfer-intelligence/transfer-analysis-results";
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

type AnalysisResultsPageProps =
  Readonly<{
    params: Promise<{
      playerId: string;
    }>;
    searchParams:
      Promise<AnalysisSearchParameters>;
  }>;

export default async function AnalysisResultsPage({
  params,
  searchParams,
}: AnalysisResultsPageProps) {
  const [
    resolvedParams,
    resolvedSearchParams,
  ] = await Promise.all([
    params,
    searchParams,
  ]);

  const parsedPlayerId =
    Number(
      resolvedParams.playerId,
    );

  if (
    !Number.isSafeInteger(
      parsedPlayerId,
    ) ||
    parsedPlayerId <= 0
  ) {
    notFound();
  }

  const parsedParameters =
    parseAnalysisSearchParameters(
      resolvedSearchParams,
    );

  if (!parsedParameters.success) {
    return (
      <PageContainer className="py-14 sm:py-20">
        <PageIntro
          eyebrow="Transfer intelligence"
          title="Invalid analysis configuration"
          description={parsedParameters.message}
          actions={
            <Link
              href={`/analysis/${parsedPlayerId}`}
              className="rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
            >
              Configure analysis
            </Link>
          }
        />

        <section className="mt-12 rounded-2xl border border-warning/25 bg-warning/10 p-6">
          <p className="font-semibold text-warning">
            The URL parameters could not be used
          </p>

          <p className="mt-2 text-sm leading-6 text-muted">
            Return to the configuration page
            and submit valid recruitment
            thresholds.
          </p>
        </section>
      </PageContainer>
    );
  }

  const initialMode =
    parseTransferMode(
      resolvedSearchParams.mode,
    ) ?? "immediate";

  const resultParameters =
    createAnalysisSearchParameters(
      parsedParameters.values,
    );

  resultParameters.set(
    "mode",
    initialMode,
  );

  const queryString =
    resultParameters.toString();

  return (
    <PageContainer className="py-10 sm:py-14">
      <PageIntro
        eyebrow="Transfer intelligence"
        title="Replacement recommendations"
        description="Review candidates across four recruitment scenarios, inspect the recommendation evidence and continue to direct player comparison."
        actions={
          <Link
            href={`/analysis/${parsedPlayerId}?${queryString}`}
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
          >
            Adjust parameters
          </Link>
        }
      />

      <div className="mt-10">
        <TransferAnalysisResults
          key={`${parsedPlayerId}:${initialMode}:${queryString}`}
          playerId={parsedPlayerId}
          values={
            parsedParameters.values
          }
          initialMode={initialMode}
        />
      </div>
    </PageContainer>
  );
}
