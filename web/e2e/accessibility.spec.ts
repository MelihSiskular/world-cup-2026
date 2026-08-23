import AxeBuilder from "@axe-core/playwright";
import {
  expect,
  test,
  type Page,
} from "@playwright/test";

const publicRoutes = [
  {
    name: "homepage",
    path: "/",
  },
  {
    name: "player discovery",
    path: "/players",
  },
  {
    name: "methodology",
    path: "/methodology",
  },
  {
    name: "system status",
    path: "/status",
  },
] as const;

async function waitForApplicationReady(
  page: Page,
  path: string,
): Promise<void> {
  await page.waitForFunction(
    () =>
      document.documentElement.dataset
        .wc26Hydrated === "true",
  );

  await page
    .locator("main h1")
    .first()
    .waitFor({
      state: "visible",
    });

  if (path === "/players") {
    await page
      .getByRole("searchbox", {
        name: "Search players",
      })
      .waitFor({
        state: "visible",
      });
  }

  if (path === "/status") {
    await page
      .getByRole("button", {
        name: "Refresh status",
      })
      .waitFor({
        state: "visible",
      });
  }
}

test.describe(
  "public accessibility",
  () => {
    for (const route of publicRoutes) {
      test(
        `${route.name} has no WCAG A or AA violations`,
        async ({
          page,
        }, testInfo) => {
          await page.goto(route.path);

          await waitForApplicationReady(
            page,
            route.path,
          );

          const results =
            await new AxeBuilder({
              page,
            })
              .withTags([
                "wcag2a",
                "wcag2aa",
                "wcag21a",
                "wcag21aa",
              ])
              .analyze();

          await testInfo.attach(
            `${route.name}-axe-violations`,
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
          ).toEqual([]);
        },
      );
    }
  },
);
