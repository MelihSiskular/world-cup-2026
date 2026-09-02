import {
  expect,
  test,
  type Page,
} from "@playwright/test";

async function waitForApplicationReady(
  page: Page,
): Promise<void> {
  await page.waitForFunction(
    () =>
      document.documentElement.dataset
        .wc26Hydrated === "true",
  );
}

async function expectNoHorizontalPageOverflow(
  page: Page,
): Promise<void> {
  const dimensions = await page.evaluate(
    () => ({
      scrollWidth:
        document.documentElement.scrollWidth,
      clientWidth:
        document.documentElement.clientWidth,
    }),
  );

  expect(
    dimensions.scrollWidth,
    `Expected no horizontal page overflow: scrollWidth=${dimensions.scrollWidth}, clientWidth=${dimensions.clientWidth}`,
  ).toBeLessThanOrEqual(
    dimensions.clientWidth,
  );
}

async function navigateToPlayers(
  page: Page,
): Promise<void> {
  const openNavigationButton =
    page.getByRole("button", {
      name: "Open navigation",
    });

  if (await openNavigationButton.isVisible()) {
    await openNavigationButton.click();

    const mobileNavigation =
      page.getByRole("navigation", {
        name: "Mobile navigation",
      });

    await expect(
      mobileNavigation,
    ).toBeVisible();

    await mobileNavigation
      .getByRole("link", {
        name: "Players",
      })
      .click();

    return;
  }

  const primaryNavigation =
    page.getByRole("navigation", {
      name: "Primary navigation",
    });

  await primaryNavigation
    .getByRole("link", {
      name: "Players",
    })
    .click();
}

test.describe(
  "WC26 complete transfer intelligence journey",
  () => {
    test(
      "searches Michael Olise, runs analysis and compares a recommendation",
      async ({ page }) => {
        test.setTimeout(90_000);

        await page.goto("/");

        await waitForApplicationReady(
          page,
        );

        await navigateToPlayers(page);

        await expect(page).toHaveURL(
          /\/players$/,
        );

        const playerSearch =
          page.getByRole("searchbox", {
            name: "Search players",
          });

        await expect(
          playerSearch,
        ).toBeVisible();

        await expectNoHorizontalPageOverflow(
          page,
        );

        await playerSearch.fill(
          "Michael Olise",
        );

        const oliseResult = page
          .getByRole("link", {
            name: /Michael Olise/i,
          })
          .first();

        await expect(
          oliseResult,
        ).toBeVisible({
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

        await expectNoHorizontalPageOverflow(
          page,
        );

        await page
          .getByRole("link", {
            name: "Run transfer analysis",
          })
          .click();

        await expect(page).toHaveURL(
          /\/analysis\/978838/,
          {
            timeout: 30_000,
          },
        );

        await expect(
          page.getByLabel(
            /^Tournament experience/,
          ),
        ).toBeVisible();

        await expect(
          page.getByLabel(
            /^Role evidence/,
          ),
        ).toBeVisible();

        await expect(
          page.getByLabel(
            /^Budget ceiling/,
          ),
        ).toBeVisible();

        await expect(
          page.getByText(
            "Advanced settings",
            {
              exact: true,
            },
          ),
        ).toBeVisible();

        await page
          .getByRole("button", {
            name: "Find transfer alternatives",
          })
          .click();

        await expect(page).toHaveURL(
          /\/analysis\/978838\/results/,
        );

        const recommendationModes =
          page.getByRole("tablist", {
            name:
              "Transfer recommendation modes",
          });

        await expect(
          recommendationModes,
        ).toBeVisible({
          timeout: 30_000,
        });

        const immediateTab =
          recommendationModes.getByRole(
            "tab",
            {
              name: /^Immediate\b/,
            },
          );

        const developmentTab =
          recommendationModes.getByRole(
            "tab",
            {
              name: /^Development\b/,
            },
          );

        const valueTab =
          recommendationModes.getByRole(
            "tab",
            {
              name: /^Value\b/,
            },
          );

        const shortTermTab =
          recommendationModes.getByRole(
            "tab",
            {
              name: /^Short term\b/,
            },
          );

        await expect(
          immediateTab,
        ).toBeVisible();

        await expect(
          developmentTab,
        ).toBeVisible();

        await expect(
          valueTab,
        ).toBeVisible();

        await expect(
          shortTermTab,
        ).toBeVisible();

        await expect(
          immediateTab,
        ).toHaveAttribute(
          "aria-selected",
          "true",
        );

        await expectNoHorizontalPageOverflow(
          page,
        );

        await expect(
          page.getByRole("heading", {
            name: "Immediate impact",
          }),
        ).toBeVisible();

        await developmentTab.click();

        await expect(
          page.getByRole("heading", {
            name:
              "Development investment",
          }),
        ).toBeVisible();

        await valueTab.click();

        await expect(
          page.getByRole("heading", {
            name:
              "Market value opportunity",
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

        const compareWithTarget =
          page
            .getByRole("link", {
              name:
                "Compare with target",
            })
            .first();

        await expect(
          compareWithTarget,
        ).toBeVisible({
          timeout: 30_000,
        });

        await compareWithTarget.click();

        await expect(page).toHaveURL(
          /\/compare\/978838\/\d+/,
        );

        await expect(
          page.getByLabel(
            "Comparison indicators",
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        await expect(
          page
            .getByText(
              "Michael Olise",
              {
                exact: true,
              },
            )
            .first(),
        ).toBeVisible();

        /*
         * Phase 6C comparison intelligence.
         *
         * Keep these assertions at the
         * browser-integration level:
         * the detailed geometry and
         * percentile semantics belong to
         * component/unit tests.
         */
        const radarComparison =
          page.getByRole(
            "region",
            {
              name:
                "Playing style radar comparison",
              exact: true,
            },
          );

        await expect(
          radarComparison,
        ).toBeVisible({
          timeout: 30_000,
        });

        await expect(
          radarComparison.getByRole(
            "img",
            {
              name:
                /^Playing style radar comparison for Michael Olise and /,
            },
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        const heatmapComparison =
          page.getByRole(
            "region",
            {
              name:
                "Heatmap profile comparison",
              exact: true,
            },
          );

        await expect(
          heatmapComparison,
        ).toBeVisible({
          timeout: 30_000,
        });

        await expect(
          heatmapComparison.getByRole(
            "img",
            {
              name:
                "Tournament heatmap for Michael Olise",
              exact: true,
            },
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        await expect(
          heatmapComparison.getByRole(
            "img",
            {
              name:
                /^Tournament heatmap for /,
            },
          ),
        ).toHaveCount(2);

        await expectNoHorizontalPageOverflow(
          page,
        );
      },
    );
  },
);