import {
  expect,
  test,
  type Page,
} from "@playwright/test";

type BrowserName =
  | "chromium"
  | "firefox"
  | "webkit";

async function waitForApplicationReady(
  page: Page,
): Promise<void> {
  await page.waitForFunction(
    () =>
      document.documentElement.dataset
        .wc26Hydrated === "true",
  );
}

async function moveFocusForward(
  page: Page,
  browserName: BrowserName,
): Promise<void> {
  await page.keyboard.press(
    browserName === "webkit"
      ? "Alt+Tab"
      : "Tab",
  );
}

async function moveFocusBackward(
  page: Page,
  browserName: BrowserName,
): Promise<void> {
  await page.keyboard.press(
    browserName === "webkit"
      ? "Alt+Shift+Tab"
      : "Shift+Tab",
  );
}

test.describe(
  "keyboard and focus accessibility",
  () => {
    test(
      "moves focus to main content through the skip link",
      async ({
        page,
        browserName,
      }) => {
        await page.goto("/");

        await waitForApplicationReady(
          page,
        );

        const skipLink =
          page.getByRole("link", {
            name: "Skip to content",
          });

        await moveFocusForward(
          page,
          browserName,
        );

        await expect(
          skipLink,
        ).toBeFocused();

        await page.keyboard.press(
          "Enter",
        );

        await expect(page).toHaveURL(
          /#main-content$/,
        );

        await expect(
          page.locator(
            "#main-content",
          ),
        ).toBeFocused();
      },
    );

    test(
      "provides a predictable desktop navigation order",
      async ({
        page,
        browserName,
      }) => {
        await page.setViewportSize({
          width: 1280,
          height: 900,
        });

        await page.goto("/");

        await waitForApplicationReady(
          page,
        );

        const skipLink =
          page.getByRole("link", {
            name: "Skip to content",
          });

        const brandLink =
          page.getByRole("link", {
            name:
              "WC26 Transfer Intelligence home",
          });

        const primaryNavigation =
          page.getByRole(
            "navigation",
            {
              name:
                "Primary navigation",
            },
          );

        const homeLink =
          primaryNavigation.getByRole(
            "link",
            {
              name: "Home",
              exact: true,
            },
          );

        await moveFocusForward(
          page,
          browserName,
        );

        await expect(
          skipLink,
        ).toBeFocused();

        await moveFocusForward(
          page,
          browserName,
        );

        await expect(
          brandLink,
        ).toBeFocused();

        await moveFocusForward(
          page,
          browserName,
        );

        await expect(
          homeLink,
        ).toBeFocused();

        await expect(
          homeLink,
        ).toHaveAttribute(
          "aria-current",
          "page",
        );
      },
    );

    test(
      "operates the mobile navigation entirely by keyboard",
      async ({
        page,
        browserName,
      }) => {
        await page.setViewportSize({
          width: 390,
          height: 844,
        });

        await page.goto("/");

        await waitForApplicationReady(
          page,
        );

        const navigationButton =
          page.locator(
            'button[aria-controls="mobile-navigation"]',
          );

        await expect(
          navigationButton,
        ).toHaveAccessibleName(
          "Open navigation",
        );

        await navigationButton.focus();

        await expect(
          navigationButton,
        ).toBeFocused();

        await page.keyboard.press(
          "Enter",
        );

        await expect(
          navigationButton,
        ).toHaveAttribute(
          "aria-expanded",
          "true",
        );

        await expect(
          navigationButton,
        ).toHaveAccessibleName(
          "Close navigation",
        );

        const mobileNavigation =
          page.getByRole(
            "navigation",
            {
              name:
                "Mobile navigation",
            },
          );

        await expect(
          mobileNavigation,
        ).toBeVisible();

        const mobileHomeLink =
          mobileNavigation.getByRole(
            "link",
            {
              name: "Home",
              exact: true,
            },
          );

        await moveFocusForward(
          page,
          browserName,
        );

        await expect(
          mobileHomeLink,
        ).toBeFocused();

        await moveFocusBackward(
          page,
          browserName,
        );

        await expect(
          navigationButton,
        ).toBeFocused();

        await page.keyboard.press(
          "Enter",
        );

        await expect(
          navigationButton,
        ).toHaveAttribute(
          "aria-expanded",
          "false",
        );

        await expect(
          navigationButton,
        ).toHaveAccessibleName(
          "Open navigation",
        );

        await expect(
          mobileNavigation,
        ).not.toBeVisible();
      },
    );

    test(
      "toggles technical details with standard keyboard controls",
      async ({ page }) => {
        await page.goto("/status");

        await waitForApplicationReady(
          page,
        );

        await expect(
          page.getByRole("button", {
            name:
              "Refresh status",
          }),
        ).toBeVisible({
          timeout: 30_000,
        });

        const details = page
          .locator("details")
          .filter({
            hasText:
              "Technical details",
          });

        const summary =
          details.locator(
            "summary",
          );

        await expect(
          details,
        ).not.toHaveAttribute(
          "open",
          "",
        );

        await summary.focus();

        await expect(
          summary,
        ).toBeFocused();

        await page.keyboard.press(
          "Enter",
        );

        await expect(
          details,
        ).toHaveAttribute(
          "open",
          "",
        );

        await page.keyboard.press(
          "Space",
        );

        await expect(
          details,
        ).not.toHaveAttribute(
          "open",
          "",
        );
      },
    );
    test(
      "honors the reduced-motion preference",
      async ({ page }) => {
        await page.emulateMedia({
          reducedMotion: "reduce",
        });

        await page.goto("/");

        await waitForApplicationReady(
          page,
        );

        const motion =
          await page.evaluate(() => {
            const probe =
              document.createElement(
                "div",
              );

            probe.className =
              "animate-pulse";

            document.body.append(
              probe,
            );

            const probeStyle =
              window.getComputedStyle(
                probe,
              );

            const skipLink =
              document.querySelector<HTMLElement>(
                'a[href="#main-content"]',
              );

            if (skipLink === null) {
              throw new Error(
                "Skip link was not found.",
              );
            }

            const skipLinkStyle =
              window.getComputedStyle(
                skipLink,
              );

            function maximumDurationInMs(
              value: string,
            ): number {
              return Math.max(
                ...value
                  .split(",")
                  .map(
                    (duration) => {
                      const normalized =
                        duration.trim();

                      const amount =
                        Number.parseFloat(
                          normalized,
                        );

                      return normalized.endsWith(
                        "ms",
                      )
                        ? amount
                        : amount * 1000;
                    },
                  ),
              );
            }

            const result = {
              animationDurationMs:
                maximumDurationInMs(
                  probeStyle.animationDuration,
                ),
              animationIterationCount:
                probeStyle.animationIterationCount,
              transitionDurationMs:
                maximumDurationInMs(
                  skipLinkStyle.transitionDuration,
                ),
            };

            probe.remove();

            return result;
          });

        expect(
          motion.animationDurationMs,
        ).toBeLessThanOrEqual(1);

        expect(
          motion.animationIterationCount,
        ).toBe("1");

        expect(
          motion.transitionDurationMs,
        ).toBeLessThanOrEqual(1);
      },
    );
  },
);
