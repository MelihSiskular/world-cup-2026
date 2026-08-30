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

  await expect(
    page.getByRole("main"),
  ).toBeVisible();
}

async function getPathname(
  page: Page,
): Promise<string> {
  return page.evaluate(
    () => window.location.pathname,
  );
}

async function getSearch(
  page: Page,
): Promise<string> {
  return page.evaluate(
    () => window.location.search,
  );
}

async function openMobileNavigationIfNeeded(
  page: Page,
): Promise<void> {
  const openNavigationButton =
    page.getByRole("button", {
      name: "Navigasyonu aç",
      exact: true,
    });

  if (
    await openNavigationButton
      .isVisible()
  ) {
    await openNavigationButton
      .click();
  }
}

test.describe(
  "EN/TR localization routing",
  () => {
    test(
      "uses English as the canonical default locale",
      async ({ page }) => {
        await page.goto("/");

        await waitForApplicationReady(
          page,
        );

        await expect.poll(
          () => getPathname(page),
        ).toBe("/");

        await expect(
          page.locator("html"),
        ).toHaveAttribute(
          "lang",
          "en",
        );

        await expect(
          page.getByRole("heading", {
            level: 1,
            name:
              /Find the right replacement/i,
          }),
        ).toBeVisible();

        await expect(
          page.getByRole("button", {
            name: /Turkish/i,
          }),
        ).toBeVisible();
      },
    );

    test(
      "renders the Turkish locale at its explicit prefix",
      async ({ page }) => {
        await page.goto("/tr");

        await waitForApplicationReady(
          page,
        );

        await expect.poll(
          () => getPathname(page),
        ).toBe("/tr");

        await expect(
          page.locator("html"),
        ).toHaveAttribute(
          "lang",
          "tr",
        );

        await expect(
          page.getByRole("heading", {
            level: 1,
            name:
              /Doğru alternatifi bulun/i,
          }),
        ).toBeVisible();

        await expect(
          page.getByRole("heading", {
            level: 1,
            name:
              /Find the right replacement/i,
          }),
        ).toHaveCount(0);

        await expect(
          page.getByRole("button", {
            name:
              /İngilizce|English/i,
          }),
        ).toBeVisible();
      },
    );

    test(
      "preserves the current route and query while switching locale",
      async ({ page }) => {
        const expectedSearch =
          "?position=M&sort_by=market_value&sort_direction=asc";

        await page.goto(
          `/players${expectedSearch}`,
        );

        await waitForApplicationReady(
          page,
        );

        await expect.poll(
          () => getPathname(page),
        ).toBe("/players");

        await expect.poll(
          () => getSearch(page),
        ).toBe(expectedSearch);

        await page
          .getByRole("button", {
            name: /Turkish/i,
          })
          .click();

        await expect.poll(
          () => getPathname(page),
        ).toBe("/tr/players");

        await expect.poll(
          () => getSearch(page),
        ).toBe(expectedSearch);

        await expect(
          page.locator("html"),
        ).toHaveAttribute(
          "lang",
          "tr",
        );

        const localeGroup =
          page.getByRole("group", {
            name:
              /Language|Dil/i,
          });

        await expect(
          localeGroup.locator(
            'button[aria-pressed="true"] [data-country-code="TUR"]',
          ),
        ).toBeVisible();

        await page
          .getByRole("button", {
            name:
              /İngilizce|English/i,
          })
          .click();

        await expect.poll(
          () => getPathname(page),
        ).toBe("/players");

        await expect.poll(
          () => getSearch(page),
        ).toBe(expectedSearch);

        await expect(
          page.locator("html"),
        ).toHaveAttribute(
          "lang",
          "en",
        );
      },
    );

    test(
      "keeps Turkish navigation inside the locale namespace",
      async ({ page }) => {
        await page.goto(
          "/tr/methodology",
        );

        await waitForApplicationReady(
          page,
        );

        await expect(
          page,
        ).toHaveTitle(
          /Metodoloji/i,
        );

        await expect(
          page.getByRole("heading", {
            level: 1,
            name:
              "Benzerlik bir kanıttır, nihai karar değildir",
          }),
        ).toBeVisible();

        await openMobileNavigationIfNeeded(
          page,
        );

        await page
          .getByRole("link", {
            name: "Kısa Listeler",
            exact: true,
          })
          .first()
          .click();

        await expect.poll(
          () => getPathname(page),
        ).toBe("/tr/shortlists");

        await expect(
          page.locator("html"),
        ).toHaveAttribute(
          "lang",
          "tr",
        );

        await expect(
          page.getByRole("main"),
        ).toBeVisible();
      },
    );
  },
);
