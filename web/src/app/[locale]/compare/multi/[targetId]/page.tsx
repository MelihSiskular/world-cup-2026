import type {
  Metadata,
} from "next";
import {
  notFound,
} from "next/navigation";
import {
  getTranslations,
  setRequestLocale,
} from "next-intl/server";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  Link,
} from "@/i18n/navigation";
import {
  PageIntro,
} from "@/components/layout/page-intro";
import {
  MultiPlayerComparison,
} from "@/components/transfer-intelligence/multi-player-comparison";
import {
  parseMultiComparisonIdentifiers,
} from "@/lib/transfer-intelligence/multi-comparison-selection";

type MultiPlayerComparisonPageProps =
  Readonly<{
    params: Promise<{
      locale: string;
      targetId: string;
    }>;
    searchParams: Promise<{
      candidates?:
        | string
        | readonly string[];
    }>;
  }>;

export async function generateMetadata({
  params,
}: Pick<
  MultiPlayerComparisonPageProps,
  "params"
>): Promise<Metadata> {
  const {
    locale,
  } = await params;

  const t = await getTranslations({
    locale,
    namespace:
      "MultiPlayerComparisonPage",
  });

  return {
    title: t("metadataTitle"),
    description:
      t("metadataDescription"),
  };
}

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

  setRequestLocale(
    resolvedParams.locale,
  );

  const t = await getTranslations({
    locale:
      resolvedParams.locale,
    namespace:
      "MultiPlayerComparisonPage",
  });

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
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
        actions={
          <Link
            href="/shortlists"
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
          >
            {t("backToShortlists")}
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
