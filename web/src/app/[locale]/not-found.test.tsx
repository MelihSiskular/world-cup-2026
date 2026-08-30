import {
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import NotFoundPage from "@/app/[locale]/not-found";
import {
  renderWithQueryClient,
} from "@/test/render-with-query-client";

vi.mock(
  "@/i18n/navigation",
  () => ({
    Link: "a",
  }),
);

describe(
  "NotFoundPage",
  () => {
    it(
      "provides stable recovery links",
      () => {
        renderWithQueryClient(
          <NotFoundPage />,
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "This page is outside the analysis zone.",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Return home",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Open players",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/players",
        );
      },
    );
    it(
      "provides localized Turkish recovery links",
      () => {
        renderWithQueryClient(
          <NotFoundPage />,
          "tr",
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Bu sayfa analiz alanının dışında.",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Ana sayfaya dön",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Oyuncuları aç",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/players",
        );
      },
    );

  },
);
