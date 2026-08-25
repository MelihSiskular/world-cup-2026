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

import ShortlistsPage, {
  metadata,
} from "@/app/shortlists/page";

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
      "publishes shortlist-specific metadata",
      () => {
        expect(
          metadata.title,
        ).toBe("Shortlists");

        expect(
          metadata.description,
        ).toContain(
          "recruitment shortlists",
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
