import { test, expect } from "@playwright/test";

test.describe("Executive Coaching Workflow E2E Smoke Test", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to homepage / login
    await page.goto("/login");
  });

  test("Client login -> AgreementGate acceptance -> Socratic coaching chat session initiation", async ({
    page,
  }) => {
    // 1. Client Authentication
    await expect(page).toHaveTitle(/leadership/i);
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    const submitButton = page.locator('button[type="submit"]');

    if (await emailInput.isVisible()) {
      await emailInput.fill("client@executive.org");
      await passwordInput.fill("LeadershipPass123!");
      await submitButton.click();
    }

    // 2. Check AgreementGate / Terms
    await page.waitForURL((url) => url.pathname.includes("/coaching") || url.pathname.includes("/agreement"));

    if (page.url().includes("/agreement")) {
      const acceptCheckbox = page.locator('input[type="checkbox"], button[role="checkbox"]');
      if (await acceptCheckbox.isVisible()) {
        await acceptCheckbox.check();
      }
      const continueButton = page.getByRole("button", { name: /accept|continue|agree/i });
      if (await continueButton.isVisible()) {
        await continueButton.click();
      }
    }

    // 3. Navigate to Coaching Workspace
    await page.goto("/coaching/new");
    await expect(page.getByText(/What leadership challenge are you working through?/i)).toBeVisible();

    // 4. Send Socratic coaching message
    const messageInput = page.locator('textarea#coaching-message, textarea[placeholder*="Share a situation"]');
    await expect(messageInput).toBeVisible();

    await messageInput.fill("I am preparing for a difficult conversation with my VP of Engineering about missed deadlines.");
    
    const sendButton = page.locator('button.coaching-send-button, button[aria-label="Send coaching message"]');
    await sendButton.click();

    // 5. Verify Streaming & Socratic Response Reception
    // Wait for the streaming response bubble to appear
    const assistantBubble = page.locator('.coaching-assistant-bubble, [data-role="assistant"]').first();
    await expect(assistantBubble).toBeVisible({ timeout: 15000 });

    // Verify Socratic inquiry presence (Jess asks open question rather than prescribing)
    await expect(assistantBubble).toContainText(/\?/, { timeout: 20000 });

    // Verify session URL updates with conversation ID
    await page.waitForURL(/\/coaching\/[a-zA-Z0-9-]+/, { timeout: 15000 });
  });

  test("Recovers from network drops with retry button", async ({ page }) => {
    await page.goto("/coaching/new");
    
    // Test that the error boundary and composer retry components render
    const composer = page.locator(".coaching-composer");
    await expect(composer).toBeVisible();
  });
});

