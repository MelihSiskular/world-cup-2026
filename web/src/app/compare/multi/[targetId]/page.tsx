import type {
  Metadata,
} from "next";
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
  MultiPlayerComparison,
} from "@/components/transfer-intelligence/multi-player-comparison";
import {
  parseMultiComparisonIdentifiers,
} from "@/lib/transfer-intelligence/multi-comparison-selection";

export const metadata: Metadata = {
  title: "Multi-player comparison",
  description:
    "Compare one target with up to three same-position recruitment candidates.",
};

type MultiPlayerComparisonPageProps =
  Readonly<{
    params: Promise<{
      targetId: string;
    }>;
    searchParams: Promise<{
      candidates?:
        | string
        | readonly string[];
    }>;
  }>;

export default async function MultiPlayerComparisonPage({
  params,
  searchParams,
}: MultiPlayerComparisonPageProps) {
  const [
    resolvedParams,
    resolvedSearchParams,
  ] = await Promise.all([
    params,
    searchParams,
  ]);

  const validation =
    parseMultiComparisonIdentifiers(
      resolvedParams.targetId,
      resolvedSearchParams
        .candidates,
    );

  if (!validation.success) {
    notFound();
  }

  return (
    <PageContainer className="py-10 sm:py-14">
      <PageIntro
        eyebrow="Player comparison"
        title="Multi-player comparison"
        description="Compare one target with up to three same-position candidates using player context and target-relative analytical evidence."
        actions={
          <Link
            href="/shortlists"
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
          >
            Back to shortlists
          </Link>
        }
      />

      <div className="mt-10">
        <MultiPlayerComparison
          identifiers={
            validation.values
          }
        />
      </div>
    </PageContainer>
  );
}
