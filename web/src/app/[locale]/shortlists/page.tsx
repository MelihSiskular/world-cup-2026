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
  ShortlistManager,
} from "@/components/shortlists/shortlist-manager";

type ShortlistsPageProps =
  Readonly<{
    params: Promise<
      Readonly<{
        locale: string;
      }>
    >;
  }>;

export async function generateMetadata({
  params,
}: ShortlistsPageProps): Promise<Metadata> {
  const {
    locale,
  } = await params;

  const translations =
    await getTranslations({
      locale,
      namespace:
        "Shortlists",
    });

  return {
    title:
      translations(
        "metadataTitle",
      ),
    description:
      translations(
        "metadataDescription",
      ),
  };
}

export default async function ShortlistsPage({
  params,
}: ShortlistsPageProps) {
  const {
    locale,
  } = await params;

  setRequestLocale(locale);

  return (
    <ShortlistsPageContent />
  );
}

export function ShortlistsPageContent() {
  return (
    <PageContainer className="py-14 sm:py-20">
      <ShortlistManager />
    </PageContainer>
  );
}
