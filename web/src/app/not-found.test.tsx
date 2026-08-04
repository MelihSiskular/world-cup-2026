import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
} from "vitest";

import NotFoundPage from "@/app/not-found";

describe(
  "NotFoundPage",
  () => {
    it(
      "provides stable recovery links",
      () => {
        render(
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
  },
);
