import {
  describe,
  expect,
  it,
} from "vitest";

import {
  primaryNavigationItems,
} from "@/lib/navigation";

describe("primaryNavigationItems", () => {
  it("keeps operational status outside the primary product journey", () => {
    expect(
      primaryNavigationItems.map(
        (item) =>
          item.messageKey,
      ),
    ).toEqual([
      "home",
      "players",
      "shortlists",
      "methodology",
    ]);
  });
});
