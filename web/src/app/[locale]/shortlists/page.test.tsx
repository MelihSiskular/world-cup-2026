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

import {
  generateMetadata,
  ShortlistsPageContent as ShortlistsPage,
} from "@/app/[locale]/shortlists/page";

vi.mock(
  "next-intl/server",
  () => ({
    getTranslations: async ({
      locale,
    }: Readonly<{
      locale: string;
    }>) => {
      const messages:
        Readonly<
          Record<
            string,
            Readonly<
              Record<
                string,
                string
              >
            >
          >
        > = {
          en: {
            metadataTitle:
              "Shortlists",
            metadataDescription:
              "Create and manage browser-saved World Cup 2026 recruitment shortlists.",
          },
          tr: {
            metadataTitle:
              "Kısa Listeler",
            metadataDescription:
              "Tarayıcıda saklanan 2026 Dünya Kupası transfer kısa listelerini oluşturun ve yönetin.",
          },
        };

      return (
        key: string,
      ) =>
        messages[locale]?.[
          key
        ] ?? key;
    },
    setRequestLocale:
      vi.fn(),
  }),
);

vi.mock(
  "@/components/shortlists/shortlist-manager",
  () => ({
    ShortlistManager: () => (
      <div>
        Shortlist manager surface
      </div>
    ),
  }),
);

describe(
  "ShortlistsPage",
  () => {
    it(
      "publishes localized shortlist metadata",
      async () => {
        const englishMetadata =
          await generateMetadata({
            params:
              Promise.resolve({
                locale: "en",
              }),
          });

        const turkishMetadata =
          await generateMetadata({
            params:
              Promise.resolve({
                locale: "tr",
              }),
          });

        expect(
          englishMetadata.title,
        ).toBe("Shortlists");

        expect(
          englishMetadata.description,
        ).toContain(
          "recruitment shortlists",
        );

        expect(
          turkishMetadata.title,
        ).toBe("Kısa Listeler");

        expect(
          turkishMetadata.description,
        ).toContain(
          "transfer kısa listelerini",
        );
      },
    );

    it(
      "renders the shortlist management surface",
      () => {
        render(
          <ShortlistsPage />,
        );

        expect(
          screen.getByText(
            "Shortlist manager surface",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
