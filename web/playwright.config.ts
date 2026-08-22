import { defineConfig, devices } from "@playwright/test";

const PRODUCTION_BASE_URL =
  "https://wc26-transfer-intelligence.vercel.app";

const LOCAL_BASE_URL =
  "http://127.0.0.1:3000";

const useLocalServer =
  process.env.WC26_E2E_LOCAL_SERVER === "1";

const baseURL = useLocalServer
  ? LOCAL_BASE_URL
  : process.env.WC26_E2E_BASE_URL ??
    PRODUCTION_BASE_URL;

const vercelAutomationBypassSecret =
  process.env.VERCEL_AUTOMATION_BYPASS_SECRET;

export default defineConfig({
  testDir: "./e2e",

  fullyParallel: true,

  forbidOnly: Boolean(process.env.CI),

  retries: process.env.CI ? 2 : 0,

  workers: process.env.CI ? 1 : undefined,

  reporter: process.env.CI
    ? [["line"], ["html", { open: "never" }]]
    : [["list"], ["html", { open: "never" }]],

  webServer: useLocalServer
    ? [
        {
          command:
            "cd .. && .venv/bin/wc26-api",
          url:
            "http://127.0.0.1:8000/ready",
          reuseExistingServer: false,
          timeout: 120_000,
          stdout: "pipe",
          stderr: "pipe",
        },
        {
          command:
            "npm run start -- --hostname 127.0.0.1 --port 3000",
          url: LOCAL_BASE_URL,
          reuseExistingServer: false,
          timeout: 120_000,
          stdout: "pipe",
          stderr: "pipe",
        },
      ]
    : undefined,

  use: {
    baseURL,
    ...(vercelAutomationBypassSecret
      ? {
          extraHTTPHeaders: {
            "x-vercel-protection-bypass":
              vercelAutomationBypassSecret,
            "x-vercel-set-bypass-cookie": "true",
          },
        }
      : {}),
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

projects: [
  {
    name: "chromium",
    use: {
      ...devices["Desktop Chrome"],
    },
  },
  {
    name: "webkit",
    use: {
      ...devices["Desktop Safari"],
    },
  },
  {
    name: "mobile-chromium",
    use: {
      ...devices["Pixel 5"],
    },
  },
  {
    name: "mobile-webkit",
    use: {
      ...devices["iPhone 12"],
    },
  },
],
});
