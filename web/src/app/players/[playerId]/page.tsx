import type {
  Metadata,
} from "next";
import {
  notFound,
} from "next/navigation";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  PlayerProfile,
} from "@/components/players/player-profile";

type PlayerProfilePageProps =
  Readonly<{
    params: Promise<{
      playerId: string;
    }>;
  }>;

function parsePlayerId(
  value: string,
): number | null {
  const playerId =
    Number(value);

  if (
    !Number.isSafeInteger(playerId) ||
    playerId <= 0
  ) {
    return null;
  }

  return playerId;
}

export async function generateMetadata({
  params,
}: PlayerProfilePageProps): Promise<Metadata> {
  const {
    playerId,
  } = await params;

  const parsedPlayerId =
    parsePlayerId(playerId);

  return {
    title:
      parsedPlayerId === null
        ? "Player not found"
        : `Player ${parsedPlayerId}`,
    description:
      "World Cup 2026 player scouting profile and transfer-analysis entry point.",
  };
}

export default async function PlayerProfilePage({
  params,
}: PlayerProfilePageProps) {
  const {
    playerId,
  } = await params;

  const parsedPlayerId =
    parsePlayerId(playerId);

  if (parsedPlayerId === null) {
    notFound();
  }

  return (
    <PageContainer className="py-10 sm:py-14">
      <PlayerProfile
        playerId={parsedPlayerId}
      />
    </PageContainer>
  );
}
