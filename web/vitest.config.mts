import path from "node:path";
import {
  fileURLToPath,
} from "node:url";

import {
  defineConfig,
} from "vitest/config";

const projectRoot =
  path.dirname(
    fileURLToPath(
      import.meta.url,
    ),
  );

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(
        projectRoot,
        "src",
      ),
    },
  },

  test: {
    environment: "jsdom",

    environmentOptions: {
      jsdom: {
        url: "http://localhost:3000",
      },
    },

    setupFiles: [
      "./src/test/setup.ts",
    ],

    include: [
      "src/**/*.test.{ts,tsx}",
    ],

    clearMocks: true,
    mockReset: true,
    restoreMocks: true,
  },
});
