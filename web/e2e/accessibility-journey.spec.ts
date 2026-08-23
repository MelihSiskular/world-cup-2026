import AxeBuilder from "@axe-core/playwright";
import {
  expect,
  test,
  type Page,
  type TestInfo,
} from "@playwright/test";

const WCAG_TAGS = [
  "wcag2a",
  "wcag2aa",
  "wcag21a",
  "wcag21aa",
];

async function waitForApplicationReady(
  page: Page,
): Promise<void> {
  await page.waitForFunction(
    () =>
      document.documentElement.dataset
        .wc26Hydrated === "true",
  );
}

async function expectNoWcagViolations(
  page: Page,
  testInfo: TestInfo,
  stage: string,
): Promise<void> {
  const results =
    await new AxeBuilder({
      page,
    })
      .withTags(WCAG_TAGS)
      .analyze();

  await testInfo.attach(
    `${stage}-axe-violations`,
    {
      body: JSON.stringify(
        results.violations,
        null,
        2,
      ),
      contentType:
        "application/json",
    },
  );

  expect(
    results.violations,
    `${stage} contains WCAG A or AA violations`,
  ).toEqual([]);
}

test.describe(
  "dynamic scouting accessibility",
  () => {
    test(
      "keeps the complete scouting journey free of WCAG A and AA violations",
      async ({
        page,
      }, testInfo) => {
        test.setTimeout(120_000);

        await page.goto(
          "/players/978838",
        );

        await waitForApplicationReady(
          page,
        );

        await expect(
          page.getByRole("heading", {
            name: "Michael Olise",
            exact: true,
          }),
        ).toBeVisible({
          timeout: 30_000,
        });

        await expect(
          page.getByText(
            "Average tournament position",
            {
              exact: true,
            },
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        await expectNoWcagViolations(
          page,
          testInfo,
          "player-profile",
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
        ).toBeVisible({
          timeout: 30_000,
        });

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

        await expectNoWcagViolations(
          page,
          testInfo,
          "transfer-analysis",
        );

        await page
          .getByRole("button", {
            name:
              "Find transfer alternatives",
          })
          .click();

        await expect(page).toHaveURL(
          /\/analysis\/978838\/results/,
          {
            timeout: 30_000,
          },
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

        await expect(
          page.getByRole("heading", {
            name: "Immediate impact",
          }),
        ).toBeVisible();

        await expectNoWcagViolations(
          page,
          testInfo,
          "recommendation-results",
        );

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
          {
            timeout: 30_000,
          },
        );

        await expect(
          page.getByLabel(
            "Comparison indicators",
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        await expect(
          page.getByRole("region", {
            name:
              "Playing style radar comparison",
            exact: true,
          }),
        ).toBeVisible({
          timeout: 30_000,
        });

        await expect(
          page.getByRole("status", {
            name:
              "Loading radar comparison",
          }),
        ).toHaveCount(0, {
          timeout: 30_000,
        });

        await expect(
          page.getByRole("status", {
            name:
              "Loading heatmap comparison",
          }),
        ).toHaveCount(0, {
          timeout: 30_000,
        });

        await expectNoWcagViolations(
          page,
          testInfo,
          "player-comparison",
        );
      },
    );
  },
);
