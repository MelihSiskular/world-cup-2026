import { expect, test } from "@playwright/test";

test.describe("WC26 complete transfer intelligence journey", () => {
  test("searches Michael Olise, runs analysis and compares a recommendation", async ({
    page,
  }) => {
    test.setTimeout(90_000);

    await page.goto("/");

    const primaryNavigation = page.getByRole("navigation", {
      name: "Primary navigation",
    });

    await primaryNavigation
      .getByRole("link", { name: "Players" })
      .click();

    await expect(page).toHaveURL(/\/players$/);

    const playerSearch = page.getByRole("searchbox", {
      name: "Search player catalogue",
    });

    await expect(playerSearch).toBeVisible();

    await playerSearch.fill("Michael Olise");

    const oliseResult = page
      .getByRole("link", {
        name: /Michael Olise/i,
      })
      .first();

    await expect(oliseResult).toBeVisible({
      timeout: 30_000,
    });

    await oliseResult.click();

    await expect(page).toHaveURL(
      /\/players\/978838$/,
    );

    await expect(
      page.getByRole("heading", {
        name: "Michael Olise",
        exact: true,
      }),
    ).toBeVisible();

    await page
      .getByRole("link", {
        name: "Run transfer analysis",
      })
      .click();

    await expect(page).toHaveURL(
      /\/analysis\/978838/,
    );

    await expect(
      page.getByLabel(
        "Minimum tournament minutes",
      ),
    ).toBeVisible();

    await expect(
      page.getByLabel(
        "Minimum role confidence",
      ),
    ).toBeVisible();

    await expect(
      page.getByLabel(
        "Maximum market value",
      ),
    ).toBeVisible();

    await expect(
      page.getByLabel(
        "Neutral heatmap score",
      ),
    ).toBeVisible();

    await page
      .getByRole("button", {
        name: "Continue to results",
      })
      .click();

    await expect(page).toHaveURL(
      /\/analysis\/978838\/results/,
    );

    const recommendationModes =
      page.getByRole("tablist", {
        name: "Transfer recommendation modes",
      });

    await expect(
      recommendationModes,
    ).toBeVisible({
      timeout: 30_000,
    });

    const immediateTab =
      recommendationModes.getByRole("tab", {
        name: /^Immediate\b/,
      });

    const developmentTab =
      recommendationModes.getByRole("tab", {
        name: /^Development\b/,
      });

    const valueTab =
      recommendationModes.getByRole("tab", {
        name: /^Value\b/,
      });

    const shortTermTab =
      recommendationModes.getByRole("tab", {
        name: /^Short term\b/,
      });

    await expect(immediateTab).toBeVisible();
    await expect(developmentTab).toBeVisible();
    await expect(valueTab).toBeVisible();
    await expect(shortTermTab).toBeVisible();

    await expect(immediateTab).toHaveAttribute(
      "aria-selected",
      "true",
    );

    await expect(
      page.getByRole("heading", {
        name: "Immediate impact",
      }),
    ).toBeVisible();

    await developmentTab.click();

    await expect(
      page.getByRole("heading", {
        name: "Development investment",
      }),
    ).toBeVisible();

    await valueTab.click();

    await expect(
      page.getByRole("heading", {
        name: "Market value opportunity",
      }),
    ).toBeVisible();

    await shortTermTab.click();

    await expect(
      page.getByRole("heading", {
        name: "Short-term solution",
      }),
    ).toBeVisible();

    await immediateTab.click();

    await expect(
      page.getByRole("heading", {
        name: "Immediate impact",
      }),
    ).toBeVisible();

    const compareWithTarget = page
      .getByRole("link", {
        name: "Compare with target",
      })
      .first();

    await expect(compareWithTarget).toBeVisible({
      timeout: 30_000,
    });

    await compareWithTarget.click();

    await expect(page).toHaveURL(
      /\/compare\/978838\/\d+/,
    );

    await expect(
      page.getByLabel("Comparison indicators"),
    ).toBeVisible({
      timeout: 30_000,
    });

    await expect(
      page.getByText("Michael Olise", {
        exact: true,
      }).first(),
    ).toBeVisible();
  });
});
