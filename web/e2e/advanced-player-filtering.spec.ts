import AxeBuilder from "@axe-core/playwright";
import {
  expect,
  test,
  type Page,
  type TestInfo,
} from "@playwright/test";

import {
  DEFAULT_PLAYER_SEARCH_LIMIT,
} from "@/lib/players/search-config";

const WCAG_TAGS = [
  "wcag2a",
  "wcag2aa",
  "wcag21a",
  "wcag21aa",
];

const FIRST_PAGE_RANGE =
  new RegExp(
    `Showing\\s+1–${DEFAULT_PLAYER_SEARCH_LIMIT}\\s+of\\s+\\d+`,
  );

const SECOND_PAGE_RANGE =
  new RegExp(
    `Showing\\s+${DEFAULT_PLAYER_SEARCH_LIMIT + 1}–${DEFAULT_PLAYER_SEARCH_LIMIT * 2}\\s+of\\s+\\d+`,
  );

async function waitForApplicationReady(
  page: Page,
): Promise<void> {
  await page.waitForFunction(
    () =>
      document.documentElement.dataset
        .wc26Hydrated === "true",
  );

  await expect(
    page.getByRole("searchbox", {
      name: "Search players",
    }),
  ).toBeVisible({
    timeout: 30_000,
  });
}

async function openAdvancedFilters(
  page: Page,
): Promise<void> {
  const toggle =
    page.getByRole("button", {
      name: /^Advanced filters/,
    });

  if (
    await toggle.isVisible()
  ) {
    await expect(
      toggle,
    ).toHaveAttribute(
      "aria-expanded",
      "false",
    );

    await toggle.click();

    await expect(
      toggle,
    ).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  }

  await expect(
    page.getByRole("checkbox", {
      name:
        /^Defender, \d+ players$/,
    }),
  ).toBeVisible({
    timeout: 30_000,
  });
}

function playerResultStatus(
  page: Page,
) {
  return page
    .locator(
      '[role="status"][aria-live="polite"]',
    )
    .filter({
      hasText: /players? found/,
    });
}

async function expectQueryParameter(
  page: Page,
  name: string,
  value: string | null,
): Promise<void> {
  await expect
    .poll(
      () =>
        new URL(
          page.url(),
        ).searchParams.get(
          name,
        ),
    )
    .toBe(value);
}

async function expectNoHorizontalPageOverflow(
  page: Page,
): Promise<void> {
  const dimensions =
    await page.evaluate(
      () => ({
        scrollWidth:
          document.documentElement
            .scrollWidth,
        clientWidth:
          document.documentElement
            .clientWidth,
      }),
    );

  expect(
    dimensions.scrollWidth,
    `Expected no horizontal page overflow: scrollWidth=${dimensions.scrollWidth}, clientWidth=${dimensions.clientWidth}`,
  ).toBeLessThanOrEqual(
    dimensions.clientWidth,
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
      .withTags(
        WCAG_TAGS,
      )
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
  "advanced player filtering",
  () => {
    test(
      "supports filter-only discovery, URL restoration and individual removal",
      async ({
        page,
      }, testInfo) => {
        test.setTimeout(90_000);

        await page.goto(
          "/players",
        );

        await waitForApplicationReady(
          page,
        );

        await openAdvancedFilters(
          page,
        );

        const defender =
          page.getByRole(
            "checkbox",
            {
              name:
                /^Defender, \d+ players$/,
            },
          );

        await defender.check();

        await expectQueryParameter(
          page,
          "position",
          "D",
        );

        const removeDefender =
          page.getByRole(
            "button",
            {
              name:
                "Remove Position: Defender filter",
            },
          );

        await expect(
          removeDefender,
        ).toBeVisible();

        await expect(
          playerResultStatus(
            page,
          ),
        ).toContainText(
          /players found/,
          {
            timeout: 30_000,
          },
        );

        await expect(
          page.getByText(
            FIRST_PAGE_RANGE,
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        await expectNoHorizontalPageOverflow(
          page,
        );

        await page.reload();

        await waitForApplicationReady(
          page,
        );

        await openAdvancedFilters(
          page,
        );

        await expect(
          page.getByRole(
            "checkbox",
            {
              name:
                /^Defender, \d+ players$/,
            },
          ),
        ).toBeChecked();

        const restoredFilter =
          page.getByRole(
            "button",
            {
              name:
                "Remove Position: Defender filter",
            },
          );

        await expect(
          restoredFilter,
        ).toBeVisible();

        await expect(
          playerResultStatus(
            page,
          ),
        ).toContainText(
          /players found/,
          {
            timeout: 30_000,
          },
        );

        await expectNoWcagViolations(
          page,
          testInfo,
          "advanced-player-filtering",
        );

        await restoredFilter.click();

        await expectQueryParameter(
          page,
          "position",
          null,
        );

        await expect(
          restoredFilter,
        ).toHaveCount(0);

        await expect(
          page.getByText(
            "Start with a player name",
            {
              exact: true,
            },
          ),
        ).toBeVisible();

        await expectNoHorizontalPageOverflow(
          page,
        );
      },
    );

    test(
      "preserves sorting and pagination across reloads",
      async ({ page }) => {
        test.setTimeout(90_000);

        await page.goto(
          "/players",
        );

        await waitForApplicationReady(
          page,
        );

        await openAdvancedFilters(
          page,
        );

        await page
          .getByRole("checkbox", {
            name:
              /^Defender, \d+ players$/,
          })
          .check();

        const sortResults =
          page.getByLabel(
            "Sort results",
          );

        await sortResults.selectOption(
          "age:asc",
        );

        await expectQueryParameter(
          page,
          "position",
          "D",
        );

        await expectQueryParameter(
          page,
          "sort_by",
          "age",
        );

        await expectQueryParameter(
          page,
          "sort_direction",
          "asc",
        );

        await expect(
          playerResultStatus(
            page,
          ),
        ).toContainText(
          /players found/,
          {
            timeout: 30_000,
          },
        );

        const nextPage =
          page.getByRole(
            "button",
            {
              name: "Next",
              exact: true,
            },
          );

        await expect(
          nextPage,
        ).toBeEnabled({
          timeout: 30_000,
        });

        await nextPage.click();

        await expectQueryParameter(
          page,
          "offset",
          String(
            DEFAULT_PLAYER_SEARCH_LIMIT,
          ),
        );

        await expect(
          page.getByText(
            "Page 2",
            {
              exact: true,
            },
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        await expect(
          page.getByText(
            SECOND_PAGE_RANGE,
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        await page.reload();

        await waitForApplicationReady(
          page,
        );

        await openAdvancedFilters(
          page,
        );

        await expect(
          page.getByRole(
            "checkbox",
            {
              name:
                /^Defender, \d+ players$/,
            },
          ),
        ).toBeChecked();

        await expect(
          page.getByLabel(
            "Sort results",
          ),
        ).toHaveValue(
          "age:asc",
        );

        await expect(
          page.getByText(
            "Page 2",
            {
              exact: true,
            },
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        await expectQueryParameter(
          page,
          "offset",
          String(
            DEFAULT_PLAYER_SEARCH_LIMIT,
          ),
        );

        await expectNoHorizontalPageOverflow(
          page,
        );
      },
    );
  },
);
