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

export const metadata: Metadata = {
  title: "Players",
  description:
    "Search the World Cup 2026 player catalogue and open scouting profiles.",
};

export default function PlayersPage() {
  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow="Player catalogue"
        title="Search and inspect tournament players"
        description="Find the correct player through stable catalogue identities, role information and market context before starting replacement analysis."
      />

      <div className="mt-12">
        <PlayerSearch />
      </div>
    </PageContainer>
  );
}
