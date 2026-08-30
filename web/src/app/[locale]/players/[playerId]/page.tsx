import type {
  Metadata,
} from "next";
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
  PlayerProfile,
} from "@/components/players/player-profile";

type PlayerProfilePageProps =
  Readonly<{
    params: Promise<{
      locale: string;
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
    locale,
    playerId,
  } = await params;

  const parsedPlayerId =
    parsePlayerId(playerId);

  const translations =
    await getTranslations({
      locale,
      namespace: "PlayerProfile",
    });

  return {
    title:
      parsedPlayerId === null
        ? translations(
            "metadataNotFoundTitle",
          )
        : translations(
            "metadataPlayerTitle",
            {
              playerId:
                parsedPlayerId,
            },
          ),
    description:
      translations(
        "metadataDescription",
      ),
  };
}

export default async function PlayerProfilePage({
  params,
}: PlayerProfilePageProps) {
  const {
    locale,
    playerId,
  } = await params;

  setRequestLocale(locale);

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
