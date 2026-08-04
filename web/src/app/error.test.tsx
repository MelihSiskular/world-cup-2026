import {
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import ApplicationErrorPage from "@/app/error";

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

        render(
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
  },
);
