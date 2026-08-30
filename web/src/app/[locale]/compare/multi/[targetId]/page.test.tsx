import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import MultiPlayerComparisonPage, {
  generateMetadata,
} from "@/app/[locale]/compare/multi/[targetId]/page";

vi.mock(
  "next-intl/server",
  () => {
    const english = {
      metadataTitle:
        "Multi-player comparison",
      metadataDescription:
        "Compare one target with up to three same-position recruitment candidates.",
      eyebrow:
        "Player comparison",
      title:
        "Multi-player comparison",
      description:
        "Compare one target with up to three same-position candidates using player context and target-relative analytical evidence.",
      backToShortlists:
        "Back to shortlists",
    };

    const turkish = {
      metadataTitle:
        "Çoklu oyuncu karşılaştırması",
      metadataDescription:
        "Bir hedef oyuncuyu aynı pozisyondaki en fazla üç transfer adayıyla karşılaştırın.",
      eyebrow:
        "Oyuncu karşılaştırması",
      title:
        "Çoklu oyuncu karşılaştırması",
      description:
        "Bir hedef oyuncuyu aynı pozisyondaki en fazla üç adayla; oyuncu bağlamı ve hedefe göre analitik kanıtlar üzerinden karşılaştırın.",
      backToShortlists:
        "Kısa listelere dön",
    };

    return {
      setRequestLocale:
        vi.fn(),
      getTranslations:
        async ({
          locale,
        }: Readonly<{
          locale: string;
        }>) => {
          const messages =
            locale === "tr"
              ? turkish
              : english;

          return (
            key:
              keyof typeof english,
          ) => messages[key];
        },
    };
  },
);

vi.mock(
  "@/i18n/navigation",
  () => ({
    Link: "a",
  }),
);

vi.mock(
  "next/navigation",
  () => ({
    notFound: () => {
      throw new Error(
        "NEXT_NOT_FOUND",
      );
    },
  }),
);

vi.mock(
  "@/components/transfer-intelligence/multi-player-comparison",
  () => ({
    MultiPlayerComparison: ({
      identifiers,
    }: Readonly<{
      identifiers: Readonly<{
        targetPlayerId: number;
        candidatePlayerIds:
          readonly number[];
      }>;
    }>) => (
      <div data-testid="multi-player-comparison">
        Target{" "}
        {
          identifiers
            .targetPlayerId
        }
        ; candidates{" "}
        {
          identifiers
            .candidatePlayerIds
            .join(",")
        }
      </div>
    ),
  }),
);

describe(
  "MultiPlayerComparisonPage",
  () => {
    it(
      "publishes comparison-specific metadata",
      async () => {
        const metadata =
          await generateMetadata({
            params:
              Promise.resolve({
                locale: "en",
                targetId:
                  "978838",
              }),
          });

        expect(
          metadata.title,
        ).toBe(
          "Multi-player comparison",
        );

        expect(
          metadata.description,
        ).toContain(
          "same-position",
        );
      },
    );

    it(
      "hydrates the canonical ordered comparison selection",
      async () => {
        render(
          await MultiPlayerComparisonPage({
            params:
              Promise.resolve({
                locale: "en",
                targetId:
                  "978838",
              }),
            searchParams:
              Promise.resolve({
                candidates:
                  "789071,805078,123456",
              }),
          }),
        );

        expect(
          screen.getByTestId(
            "multi-player-comparison",
          ),
        ).toHaveTextContent(
          "Target 978838; candidates 789071,805078,123456",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Back to shortlists",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/shortlists",
        );
      },
    );

    it(
      "rejects a non-canonical comparison URL",
      async () => {
        await expect(
          MultiPlayerComparisonPage({
            params:
              Promise.resolve({
                locale: "en",
                targetId:
                  "978838",
              }),
            searchParams:
              Promise.resolve({
                candidates: [
                  "789071",
                  "805078",
                ],
              }),
          }),
        ).rejects.toThrow(
          "NEXT_NOT_FOUND",
        );
      },
    );

    it(
      "renders the page shell in Turkish",
      async () => {
        render(
          await MultiPlayerComparisonPage({
            params:
              Promise.resolve({
                locale: "tr",
                targetId:
                  "978838",
              }),
            searchParams:
              Promise.resolve({
                candidates:
                  "789071,805078",
              }),
          }),
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Çoklu oyuncu karşılaştırması",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Kısa listelere dön",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/shortlists",
        );
      },
    );

  },
);
