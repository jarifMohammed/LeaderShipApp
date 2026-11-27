import { test, expect } from "@playwright/test";

test.describe("Admin Coach Command Center E2E Smoke Test", () => {
  test("Admin login -> navigation to client dossier -> inspecting 360 overview, coach sessions, and X-ray inspector", async ({
    page,
  }) => {
    // 1. Admin Authentication
    await page.goto("/login");
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    const submitButton = page.locator('button[type="submit"]');

    if (await emailInput.isVisible()) {
      await emailInput.fill("admin@executivecoaching.internal");
      await passwordInput.fill("AdminLeadershipPass123!");
      await submitButton.click();
    }

    // 2. Navigate to Client Supervision Dossier
    await page.goto("/dashboard/users/1");

    // 3. Inspect Dossier Tabs
    const tabsList = page.getByRole("tablist");
    await expect(tabsList).toBeVisible({ timeout: 15000 });

    // Tab 1: Client 360° Overview
    const overviewTab = page.getByRole("tab", { name: /360° Overview|Overview/i });
    if (await overviewTab.isVisible()) {
      await overviewTab.click();
      await expect(page.getByText(/Executive Summary|Stakeholder/i)).toBeVisible();
    }

    // Tab 2: Human Coach Sessions
    const sessionsTab = page.getByRole("tab", { name: /Human Coach Sessions|Sessions/i });
    if (await sessionsTab.isVisible()) {
      await sessionsTab.click();
      await expect(page.getByText(/Upload Session|Transcription Status/i)).toBeVisible();
    }

    // Tab 3: Goals & Commitments
    const goalsTab = page.getByRole("tab", { name: /Goals & Commitments|Goals/i });
    if (await goalsTab.isVisible()) {
      await goalsTab.click();
      await expect(page.getByText(/Active Goals|Commitments/i)).toBeVisible();
    }

    // Tab 4: AI Chat & Diagnostics X-Ray
    const chatTab = page.getByRole("tab", { name: /AI Chat Sessions|Diagnostics/i });
    if (await chatTab.isVisible()) {
      await chatTab.click();
      await expect(page.getByText(/Session Messages|Turn Diagnostics/i)).toBeVisible();
    }
  });
});

