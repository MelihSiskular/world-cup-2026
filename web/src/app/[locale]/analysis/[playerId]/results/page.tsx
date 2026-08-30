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
  TransferAnalysisResults,
} from "@/components/transfer-intelligence/transfer-analysis-results";
import {
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
      locale: string;
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

  const locale =
    resolvedParams.locale;

  setRequestLocale(locale);

  const translations =
    await getTranslations({
      locale,
      namespace:
        "AnalysisResultsPage",
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

  if (!parsedParameters.success) {
    return (
      <PageContainer className="py-14 sm:py-20">
        <PageIntro
          eyebrow={translations(
            "eyebrow",
          )}
          title={translations(
            "invalidTitle",
          )}
          description={translations(
            "invalidDescription",
          )}
          actions={
            <Link
              href={`/analysis/${parsedPlayerId}`}
              className="rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
            >
              {translations(
                "configureAnalysis",
              )}
            </Link>
          }
        />

        <section className="mt-12 rounded-2xl border border-warning/25 bg-warning/10 p-6">
          <p className="font-semibold text-warning">
            {translations(
              "invalidParametersTitle",
            )}
          </p>

          <p className="mt-2 text-sm leading-6 text-muted">
            {translations(
              "invalidParametersDescription",
            )}
          </p>
        </section>
      </PageContainer>
    );
  }

  const initialMode =
    parseTransferMode(
      resolvedSearchParams.mode,
    ) ?? "immediate";

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
      />

      <div className="mt-10">
        <TransferAnalysisResults
          key={`${parsedPlayerId}:${initialMode}`}
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
