import {
  expect,
  test,
} from "@playwright/test";

test.describe(
  "methodology layout",
  () => {
    test.use({
      viewport: {
        width: 1365,
        height: 900,
      },
    });

    test(
      "keeps the final-role map inside its desktop column",
      async ({ page }, testInfo) => {
        test.skip(
          testInfo.project.name.startsWith(
            "mobile-",
          ),
          "Desktop-only layout regression",
        );

        await page.goto(
          "/en/methodology",
        );

        await page.waitForFunction(
          () =>
            document.documentElement
              .dataset.wc26Hydrated ===
            "true",
        );

        await page
          .getByRole("tab", {
            name: "Forwards",
          })
          .click();

        const visual = page.locator(
          ".final-role-map-visual > div",
        );
        const roleIndex = page.locator(
          ".final-role-map-index",
        );

        await expect(visual).toBeVisible();
        await expect(roleIndex).toBeVisible();

        const visualBox =
          await visual.boundingBox();
        const roleIndexBox =
          await roleIndex.boundingBox();

        expect(visualBox).not.toBeNull();
        expect(roleIndexBox).not.toBeNull();

        if (!visualBox || !roleIndexBox) {
          throw new Error(
            "Final-role map layout bounds are unavailable",
          );
        }

        expect(
          visualBox.x + visualBox.width,
        ).toBeLessThanOrEqual(
          roleIndexBox.x + 1,
        );
      },
    );
  },
);
