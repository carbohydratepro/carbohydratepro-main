import { expect, test } from "../fixtures/base";

test.describe("レスポンシブ", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("E2E-RESP-001 390px幅で主要導線を操作できる", async ({ page }) => {
    // Spec: docs/e2e/release-test-spec.md#e2e-resp-001
    await page.goto("/top/");

    await expect(page.getByRole("heading", { name: "Life Management" })).toBeVisible();
    await page.getByRole("button", { name: "Toggle navigation" }).click();

    const navigation = page.locator("#navbarSupportedContent");
    await expect(navigation.getByRole("link", { name: "デモ" })).toBeVisible();
    await expect(navigation.getByRole("link", { name: "ログイン" })).toBeVisible();
    await expect(navigation.getByRole("link", { name: "サインアップ" })).toBeVisible();

    await navigation.getByRole("link", { name: "デモ" }).click();
    await expect(page).toHaveURL(/\/demo\/expenses\/?$/);
    await expect(page.getByText("デモモード")).toBeVisible();
  });
});
