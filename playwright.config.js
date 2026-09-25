import { defineConfig, devices } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL || 'http://127.0.0.1:5176'

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    headless: process.env.HEADED ? false : true,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: process.env.CI
    ? undefined
    : {
        command: 'npm run dev --prefix customer',
        url: BASE_URL,
        reuseExistingServer: true,
        timeout: 120_000,
      },
})
