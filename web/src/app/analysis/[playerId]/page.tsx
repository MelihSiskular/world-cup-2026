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
  TransferAnalysisForm,
} from "@/components/transfer-intelligence/transfer-analysis-form";
import {
  DEFAULT_TRANSFER_ANALYSIS_VALUES,
  parseAnalysisSearchParameters,
} from "@/lib/transfer-intelligence/analysis-form";
import type {
  AnalysisSearchParameters,
} from "@/lib/transfer-intelligence/analysis-form";

type TransferAnalysisPageProps =
  Readonly<{
    params: Promise<{
      playerId: string;
    }>;
    searchParams:
      Promise<AnalysisSearchParameters>;
  }>;

export default async function TransferAnalysisPage({
  params,
  searchParams,
}: TransferAnalysisPageProps) {
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

  const initialValues =
    parsedParameters.success
      ? parsedParameters.values
      : {
          ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
        };

  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow="Transfer intelligence"
        title="Configure replacement analysis"
        description="Set recruitment thresholds before ranking candidates across immediate, development, value and short-term scenarios."
        actions={
          <Link
            href={`/players/${parsedPlayerId}`}
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold transition-colors hover:bg-surface-secondary"
          >
            Back to player profile
          </Link>
        }
      />

      <div className="mt-12">
        <TransferAnalysisForm
          playerId={parsedPlayerId}
          initialValues={initialValues}
        />
      </div>
    </PageContainer>
  );
}
