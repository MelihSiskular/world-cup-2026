import { expect, test } from "@playwright/test";

test.describe("WC26 production web foundation", () => {
  test("public application is reachable and exposes the main product navigation", async ({
    page,
  }) => {
    await page.goto("/");

    await expect(page).toHaveTitle(/WC26|Transfer Intelligence/i);

    await expect(page.getByRole("main")).toBeVisible();

    await expect(
      page.getByRole("link", { name: /players/i }).first(),
    ).toBeVisible();

    await expect(
      page.getByRole("link", { name: /methodology/i }).first(),
    ).toBeVisible();
  });

  test("players page is reachable", async ({ page }) => {
    await page.goto("/players");

    await expect(page).toHaveURL(/\/players/);

    await expect(page.getByRole("main")).toBeVisible();
  });

  test("status page is reachable", async ({ page }) => {
    await page.goto("/status");

    await expect(page).toHaveURL(/\/status/);

    await expect(page.getByRole("main")).toBeVisible();
  });
});
