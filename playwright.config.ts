import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests/end-to-end",
  timeout: 90000,
  expect: { timeout: 15000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [
    ["list"],
    [
      "json",
      {
        outputFile:
          process.env.NX_TEST_REPORT || "test-results/browser-results.json",
      },
    ],
  ],
  outputDir: process.env.NX_TEST_OUTPUT || "test-results/artifacts",
  use: {
    baseURL: process.env.NX_BASE_URL || "http://127.0.0.1:8876",
    viewport: { width: 1680, height: 1050 },
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
});
