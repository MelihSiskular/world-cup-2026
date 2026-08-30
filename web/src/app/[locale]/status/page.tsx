import type {
  Metadata,
} from "next";
import {
  getTranslations,
  setRequestLocale,
} from "next-intl/server";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  PageIntro,
} from "@/components/layout/page-intro";
import {
  ApiStatusOverview,
} from "@/components/status/api-status-overview";

type StatusPageProps =
  Readonly<{
    params: Promise<{
      locale: string;
    }>;
  }>;

export async function generateMetadata({
  params,
}: StatusPageProps): Promise<Metadata> {
  const { locale } = await params;

  const t = await getTranslations({
    locale,
    namespace: "StatusPage",
  });

  return {
    title: t("metadataTitle"),
    description:
      t("metadataDescription"),
  };
}

export default async function StatusPage({
  params,
}: StatusPageProps) {
  const { locale } = await params;

  setRequestLocale(locale);

  const t = await getTranslations({
    locale,
    namespace: "StatusPage",
  });

  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t(
          "description",
        )}
      />

      <section className="mt-12">
        <ApiStatusOverview />
      </section>
    </PageContainer>
  );
}
