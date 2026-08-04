import Link from "next/link";
import {
  notFound,
} from "next/navigation";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  PageIntro,
} from "@/components/layout/page-intro";

type PlayerProfilePageProps =
  Readonly<{
    params: Promise<{
      playerId: string;
    }>;
  }>;

export default async function PlayerProfilePage({
  params,
}: PlayerProfilePageProps) {
  const {
    playerId,
  } = await params;

  const parsedPlayerId =
    Number(playerId);

  if (
    !Number.isSafeInteger(
      parsedPlayerId,
    ) ||
    parsedPlayerId <= 0
  ) {
    notFound();
  }

  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow="Player profile"
        title={`Player ${parsedPlayerId}`}
        description="The stable player route is connected. The complete scouting profile will be delivered in the next product phase."
        actions={
          <Link
            href="/players"
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold transition-colors hover:bg-surface-secondary"
          >
            Back to player search
          </Link>
        }
      />

      <section className="mt-12 rounded-2xl border border-border bg-surface p-6 shadow-sm">
        <p className="font-semibold">
          Profile contract ready
        </p>

        <p className="mt-2 text-sm leading-6 text-muted">
          This route uses the stable player ID
          selected from the catalogue. Player
          profile data and transfer-analysis
          actions will be connected in Phase
          5C.2.
        </p>
      </section>
    </PageContainer>
  );
}
