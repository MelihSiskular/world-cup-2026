import {
  expect,
  test,
  type Page,
} from "@playwright/test";

const PLAYER_NAME =
  "Michael Olise";

const INITIAL_LIST_NAME =
  "Summer 2027 — Creators";

const RENAMED_LIST_NAME =
  "Summer 2027 — Attackers";

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

async function navigateToShortlists(
  page: Page,
): Promise<void> {
  const primaryNavigation =
    page.getByRole(
      "navigation",
      {
        name:
          "Primary navigation",
      },
    );

  if (
    await primaryNavigation
      .isVisible()
  ) {
    await primaryNavigation
      .getByRole("link", {
        name: "Shortlists",
        exact: true,
      })
      .click();

    return;
  }

  const navigationButton =
    page.getByRole(
      "button",
      {
        name:
          "Open navigation",
      },
    );

  await navigationButton.click();

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

  await mobileNavigation
    .getByRole("link", {
      name: "Shortlists",
      exact: true,
    })
    .click();
}

test.describe(
  "shortlist recruitment journey",
  () => {
    test(
      "manages a browser-persisted shortlist across navigation and reload",
      async ({ page }) => {
        test.setTimeout(90_000);

        await page.goto(
          "/players/978838",
        );

        await waitForApplicationReady(
          page,
        );

        await expect(
          page.getByRole(
            "heading",
            {
              name:
                PLAYER_NAME,
              exact: true,
            },
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        const shortlistButton =
          page.getByRole(
            "button",
            {
              name:
                "Add to shortlist",
            },
          );

        await expect(
          shortlistButton,
        ).toBeEnabled({
          timeout: 30_000,
        });

        await shortlistButton.click();

        await page
          .getByRole("textbox", {
            name: "New shortlist",
          })
          .fill(
            INITIAL_LIST_NAME,
          );

        await page
          .getByRole("button", {
            name:
              "Create and add",
          })
          .click();

        const shortlistOptions =
          page.getByRole(
            "region",
            {
              name:
                `Shortlist options for ${PLAYER_NAME}`,
            },
          );

        await expect(
          shortlistOptions.getByRole(
            "status",
          ),
        ).toContainText(
          `${INITIAL_LIST_NAME} created and ${PLAYER_NAME} added.`,
        );

        await expect(
          page.getByRole(
            "button",
            {
              name:
                "Shortlisted (1)",
            },
          ),
        ).toBeVisible();

        await expectNoHorizontalPageOverflow(
          page,
        );

        await navigateToShortlists(
          page,
        );

        await expect(page).toHaveURL(
          /\/shortlists$/,
        );

        await expect(
          page.getByRole(
            "heading",
            {
              name:
                "Shortlist workspace",
            },
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        await expect(
          page.getByRole(
            "heading",
            {
              name:
                INITIAL_LIST_NAME,
            },
          ),
        ).toBeVisible();

        await expect(
          page.getByRole(
            "link",
            {
              name:
                PLAYER_NAME,
            },
          ),
        ).toBeVisible();

        const persistedBeforeReload =
          await page.evaluate(() => {
            const serialized =
              window.localStorage
                .getItem(
                  "wc26.shortlists",
                );

            if (
              serialized === null
            ) {
              return null;
            }

            return JSON.parse(
              serialized,
            ) as {
              version: number;
              lists: Array<{
                name: string;
                entries: Array<{
                  player: {
                    playerId: number;
                  };
                }>;
              }>;
            };
          });

        expect(
          persistedBeforeReload
            ?.version,
        ).toBe(1);

        expect(
          persistedBeforeReload
            ?.lists[0]?.name,
        ).toBe(
          INITIAL_LIST_NAME,
        );

        expect(
          persistedBeforeReload
            ?.lists[0]?.entries[0]
            ?.player.playerId,
        ).toBe(978838);

        await page.reload();

        await waitForApplicationReady(
          page,
        );

        await expect(
          page.getByRole(
            "heading",
            {
              name:
                INITIAL_LIST_NAME,
            },
          ),
        ).toBeVisible({
          timeout: 30_000,
        });

        await expect(
          page.getByRole(
            "link",
            {
              name:
                PLAYER_NAME,
            },
          ),
        ).toBeVisible();

        await page
          .getByRole("button", {
            name: "Rename",
            exact: true,
          })
          .click();

        const renameInput =
          page.getByRole(
            "textbox",
            {
              name:
                `Rename ${INITIAL_LIST_NAME}`,
            },
          );

        await renameInput.fill(
          RENAMED_LIST_NAME,
        );

        await page
          .getByRole("button", {
            name: "Save name",
          })
          .click();

        await expect(
          page.getByRole(
            "heading",
            {
              name:
                RENAMED_LIST_NAME,
            },
          ),
        ).toBeVisible();

        await page
          .getByRole("button", {
            name:
              `Remove ${PLAYER_NAME} from ${RENAMED_LIST_NAME}`,
          })
          .click();

        await expect(
          page.getByRole(
            "link",
            {
              name:
                PLAYER_NAME,
            },
          ),
        ).toHaveCount(0);

        await expect(
          page.getByText(
            "This shortlist is empty",
            {
              exact: true,
            },
          ),
        ).toBeVisible();

        await page
          .getByRole("button", {
            name: "Delete",
            exact: true,
          })
          .click();

        await page
          .getByRole("button", {
            name:
              `Confirm delete ${RENAMED_LIST_NAME}`,
          })
          .click();

        await expect(
          page.getByText(
            "No shortlists yet",
            {
              exact: true,
            },
          ),
        ).toBeVisible();

        const finalPersistedState =
          await page.evaluate(() => {
            const serialized =
              window.localStorage
                .getItem(
                  "wc26.shortlists",
                );

            return serialized === null
              ? null
              : JSON.parse(
                  serialized,
                ) as {
                  lists: unknown[];
                };
          });

        expect(
          finalPersistedState
            ?.lists,
        ).toEqual([]);

        await expectNoHorizontalPageOverflow(
          page,
        );
      },
    );
  },
);
