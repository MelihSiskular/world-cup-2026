import {
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import ApplicationErrorPage from "@/app/[locale]/error";
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
  "ApplicationErrorPage",
  () => {
    it(
      "shows the digest and invokes reset",
      async () => {
        const reset =
          vi.fn();

        const error =
          Object.assign(
            new Error(
              "Render failed.",
            ),
            {
              digest:
                "digest-123",
            },
          );

        const user =
          userEvent.setup();

        renderWithQueryClient(
          <ApplicationErrorPage
            error={error}
            reset={reset}
          />,
        );

        expect(
          screen.getByText(
            "digest-123",
          ),
        ).toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Try again",
            },
          ),
        );

        expect(
          reset,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );
    it(
      "localizes recovery actions in Turkish",
      async () => {
        const reset = vi.fn();
        const user =
          userEvent.setup();

        renderWithQueryClient(
          <ApplicationErrorPage
            error={
              new Error(
                "Render failed.",
              )
            }
            reset={reset}
          />,
          "tr",
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Bu analiz görünümü gösterilemedi",
            },
          ),
        ).toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Yeniden dene",
            },
          ),
        );

        expect(
          reset,
        ).toHaveBeenCalledOnce();

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
      },
    );

  },
);
