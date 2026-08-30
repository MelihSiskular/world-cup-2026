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
  PlayerSearch,
} from "@/components/players/player-search";
import {
  readPlayerSearchUrlParameters,
} from "@/lib/players/search-parameters";

type PlayersPageProps =
  Readonly<{
    params: Promise<
      Readonly<{
        locale: string;
      }>
    >;
    searchParams: Promise<
      Readonly<
        Record<
          string,
          string |
            readonly string[] |
            undefined
        >
      >
    >;
  }>;

export async function generateMetadata({
  params,
}: Pick<
  PlayersPageProps,
  "params"
>): Promise<Metadata> {
  const {
    locale,
  } = await params;

  const translations =
    await getTranslations({
      locale,
      namespace:
        "PlayerDiscovery",
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

function createUrlSearchParameters(
  values: Readonly<
    Record<
      string,
      string |
        readonly string[] |
        undefined
    >
  >,
): URLSearchParams {
  const searchParameters =
    new URLSearchParams();

  for (
    const [
      name,
      value,
    ] of Object.entries(values)
  ) {
    if (
      typeof value === "string"
    ) {
      searchParameters.append(
        name,
        value,
      );
      continue;
    }

    for (
      const item of value ?? []
    ) {
      searchParameters.append(
        name,
        item,
      );
    }
  }

  return searchParameters;
}

export default async function PlayersPage({
  params,
  searchParams,
}: PlayersPageProps) {
  const [
    {
      locale,
    },
    searchParameterValues,
  ] = await Promise.all([
    params,
    searchParams,
  ]);

  setRequestLocale(locale);

  const translations =
    await getTranslations({
      locale,
      namespace:
        "PlayerDiscovery",
    });

  const initialParameters =
    readPlayerSearchUrlParameters(
      createUrlSearchParameters(
        searchParameterValues,
      ),
    );

  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow={
          translations(
            "eyebrow",
          )
        }
        title={
          translations(
            "title",
          )
        }
        description={
          translations(
            "description",
          )
        }
      />

      <div className="mt-12">
        <PlayerSearch
          initialParameters={
            initialParameters
          }
        />
      </div>
    </PageContainer>
  );
}
