import {
  describe,
  expect,
  it,
} from "vitest";

import {
  isNavigationItemActive,
  primaryNavigationItems,
} from "@/lib/navigation";

describe(
  "shortlist navigation",
  () => {
    it(
      "keeps shortlist routes in their own active boundary",
      () => {
        const shortlistItem =
          primaryNavigationItems.find(
            (item) =>
              item.href ===
              "/shortlists",
          );

        if (
          shortlistItem ===
          undefined
        ) {
          throw new Error(
            "Shortlists navigation item was not found.",
          );
        }

        expect(
          isNavigationItemActive(
            "/shortlists",
            shortlistItem,
          ),
        ).toBe(true);

        expect(
          isNavigationItemActive(
            "/shortlists/summer-2027",
            shortlistItem,
          ),
        ).toBe(true);

        expect(
          isNavigationItemActive(
            "/players",
            shortlistItem,
          ),
        ).toBe(false);

        expect(
          isNavigationItemActive(
            "/shortlisting",
            shortlistItem,
          ),
        ).toBe(false);
      },
    );
  },
);
