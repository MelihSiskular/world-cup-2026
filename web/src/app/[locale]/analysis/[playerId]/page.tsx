import {
  getTranslations,
  setRequestLocale,
} from "next-intl/server";
import {
  notFound,
} from "next/navigation";

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
      locale: string;
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

  const locale =
    resolvedParams.locale;

  setRequestLocale(locale);

  const translations =
    await getTranslations({
      locale,
      namespace:
        "TransferAnalysisPage",
    });

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
    <PageContainer className="py-10 sm:py-14">
      <PageIntro
        eyebrow={translations(
          "eyebrow",
        )}
        title={translations(
          "title",
        )}
        description={translations(
          "description",
        )}
        actions={
          <Link
            href={`/players/${parsedPlayerId}`}
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold transition-colors hover:bg-surface-secondary"
          >
            {translations(
              "backToProfile",
            )}
          </Link>
        }
      />

      <div className="mt-8">
        <TransferAnalysisForm
          playerId={parsedPlayerId}
          initialValues={initialValues}
        />
      </div>
    </PageContainer>
  );
}
