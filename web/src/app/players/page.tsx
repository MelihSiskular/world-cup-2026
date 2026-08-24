import type {
  Metadata,
} from "next";

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

export const metadata: Metadata = {
  title: "Players",
  description:
    "Search the World Cup 2026 player catalogue and open scouting profiles.",
};

type PlayersPageProps =
  Readonly<{
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
  searchParams,
}: PlayersPageProps) {
  const initialParameters =
    readPlayerSearchUrlParameters(
      createUrlSearchParameters(
        await searchParams,
      ),
    );

  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow="Player catalogue"
        title="Search and inspect tournament players"
        description="Find the correct player through stable catalogue identities, role information and market context before starting replacement analysis."
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
