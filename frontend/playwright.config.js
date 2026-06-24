import { defineConfig, devices } from "@playwright/test";

// Drives the real dev servers (Vite + FastAPI) against real backend/data/,
// not a fixture tree — these are the golden-path flows that already broke
// once in production-shaped data (see CONTEXT.md §5.7, §4.9).
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  webServer: [
    {
      // Reuses the project's own dev-server target instead of duplicating
      // its Python interpreter resolution logic (see Makefile `server`).
      command: "cd .. && make server",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command: "npm run dev",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
